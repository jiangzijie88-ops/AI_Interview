from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class InterviewReport(Base):
  # 对应刚才手动创建的数据库表
  __tablename__ = "interview_reports"

  # 报告自己的编号
  id: Mapped[int] = mapped_column(primary_key=True)
  # 关联练习：一次练习最多保存一条报告记录
  session_id: Mapped[int] = mapped_column(
    ForeignKey("interview_sessions.id"),
    nullable=False,
    unique=True
    )
  # 报告生成状态，与练习本身的状态分开
  status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
  # 生成报告时使用的数据
  input_snapshot: Mapped[dict|None] = mapped_column(JSON, nullable=True)
  # 模型生成的结构化报告
  report_content: Mapped[dict|None] = mapped_column(JSON, nullable=True)
  model_name: Mapped[str|None] = mapped_column(String(100), nullable=True)
  # 保存本次生成所使用的提示词版本
  prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
  error_message: Mapped[str|None] = mapped_column(Text, nullable=True)
  # 后续由业务函数填写UTC时间
  created_at: Mapped[datetime] = mapped_column(DateTime,nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime,nullable=False)









