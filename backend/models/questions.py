from backend.database import Base
from sqlalchemy import ForeignKey,String,Text
from sqlalchemy.orm import Mapped,mapped_column



# 对应question表
class Question(Base):
  __tablename__ = "questions"
  # 题目编号：整数主键
  id:Mapped[int] = mapped_column(primary_key=True)
  # 问题正文
  content:Mapped[str] = mapped_column(Text,nullable=False)
  # 难度：basic 基础，advanced 进阶
  difficulty:Mapped[str] = mapped_column(String(20),nullable=False,default="basic")
  # 回答应覆盖的参考要点
  reference_points:Mapped[str] = mapped_column(Text,nullable=False)
  # 以下三个字段允许没有值
  common_mistakes:Mapped[str|None] = mapped_column(Text,nullable=True)
  followup_direction:Mapped[str|None] = mapped_column(Text,nullable=True)
  sources:Mapped[str|None] = mapped_column(Text,nullable=True)
  # 状态：draft 草稿，approved 已审核，disabled 禁用
  status:Mapped[str] = mapped_column(String(20),nullable=False,default="draft")
  # 修改号，后续编辑时由业务代码递增
  revision:Mapped[int] = mapped_column(nullable=False,default=1)



# 对应题目与岗位的关联表
class QuestionJobRole(Base):
  __tablename__ = "question_job_roles"
  # 两列共同组成主键：这里的编号引用也有记录，不自动生成
  question_id:Mapped[int] = mapped_column(ForeignKey("questions.id"),primary_key=True)
  job_role_id:Mapped[int] = mapped_column(ForeignKey("job_roles.id"),primary_key=True)

# 对应题目与知识点的关联表
class QuestionKnowledgePoint(Base):
  __tablename__ = "question_knowledge_points"
  # 两列共同组成主键：这里的编号引用也有记录，不自动生成
  question_id:Mapped[int] = mapped_column(ForeignKey("questions.id"),primary_key=True)
  knowledge_point_id:Mapped[int] = mapped_column(ForeignKey("knowledge_points.id"),primary_key=True)



