import logging
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.interview_answers import InterviewAnswer
from backend.models.interview_followup import InterviewFollowup
from backend.models.interview_followup_answer import InterviewFollowupAnswer
from backend.models.interview_followup_feedback import InterviewFollowupFeedback
from backend.models.interview_questions import QuestionRecord
from backend.models.interview_sessions import InterviewSession
from backend.services.interview_followup_feedback import (
    FOLLOWUP_FEEDBACK_PROMPT_VERSION,
    generate_followup_feedback,
)


logger = logging.getLogger("uvicorn.error")


async def ensure_followup_feedback(
    db: AsyncSession,
    followup_answer_id: int,
    user_id: int,
) -> dict:
    """复用已有点评，或生成并保存追问回答的点评。"""
    # 1. 同时查询追问回答和追问问题，并检查用户归属
    result = await db.execute(
        select(InterviewFollowupAnswer, InterviewFollowup)
        .join(
            InterviewFollowup,
            InterviewFollowupAnswer.followup_id == InterviewFollowup.id,
        )
        .join(
            InterviewAnswer,
            InterviewFollowup.parent_answer_id == InterviewAnswer.id,
        )
        .join(
            QuestionRecord,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .join(
            InterviewSession,
            QuestionRecord.session_id == InterviewSession.id,
        )
        .where(
            InterviewFollowupAnswer.id == followup_answer_id,
            InterviewSession.user_id == user_id,
        )
        .with_for_update()
    )
    row = result.one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="追问回答不存在")

    answer, followup = row

    # 2. 成功的点评直接复用，处理中则拒绝重复生成
    feedback = await db.scalar(
        select(InterviewFollowupFeedback)
        .where(
            InterviewFollowupFeedback.followup_answer_id == answer.id
        )
        .with_for_update()
    )

    if feedback is not None:
        if feedback.status == "succeeded":
            return {
                "followup_answer_id": answer.id,
                "status": feedback.status,
                "feedback_content": feedback.feedback_content,
                "error_message": None,
            }

        if feedback.status == "processing":
            raise HTTPException(
                status_code=409,
                detail="追问点评正在生成中，请稍后查询",
            )

    # 生成点评前，追问本身必须完整且生成成功
    if (
        followup.status != "succeeded"
        or not followup.question_content
        or not followup.reference_points
    ):
        raise HTTPException(
            status_code=409,
            detail="追问问题或参考要点不完整，暂时无法点评",
        )

    question_text = followup.question_content
    reference_text = followup.reference_points
    answer_text = answer.content

    # 3. 创建或复用记录，先提交处理中状态
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if feedback is None:
        feedback = InterviewFollowupFeedback(
            followup_answer_id=answer.id,
            created_at=now,
        )
        db.add(feedback)

    feedback.status = "processing"
    feedback.feedback_content = None
    feedback.error_message = None
    feedback.model_name = os.environ["LLM_MODEL"]
    feedback.prompt_version = FOLLOWUP_FEEDBACK_PROMPT_VERSION
    feedback.updated_at = now

    # 提交后释放锁，再等待模型
    await db.commit()

    # 4. 调用追问点评链
    try:
        content = await generate_followup_feedback(
            question=question_text,
            reference_points=reference_text,
            answer=answer_text,
        )

        feedback.feedback_content = content.model_dump()
        feedback.status = "succeeded"

    except Exception as exc:
        logger.error(
            "追问点评失败：followup_answer_id=%s，异常类型=%s",
            followup_answer_id,
            type(exc).__name__,
        )
        feedback.status = "failed"
        feedback.error_message = "追问点评生成失败，请稍后重试"

    # 5. 保存最终结果
    feedback.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()

    return {
        "followup_answer_id": followup_answer_id,
        "status": feedback.status,
        "feedback_content": feedback.feedback_content,
        "error_message": feedback.error_message,
    }