import logging
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.interview_answers import InterviewAnswer
from backend.models.interview_feedback import InterviewFeedback
from backend.models.interview_questions import QuestionRecord
from backend.models.interview_sessions import InterviewSession
from backend.services.interview_feedback import generate_feedback
from backend.services.document_index import search_documents
from backend.database import AsyncSessionLocal


logger = logging.getLogger("uvicorn.error")


# 处理点评业务：检查、复用、生成、保存点评	
async def ensure_main_feedback(db: AsyncSession,answer_id: int,user_id: int,) -> dict:
    """复用已有点评，或生成并保存主回答的点评。"""
    # 查询回答和题目快照，并检查用户归属
    # 锁定记录，避免同一回答的两个生成请求同时创建点评
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
    feedback = await db.scalar(
        select(InterviewFeedback)
        .where(InterviewFeedback.answer_id == answer_id)
        .with_for_update()
    )
    if feedback is not None:
        if feedback.status == "succeeded":
            # 已成功则使用保存的结果，不重复请求模型
            return{
                "answer_id": answer_id,
                "status": feedback.status,
                "feedback_content": feedback.feedback_content,
                "error_message": feedback.error_message,
            }
        if feedback.status == "processing":
            raise HTTPException(status_code=409, detail="点评正在生成中")
    # 2.创建或更新点评记录，先保存“处理中”
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if feedback is None:
        feedback = InterviewFeedback(
            answer_id=answer_id,
            created_at=now,
        )
        db.add(feedback)

    feedback.status = "processing"
    feedback.feedback_content = None
    feedback.error_message = None
    feedback.model_name = os.environ["LLM_MODEL"]
    feedback.updated_at = now

    # 先保存题目和回答文本，提交状态并释放原有记录锁
    question_text = question.content
    reference_text = question.reference_points
    answer_text = answer.content
    # 提交状态并释放锁，不在等待模型时一直锁住练习
    await db.commit()

    # 3.调用点评链：失败只影响点评，不影响已保存的回答
    try:
        documents = []
        retrieval_status = "failed"
        retrieval_note = "资料检索暂不可用，本次根据题目和参考要点评价。"

        # 检索失败只影响辅助资料，不阻止生成点评
        try:
            async with AsyncSessionLocal() as search_db:
                documents = await search_documents(
                    search_db,
                    query=question_text,
                    k=3,
                )

            if documents:
                retrieval_status = "succeeded"
                retrieval_note = "已提供检索参考片段。"
            else:
                retrieval_status = "empty"
                retrieval_note = "未找到符合条件的片段，本次根据题目和参考要点评价。"

        except Exception as exc:
            logger.warning(
                "资料检索未完成，继续生成点评：answer_id=%s，异常类型=%s",
                answer_id,
                type(exc).__name__,
            )

        context_parts = []
        reference_sources = []

        for number, document in enumerate(documents, start=1):
            metadata = document.metadata

            # 给模型阅读的文本，每个片段有独立的引用编号
            context_parts.append(
                f"[资料{number}]\n"
                f"标题：{metadata['title']}\n"
                f"来源：{metadata.get('source_url', '')}\n"
                f"正文：\n{document.page_content}"
            )

            # 保存本次提供的片段快照，便于以后回看来源
            reference_sources.append({
                "number": number,
                "document_id": metadata["document_id"],
                "revision": metadata["revision"],
                "position": metadata["position"],
                "title": metadata["title"],
                "source_url": metadata.get("source_url", ""),
                "version_note": metadata.get("version_note", ""),
                "content": document.page_content,
            })

        retrieved_context = (
            "\n\n".join(context_parts)
            if context_parts
                else retrieval_note
        )

        content = await generate_feedback(
            question=question_text,
            reference_points=reference_text,
            answer=answer_text,
            retrieved_context=retrieved_context,
        )

        # 模型负责生成点评，来源由后端记录，避免让模型编造链接
        feedback_data = content.model_dump()
        feedback_data["reference_sources"] = reference_sources
        feedback_data["retrieval_status"] = retrieval_status
        feedback_data["retrieval_note"] = retrieval_note

        feedback.feedback_content = feedback_data
        feedback.status = "succeeded"
    except Exception as exc:
        # 先记录回答编号和异常类型，不打印密钥或完整回答内容
        logger.error(
            "AI 点评失败：answer_id=%s，异常类型=%s",
            answer_id,
            type(exc).__name__,
        )

        feedback.error_message = "点评生成或结果解析失败，请稍后重试"
        feedback.status = "failed"
    # 4.保存最终结果
    feedback.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()

    return {
        "answer_id": answer_id,
        "status": feedback.status,
        "feedback_content": feedback.feedback_content,
        "error_message": feedback.error_message,
    }









