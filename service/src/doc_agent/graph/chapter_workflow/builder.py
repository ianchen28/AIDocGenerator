# service/src/doc_agent/graph/builder.py
from langgraph.graph import END, StateGraph
from loguru import logger

from ..state import ResearchState


def build_graph(planner_node, researcher_node, writer_node,
                supervisor_router_func):
    """构建并编译LangGraph图，节点和决策函数由外部传入（已绑定依赖）"""
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)

    def writer_with_log(*args, **kwargs):
        logger.info("🚩 已进入 writer 节点，准备终止流程（END）")
        return writer_node(*args, **kwargs)

    workflow.add_node("writer", writer_with_log)

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


def build_chapter_workflow_graph(
    planner_node,
    researcher_node,
    writer_node,
    supervisor_router_func,
    reflection_node=None,
):
    """
    构建章节工作流图
    该工作流用于处理单个章节的研究和写作：
    1. planner: 为当前章节制定研究计划
    2. researcher: 执行研究收集数据
    3. supervisor_router: 决定是否需要更多研究
    4. reflector: 智能查询扩展节点（新增）
    5. writer: 基于研究数据和上下文撰写章节内容
    Args:
        planner_node: 已绑定依赖的规划节点函数
        researcher_node: 已绑定依赖的研究节点函数
        writer_node: 已绑定依赖的写作节点函数
        supervisor_router_func: 已绑定依赖的路由决策函数
        reflection_node: 已绑定依赖的智能查询扩展节点函数（可选，必须提供）
    Returns:
        CompiledGraph: 编译后的章节工作流图
    """
    # 创建状态图
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)

    # 注册反思节点
    if reflection_node is None:
        raise ValueError("必须提供 reflection_node 参数")
    workflow.add_node("reflector", reflection_node)

    # 为 writer 节点添加日志
    def writer_with_log(*args, **kwargs):
        logger.info("📝 进入章节 writer 节点，撰写当前章节内容")
        return writer_node(*args, **kwargs)

    workflow.add_node("writer", writer_with_log)

    # 设置入口点
    workflow.set_entry_point("planner")

    # 添加固定边
    workflow.add_edge("planner", "researcher")

    # 添加条件路由
    # supervisor_router 决定是继续研究、反思，还是开始写作
    workflow.add_conditional_edges("researcher", supervisor_router_func, {
        "continue_to_writer": "writer",
        "rerun_researcher": "reflector"
    })

    # reflector 节点无条件回到 researcher
    workflow.add_edge("reflector", "researcher")

    # writer 完成后结束
    workflow.add_edge("writer", END)

    # 编译并返回图
    return workflow.compile()
