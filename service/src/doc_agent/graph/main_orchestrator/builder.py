# service/src/doc_agent/graph/main_orchestrator/builder.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from ..state import ResearchState
from . import nodes


def create_chapter_processing_node(chapter_workflow_graph):
    """
    创建章节处理节点的工厂函数
    
    Args:
        chapter_workflow_graph: 编译后的章节工作流图
        
    Returns:
        章节处理节点函数
    """

    async def chapter_processing_node(state: ResearchState) -> dict:
        """
        章节处理节点
        
        调用章节子工作流处理当前章节，并更新状态
        
        Args:
            state: 研究状态
            
        Returns:
            dict: 更新后的状态字段
        """
        # 获取当前状态信息
        current_chapter_index = state.get("current_chapter_index", 0)
        chapters_to_process = state.get("chapters_to_process", [])
        completed_chapters_content = state.get("completed_chapters_content",
                                               [])
        topic = state.get("topic", "")

        # 验证索引
        if current_chapter_index >= len(chapters_to_process):
            raise ValueError(f"章节索引 {current_chapter_index} 超出范围")

        # 获取当前章节
        current_chapter = chapters_to_process[current_chapter_index]
        chapter_title = current_chapter.get("chapter_title", "")

        print(
            f"\n📖 开始处理第 {current_chapter_index + 1}/{len(chapters_to_process)} 章: {chapter_title}"
        )

        # 准备子工作流的输入状态
        # 关键：传递已完成章节的内容以保持连贯性
        chapter_workflow_input = {
            "topic": topic,
            "current_chapter_index": current_chapter_index,
            "chapters_to_process": chapters_to_process,
            "completed_chapters_content":
            completed_chapters_content,  # 关键：传递上下文
            "search_queries": [],  # 初始化搜索查询，planner节点会生成
            "research_plan": "",  # 初始化研究计划，planner节点会生成
            "gathered_data": "",  # 初始化收集的数据，researcher节点会填充
            "messages": []  # 新的消息历史
        }

        try:
            # 调用章节工作流
            print(f"🔄 调用章节工作流处理: {chapter_title}")
            chapter_result = await chapter_workflow_graph.ainvoke(
                chapter_workflow_input)

            # 从结果中提取章节内容
            # 注意：章节工作流应该返回 final_document 字段
            chapter_content = chapter_result.get("final_document", "")

            if not chapter_content:
                print(f"⚠️  章节工作流未返回内容，使用默认内容")
                chapter_content = f"## {chapter_title}\n\n章节内容生成失败。"

            print(f"✅ 章节处理完成，内容长度: {len(chapter_content)} 字符")

            # 更新已完成章节列表
            updated_completed_chapters = completed_chapters_content.copy()
            updated_completed_chapters.append(chapter_content)

            # 更新章节索引
            updated_chapter_index = current_chapter_index + 1

            print(
                f"📊 进度: {updated_chapter_index}/{len(chapters_to_process)} 章节已完成"
            )

            return {
                "completed_chapters_content": updated_completed_chapters,
                "current_chapter_index": updated_chapter_index
            }

        except Exception as e:
            print(f"❌ 章节处理失败: {str(e)}")
            # 失败时仍然推进索引，避免无限循环
            return {
                "completed_chapters_content":
                completed_chapters_content +
                [f"## {chapter_title}\n\n章节处理失败: {str(e)}"],
                "current_chapter_index":
                current_chapter_index + 1
            }

    return chapter_processing_node


def chapter_decision_function(state: ResearchState) -> str:
    """
    决策函数：判断是否还有章节需要处理
    
    Args:
        state: 研究状态
        
    Returns:
        str: "process_chapter" 或 "finalize_document"
    """
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])

    print(f"\n🤔 章节处理决策: {current_chapter_index}/{len(chapters_to_process)}")

    if current_chapter_index < len(chapters_to_process):
        print(f"➡️  继续处理第 {current_chapter_index + 1} 章")
        return "process_chapter"
    else:
        print(f"✅ 所有章节已处理完成")
        return "finalize_document"


def finalize_document_node(state: ResearchState) -> dict:
    """
    文档最终化节点
    
    将所有章节内容合并为最终文档
    
    Args:
        state: 研究状态
        
    Returns:
        dict: 包含 final_document 的字典
    """
    topic = state.get("topic", "")
    document_outline = state.get("document_outline", {})
    completed_chapters_content = state.get("completed_chapters_content", [])

    print(f"\n📑 开始生成最终文档")

    # 获取文档标题和摘要
    doc_title = document_outline.get("title", topic)
    doc_summary = document_outline.get("summary", "")

    # 构建最终文档
    final_document_parts = []

    # 添加标题
    final_document_parts.append(f"# {doc_title}\n")

    # 添加摘要
    if doc_summary:
        final_document_parts.append(f"## 摘要\n\n{doc_summary}\n")

    # 添加目录
    final_document_parts.append("\n## 目录\n")
    chapters = document_outline.get("chapters", [])
    for i, chapter in enumerate(chapters):
        chapter_title = chapter.get("chapter_title", f"第{i+1}章")
        final_document_parts.append(f"{i+1}. {chapter_title}\n")

    final_document_parts.append("\n---\n")

    # 添加所有章节内容
    for chapter_content in completed_chapters_content:
        final_document_parts.append(f"\n{chapter_content}\n")
        final_document_parts.append("\n---\n")

    # 合并为最终文档
    final_document = "\n".join(final_document_parts)

    print(f"✅ 最终文档生成完成，总长度: {len(final_document)} 字符")
    print(f"📊 包含 {len(completed_chapters_content)} 个章节")

    return {"final_document": final_document}


def build_main_orchestrator_graph(initial_research_node,
                                  outline_generation_node,
                                  split_chapters_node,
                                  chapter_workflow_graph,
                                  finalize_document_node_func=None):
    """
    构建主编排器图
    
    主工作流程：
    1. 初始研究 -> 生成大纲 -> 拆分章节
    2. 循环处理每个章节（调用章节子工作流）
    3. 所有章节完成后，生成最终文档
    
    Args:
        initial_research_node: 已绑定依赖的初始研究节点
        outline_generation_node: 已绑定依赖的大纲生成节点
        split_chapters_node: 章节拆分节点
        chapter_workflow_graph: 编译后的章节工作流图
        finalize_document_node_func: 可选的文档最终化节点函数
        
    Returns:
        CompiledGraph: 编译后的主编排器图
    """
    # 创建状态图
    workflow = StateGraph(ResearchState)

    # 创建章节处理节点
    chapter_processing_node = create_chapter_processing_node(
        chapter_workflow_graph)

    # 使用提供的或默认的文档最终化节点
    if finalize_document_node_func is None:
        finalize_document_node_func = finalize_document_node

    # 注册所有节点
    workflow.add_node("initial_research", initial_research_node)
    workflow.add_node("outline_generation", outline_generation_node)
    workflow.add_node("split_chapters", split_chapters_node)
    workflow.add_node("chapter_processing", chapter_processing_node)
    workflow.add_node("finalize_document", finalize_document_node_func)

    # 设置入口点
    workflow.set_entry_point("initial_research")

    # 添加顺序边
    workflow.add_edge("initial_research", "outline_generation")
    workflow.add_edge("outline_generation", "split_chapters")

    # 从 split_chapters 到条件决策点
    workflow.add_conditional_edges(
        "split_chapters", chapter_decision_function, {
            "process_chapter": "chapter_processing",
            "finalize_document": "finalize_document"
        })

    # 章节处理完成后，回到条件决策点（形成循环）
    workflow.add_conditional_edges(
        "chapter_processing",
        chapter_decision_function,
        {
            "process_chapter": "chapter_processing",  # 继续处理下一章
            "finalize_document": "finalize_document"  # 所有章节完成
        })

    # 最终化后结束
    workflow.add_edge("finalize_document", END)

    # 编译并返回图
    print("🏗️  主编排器图构建完成")
    return workflow.compile()
