from typing import Literal,NotRequired,TypedDict



# 一道主问题的点评、追问流程所需的状态
class InterviewState(TypedDict):
  # 这条流程属于谁、哪次练习、哪条主回答
  user_id: int
  session_id: int
  answer_id: int

  # 尚未生成追问时，可以没有这些字段
  followup_id: NotRequired[int]
  followup_answer_id: NotRequired[int]

  # 当前业务阶段，由后端节点更新
  stage:NotRequired[Literal[
    "loading",     # 正在核对流程需要的数据
    "main_feedback",   # 准备进入主回答点评
    "waiting_choice",   # 等待用户回答追问
    "generating_followup",
    "waiting_followup_answer",
    "followup_feedback",
    "completed",   # 这道题的工作流完成
    "failed",
  ]]




