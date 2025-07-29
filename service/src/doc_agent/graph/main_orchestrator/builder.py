# service/src/doc_agent/graph/main_orchestrator/builder.py
from loguru import logger
import pprint
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

        logger.info(
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
            "gathered_sources": [],  # 初始化收集的源数据，researcher节点会填充
            "gathered_data": "",  # 保持向后兼容
            "messages": []  # 新的消息历史
        }

        logger.debug(
            f"Chapter workflow input state:\n{pprint.pformat(chapter_workflow_input)}"
        )

        try:
            # 调用章节工作流
            logger.info(f"🔄 调用章节工作流处理: {chapter_title}")
            chapter_result = await chapter_workflow_graph.ainvoke(
                chapter_workflow_input)

            # 调试：打印章节工作流的完整输出
            logger.info(f"📊 章节工作流输出键: {list(chapter_result.keys())}")
            logger.info(f"📊 章节工作流输出: {chapter_result}")

            # 从结果中提取章节内容和引用源
            chapter_content = chapter_result.get("final_document", "")
            cited_sources_in_chapter = chapter_result.get(
                "cited_sources_in_chapter", [])

            if not chapter_content:
                logger.warning(f"⚠️  章节工作流未返回内容，使用默认内容")
                chapter_content = f"## {chapter_title}\n\n章节内容生成失败。"

            logger.info(f"✅ 章节处理完成，内容长度: {len(chapter_content)} 字符")
            logger.info(f"📚 章节引用源数量: {len(cited_sources_in_chapter)}")

            # 更新已完成章节列表
            updated_completed_chapters = completed_chapters_content.copy()
            updated_completed_chapters.append(chapter_content)

            # 更新章节索引
            updated_chapter_index = current_chapter_index + 1

            # 更新全局引用源
            current_cited_sources = state.get("cited_sources", {})
            updated_cited_sources = current_cited_sources.copy()

            # 将章节的引用源添加到全局引用源中
            for source in cited_sources_in_chapter:
                if hasattr(source, 'id'):
                    updated_cited_sources[source.id] = source
                    logger.debug(f"📚 添加引用源到全局: [{source.id}] {source.title}")

            logger.info(
                f"📊 进度: {updated_chapter_index}/{len(chapters_to_process)} 章节已完成"
            )
            logger.info(f"📚 全局引用源总数: {len(updated_cited_sources)}")

            return {
                "completed_chapters_content": updated_completed_chapters,
                "current_chapter_index": updated_chapter_index,
                "cited_sources": updated_cited_sources
            }

        except Exception as e:
            logger.error(f"❌ 章节处理失败: {str(e)}")
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

    logger.info(
        f"\n🤔 章节处理决策: {current_chapter_index}/{len(chapters_to_process)}")

    if current_chapter_index < len(chapters_to_process):
        logger.info(f"➡️  继续处理第 {current_chapter_index + 1} 章")
        return "process_chapter"
    else:
        logger.info(f"✅ 所有章节已处理完成")
        return "finalize_document"


def finalize_document_node(state: ResearchState) -> dict:
    """
    文档最终化节点
    
    将所有章节内容合并为最终文档，并进行格式清理
    
    Args:
        state: 研究状态
        
    Returns:
        dict: 包含 final_document 的字典
    """
    topic = state.get("topic", "")
    document_outline = state.get("document_outline", {})
    completed_chapters_content = state.get("completed_chapters_content", [])

    logger.info(f"\n📑 开始生成最终文档")

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

    # 添加所有章节内容（进行格式清理）
    for chapter_content in completed_chapters_content:
        cleaned_content = _clean_chapter_content(chapter_content)
        final_document_parts.append(f"\n{cleaned_content}\n")
        final_document_parts.append("\n---\n")

    # 合并为最终文档
    final_document = "\n".join(final_document_parts)

    logger.info(f"✅ 最终文档生成完成，总长度: {len(final_document)} 字符")
    logger.info(f"📊 包含 {len(completed_chapters_content)} 个章节")

    return {"final_document": final_document}


def _clean_chapter_content(content: str) -> str:
    """
    清理章节内容格式
    
    Args:
        content: 原始章节内容
        
    Returns:
        str: 清理后的内容
    """
    if not content:
        return content

    # 1. 移除 markdown 代码块标记
    # 移除开头的 ```markdown 或 ``` 标记
    content = content.strip()
    if content.startswith("```markdown"):
        content = content[11:]  # 移除 ```markdown
    elif content.startswith("```"):
        content = content[3:]  # 移除 ```

    # 移除结尾的 ``` 标记
    if content.endswith("```"):
        content = content[:-3]

    # 2. 调整标题层级
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        # 将一级标题 (# 标题) 降级为二级标题 (## 标题)
        if line.startswith('# ') and not line.startswith('## '):
            # 这是一级标题，需要降级
            line = '#' + line  # 添加一个 # 变成二级标题

        # 将二级标题 (## 标题) 降级为三级标题 (### 标题)
        elif line.startswith('## ') and not line.startswith('### '):
            # 这是二级标题，需要降级
            line = '#' + line  # 添加一个 # 变成三级标题

        # 将三级标题 (### 标题) 降级为四级标题 (#### 标题)
        elif line.startswith('### ') and not line.startswith('#### '):
            # 这是三级标题，需要降级
            line = '#' + line  # 添加一个 # 变成四级标题

        cleaned_lines.append(line)

    # 重新组合内容
    cleaned_content = '\n'.join(cleaned_lines)

    # 3. 移除多余的空行
    # 将连续的空行压缩为最多两个空行
    import re
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)

    return cleaned_content.strip()


def build_main_orchestrator_graph(initial_research_node,
                                  outline_generation_node,
                                  split_chapters_node,
                                  chapter_workflow_graph,
                                  finalize_document_node_func=None,
                                  bibliography_node_func=None):
    """
    构建主编排器图
    
    主工作流程：
    1. 初始研究 -> 生成大纲 -> 拆分章节
    2. 循环处理每个章节（调用章节子工作流）
    3. 所有章节完成后，生成最终文档
    4. 生成参考文献
    
    Args:
        initial_research_node: 已绑定依赖的初始研究节点
        outline_generation_node: 已绑定依赖的大纲生成节点
        split_chapters_node: 章节拆分节点
        chapter_workflow_graph: 编译后的章节工作流图
        finalize_document_node_func: 可选的文档最终化节点函数
        bibliography_node_func: 可选的参考文献生成节点函数
        
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

    # 使用提供的或默认的参考文献生成节点
    if bibliography_node_func is None:
        bibliography_node_func = nodes.bibliography_node

    # 注册所有节点
    workflow.add_node("initial_research", initial_research_node)
    workflow.add_node("outline_generation", outline_generation_node)
    workflow.add_node("split_chapters", split_chapters_node)
    workflow.add_node("chapter_processing", chapter_processing_node)
    workflow.add_node("finalize_document", finalize_document_node_func)
    workflow.add_node("generate_bibliography", bibliography_node_func)

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

    # 最终化后进入参考文献生成
    workflow.add_edge("finalize_document", "generate_bibliography")

    # 参考文献生成后结束
    workflow.add_edge("generate_bibliography", END)

    # 编译并返回图
    logger.info("🏗️  主编排器图构建完成")
    return workflow.compile()
