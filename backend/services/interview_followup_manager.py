import json
import logging
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.interview_answers import InterviewAnswer
from backend.models.interview_feedback import InterviewFeedback
from backend.models.interview_followup import InterviewFollowup
from backend.models.interview_questions import QuestionRecord
from backend.models.interview_sessions import InterviewSession
from backend.services.interview_followup import (
    FOLLOWUP_PROMPT_VERSION,
    generate_followup,
)


logger = logging.getLogger("uvicorn.error")


async def ensure_followup(
    db: AsyncSession,
    answer_id: int,
    user_id: int,
) -> dict:
    """复用已有追问，或根据主回答和主点评生成并保存追问。"""
    # 1.查询主回答和题目快照，检查用户归属并锁定
    result = await db.execute(
        select(InterviewAnswer,QuestionRecord)
        .join(QuestionRecord, InterviewAnswer.question_record_id == QuestionRecord.id)
        .join(InterviewSession, QuestionRecord.session_id == InterviewSession.id)
        .where(
            InterviewAnswer.id == answer_id,
            InterviewSession.user_id == user_id,
        ).with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="回答不存在")
    answer,question = row
    # 2. 已有成功追问直接复用，正在生成则拒绝重复请求
    followup = await db.scalar(
        select(InterviewFollowup)
        .where(
            InterviewFollowup.parent_answer_id == answer_id,
        ).with_for_update()
    )
    if followup is not None:
        if followup.status == "succeeded":
            # 成功后直接复用，不重复生成
            return {
                "parent_answer_id": answer_id,
                "followup_id": followup.id,
                "status": followup.status,
                "question_content": followup.question_content,
                "error_message": None,
            }

        if followup.status == "processing":
            raise HTTPException(
                status_code=409,
                detail="追问正在生成中，请稍后查询",
            )
    # 3.必须先有成功的主点评，才生成针对性追问
    feedback = await db.scalar(
        select(InterviewFeedback)
        .where(
            InterviewFeedback.answer_id == answer_id,
        ).with_for_update()
    )
    if feedback is None or feedback.status != "succeeded":
        raise HTTPException(status_code=400, detail="请先生成主点评，再生成追问")
    # 将点评JSON字典转换为提示词需要的文本
    feedback_text = json.dumps(feedback.feedback_content,ensure_ascii=False)
    question_text = question.content
    reference_text = question.reference_points
    answer_text = answer.content
    # 4. 新建记录或复用失败记录，先保存处理中状态
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if followup is None:
        followup = InterviewFollowup(
            parent_answer_id=answer_id,
            created_at=now,
        )
        db.add(followup)
    followup.status = "processing"
    followup.question_content = None
    followup.reference_points = None
    followup.error_message = None
    followup.model_name = os.environ["LLM_MODEL"]
    followup.prompt_version = FOLLOWUP_PROMPT_VERSION
    followup.updated_at = now
    # 释放锁后再等待模型，避免长时间锁住业务记录
    await db.commit()
    # 5.调用追问链，保存生成结果
    try:
        content = await generate_followup(
            question=question_text,
            reference_points=reference_text,
            answer=answer_text,
            feedback=feedback_text,
        )
        followup.question_content = content.question_content
        followup.reference_points = content.reference_points
        followup.status = "succeeded"
    except Exception as exc:
        logger.error(
            "AI 追问生成失败：answer_id=%s，异常类型=%s",
            answer_id,
            type(exc).__name__,
        )
        followup.status = "failed"
        followup.error_message = "追问生成失败，请稍后重试"
    followup.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    # 参考要点只保存在数据库，不在这里返回给用户
    return {
        "parent_answer_id": answer_id,
        "followup_id": followup.id,
        "status": followup.status,
        "question_content": followup.question_content,
        "error_message": followup.error_message,
    }





