from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


# 对应知识点表，一条记录表示一个知识点
class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    # 对应表中的整数主键id
    id: Mapped[int] = mapped_column(primary_key=True)
    # 知识点名称：最多100个字符，不为空不重复
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)









