import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


# 当前文件在 backend/ 中，往上两级得到项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 明确读取项目根目录下的 .env
load_dotenv(PROJECT_ROOT / ".env")

# 分别传入账号、密码等信息，避免手动拼接 URL 时处理特殊字符
database_url = URL.create(
    drivername="mysql+aiomysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
    query={"charset": "utf8mb4"},
)

# 创建异步引擎，管理数据库连接池
async_engine = create_async_engine(
    database_url,
    echo=False,          # 暂不输出所有 SQL；学习调试时可改为 True
    pool_pre_ping=True,  # 取出连接时检查是否有效
    pool_size=5,         # 连接池容量；不是启动时立即创建 5 条连接
    max_overflow=5,      # 连接池满后，最多临时增加 5 条连接
)

# 创建会话工厂：调用它可获得一个新的异步会话
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


# FastAPI 的数据库依赖：为请求提供独立会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            # 把会话交给接口使用；接口结束后继续执行清理
            yield session
        except Exception:
            # 发生异常时，撤销尚未提交的修改
            await session.rollback()
            raise

class Base(DeclarativeBase):
    pass