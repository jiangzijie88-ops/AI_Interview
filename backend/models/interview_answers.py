from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime,DateTime,ForeignKey,Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base



# 一条记录表示对某道练习题目快照的正式回答
class InterviewAnswer(Base):
  __tablename__ = "interview_answers"
  id: Mapped[int] = mapped_column(primary_key=True)
  # 回答的是本次练习中的哪道题，不是公共题库ID
  question_record_id: Mapped[int] = mapped_column(
    ForeignKey("interview_questions.id"),
    nullable=False,
    unique=True,
  )
  # 标识同一次提交，后续用于识别请求重试
  submission_id: Mapped[str] = mapped_column(String(36),nullable=False,unique=True)
  # 保存用户原始回答
  content: Mapped[str] = mapped_column(Text, nullable=False)
  # 由提交接口填写UTC时间
  created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)



