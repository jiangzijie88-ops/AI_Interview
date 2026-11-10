from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models.interview_answers import InterviewAnswer
from backend.models.interview_questions import QuestionRecord
from backend.models.interview_sessions import InterviewSession
from backend.workflows.interview_state import InterviewState
from backend.services.interview_feedback_manager import ensure_main_feedback
from langgraph.types import interrupt
from backend.services.interview_followup_manager import ensure_followup
from backend.models.interview_followup_answer import InterviewFollowupAnswer
from backend.services.interview_followup_feedback_manager import (
    ensure_followup_feedback,
)



async def load_context(state: InterviewState)->dict:
  # 核对主回答，练习和用户的关联关系

  # 节点自行获取数据库会话，用完后关闭
  async with AsyncSessionLocal() as db:
    answer_id = await db.scalar(
      select(InterviewAnswer.id)
      .join(
        QuestionRecord,
        InterviewAnswer.question_record_id == QuestionRecord.id
        )
        .join(
          InterviewSession,
          QuestionRecord.session_id == InterviewSession.id
        )
        .where(
          InterviewSession.user_id == state["user_id"],
          InterviewSession.id == state["session_id"],
          InterviewAnswer.id == state["answer_id"]
        )
      )
    if answer_id is None:
      raise ValueError("主回答不存在，或不属于指定用户和练习")

    # 返回需要更新的字段，其余状态由图保留
    return{"stage":"main_feedback"}
    


async def main_feedback_node(state: InterviewState)->dict:
  """生成或复用主回答点评，然后更新工作流阶段"""
  # 为本节点创建数据库会话
  async with AsyncSessionLocal() as db:
    result = await ensure_main_feedback(
      db = db,
      answer_id = state["answer_id"],
      user_id = state["user_id"],
    )
    # 点评业务函数会返回数据库中的点评状态
    if result["status"] == "succeeded":
      return {"stage":"waiting_choice"}
    
    return {"stage":"failed"}



def wait_choice_node(state: InterviewState)->dict:
  """暂停工作流，等待用户是否决定生成追问"""

  # 第一次允许到这里会暂停，将提示信息返回给调用者
  # 恢复时，外部传入的选择会成为choice的值
  choice = interrupt({
    "message":"主点评已准备好，是否生成针对性追问？",
    "answer_id":state["answer_id"],
    "options":["generate_followup","finish"]
  })
  # 恢复后才会执行下面的代码
  if choice == "generate_followup":
    return {"stage":"generating_followup"}
  elif choice == "finish":
    return {"stage":"completed"}
  else:
    raise ValueError("不支持的追问选择")


def route_after_main_feedback(state: InterviewState) -> str:
    """根据主点评结果，决定下一步去哪里。"""

    if state["stage"] == "waiting_choice":
        return "wait_choice"

    return "end"


async def generate_followup_node(state: InterviewState)->dict:
  """生成或复用追问，将追问编号写入工作流状态"""
  async with AsyncSessionLocal() as db:
    result = await ensure_followup(
      db = db,
      answer_id = state["answer_id"],
      user_id = state["user_id"],
    )
    if result["status"] == "succeeded":
      return {
        "stage":"waiting_followup_answer",
        "followup_id":result["followup_id"],
      }
    return {"stage":"failed"}


def route_after_choice(state: InterviewState) -> str:
    """根据用户选择，决定生成追问还是结束"""

    if state["stage"] == "generating_followup":
        return "generate_followup"

    return "end"



async def wait_followup_answer_node(state: InterviewState)->dict:
  """等待已保存的追问回答，并核对它属于当前追问"""

  # 暂停时不持有数据库会话：恢复值是已保存的回答编号
  answer_id = interrupt({
    "message":"请提交追问回答，再用追问回答编号恢复流程",
    "followup_id":state["followup_id"],
  })

  # 恢复值需要是正整数编号
  if type(answer_id) is not int or answer_id <= 0:
    raise ValueError("追问回答编号必须是正整数")

  async with AsyncSessionLocal() as db:
    saved_answer_id = await db.scalar(
      select(InterviewFollowupAnswer.id)
      .where(
        InterviewFollowupAnswer.id == answer_id,
        InterviewFollowupAnswer.followup_id == state["followup_id"],
      )
    )
    if saved_answer_id is None:
      raise ValueError("该追问回答不存在，或不属于当前追问")
    return {"stage":"followup_feedback","followup_answer_id":saved_answer_id}



def route_after_generate_followup(state: InterviewState) -> str:
    """追问生成成功才等待回答，失败则结束本次执行。"""

    if state["stage"] == "waiting_followup_answer":
        return "wait_followup_answer"

    return "end"



async def followup_feedback_node(state: InterviewState) -> dict:
    """生成或复用追问回答点评，更新最终业务阶段。"""

    async with AsyncSessionLocal() as db:
        result = await ensure_followup_feedback(
            db=db,
            followup_answer_id=state["followup_answer_id"],
            user_id=state["user_id"],
        )

    if result["status"] == "succeeded":
        return {"stage": "completed"}

    return {"stage": "failed"}



