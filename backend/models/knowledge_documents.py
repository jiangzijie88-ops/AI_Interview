from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import LONGTEXT

from backend.database import Base




class KnowledgeDocument(Base):
  """一条记录对应一篇完整的参考资料"""

  __tablename__ = 'knowledge_documents'

  id : Mapped[int] = mapped_column(primary_key=True)
  # 资料标题，例如”FastAPI 异步开发“
  title : Mapped[str] = mapped_column(String(200),nullable=False)
  # 保存完整原文，后续根据它切分文本，建立索引
  content:Mapped[str] = mapped_column(LONGTEXT,nullable=False)
  # 原始资料的来源链接
  source_url:Mapped[str|None] = mapped_column(String(1000),nullable=True)
  # 适用版本或整理说明
  version_note:Mapped[str|None] = mapped_column(String(200),nullable=True)
  # 草稿、已审核、停用
  status:Mapped[str] = mapped_column(String(20),nullable=False,default='draft')
  # 修改资料后增加，用于区分不用版本
  revision:Mapped[int] = mapped_column(Integer,nullable=False,default=1)
  # 后续由业务函数填写UTC时间
  created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)




