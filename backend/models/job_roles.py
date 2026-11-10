from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base



# 对应岗位表，一条记录表示一个岗位方向
class JobRole(Base):
    __tablename__ = 'job_roles'

    # 对应表中的整数主键id
    id:Mapped[int] = mapped_column(primary_key=True)
    # 岗位名称:最多50个字符，不为空不重复
    name:Mapped[str] = mapped_column(String(50), nullable=False, unique=True)






