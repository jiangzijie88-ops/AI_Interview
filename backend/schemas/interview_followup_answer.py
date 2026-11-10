from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# 用户提交追问回答时的请求格式
class FollowupAnswerCreate(BaseModel):
    # 同一次提交重试时保持不变
    submission_id: UUID = Field(
        description="本次提交的唯一标识，重试时保持不变"
    )

    # 与主回答一样，最多允许1000个字符
    content: str = Field(
        min_length=1,
        max_length=1000,
    )

    @field_validator("content")
    @classmethod
    def check_not_blank(cls, value: str) -> str:
        # 拒绝只有空格或换行的回答
        if not value.strip():
            raise ValueError("回答不能为空")

        # 保留原始内容，避免破坏代码缩进
        return value