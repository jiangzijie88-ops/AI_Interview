from backend.schemas.users import UserCreate, UserLogin, UserNicknameUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import FastAPI, Depends
from backend.database import get_db
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from backend.models.users import User
import os
from datetime import datetime, timedelta, timezone

import jwt
# 读取请求头中的 Bearer token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer





app = FastAPI(title="AI面试平台")

@app.get("/health")
def read_root():
    return {"message": "后端连接成功"}

@app.get("/health/db")
async def database_health(
    # FastAPI 执行 get_db()，将 yield 出来的会话传给 db
    db: AsyncSession = Depends(get_db),
):
    # 等待数据库执行查询；等待期间事件循环可处理其他任务
    result = await db.execute(text("SELECT DATABASE()"))

    # 结果已经取回，读取它不需要再 await
    database_name = result.scalar_one()

    return {
        "status": "ok",
        "database": database_name,
    }



# 创建密码哈希工具，供注册和后续登录复用
password_hasher = PasswordHash.recommended()
# .env 已由 database.py 加载，这里读取签名密钥
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]

@app.post("/users/register",status_code=201)
async def register(
    data:UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # 用户名去除首位空格
    username = data.username.strip()
    # 后端也必须校验，避免绕过页面提交全空格用户名
    if not username:
        raise HTTPException(status_code=422, detail="用户名不能为空")
    # 查询是否已有同名用户
    result = await db.execute(
        select(User).where(User.username == username)
    )
    # 找到用户时返回对象，没用找到时返回none
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="用户名已存在")
    # 密码哈希
    hashed_password = await run_in_threadpool(
        password_hasher.hash,
        data.password,
    )
    # 创建用户对象
    user = User(
        username=username,
        password_hash=hashed_password,
        nickname=data.nickname,
        role="user"
    )
    # 将对象加入会话，此时还没有提交到数据库
    db.add(user)
    try:
        # 提交会话，此时对象才会写入数据库
        await db.commit()
    except IntegrityError as exc:
        # 提交时出错，说明用户名已存在，回滚
        await db.rollback()
        if exc.orig.args[0] == 1062:
            raise HTTPException(
                status_code=400,
                detail="用户名已存在",
                headers={"X-Error-Code": "1062"},
            )
        else:
            raise
    return{
        "message": "注册成功",
        "username": username,
        "nickname":user.nickname,
    }
    


@app.post("/users/login")
async def login(
    data:UserLogin,
    db: AsyncSession = Depends(get_db),
):
    # 与注册保持一致，去除用户名首尾空格
    username = data.username.strip()
    # 根据用户名查询用户
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    # 用户不存在，返回登录失败
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )
    # 验证原始密码与数据库中的哈希是否匹配
    # 密码验证包含计算，放到工作线程中执行
    password_valid = await run_in_threadpool(
        password_hasher.verify,
        data.password,
        user.password_hash,
    )
    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )
    # 令牌保存用户编号和过期时间，不保存密码
    payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    # 使用密钥签名，生成 jwt 令牌
    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm="HS256",
    )
    return {
        "token": token,
        "token_type": "bearer"
    }

# 提取 Authorization 请求头；缺少凭证时由我们统一返回 401
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    # 为各种身份验证失败准备统一响应
    auth_error = HTTPException(
        status_code=401,
        detail="请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 请求没有携带 Bearer token
    if credentials is None:
        raise auth_error

    try:
        # 验证签名、过期时间，并要求包含用户编号和过期时间
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )

        # JWT 中的用户编号是字符串，转换成数据库使用的整数
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        # token 无效、过期或用户编号格式不正确
        raise auth_error

    # 按主键查询用户，确认账号仍然存在
    user = await db.get(User, user_id)

    if user is None:
        raise auth_error

    # 把查到的用户交给需要登录的接口
    return user



@app.get("/users/me")
async def read_me(
    # FastAPI 先验证 token，再把用户对象传进来
    current_user: User = Depends(get_current_user),
):
    # 明确选择返回字段，避免返回密码哈希
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nickname": current_user.nickname,
        "role": current_user.role,
    }


# PATCH 表示更新资源的一部分，这里只更新昵称
@app.patch("/users/me")
async def update_nickname(
    data: UserNicknameUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # current_user 已经过 token 验证，并由数据库查询得到
    # 修改对象属性，SQLAlchemy 会跟踪这次变化
    current_user.nickname = data.nickname.strip()

    # 提交事务，将昵称更新保存到数据库
    await db.commit()

    return {
        "message": "昵称修改成功",
        "nickname": current_user.nickname,
    }


