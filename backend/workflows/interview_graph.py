from langgraph.graph import END,START,StateGraph
from backend.workflows.interview_nodes import (
    load_context,
    main_feedback_node,
    wait_choice_node,
    route_after_main_feedback,
    generate_followup_node,
    route_after_choice,
    wait_followup_answer_node,
    route_after_generate_followup,
    followup_feedback_node,
)
from backend.workflows.interview_state import InterviewState




def build_interview_graph(checkpointer):
    """创建并编译一道主问题的工作流"""

    # 指定这张图使用的是共享状态结构
    builder = StateGraph(InterviewState)

    builder.add_node("load_context",load_context)
    builder.add_node("main_feedback", main_feedback_node)
    builder.add_node("wait_choice", wait_choice_node)
    builder.add_node("generate_followup", generate_followup_node)
    builder.add_node("wait_followup_answer", wait_followup_answer_node)
    builder.add_node("followup_feedback", followup_feedback_node)

    builder.add_edge(START,"load_context")
    builder.add_edge("load_context", "main_feedback")
    builder.add_conditional_edges(
    "main_feedback",
    route_after_main_feedback,
    {
        "wait_choice": "wait_choice",
        "end": END,
    },
    )
    builder.add_conditional_edges(
    "wait_choice",
    route_after_choice,
    {
        "generate_followup": "generate_followup",
        "end": END,
    },
    )
    builder.add_conditional_edges(
    "generate_followup",
    route_after_generate_followup,
    {
        "wait_followup_answer": "wait_followup_answer",
        "end": END,
    },
    )
    builder.add_edge("wait_followup_answer", "followup_feedback")
    
    builder.add_edge("followup_feedback", END)
    
    # 编译图
    # 使用调用者传入的检查点保存器
    return builder.compile(checkpointer=checkpointer)







