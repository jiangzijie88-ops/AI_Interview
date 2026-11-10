from pydantic import BaseModel, Field


class ReportWeakPoint(BaseModel):
    """一条有题目证据的待复习知识点。"""

    knowledge_point: str = Field(
        description="需要复习的知识点名称"
    )

    question_positions: list[int] = Field(
        description="证据来自本次练习的哪些主问题序号，例如 [1, 3]"
    )

    reason: str = Field(
        description="依据首次主回答及其点评，说明核心遗漏或错误；不把未回答当作不会"
    )

    suggestion: str = Field(
        description="针对这个知识点的一条具体复习建议"
    )


class ReportFollowupReview(BaseModel):
    """区分追问巩固表现与首次回答。"""

    question_position: int = Field(
        description="这道追问所属的主问题序号"
    )

    observation: str = Field(
        description="描述追问回答表现；只有与主回答可比较时才说明改善，不夸大掌握程度"
    )


class ReportContent(BaseModel):
    """模型需要输出的整场练习总结。"""

    can_summarize: bool = Field(description="现有回答和点评是否足以形成有依据的学习总结")

    overall_summary: str = Field(description="简要总结本次练习表现；依据不足时说明限制，不预测招聘结果")

    strengths: list[str] = Field(description="有实际回答支持的表现较好之处，没有则返回空列表")

    weak_points: list[ReportWeakPoint] = Field(description="首次主回答体现出的核心待复习点，没有可靠证据则返回空列表")

    followup_reviews: list[ReportFollowupReview] = Field(description="已回答追问的巩固表现，没有则返回空列表")

    study_suggestions: list[str] = Field(description="结合本次证据给出的整体复习安排，简明且可执行")






