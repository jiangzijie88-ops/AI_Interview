from pydantic import BaseModel,Field,field_validator



# 模型生成一道追问时，必须返回的内容
class FollowupContent(BaseModel):
    question_content: str = Field(min_length=1,max_length=1000,description="一道围绕原回答薄弱点的应用或迁移问题，不包含答案")
    reference_points: str = Field(min_length=1,max_length=1000,description="用于评价追问回答的参考要点，不向尚未回答的用户展示")

    @field_validator("question_content","reference_points")
    @classmethod
    def check_not_blank(cls,value:str) -> str:
        # 不能只包含空格或换行：保留原文中的正常格式
        if not value.strip():
            raise ValueError("追问正文和参考要点不能为空")
        return value








