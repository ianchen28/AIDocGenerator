# service/src/doc_agent/graph/fast_builder.py
"""
快速版本的图构建器
使用简化的节点和配置，目标：3-5分钟内完成文档生成
"""
from langgraph.graph import END, StateGraph
from loguru import logger

from .fast_nodes import (
    fast_planner_node,
    fast_researcher_node,
    fast_supervisor_router,
    fast_writer_node,
)
from .state import ResearchState


def build_fast_chapter_workflow(planner_node, researcher_node, writer_node,
                                supervisor_router_func):
    """构建并编译快速章节工作流图"""
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)

    def writer_with_log(*args, **kwargs):
        logger.info("🚩 已进入快速 writer 节点，准备终止流程（END）")
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


def build_fast_main_workflow(web_search_tool=None,
                             es_search_tool=None,
                             reranker_tool=None,
                             llm_client=None):
    """构建快速主工作流图"""
    # 绑定依赖到快速节点
    from functools import partial

    from .fast_nodes import fast_initial_research_node, fast_outline_generation_node
    from .main_orchestrator.builder import (
        chapter_decision_function,
        create_chapter_processing_node,
        finalize_document_node,
    )

    fast_initial_research_node_bound = partial(fast_initial_research_node,
                                               web_search_tool=web_search_tool,
                                               es_search_tool=es_search_tool,
                                               reranker_tool=reranker_tool,
                                               llm_client=llm_client)

    fast_outline_generation_node_bound = partial(fast_outline_generation_node,
                                                 llm_client=llm_client)

    # 绑定快速章节工作流的依赖
    fast_planner_node_bound = partial(fast_planner_node, llm_client=llm_client)

    fast_researcher_node_bound = partial(fast_researcher_node,
                                         web_search_tool=web_search_tool,
                                         es_search_tool=es_search_tool,
                                         reranker_tool=reranker_tool)

    fast_writer_node_bound = partial(fast_writer_node, llm_client=llm_client)

    fast_supervisor_router_bound = partial(fast_supervisor_router,
                                           llm_client=llm_client)

    # 创建快速章节工作流
    fast_chapter_workflow = build_fast_chapter_workflow(
        fast_planner_node_bound, fast_researcher_node_bound,
        fast_writer_node_bound, fast_supervisor_router_bound)

    # 创建章节处理节点
    fast_chapter_processing_node = create_chapter_processing_node(
        fast_chapter_workflow)

    # 构建主工作流
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("initial_research", fast_initial_research_node_bound)
    workflow.add_node("outline_generation", fast_outline_generation_node_bound)
    workflow.add_node("split_chapters", fast_split_chapters_node)
    workflow.add_node("chapter_processing", fast_chapter_processing_node)
    workflow.add_node("finalize_document", finalize_document_node)

    # 设置入口
    workflow.set_entry_point("initial_research")

    # 添加边
    workflow.add_edge("initial_research", "outline_generation")
    workflow.add_edge("outline_generation", "split_chapters")
    workflow.add_edge("split_chapters", "chapter_processing")

    # 添加条件路由
    workflow.add_conditional_edges(
        "chapter_processing", chapter_decision_function, {
            "process_chapter": "chapter_processing",
            "finalize_document": "finalize_document"
        })

    workflow.add_edge("finalize_document", END)

    return workflow.compile()


def fast_split_chapters_node(state: ResearchState) -> dict:
    """
    快速章节拆分节点 - 简化版本

    将文档大纲拆分为独立的章节任务列表，限制章节数量
    """
    document_outline = state.get("document_outline", {})

    if not document_outline or "chapters" not in document_outline:
        raise ValueError("文档大纲不存在或格式无效")

    logger.info("📂 开始快速拆分章节任务")

    # 从大纲中提取章节信息
    chapters = document_outline.get("chapters", [])

    # 限制章节数量，只处理前2个章节
    limited_chapters = chapters[:2]
    logger.info(f"🔧 快速模式：限制为 {len(limited_chapters)} 个章节")

    # 创建章节任务列表
    chapters_to_process = []
    for chapter in limited_chapters:
        chapter_task = {
            "chapter_number":
            chapter.get("chapter_number",
                        len(chapters_to_process) + 1),
            "chapter_title":
            chapter.get("chapter_title", f"第{len(chapters_to_process) + 1}章"),
            "description":
            chapter.get("description", ""),
            "key_points":
            chapter.get("key_points", []),
            "estimated_sections":
            chapter.get("estimated_sections", 2),  # 减少预估章节数
            "research_data":
            ""
        }
        chapters_to_process.append(chapter_task)

    logger.info(f"✅ 成功创建 {len(chapters_to_process)} 个快速章节任务")

    # 打印章节列表
    for _i, chapter in enumerate(chapters_to_process):
        logger.info(
            f"  📄 第{chapter['chapter_number']}章: {chapter['chapter_title']}")

    return {
        "chapters_to_process": chapters_to_process,
        "current_chapter_index": 0,
        "completed_chapters_content": []
    }
