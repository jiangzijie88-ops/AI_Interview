from datetime import datetime
from sqlalchemy import DateTime, ForeignKey,String,Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base



# 一条主回答对应一次追问
class InterviewFollowup(Base):
    __tablename__ = "interview_followups"
    # 记录自己的编号
    id: Mapped[int] = mapped_column(primary_key=True)
    # 关联主问题的正式回答，不是题目快照编号
    parent_answer_id: Mapped[int] = mapped_column(ForeignKey("interview_answers.id"), nullable=False,unique=True)
    # 追问问题的生成状态：processing / succeeded / failed
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # 尚未生成成功时，正文和参考要点可以为空
    question_content: Mapped[str|None] = mapped_column(Text, nullable=True)
    reference_points: Mapped[str|None] = mapped_column(Text, nullable=True)
    # 本次生成使用的模型和提示词版本
    model_name: Mapped[str|None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # 生成失败的简短原因
    error_message: Mapped[str|None] = mapped_column(Text, nullable=True)
    # 时间由后续业务函数填写
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
