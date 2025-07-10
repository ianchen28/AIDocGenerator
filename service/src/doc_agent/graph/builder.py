# service/src/doc_agent/graph/builder.py
from langgraph.graph import StateGraph, END
from .state import ResearchState
from . import nodes
from . import router


def build_graph():
    """构建并编译LangGraph图"""
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("planner", nodes.planner_node)
    workflow.add_node("researcher", nodes.researcher_node)
    workflow.add_node("writer", nodes.writer_node)

    # 设置入口和固定边
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "researcher")

    # 添加条件路由
    workflow.add_conditional_edges(
        "researcher",
        router.supervisor_router,
        {
            "continue_to_writer": "writer",
            "rerun_researcher": "researcher"  # 形成循环
        })
    workflow.add_edge("writer", END)

    return workflow.compile()
