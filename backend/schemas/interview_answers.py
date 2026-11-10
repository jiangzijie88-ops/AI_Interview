from uuid import UUID
from pydantic import BaseModel,Field,field_validator


# 提交当前题目的回答
class InterviewAnswerCreate(BaseModel):
    # 当前题目接受返回的快照ID
    question_record_id: int = Field(gt = 0)
    # 合法的UUID，重试同一次提交时保持不变
    submission_id: UUID = Field(description="合法的UUID，重试同一次提交时保持不变")
    # 当前题目接口返回的练习修订号
    revision: int = Field(ge = 1)
    # 原始回答，最多1000个字符
    content: str = Field(max_length=1000,min_length=1)
    @field_validator("content")
    @classmethod
    def check_not_blank(cls, value: str):
        # 检查空白，但不删除回答中的换行和缩进
        if not value.strip():
            raise ValueError("回答不能为空")
        return value











