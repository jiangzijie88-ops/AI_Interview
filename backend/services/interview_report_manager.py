from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.interview_sessions import InterviewSession
from backend.models.interview_questions import QuestionRecord
from backend.models.interview_answers import InterviewAnswer
from backend.models.interview_feedback import InterviewFeedback

from backend.models.interview_followup import InterviewFollowup
from backend.models.interview_followup_answer import InterviewFollowupAnswer
from backend.models.interview_followup_feedback import InterviewFollowupFeedback
from backend.schemas.interview_reports import ReportContent

import logging
import os
from datetime import datetime, timezone

from backend.models.interview_reports import InterviewReport
from backend.services.interview_report import (
    REPORT_PROMPT_VERSION,
    generate_report,
)


logger = logging.getLogger("uvicorn.error")



async def collect_report_input(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> dict:
    """读取一次已结束练习的问答，整理成报告输入。"""

    # 1. 确认练习存在，而且属于当前用户
    session = await db.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )

    if session is None:
        raise HTTPException(status_code=404, detail="练习不存在")

    # 练习结束后才能生成整场报告
    if session.status not in ("completed", "ended_early"):
        raise HTTPException(
            status_code=409,
            detail="请先结束练习，再生成报告",
        )

    # 2. 从题目快照出发，关联可能存在的回答和点评
    result = await db.execute(
        select(
            QuestionRecord,
            InterviewAnswer,
            InterviewFeedback,
            InterviewFollowup,
            InterviewFollowupAnswer,
            InterviewFollowupFeedback,
        )
        .outerjoin(
            InterviewAnswer,
            InterviewAnswer.question_record_id == QuestionRecord.id,
        )
        .outerjoin(
            InterviewFeedback,
            InterviewFeedback.answer_id == InterviewAnswer.id,
        )
        # 追问关联的是主回答，不是题目快照
        .outerjoin(
            InterviewFollowup,
            InterviewFollowup.parent_answer_id == InterviewAnswer.id,
        )
        .outerjoin(
            InterviewFollowupAnswer,
            InterviewFollowupAnswer.followup_id == InterviewFollowup.id,
        )
        .outerjoin(
            InterviewFollowupFeedback,
            InterviewFollowupFeedback.followup_answer_id
            == InterviewFollowupAnswer.id,
        )
        .where(QuestionRecord.session_id == session_id)
        .order_by(QuestionRecord.position)
    )

    rows = result.all()

    # 3. 将数据库对象整理成普通字典
    questions = []
    answered_count = 0
    feedback_count = 0

    for (
        question,
        answer,
        feedback,
        followup,
        followup_answer,
        followup_feedback,
    ) in rows:
        if answer is not None:
            answered_count += 1

        feedback_succeeded = (
            feedback is not None
            and feedback.status == "succeeded"
        )

        if feedback_succeeded:
            feedback_count += 1

        # 只有成功生成的追问，才作为正式问题整理
        followup_succeeded = (
            followup is not None
            and followup.status == "succeeded"
        )

        followup_feedback_succeeded = (
            followup_feedback is not None
            and followup_feedback.status == "succeeded"
        )

        # 默认没有可供分析的追问
        followup_data = None

        if followup_succeeded:
            followup_data = {
                "followup_id": followup.id,
                "question_content": followup.question_content,
                "reference_points": followup.reference_points,
                "answer_id": (
                    followup_answer.id
                    if followup_answer is not None else None
                ),
                "answer_content": (
                    followup_answer.content
                    if followup_answer is not None else None
                ),
                "feedback_status": (
                    followup_feedback.status
                    if followup_feedback is not None
                    else "not_generated"
                ),
                "feedback_content": (
                    followup_feedback.feedback_content
                    if followup_feedback_succeeded else None
                ),
            }

        questions.append({
            "position": question.position,
            "question_record_id": question.id,
            "question_content": question.content,
            "reference_points": question.reference_points,
            "knowledge_points": question.knowledge_points_snapshot,

            # 未回答时明确保存为空，不编造回答
            "answer_id": answer.id if answer is not None else None,
            "answer_content": (
                answer.content if answer is not None else None
            ),

            # 记录点评状态，仅将成功的点评作为正式分析材料
            "feedback_status": (
                feedback.status if feedback is not None
                else "not_generated"
            ),
            "feedback_content": (
                feedback.feedback_content
                if feedback_succeeded else None
            ),
            # 区分未生成追问、生成失败、生成成功等情况
            "followup_status": (
                followup.status if followup is not None
                else "not_generated"
            ),

            # 成功追问及其回答、点评；没有成功追问则为空
            "followup": followup_data,
        })

    # 4. 统计由代码计算，模型只负责分析
    return {
        "session_id": session.id,
        "session_status": session.status,
        "config": session.config_snapshot,
        "statistics": {
            "question_count": len(questions),
            "answered_count": answered_count,
            "unanswered_count": len(questions) - answered_count,
            "main_feedback_succeeded_count": feedback_count,
        },
        "questions": questions,
    }



def validate_report(
    report: ReportContent,
    report_input: dict,
) -> None:
    """校验报告的题号和知识点是否与本次输入对应。"""

    # 将题目列表转换为“题号 → 题目数据”，方便按编号查找
    questions = {
        question["position"]: question
        for question in report_input["questions"]
    }

    # 依据不足时，不允许同时输出确定性的表现和薄弱点结论
    if not report.can_summarize:
        if (
            report.strengths
            or report.weak_points
            or report.followup_reviews
        ):
            raise ValueError("依据不足时，不应输出表现、薄弱点或追问评价")

    # 完全没有主回答时，不能声称能够总结学习表现
    has_answer = any(
        question["answer_content"] is not None
        for question in questions.values()
    )

    if report.can_summarize and not has_answer:
        raise ValueError("没有主回答，不能形成学习表现总结")

    # 检查每条薄弱点的证据
    for weak_point in report.weak_points:
        if not weak_point.question_positions:
            raise ValueError("薄弱点必须关联至少一道题")

        for position in weak_point.question_positions:
            question = questions.get(position)

            if question is None:
                raise ValueError(f"薄弱点引用了不存在的第 {position} 题")

            if question["answer_content"] is None:
                raise ValueError(f"第 {position} 题未回答，不能作为薄弱点证据")

            point_names = {
                point["name"]
                for point in question["knowledge_points"]
            }

            if weak_point.knowledge_point not in point_names:
                raise ValueError(
                    f"知识点与第 {position} 题的知识点不匹配"
                )

    # 检查追问回顾是否有真实回答
    reviewed_positions = set()

    for review in report.followup_reviews:
        position = review.question_position
        question = questions.get(position)

        if question is None:
            raise ValueError(f"追问回顾引用了不存在的第 {position} 题")

        followup = question["followup"]

        if followup is None or followup["answer_content"] is None:
            raise ValueError(f"第 {position} 题没有追问回答，不能生成回顾")

        if position in reviewed_positions:
            raise ValueError(f"第 {position} 题的追问回顾重复")

        reviewed_positions.add(position)


async def ensure_report(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> InterviewReport:
    """复用成功报告，或生成、校验并保存报告。"""

    # 锁定所属练习，避免同时为同一次练习创建报告记录
    session = await db.scalar(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
        .with_for_update()
    )

    if session is None:
        raise HTTPException(status_code=404, detail="练习不存在")

    if session.status not in ("completed", "ended_early"):
        raise HTTPException(
            status_code=409,
            detail="请先结束练习，再生成报告",
        )

    # 查询这次练习已有的报告
    report = await db.scalar(
        select(InterviewReport)
        .where(InterviewReport.session_id == session_id)
        .with_for_update()
    )

    if report is not None:
        if report.status == "succeeded":
            return report

        if report.status == "processing":
            raise HTTPException(
                status_code=409,
                detail="报告正在生成中，请稍后查询",
            )

    # 汇总本次生成实际使用的输入
    report_input = await collect_report_input(
        db=db,
        session_id=session_id,
        user_id=user_id,
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if report is None:
        report = InterviewReport(
            session_id=session_id,
            created_at=now,
        )
        db.add(report)

    # 首次生成或失败重试，都更新为本次输入和生成配置
    report.status = "processing"
    report.input_snapshot = report_input
    report.report_content = None
    report.error_message = None
    report.model_name = os.environ["LLM_MODEL"]
    report.prompt_version = REPORT_PROMPT_VERSION
    report.updated_at = now

    # 保存处理中状态，释放锁后再等待模型
    await db.commit()

    try:
        content = await generate_report(report_input)

        # 关联校验通过后，才保存正式报告内容
        validate_report(content, report_input)

        report.report_content = content.model_dump()
        report.status = "succeeded"

    except Exception as exc:
        logger.error(
            "练习报告生成失败：session_id=%s，异常类型=%s",
            session_id,
            type(exc).__name__,
        )
        report.status = "failed"
        report.error_message = "报告生成或校验失败，请稍后重试"

    report.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 最终提交失败会向外抛异常，不返回保存成功
    await db.commit()

    return report




