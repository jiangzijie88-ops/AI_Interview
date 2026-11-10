from sqlalchemy import Column, Text, DateTime, JSON, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from  backend.database import Base



# 一条记录表示某次练习中的一道主问题快照
class QuestionRecord(Base):
    __tablename__ = "interview_questions"
    # 同一次练习中，题目序号不能重复
    __table_args__ = (UniqueConstraint("session_id", "position"),)
    # 快照记录自己的唯一编号
    id: Mapped[int] = mapped_column(primary_key=True)
    # 属于哪次练习
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"),nullable=False)
    # 快照来源于哪道公共题目
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"),nullable=False)
    # 本次练习中的主问题序号
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # 创建快照时，来源题目的修订号
    question_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    # 一下字段保存复制后的内容，不随题库自动变化
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reference_points: Mapped[str] = mapped_column(Text, nullable=False)

    common_mistakes: Mapped[str|None] = mapped_column(Text, nullable=True)
    followup_direction: Mapped[str|None] = mapped_column(Text, nullable=True)
    sources: Mapped[str|None] = mapped_column(Text, nullable=True)
    # 保存创建时关联的知识点编号和名称
    knowledge_points_snapshot: Mapped[list[dict]] = mapped_column(JSON, nullable=False)





