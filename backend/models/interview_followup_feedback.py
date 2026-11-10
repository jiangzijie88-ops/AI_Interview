from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


# 对一条追问回答生成的 AI 点评
class InterviewFollowupFeedback(Base):
    __tablename__ = "interview_followup_feedbacks"

    # 点评记录自己的编号
    id: Mapped[int] = mapped_column(primary_key=True)

    # 关联追问回答；一份回答最多保留一份点评
    followup_answer_id: Mapped[int] = mapped_column(
        ForeignKey("interview_followup_answers.id"),
        nullable=False,
        unique=True,
    )

    # pending / processing / succeeded / failed
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # 复用 FeedbackContent 的结果结构，以字典形式保存
    feedback_content: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # 记录生成时的模型和提示词版本
    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    prompt_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # 失败时保存简短原因
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 时间由后续接口填写
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )