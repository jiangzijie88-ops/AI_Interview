from typing import Literal

from pydantic import BaseModel, Field


class WorkflowChoice(BaseModel):
    # 只接受这两个选项，其他值由 FastAPI 返回 422
    choice: Literal["generate_followup", "finish"]


class WorkflowAnswerReady(BaseModel):
    # 必须是已经保存到数据库的追问回答编号
    followup_answer_id: int = Field(gt=0, strict=True)




    
