from pydantic import BaseModel, Field


# 一次单题点评的结构化结果
class FeedbackContent(BaseModel):
  # 允许模型明确说明：当前依据不足，无法可靠评价
  can_evaluate: bool = Field(description="是否可以可靠评价")
  evaluation_note:str = Field(description="简要说明评价依据；无法可靠评价时说明原因")
  strengths: list[str] = Field(description="回答正确或表现较好的地方，没有则返回空列表")
  missing_points: list[str] = Field(description="遗漏的关键要点，没有则返回空列表")
  errors: list[str] = Field(description="回答中的具体错误及解释，没有则返回空列表")
  suggestions: list[str] = Field(description="针对这份回答的改进建议，没有则返回空列表")








