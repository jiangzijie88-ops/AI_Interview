from typing import Literal
from pydantic import BaseModel,Field



# 用户创建一次练习时提交的数据
class InterviewSessionCreate(BaseModel):
    # 必须选择一个岗位，编号为正整数
    job_role_id: int = Field(gt=0)
    # 默认练习基础题
    difficulty: Literal["basic", "advanced"] = "basic"
    # 主问题数量，只允许这三个选项
    question_count: Literal[3, 5, 10] = 5
    # 不选择知识点时，使用空列表，表示不限制
    knowledge_point_ids: list[int] = Field(default_factory=list)



# 完成练习：有未作答题时，需要明确确认
class InterviewSessionFinish(BaseModel):
    revision: int = Field(ge=1)
    confirm_unanswered: bool = False


# 提前结束练习时提交的数据
class InterviewSessionEnd(BaseModel):
    # 使用页面读取到的版本，避免依据旧状态结束练习
    revision: int = Field(ge=1)
