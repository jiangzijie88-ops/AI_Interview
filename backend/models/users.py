from backend.database import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column



# 一个User对象对应users表中的一条用户记录
class User(Base):
  # 数据库中的表名
  __tablename__ = "users"
  # 用户ID，主键，自增
  id : Mapped[int] = mapped_column(primary_key=True)
  # 用户名：50字以内，不能为空不能重复
  username : Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
  # 保存哈希密码，不保存原始密码
  password_hash : Mapped[str] = mapped_column(String(128), nullable=False)
  # 昵称
  nickname : Mapped[str] = mapped_column(String(50), nullable=False)
  # 角色：普通用户user，管理员admin
  role : Mapped[str] = mapped_column(String(10), nullable=False, default="user")

