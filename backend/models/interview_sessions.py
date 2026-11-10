from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base





# 一条记录对应某个用户的一次面试练习
class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 练习属于哪个用户，后续由登录身份确认
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 选择的岗位方向
    job_role_id: Mapped[int] = mapped_column(ForeignKey("job_roles.id"), nullable=False)
    # 难度与主问题数量
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # 旧版顺序练习的兼容字段；新版页面选题不依赖它
    current_position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # 进行中，已完成或提前结束
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    # 保存创建时的配置
    config_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False, default=1)
    # 时间由后续业务代码填写
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime|None] = mapped_column(DateTime, nullable=True)











