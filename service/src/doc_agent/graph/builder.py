# service/src/doc_agent/graph/builder.py
from langgraph.graph import StateGraph, END
from .state import ResearchState
from . import nodes
from . import router


def build_graph(planner_node, researcher_node, writer_node,
                supervisor_router_func):
    """构建并编译LangGraph图，节点和决策函数由外部传入（已绑定依赖）"""
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)

    # 设置入口和固定边
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "researcher")

    # 添加条件路由
    workflow.add_conditional_edges("researcher", supervisor_router_func, {
        "continue_to_writer": "writer",
        "rerun_researcher": "researcher"
    })

    workflow.add_edge("writer", END)

    return workflow.compile()
