from backend.schemas.users import UserCreate, UserLogin, UserNicknameUpdate
from backend.services.interview_followup_feedback_manager import ensure_followup_feedback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text,func
from fastapi import FastAPI, Depends,Query,Body,Request
from backend.database import get_db, AsyncSessionLocal
from fastapi import HTTPException
from sqlalchemy import update
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from backend.models.users import User
import os,json
from datetime import datetime, timedelta, timezone
from backend.models.job_roles import JobRole
from backend.models.knowledge_points import KnowledgePoint
from backend.schemas.questions import (
    QuestionCreate,
    QuestionUpdate,
    QuestionStatusUpdate,
)
from backend.models.questions import (
    Question,
    QuestionJobRole,
    QuestionKnowledgePoint,
)
from typing import Literal
from sqlalchemy import delete
import jwt
# 读取请求头中的 Bearer token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Any
from pydantic import ValidationError
from backend.schemas.interview_sessions import (
    InterviewSessionCreate,
    InterviewSessionFinish,
    InterviewSessionEnd,
)
from backend.models.interview_sessions import InterviewSession
from backend.models.interview_questions import QuestionRecord
from backend.models.interview_answers import InterviewAnswer
from backend.schemas.interview_answers import InterviewAnswerCreate
from backend.models.interview_feedback import InterviewFeedback
import logging
from backend.models.interview_followup import InterviewFollowup
from backend.models.interview_followup_answer import InterviewFollowupAnswer
from backend.schemas.interview_followup_answer import FollowupAnswerCreate
from backend.models.interview_followup_feedback import InterviewFollowupFeedback
from backend.services.interview_feedback_manager import ensure_main_feedback
from backend.services.interview_followup_manager import ensure_followup
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from backend.workflows.interview_graph import build_interview_graph
from langgraph.types import Command
from backend.schemas.interview_workflow import (
    WorkflowChoice,
    WorkflowAnswerReady,
)

from backend.models.interview_reports import InterviewReport
from backend.services.interview_report_manager import ensure_report
from backend.models.knowledge_documents import KnowledgeDocument
from backend.schemas.knowledge_documents import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentStatusUpdate,
    KnowledgeDocumentUpdate,
)
from backend.services.document_splitter import split_document
from backend.services.document_index import (
    rebuild_document_index,
    search_documents,
)



# 使用 Uvicorn 的日志通道，在后端终端查看错误
logger = logging.getLogger("uvicorn.error")

# 同一进程中，同一条回答的工作流启动请求依次处理
workflow_locks: dict[str, asyncio.Lock] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 固定使用项目根目录，避免启动目录不同导致数据库文件位置变化
    project_root = Path(__file__).resolve().parent.parent
    runtime_dir = project_root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = runtime_dir / "interview_checkpoints.sqlite"

    # 后端运行期间保持连接打开，关闭后端时自动释放
    async with AsyncSqliteSaver.from_conn_string(
        str(checkpoint_file)
    ) as checkpointer:
        # 将构建好的工作流保存在应用对象上
        app.state.interview_graph = build_interview_graph(checkpointer)
        # 单进程本地运行：上次退出时遗留的生成任务已无法继续
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        async with AsyncSessionLocal() as db:
            # 三张表都有相同的状态、错误说明和更新时间字段
            for model in (
                InterviewFeedback,
                InterviewFollowup,
                InterviewFollowupFeedback,
                InterviewReport,
            ):
                await db.execute(
                    update(model)
                    .where(model.status == "processing")
                    .values(
                        status="failed",
                        error_message="上次生成因服务退出而中断，请重试",
                        updated_at=now,
                    )
                )

            await db.commit()
        # 暂停生命周期初始化，让 FastAPI 开始接收请求
        yield

# tags 用于 /docs 的接口分组，顺序由这里的配置决定
app = FastAPI(
    lifespan=lifespan,
    title="AI面试平台",
    openapi_tags=[
        {"name": "系统检查", "description": "后端服务和数据库连接检查"},
        {"name": "用户管理", "description": "注册、登录和个人信息维护"},
        {"name": "基础分类", "description": "岗位和知识点查询"},
        {"name": "题库管理", "description": "管理员维护、审核和批量导入题目"},
        {"name": "面试练习", "description": "创建练习、查询历史和读取当前题目"},
        {"name": "回答提交", "description": "保存练习回答和识别重复提交"},
        {"name": "AI点评", "description": "生成、查询和重试单题点评"},
        {"name": "AI追问", "description": "生成、查询追问及后续作答"},
    ],
)

@app.get("/health", tags=["系统检查"], summary="检查后端服务")
def read_root():
    return {"message": "后端连接成功"}

@app.get("/health/db", tags=["系统检查"], summary="检查数据库连接")
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

@app.post("/users/register", status_code=201, tags=["用户管理"], summary="注册账号")
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
    


@app.post("/users/login", tags=["用户管理"], summary="登录并获取 token")
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



@app.get("/users/me", tags=["用户管理"], summary="查看我的信息")
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
@app.patch("/users/me", tags=["用户管理"], summary="修改我的昵称")
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



@app.get("/job_roles", tags=["基础分类"], summary="查询岗位列表")
async def list_job_roles(db: AsyncSession = Depends(get_db)):
    # 查询所有岗位,按id从小到大排序
    result = await db.execute(select(JobRole).order_by(JobRole.id))
    # 取出所有岗位对象
    job_roles = result.scalars().all()
    # 将岗位对象转换为列表中的字典
    return [{"id": job_role.id, "name": job_role.name} for job_role in job_roles]

@app.get("/knowledge_points", tags=["基础分类"], summary="查询知识点列表")
async def list_knowledge_points(db: AsyncSession = Depends(get_db)):
    # 查询所有知识点,按id从小到大排序
    result = await db.execute(select(KnowledgePoint).order_by(KnowledgePoint.id))
    # 取出所有知识点对象
    knowledge_points = result.scalars().all()
    # 将知识点对象转换为列表中的字典
    return [{"id": knowledge_point.id, "name": knowledge_point.name} for knowledge_point in knowledge_points]


# 先验证登陆身份，再检查管理员角色
async def get_admin_user(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限",
        )
    return current_user



# 通用业务函数：校验并保存一道题
async def save_question(
    data: QuestionCreate,
    db: AsyncSession,
):
    # 去掉重复编号
    job_ids = set(data.job_role_ids)
    knowledge_ids = set(data.knowledge_point_ids)
    # 查询这些岗位编号中，实际存在的编号
    result = await db.execute(
        select(JobRole.id).where(JobRole.id.in_(job_ids))
    )
    existing_job_ids = set(result.scalars().all())
    if job_ids != existing_job_ids:
        raise HTTPException(status_code=400, detail="存在无效的岗位编号")
    # 检查知识点编号是否全部存在
    result = await db.execute(
        select(KnowledgePoint.id).where(KnowledgePoint.id.in_(knowledge_ids))
    )
    existing_point_ids = set(result.scalars().all())
    if knowledge_ids != existing_point_ids:
        raise HTTPException(status_code=400, detail="存在无效的知识点编号")

    #  创建题目，固定从草稿、修订号1开始
    question = Question(
        content=data.content,
        difficulty=data.difficulty,
        reference_points=data.reference_points,
        common_mistakes=data.common_mistakes,
        followup_direction=data.followup_direction,
        sources=data.sources,
        status="draft",
        revision=1,
    )
    db.add(question)
    # 执行题目插入，获得数据库生成的ID，但暂时不提交
    await db.flush()
    # 保存题目与岗位的关联
    for job_id in job_ids:
        db.add(QuestionJobRole(question_id=question.id, job_role_id=job_id))
    # 保存题目与知识点的关联
    for point_id in knowledge_ids:
        db.add(QuestionKnowledgePoint(question_id=question.id, knowledge_point_id=point_id))
    # 题目和全部关联一起提交
    await db.commit()
    return {"message": "题目创建成功", "id": question.id,"status":question.status,"revision":question.revision}

# HTTP接口：负责接受请求和检查管理员身份
@app.post("/questions", status_code=201, tags=["题库管理"], summary="新增题目草稿")
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    # 把校验后的数据和数据库会话交给业务函数
    return await save_question(data, db)



# 管理员查询题目列表
@app.get("/questions", tags=["题库管理"], summary="分页筛选题目")
async def list_questions(
    # 页码从 1 开始，每页默认 10 条，最多 50 条
    page:int = Query(default=1, ge=1),
    page_size:int = Query(default=10, ge=1, le=50),
    # 不填写时，不按该条件筛选
    difficulty:Literal["basic","advanced"] | None = None,
    status:Literal["draft","approved","disabled"] | None = None,
    # 可选筛选条件；不传时不限制岗位或知识点
    job_role_id: int | None = Query(default=None, ge=1),
    knowledge_point_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    # 收集筛选条件
    conditions = []
    if difficulty is not None:
        conditions.append(Question.difficulty == difficulty)
    if status is not None:
        conditions.append(Question.status == status)
    if job_role_id is not None:
        # 找到与指定岗位关联的题目编号
        matching_question_ids = select(QuestionJobRole.question_id).where(QuestionJobRole.job_role_id == job_role_id)
        # 只保留编号属于这些结果的题目
        conditions.append(Question.id.in_(matching_question_ids))
    if knowledge_point_id  is not None:
        # 找到与指定知识点关联的题目编号
        matching_question_ids = select(QuestionKnowledgePoint.question_id).where(QuestionKnowledgePoint.knowledge_point_id == knowledge_point_id)
        # 只保留编号属于这些结果的题目
        conditions.append(Question.id.in_(matching_question_ids))

    # 统计符合条件的题目总数，不受分页影响
    total = await db.scalar(
        select(func.count()).select_from(Question).where(*conditions)
    )
    # 查询当前页，从ID排序，按顺序明确
    result = await db.execute(
        select(Question).where(*conditions).order_by(Question.id).offset((page-1)*page_size).limit(page_size)
    )
    questions = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": question.id,
                "content": question.content,
                "difficulty": question.difficulty,
                "status": question.status,
                "revision": question.revision,
            } for question in questions
        ]
    }


# 管理员查看指定题目的完整信息
@app.get("/questions/{question_id}", dependencies=[Depends(get_admin_user)], tags=["题库管理"], summary="查看题目详情")
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
):
    # 按主键查询题目
    question = await db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    # 通过关联表，查询这道题使用的岗位
    result = await db.execute(
        select(JobRole).join(QuestionJobRole,JobRole.id == QuestionJobRole.job_role_id)
        .where(QuestionJobRole.question_id == question_id)
        .order_by(JobRole.id)
    )
    job_roles = result.scalars().all()
    # 通过关联表，查询这道题考的知识点
    result = await db.execute(
        select(KnowledgePoint).join(QuestionKnowledgePoint,KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id)
        .where(QuestionKnowledgePoint.question_id == question_id)
        .order_by(KnowledgePoint.id)
    )
    knowledge_points = result.scalars().all()
    return {
        "id": question.id,
        "content": question.content,
        "difficulty": question.difficulty,
        "reference_points": question.reference_points,
        "common_mistakes": question.common_mistakes,
        "followup_direction": question.followup_direction,
        "sources": question.sources,
        "status": question.status,
        "revision": question.revision,
        "job_roles": [{"id": job.id, "name": job.name}for job in job_roles],
        "knowledge_points": [{"id": point.id, "name": point.name} for point in knowledge_points],
    }


# 编辑已有题目
@app.put("/questions/{question_id}", dependencies=[Depends(get_admin_user)], tags=["题库管理"], summary="编辑题目内容及关联")
async def update_question(
    question_id: int,
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
):
    # 找到要修改的题目
    question = await db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    # 去重
    job_ids = set(data.job_role_ids)
    knowledge_ids = set(data.knowledge_point_ids)
    # 检查岗位是否全部存在
    result = await db.execute(
        select(JobRole.id).where(JobRole.id.in_(job_ids))
    )
    if job_ids != set(result.scalars().all()):
        raise HTTPException(status_code=400, detail="存在无效的岗位编号")
    # 检查知识点是否全部存在
    result = await db.execute(
        select(KnowledgePoint.id).where(KnowledgePoint.id.in_(knowledge_ids))
    )
    if knowledge_ids != set(result.scalars().all()):
        raise HTTPException(status_code=400, detail="存在无效的知识点编号")
    # 更新题目信息
    question.content = data.content
    question.reference_points = data.reference_points
    question.difficulty = data.difficulty
    question.common_mistakes = data.common_mistakes
    question.followup_direction = data.followup_direction
    question.sources = data.sources
    # 编辑后回到草稿，需要重新审核
    question.status = "draft"
    question.revision += 1
    # 删除原有岗位关联,不删除岗位本身
    await db.execute(
        delete(QuestionJobRole).where(QuestionJobRole.question_id == question_id)
    )
    # 删除原有知识点关联,不删除知识点本身
    await db.execute(
        delete(QuestionKnowledgePoint).where(QuestionKnowledgePoint.question_id == question_id)
    )
    # 确保旧关联已删除，再添加新的关联
    await db.flush()
    for job_id in job_ids:
        db.add(QuestionJobRole(question_id=question_id, job_role_id=job_id))
    for knowledge_id in knowledge_ids:
        db.add(QuestionKnowledgePoint(question_id=question_id, knowledge_point_id=knowledge_id))
    # 题目修改、旧关联删除、新关联添加，一起提交
    await db.commit()
    return{
        "message": "题目修改成功",
        "id": question_id,
        "status": question.status,
        "revision": question.revision,
    }


# 只有管理员可以改变题目状态
@app.patch("/questions/{question_id}/status", dependencies=[Depends(get_admin_user)], tags=["题库管理"], summary="审核、停用或退回草稿")
async def update_question_status(
    question_id: int,
    data: QuestionStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    # 查找要操作的题目
    question = await db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    # 状态实际发生变化时才保存，避免重复操作增加修订号
    if question.status != data.status:
        question.status = data.status
        question.revision += 1
        await db.commit()
    return{
        "message": "题目状态修改成功",
        "id": question_id,
        "status": question.status,
        "revision": question.revision,
    }


@app.post(
    "/questions/import",
    dependencies=[Depends(get_admin_user)],
    tags=["题库管理"],
    summary="批量导入题目草稿",
)
async def import_questions(
    # 请求体直接是 JSON 列表，一次接收 1～100 道
    items: list[Any] = Body(min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    results = []
    success_count = 0

    # 从 1 开始编号，方便对照文件里的第几道题
    for index, item in enumerate(items, start=1):
        try:
            # 使用与单条新增相同的规则校验当前题目
            data = QuestionCreate.model_validate(item)

            # 保存函数内部会提交当前题目及其关联
            saved = await save_question(data, db)

            results.append({
                "index": index,
                "success": True,
                "id": saved["id"],
            })
            success_count += 1

        except ValidationError as exc:
            # 格式错误时还没有写入当前题目
            # 仅返回字段位置和描述，不返回原始输入等附加信息
            errors = [
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                }
                for error in exc.errors()
            ]
            results.append({
                "index": index,
                "success": False,
                "errors": errors,
            })

        except HTTPException as exc:
            # 保存函数发现岗位或知识点不存在等业务错误
            await db.rollback()
            results.append({
                "index": index,
                "success": False,
                "error": exc.detail,
            })

        except SQLAlchemyError:
            # 数据库写入失败，回滚当前题目，不撤销已提交的其他题目
            await db.rollback()
            results.append({
                "index": index,
                "success": False,
                "error": "数据库操作失败，请检查服务端日志和表结构",
            })

    return {
        "total": len(items),
        "success_count": success_count,
        "failed_count": len(items) - success_count,
        "results": results,
    }


@app.post("/interview_sessions", status_code=201, tags=["面试练习"], summary="创建面试练习")
async def create_interview_session(
    data: InterviewSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1.检查岗位是否存在
    job = await db.get(JobRole, data.job_role_id)
    if job is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    # 2.检查用户选择的知识点，空列表表示不限制
    point_ids = set(data.knowledge_point_ids)
    result = await db.execute(
        select(KnowledgePoint)
        .where(KnowledgePoint.id.in_(point_ids))
        .order_by(KnowledgePoint.id)
        )
    selected_points = result.scalars().all()
    if point_ids != {point.id for point in selected_points}:
        raise HTTPException(status_code=404, detail="知识点不存在")
    # 3.必须满足：已审核、指定难度、使用指定岗位
    conditions = [
        Question.status == "approved",
        Question.difficulty == data.difficulty,
        Question.id.in_(select(QuestionJobRole.question_id).where(QuestionJobRole.job_role_id == job.id)),
    ]
    # 选择了知识点时，至少匹配其中一个
    if point_ids: 
        conditions.append(
            Question.id.in_(
                select(QuestionKnowledgePoint.question_id).where(
                    QuestionKnowledgePoint.knowledge_point_id.in_(point_ids))))
    # 4.题目不足时直接返回，不创建练习
    available_count = await db.scalar(
        select(func.count()).select_from(
            Question).where(*conditions))
    if available_count < data.question_count:
        raise HTTPException(
            status_code=400, 
            detail={"message":"题目不足",
                    "available_count": available_count,
                    "required_count": data.question_count,
            }
        )
    # 5.查当前用户每道题最近被安排的时间
    last_used = (
        select(
            QuestionRecord.question_id,
            func.max(InterviewSession.started_at).label("last_used_at"),
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(InterviewSession.user_id == current_user.id)
        .group_by(QuestionRecord.question_id)
        .subquery()
    )
    # MySQL 升序时 NULL 排在前面：未安排过的优先，其次较早的
    result = await db.execute(
        select(Question)
        .outerjoin(last_used, Question.id == last_used.c.question_id)
        .where(*conditions)
        .order_by(last_used.c.last_used_at.asc(), func.rand())
        .limit(data.question_count)
    )
    questions = result.scalars().all()
    # 6. 创建练习，用户编号来自登录身份
    session = InterviewSession(
        user_id=current_user.id,
        job_role_id=job.id,
        difficulty=data.difficulty,
        question_count=data.question_count,
        current_position=1,
        status="in_progress",
        revision=1,
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        config_snapshot={
            "job_role_id": job.id,
            "job_role_name": job.name,
            "difficulty": data.difficulty,
            "question_count": data.question_count,
            "knowledge_points": [
                {"id": point.id, "name": point.name}
                for point in selected_points
            ],
        },
    )
    db.add(session)
    await db.flush()

    # 7. 按本次选题顺序保存快照
    records = []

    for position, question in enumerate(questions, start=1):
        # 保存题目全部关联知识点，不只是用户筛选的知识点
        result = await db.execute(
            select(KnowledgePoint)
            .join(
                QuestionKnowledgePoint,
                KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id,
            )
            .where(QuestionKnowledgePoint.question_id == question.id)
            .order_by(KnowledgePoint.id)
        )
        points = result.scalars().all()

        record = QuestionRecord(
            session_id=session.id,
            question_id=question.id,
            position=position,
            question_revision=question.revision,
            content=question.content,
            reference_points=question.reference_points,
            common_mistakes=question.common_mistakes,
            followup_direction=question.followup_direction,
            sources=question.sources,
            knowledge_points_snapshot=[
                {"id": point.id, "name": point.name}
                for point in points
            ],
        )
        db.add(record)
        records.append(record)

    # 8.练习和全部快照一起提交
    await db.commit()
    # 9.只返回第一道题允许展示的信息，不返回参考答案
    first = records[0]
    return {
        "id": session.id,
        "status": session.status,
        "question_count": session.question_count,
        "current_position": session.current_position,
        "current_question": {
            "id": first.id,
            "position": first.position,
            "content": first.content,
        }
    }


@app.get("/interview_sessions/{session_id}/current", tags=["面试练习"], summary="读取指定题目及全部作答状态")
async def get_current_interview_question(
    session_id: int,
    position: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 先检查练习归属；页面选择题号不会改变数据库中的练习状态
    session = await db.scalar(select(InterviewSession).where(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ))
    if session is None:
        raise HTTPException(status_code=404, detail="练习不存在")
    result = await db.execute(
        select(QuestionRecord, InterviewAnswer)
        .outerjoin(InterviewAnswer, InterviewAnswer.question_record_id == QuestionRecord.id)
        .where(QuestionRecord.session_id == session.id)
        .order_by(QuestionRecord.position)
    )
    rows = result.all()
    selected = next((row for row in rows if row[0].position == position), None)
    if selected is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    question, answer = selected
    # 仅返回题目和用户回答，不暴露参考要点
    return {
        "id": session.id,
        "status": session.status,
        "question_count": session.question_count,
        "revision": session.revision,
        "selected_position": position,
        "questions": [
            {"id": q.id, "position": q.position, "answered": a is not None}
            for q, a in rows
        ],
        "answered_count": sum(a is not None for q, a in rows),
        "current_question": {"id": question.id, "position": question.position, "content": question.content},
        "current_answer": {"id": answer.id, "content": answer.content} if answer else None,
    }


@app.get("/interview_sessions", tags=["面试练习"], summary="分页查询我的练习")
async def list_interview_sessions(
    # 分页参数
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),

    # 不填写时，不限制岗位或状态
    job_role_id: int | None = Query(default=None, ge=1),
    status: Literal["in_progress", "completed", "ended_early"] | None = None,

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 用户归属是必需条件，不能根据前端传来的用户编号查询
    conditions = [
        InterviewSession.user_id == current_user.id
    ]

    if job_role_id is not None:
        conditions.append(
            InterviewSession.job_role_id == job_role_id
        )

    if status is not None:
        conditions.append(
            InterviewSession.status == status
        )

    # 统计符合条件的练习数量
    total = await db.scalar(
        select(func.count())
        .select_from(InterviewSession)
        .where(*conditions)
    )

    # 新创建的练习排在前面，ID 用于同一时间下的稳定排序
    result = await db.execute(
        select(InterviewSession)
        .where(*conditions)
        .order_by(
            InterviewSession.started_at.desc(),
            InterviewSession.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    sessions = result.scalars().all()

    # 只返回列表需要的信息，不返回题目和参考答案
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": session.id,
                "job_role_id": session.job_role_id,
                "job_role_name": session.config_snapshot["job_role_name"],
                "difficulty": session.difficulty,
                "question_count": session.question_count,
                "current_position": session.current_position,
                "status": session.status,

                # 数据库按 UTC 保存，这里给返回值补上时区标记
                "started_at": session.started_at.replace(
                    tzinfo=timezone.utc
                ),
                "ended_at": (
                    session.ended_at.replace(tzinfo=timezone.utc)
                    if session.ended_at is not None
                    else None
                ),
            }
            for session in sessions
        ],
    }


@app.post("/interview_sessions/{session_id}/answers", tags=["回答提交"], summary="提交指定题目的回答")
async def submit_interview_answer(
    session_id: int,
    data: InterviewAnswerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1.查询自己的练习，并锁定这条练习记录
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        ).with_for_update()
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404,detail="练习不存在")
    # 2.确认提交的题目快照属于这次练习
    result = await db.execute(
        select(QuestionRecord)
        .where(QuestionRecord.session_id == session_id,
            QuestionRecord.id == data.question_record_id,
        )
    )
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=409,detail="题目不存在")
    # UUID 转为数据库字符串
    submission_id = str(data.submission_id)
    # 3.检查这道题是否已经有正式回答
    # 锁定读取，确保能看到其他请求刚提交的记录
    result = await db.execute(
        select(InterviewAnswer)
        .where(InterviewAnswer.question_record_id == question.id)
        .with_for_update()
    )
    existing_answer = result.scalar_one_or_none()
    if existing_answer is not None:
        # 相同标识，相同内容，表示上一次提交的重试
        if(
            existing_answer.submission_id == submission_id
            and existing_answer.content == data.content
        ):
            return{
                "message": "回答已保存",
                "answer_id": existing_answer.id,
                "revision":session.revision,
                "replayed": True,
            }
        # 不允许标识符再次作答，也不允许同标识符修改内容
        raise HTTPException(status_code=409,detail="题目已回答")
    # 4.允许回答本次练习中的任意题，但练习必须进行中且版本一致
    if session.status != "in_progress":
        raise HTTPException(status_code=409,detail="练习已结束")
    if data.revision != session.revision:
        raise HTTPException(status_code=409,detail="练习状态已更新，请重新读取当前题目")
    # 5.创建回答记录，保留原始文本
    answer = InterviewAnswer(
        question_record_id=question.id,
        submission_id=submission_id,
        content=data.content,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(answer)
    # 回答已提交，状态版本改变，但题目位置保持不变
    session.revision += 1
    try:
        # 回答和版本更新一起提交
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409,detail="提交标识或题目回答发生冲突，请重新查询")
    return {
        "message": "回答已保存",
        "answer_id": answer.id,
        "revision": session.revision,
        "replayed": False,
    }



@app.post("/interview_sessions/{session_id}/finish", tags=["面试练习"], summary="完成本次练习")
async def finish_interview_session(
    session_id: int,
    data: InterviewSessionFinish,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        ).with_for_update()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="练习不存在")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="练习已结束")
    if data.revision != session.revision:
        raise HTTPException(status_code=409, detail="练习状态已更新，请重新读取")
    answered_count = await db.scalar(
        select(func.count()).select_from(InterviewAnswer)
        .join(QuestionRecord, InterviewAnswer.question_record_id == QuestionRecord.id)
        .where(QuestionRecord.session_id == session.id)
    )
    unanswered_count = session.question_count - answered_count
    # 有未作答题时必须确认；不自动提交页面中的草稿
    if unanswered_count and not data.confirm_unanswered:
        raise HTTPException(status_code=409, detail={
            "message": "还有未作答题目，请确认后结束",
            "unanswered_count": unanswered_count,
        })
    session.status = "completed" if unanswered_count == 0 else "ended_early"
    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.revision += 1
    await db.commit()
    return {"id": session.id, "status": session.status, "revision": session.revision,
            "answered_count": answered_count, "unanswered_count": unanswered_count}


@app.post(
    "/interview_sessions/{session_id}/end",
    tags=["面试练习"],
    summary="提前结束练习",
)
async def end_interview_session(
    session_id: int,
    data: InterviewSessionEnd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 查询自己的练习，并锁定记录，避免与提交回答、下一题同时修改
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
        .with_for_update()
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="练习不存在")

    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="练习已结束")

    if data.revision != session.revision:
        raise HTTPException(
            status_code=409,
            detail="练习状态已更新，请重新读取当前题目",
        )

    # 保留当前位置和已有回答，只修改结束状态和时间
    session.status = "ended_early"
    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.revision += 1

    await db.commit()

    return {
        "id": session.id,
        "status": session.status,
        "current_position": session.current_position,
        "revision": session.revision,
    }


@app.get(
    "/interview_answers/{answer_id}/feedback",
    tags=["AI点评"],
    summary="查询回答的点评",
)
async def get_interview_feedback(
    answer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 从回答关联到题目快照，再关联到练习，检查回答归属
    answer = await db.scalar(
        select(InterviewAnswer)
        .join(QuestionRecord, InterviewAnswer.question_record_id == QuestionRecord.id)
        .join(InterviewSession, QuestionRecord.session_id == InterviewSession.id)
        .where(
            InterviewAnswer.id == answer_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    if answer is None:
        raise HTTPException(status_code=404, detail="回答不存在")
    # 查找这条回答对应的点评记录
    feedback = await db.scalar(
        select(InterviewFeedback)
        .where(InterviewFeedback.answer_id == answer_id)
    )
    if feedback is None:
        return{
            "answer_id": answer_id,
            "status": "not_generated",
            "feedback_content":None,
            "error_message": None,
        }
    return {
        "answer_id": answer_id,
        "status": feedback.status,
        "feedback_content": feedback.feedback_content,
        "error_message": feedback.error_message,
    }


@app.post(
    "/interview_answers/{answer_id}/feedback",
    tags=["AI点评"],
    summary="生成回答的点评",
)
async def generate_interview_feedback(
    answer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 接口负责获取登录用户和数据库会话，再交给业务函数处理
    return await ensure_main_feedback(
        db = db,
        answer_id = answer_id,
        user_id = current_user.id,
        )
    

@app.get(
    "/interview_answers/{answer_id}/followup",
    tags=["AI追问"],
    summary="查询主回答对应的追问",
)
async def get_interview_followup(
    answer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):  
    # 先确认这条主回答属于当前登录用户
    answer = await db.scalar(
        select(InterviewAnswer)
        .join(QuestionRecord, InterviewAnswer.question_record_id == QuestionRecord.id)
        .join(InterviewSession, QuestionRecord.session_id == InterviewSession.id)
        .where(
            InterviewAnswer.id == answer_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    if answer is None:
        raise HTTPException(status_code=404, detail="回答不存在")
    # 根据主回答编号查找编号
    followup = await db.scalar(
        select(InterviewFollowup)
        .where(InterviewFollowup.parent_answer_id == answer_id)
    )
    if followup is None:
        return{
            "parent_answer_id": answer_id,
            "followup_id": None,
            "status": "not_generated",
            "question_content":None,
            "error_message": None,
            "followup_answer": None,

        }
    # 根据追问编号查找已提交的回答
    followup_answer = await db.scalar(
        select(InterviewFollowupAnswer).where(
            InterviewFollowupAnswer.followup_id == followup.id
        )
    )
    return {
        "parent_answer_id": answer_id,
        "followup_id": followup.id,
        "status": followup.status,
        # 只有成功生成的问题才展示
        "question_content": (
            followup.question_content
            if followup.status == "succeeded"
            else None
        ),
        "error_message": followup.error_message,
                # 未回答时为 null；已回答时返回编号和原文
        "followup_answer": (
            {
                "id": followup_answer.id,
                "content": followup_answer.content,
            }
            if followup_answer is not None
            else None
        ),
    }



@app.post(
    "/interview_answers/{answer_id}/followup",
    tags=["AI追问"],
    summary="生成追问，失败时可重试",
)
async def create_interview_followup(
    answer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 接口提供登录用户和数据库会话，业务函数负责生成或复用追问
    return await ensure_followup(
        db=db,
        answer_id=answer_id,
        user_id=current_user.id,
    )
    


@app.post(
    "/interview_followups/{followup_id}/answers",
    tags=["AI追问"],
    summary="提交追问回答",
)
async def submit_followup_answer(
    followup_id: int,
    data: FollowupAnswerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 沿关联查找追问，检查归属，并锁定记录
    followup = await db.scalar(
        select(InterviewFollowup)
        .join(
            InterviewAnswer,
            InterviewFollowup.parent_answer_id == InterviewAnswer.id,
        )
        .join(
            QuestionRecord,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(
            InterviewFollowup.id == followup_id,
            InterviewSession.user_id == current_user.id,
        )
        .with_for_update()
    )

    if followup is None:
        raise HTTPException(status_code=404, detail="追问不存在")

    submission_id = str(data.submission_id)

    # 2. 查询是否已有正式回答
    existing = await db.scalar(
        select(InterviewFollowupAnswer)
        .where(InterviewFollowupAnswer.followup_id == followup.id)
        .with_for_update()
    )

    if existing is not None:
        # 同一标识、同一内容：返回原结果，不重复保存
        if (
            existing.submission_id == submission_id
            and existing.content == data.content
        ):
            return {
                "followup_id": followup.id,
                "followup_answer_id": existing.id,
                "message": "追问回答已保存",
                "replayed": True,
            }

        raise HTTPException(
            status_code=409,
            detail="这道追问已经回答，不能重复提交或修改",
        )

    # 3. 只有成功生成的问题才允许作答
    if followup.status != "succeeded":
        raise HTTPException(
            status_code=409,
            detail="追问尚未成功生成，暂时不能回答",
        )

    # 4. 保存用户原始回答
    answer = InterviewFollowupAnswer(
        followup_id=followup.id,
        submission_id=submission_id,
        content=data.content,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(answer)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="提交标识或追问回答发生冲突，请重新查询",
        )

    return {
        "followup_id": followup_id,
        "followup_answer_id": answer.id,
        "message": "追问回答已保存",
        "replayed": False,
    }


@app.get(
    "/interview_followup_answers/{followup_answer_id}/feedback",
    tags=["AI追问"],
    summary="查询追问回答的点评",
)
async def get_followup_feedback(
    followup_answer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 沿关联检查这条追问回答是否属于当前用户
    answer = await db.scalar(
        select(InterviewFollowupAnswer)
        .join(
            InterviewFollowup,
            InterviewFollowupAnswer.followup_id == InterviewFollowup.id,
        )
        .join(
            InterviewAnswer,
            InterviewFollowup.parent_answer_id == InterviewAnswer.id,
        )
        .join(
            QuestionRecord,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(
            InterviewFollowupAnswer.id == followup_answer_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if answer is None:
        raise HTTPException(status_code=404, detail="追问回答不存在")

    # 根据追问回答编号查询点评
    feedback = await db.scalar(
        select(InterviewFollowupFeedback).where(
            InterviewFollowupFeedback.followup_answer_id == answer.id
        )
    )

    if feedback is None:
        return {
            "followup_answer_id": answer.id,
            "status": "not_generated",
            "feedback_content": None,
            "error_message": None,
        }

    return {
        "followup_answer_id": answer.id,
        "status": feedback.status,
        "feedback_content": feedback.feedback_content,
        "error_message": feedback.error_message,
    }


@app.post(
    "/interview_followup_answers/{followup_answer_id}/feedback",
    tags=["AI追问"],
    summary="生成追问回答的点评，失败时可重试",
)
async def create_followup_feedback(
    followup_answer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 接口提供回答编号、登录用户和数据库会话
    return await ensure_followup_feedback(
        db=db,
        followup_answer_id=followup_answer_id,
        user_id=current_user.id,

    )
    



@app.post(
    "/interview_sessions/{session_id}/answers/{answer_id}/workflow/start",
    tags=["AI追问"],
    summary="启动或读取一道主问题的工作流",
)
async def start_interview_workflow(
    session_id: int,
    answer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 获取后端启动时创建的共享工作流
    interview_graph = request.app.state.interview_graph
    # 先检查回答、练习、当前用户的关联，避免读取别人的工作流
    owned_answer_id = await db.scalar(
        select(InterviewAnswer.id)
        .join(
            QuestionRecord,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(
            InterviewAnswer.id == answer_id,
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    # 未查到说明回答不存在，或不属于指定练习和当前用户
    if owned_answer_id is None:
        raise HTTPException(status_code=404, detail="回答不存在")
    # 使用后端验证的用户编号构造工作流编号
    thread_id = f"user-{current_user.id}-session-{session_id}-answer-{answer_id}"
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    # 每个工作流使用自己的锁，不阻塞其他回答的启动
    lock = workflow_locks.setdefault(thread_id, asyncio.Lock())

    async with lock:
        # 读取当前进程保存的检查点
        snapshot = await interview_graph.aget_state(config)

        # 没有检查点时首次启动
        # 业务失败且本次执行已经结束时，允许从入口重新尝试
        retry_failed = (
            snapshot.values.get("stage") == "failed"
            and not snapshot.next
        )
        # 节点抛出异常时，检查点可能保留待执行节点和错误信息
        retry_node_error = any(
            task.error is not None
            for task in snapshot.tasks
        )

        if not snapshot.values or retry_failed:
            await interview_graph.ainvoke(
                {
                    "user_id": current_user.id,
                    "session_id": session_id,
                    "answer_id": answer_id,
                    "stage": "loading",
                },
                config=config,
            )
        elif retry_node_error:
            # 不传入新的初始状态，从检查点重试未完成的节点
            await interview_graph.ainvoke(
                None,
                config=config,
            )

        # 无论首次启动、失败重试，还是只查询，都读取最新检查点
        snapshot = await interview_graph.aget_state(config)

        # 将暂停对象转换为前端容易使用的普通字典
        interrupts = [
            {
                "id": item.id,
                "value": item.value,
            }
            for task in snapshot.tasks
            for item in task.interrupts
        ]

        return {
            "thread_id": thread_id,
            "state": snapshot.values,
            "next_nodes": list(snapshot.next),
            "interrupts": interrupts,
        }



@app.post(
    "/interview_sessions/{session_id}/answers/{answer_id}/workflow/choice",
    tags=["AI追问"],
    summary="提交选择并恢复工作流",
)
async def choose_interview_followup(
    session_id: int,
    answer_id: int,
    data: WorkflowChoice,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 获取后端启动时创建的共享工作流
    interview_graph = request.app.state.interview_graph
    # 每次请求都检查归属，不能仅凭工作流编号恢复
    owned_answer_id = await db.scalar(
        select(InterviewAnswer.id)
        .join(
            QuestionRecord,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(
            InterviewAnswer.id == answer_id,
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if owned_answer_id is None:
        raise HTTPException(status_code=404, detail="回答不存在")

    # 与启动接口使用完全相同的编号规则
    thread_id = f"user-{current_user.id}-session-{session_id}-answer-{answer_id}"
    config = {"configurable": {"thread_id": thread_id}}
    lock = workflow_locks.setdefault(thread_id, asyncio.Lock())

    async with lock:
        snapshot = await interview_graph.aget_state(config)

        if not snapshot.values:
            raise HTTPException(
                status_code=409,
                detail="工作流未启动或进度已丢失，请先调用启动接口",
            )

        # 必须确实暂停在选择节点，避免把选择传给等待回答的节点
        waiting_choice = any(
            task.name == "wait_choice" and task.interrupts
            for task in snapshot.tasks
        )

        if (
            snapshot.values.get("stage") != "waiting_choice"
            or not waiting_choice
        ):
            raise HTTPException(
                status_code=409,
                detail="当前流程不在等待追问选择，请先查询工作流状态",
            )

        # 用户选择成为 wait_choice_node 中 interrupt() 的返回值
        await interview_graph.ainvoke(
            Command(resume=data.choice),
            config=config,
        )

        # 读取恢复后的最新状态及下一次暂停信息
        snapshot = await interview_graph.aget_state(config)

        interrupts = [
            {"id": item.id, "value": item.value}
            for task in snapshot.tasks
            for item in task.interrupts
        ]

        return {
            "thread_id": thread_id,
            "state": snapshot.values,
            "next_nodes": list(snapshot.next),
            "interrupts": interrupts,
        }


@app.post(
    "/interview_sessions/{session_id}/answers/{answer_id}/workflow/answer-ready",
    tags=["AI追问"],
    summary="确认追问回答已保存并恢复工作流",
)
async def resume_after_followup_answer(
    session_id: int,
    answer_id: int,
    data: WorkflowAnswerReady,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 获取后端启动时创建的共享工作流
    interview_graph = request.app.state.interview_graph
    # 先确认主回答属于指定练习和当前用户
    owned_answer_id = await db.scalar(
        select(InterviewAnswer.id)
        .join(
            QuestionRecord,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(
            InterviewAnswer.id == answer_id,
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if owned_answer_id is None:
        raise HTTPException(status_code=404, detail="回答不存在")

    thread_id = f"user-{current_user.id}-session-{session_id}-answer-{answer_id}"
    config = {"configurable": {"thread_id": thread_id}}
    lock = workflow_locks.setdefault(thread_id, asyncio.Lock())

    async with lock:
        snapshot = await interview_graph.aget_state(config)

        if not snapshot.values:
            raise HTTPException(
                status_code=409,
                detail="工作流未启动或进度已丢失，请先调用启动接口",
            )

        # 确认当前暂停位置确实是在等待追问回答
        waiting_answer = any(
            task.name == "wait_followup_answer" and task.interrupts
            for task in snapshot.tasks
        )

        if (
            snapshot.values.get("stage") != "waiting_followup_answer"
            or not waiting_answer
        ):
            raise HTTPException(
                status_code=409,
                detail="当前流程不在等待追问回答",
            )

        # 在恢复前校验编号，避免错误输入进入工作流节点
        saved_answer_id = await db.scalar(
            select(InterviewFollowupAnswer.id)
            .join(
                InterviewFollowup,
                InterviewFollowupAnswer.followup_id == InterviewFollowup.id,
            )
            .where(
                InterviewFollowupAnswer.id == data.followup_answer_id,
                InterviewFollowup.id == snapshot.values["followup_id"],
                InterviewFollowup.parent_answer_id == answer_id,
            )
        )

        if saved_answer_id is None:
            raise HTTPException(
                status_code=404,
                detail="追问回答不存在，或不属于当前追问",
            )

        # 将回答编号交给等待节点，后续自动执行追问点评节点
        await interview_graph.ainvoke(
            Command(resume=saved_answer_id),
            config=config,
        )

        snapshot = await interview_graph.aget_state(config)

        interrupts = [
            {"id": item.id, "value": item.value}
            for task in snapshot.tasks
            for item in task.interrupts
        ]

        return {
            "thread_id": thread_id,
            "state": snapshot.values,
            "next_nodes": list(snapshot.next),
            "interrupts": interrupts,
        }


@app.post(
    "/interview_sessions/{session_id}/report",
    tags=["练习报告"],
    summary="生成练习报告，成功后直接复用",
)
async def create_interview_report(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # manager 负责归属检查、练习状态检查、生成和保存
    report = await ensure_report(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    snapshot = report.input_snapshot or {}

    return {
        "session_id": session_id,
        "report_id": report.id,
        "status": report.status,
        "config": snapshot.get("config"),
        "statistics": snapshot.get("statistics"),
        "report_content": report.report_content,
        "error_message": report.error_message,
    }


@app.get(
    "/interview_sessions/{session_id}/report",
    tags=["练习报告"],
    summary="查询已保存的练习报告",
)
async def get_interview_report(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 查询前也必须验证练习归属
    session = await db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(status_code=404, detail="练习不存在")

    report = await db.scalar(
        select(InterviewReport).where(
            InterviewReport.session_id == session_id,
        )
    )

    if report is None:
        return {
            "session_id": session_id,
            "report_id": None,
            "status": "not_generated",
            "config": None,
            "statistics": None,
            "report_content": None,
            "error_message": None,
        }

    snapshot = report.input_snapshot or {}

    return {
        "session_id": session_id,
        "report_id": report.id,
        "status": report.status,
        "config": snapshot.get("config"),
        "statistics": snapshot.get("statistics"),
        "report_content": report.report_content,
        "error_message": report.error_message,
    }



@app.post("/knowledge_documents", tags=["资料管理"], summary="管理员新增参考资料",status_code=201)
async def create_knowledge_document(
    data: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),   
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # 新资料默认是草稿，不直接参与后续检索
    document = KnowledgeDocument(
        content=data.content,
        source_url=data.source_url,
        title=data.title,
        version_note=data.version_note,
        status="draft",
        revision=1,
        created_at=now,
        updated_at=now,
    )
    # add登记待保存对象，commit真正提交数据库
    db.add(document)
    await db.commit()
    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
        "revision": document.revision,
        "message":"资料已保存为草稿"
    }
    


@app.get("/knowledge_documents", tags=["资料管理"], summary="管理员查询参考资料")
async def list_knowledge_documents(
    page:int = Query(default=1, ge=1),
    page_size:int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    # 查询资料总数，用于前端显示数量和分页
    total = await db.scalar(
        select(func.count()).select_from(KnowledgeDocument)
    )
    # 按编号倒序查询，最新添加的资料排在前面
    result = await db.execute(
        select(KnowledgeDocument)
        .order_by(KnowledgeDocument.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    documents = result.scalars().all()
    # 列表只返回摘要，正文通过详情接口获取
    return {
        "total": total,
        "items": [
            {
                "id": document.id,
                "title": document.title,
                "status": document.status,
                "revision": document.revision,
                "version_note": document.version_note,
            }
            for document in documents
        ],
    }


@app.get(
    "/knowledge_documents/search",
    tags=["资料管理"],
    summary="管理员检索参考资料",
)
async def search_knowledge_documents(
    query: str = Query(min_length=1, max_length=500),
    k: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    try:
        documents = await search_documents(db, query, k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("资料检索失败")
        raise HTTPException(
            status_code=502,
            detail="资料检索失败，请查看后端日志",
        )

    # 将 LangChain Document 转成接口返回的字典
    return {
        "query": query,
        "count": len(documents),
        "items": [
            {
                "content": document.page_content,
                "metadata": document.metadata,
            }
            for document in documents
        ],
    }


@app.get(
    "/knowledge_documents/{document_id}",
    tags=["资料管理"],
    summary="管理员查看资料详情",
)
async def get_knowledge_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    # 根据主键查找一份资料
    document = await db.get(KnowledgeDocument, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 详情接口返回完整正文和来源信息
    return {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "source_url": document.source_url,
        "version_note": document.version_note,
        "status": document.status,
        "revision": document.revision,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }



@app.patch(
    "/knowledge_documents/{document_id}/status",
    tags=["资料管理"],
    summary="管理员修改资料状态",
)
async def update_knowledge_document_status(
    document_id: int,
    data: KnowledgeDocumentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    # 先根据资料编号找到对应的数据库记录
    document = await db.get(KnowledgeDocument, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 状态确实发生变化时，才修改记录
    if document.status != data.status:
        document.status = data.status
        document.revision += 1
        document.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # 将修改提交到数据库
        await db.commit()

    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
        "revision": document.revision,
    }


@app.put(
    "/knowledge_documents/{document_id}",
    tags=["资料管理"],
    summary="管理员编辑资料",
)
async def update_knowledge_document(
    document_id: int,
    data: KnowledgeDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    # 查找要修改的资料
    document = await db.get(KnowledgeDocument, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 用提交的完整内容更新资料
    document.title = data.title
    document.content = data.content
    document.source_url = data.source_url
    document.version_note = data.version_note

    # 修改后重新进入草稿状态，等待审核
    document.status = "draft"
    document.revision += 1
    document.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()

    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
        "revision": document.revision,
        "message": "资料已修改，请重新审核",
    }


@app.get(
    "/knowledge_documents/{document_id}/chunks",
    tags=["资料管理"],
    summary="管理员预览资料切分结果",
)
async def preview_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    # 从数据库读取完整资料
    document = await db.get(KnowledgeDocument, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 调用切分服务，返回字符串列表
    chunks = split_document(document.content)

    return {
        "document_id": document.id,
        "title": document.title,
        "revision": document.revision,
        "chunk_count": len(chunks),
        "chunks": [
            {
                "position": position,
                "character_count": len(chunk),
                "content": chunk,
            }
            for position, chunk in enumerate(chunks, start=1)
        ],
    }



@app.post(
    "/knowledge_documents/index/rebuild",
    tags=["资料管理"],
    summary="管理员重建资料索引",
)
async def rebuild_knowledge_index(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    try:
        # 具体业务交给 service，接口只负责调用和返回
        result = await rebuild_document_index(db)
    except ValueError as exc:
        # 例如：没有已审核资料
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("重建资料索引失败")
        raise HTTPException(
            status_code=502,
            detail="索引建立失败，请查看后端日志",
        )

    return result
