from pydantic import BaseModel, Field,field_validator
from typing import Literal


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    # 先限制单篇资料大小，避免一次提交过长的内容
    content: str = Field(min_length=1, max_length=10000)
    source_url: str | None = Field(default=None,max_length=1000)
    version_note: str | None = Field(default=None,max_length=200)

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str)-> str:
        # 标题清理收尾空格
        value = value.strip()
        if not value:
            raise ValueError("标题不能为空")
        return value

    @field_validator("content")
    @classmethod
    def check_content(cls, value: str)-> str:
        # 只检查是否为空，保留正文原来的换行和代码缩进
        if not value.strip():
            raise ValueError("资料正文不能为空或全是空格")
        return value


class KnowledgeDocumentStatusUpdate(BaseModel):
    # 只允许提交以下三种状态，其他值会被 FastAPI 拒绝
    status: Literal["draft", "approved", "disabled"]


class KnowledgeDocumentUpdate(KnowledgeDocumentCreate):
    # 编辑时提交完整资料，沿用新增资料的字段和校验规则
    pass


