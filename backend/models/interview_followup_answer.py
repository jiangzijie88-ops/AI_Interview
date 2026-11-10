from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


# 保存用户对一道追问的正式回答
class InterviewFollowupAnswer(Base):
    __tablename__ = "interview_followup_answers"

    # 追问回答自己的编号
    id: Mapped[int] = mapped_column(primary_key=True)

    # 关联追问；一道追问最多有一条正式回答
    followup_id: Mapped[int] = mapped_column(
        ForeignKey("interview_followups.id"),
        nullable=False,
        unique=True,
    )

    # 同一次提交重试时保持不变
    submission_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
    )

    # 保留回答原文，包括代码缩进和换行
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 由后续提交接口填写 UTC 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )