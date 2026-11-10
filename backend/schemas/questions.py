from typing import Literal, Optional
from pydantic import BaseModel, Field,field_validator



# 管理员新增题目时提交的数据
class QuestionCreate(BaseModel):
  # 必须提供问题正文和参考要点
  content: str = Field(min_length=1,max_length=1000)
  reference_points: str = Field(min_length=1,max_length=1000)
  # 只能填写这两种难度，默认基础
  difficulty: Literal["basic","advanced"] = "basic"
  # 可选信息，不填写时为None
  common_mistakes: str|None = Field(default=None,max_length=1000)
  followup_direction: str|None = Field(default=None,max_length=1000)
  sources: str|None = Field(default=None,max_length=1000)
  # 至少选择一个岗位、一个知识点，提交它们的数据库编号
  job_role_ids: list[int] = Field(min_length=1)
  knowledge_point_ids: list[int] = Field(min_length=1)
  # 校验正文和参考要点，拒绝只包含空格的输入
  @field_validator("content","reference_points")
  @classmethod
  def check_not_blank(cls,value:str):
    value = value.strip()
    if not value:
      raise ValueError("内容不能为空或全是空格")
    return value



# 编辑和新增使用相同字段、相同校验规则
class QuestionUpdate(QuestionCreate):
    pass

# 修改状态时，只接收 status 字段
class QuestionStatusUpdate(BaseModel):
    status: Literal["draft", "approved", "disabled"]



