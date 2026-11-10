from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Column, ForeignKey,JSON,Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base



# 一条记录对应一条正式回答的AI点评
class InterviewFeedback(Base):
  __tablename__ = "interview_feedbacks"
  # 点评记录自己的编号
  id: Mapped[int] = mapped_column(primary_key=True)
  # 关联用户回答：一条回答最多保存一条点评记录
  answer_id: Mapped[int] = mapped_column(ForeignKey("interview_answers.id"), nullable=False,unique=True)
  # 点评状态：pending/processing/succeeded/failed
  status:Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
  # 成功后保存结构化点评，尚未生成时为空
  feedback_content: Mapped[dict|None] = mapped_column(JSON, nullable=True)
  # 记录实际使用的模型名称
  model_name: Mapped[str|None] = mapped_column(String(100), nullable=True)
  # 失败时记录简短原因
  error_message: Mapped[str|None] = mapped_column(Text, nullable=True)
  # 时间由后面的业务代码填写
  created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)







