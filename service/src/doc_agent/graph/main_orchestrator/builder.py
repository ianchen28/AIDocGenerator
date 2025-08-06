# service/src/doc_agent/graph/main_orchestrator/builder.py
import pprint
from typing import Any, Dict

from langgraph.graph import END, StateGraph
from loguru import logger

from doc_agent.graph.main_orchestrator import nodes
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients import get_llm_client
from doc_agent.llm_clients.base import LLMClient


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
        completed_chapters = state.get("completed_chapters", [])
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
        # 将新的 completed_chapters 结构转换为旧的 completed_chapters_content 格式以保持兼容性
        completed_chapters_content = []
        for chapter in completed_chapters:
            if isinstance(chapter, dict):
                completed_chapters_content.append(chapter.get("content", ""))
            else:
                completed_chapters_content.append(str(chapter))
        current_citation_index = state.get('current_citation_index', 0)

        chapter_workflow_input = {
            "topic":
            topic,
            "current_chapter_index":
            current_chapter_index,
            "chapters_to_process":
            chapters_to_process,
            "completed_chapters_content":
            completed_chapters_content,  # 关键：传递上下文
            "search_queries": [],  # 初始化搜索查询，planner节点会生成
            "research_plan":
            "",  # 初始化研究计划，planner节点会生成
            "gathered_sources": [],  # 初始化收集的源数据，researcher节点会填充
            "gathered_data":
            "",  # 保持向后兼容
            "messages": [],  # 新的消息历史
            # 传递风格指南和需求文档到章节工作流
            "current_citation_index":
            current_citation_index,
            "style_guide_content":
            state.get("style_guide_content"),
            "requirements_content":
            state.get("requirements_content"),
            # 传递完整的大纲信息，包括子节结构
            "document_outline":
            state.get("document_outline", {}),
            # 传递当前章节的子节信息
            "current_chapter_sub_sections":
            current_chapter.get("sub_sections", []) if current_chapter else []
        }

        logger.debug(
            f"Chapter workflow input state:\n{pprint.pformat(chapter_workflow_input)}"
        )

        try:
            # 调用章节工作流
            logger.info(f"🔄 调用章节工作流处理: {chapter_title}")
            chapter_result = await chapter_workflow_graph.ainvoke(
                chapter_workflow_input)

            # 详细的调试信息
            logger.info(f"📊 章节工作流输出键: {list(chapter_result.keys())}")
            logger.info(f"📊 章节工作流完整输出: {chapter_result}")

            # 检查关键字段是否存在
            if "final_document" in chapter_result:
                logger.info(
                    f"✅ 找到 final_document，长度: {len(chapter_result['final_document'])}"
                )
            else:
                logger.warning("⚠️  未找到 final_document 字段")

            if "cited_sources_in_chapter" in chapter_result:
                cited_sources = chapter_result["cited_sources_in_chapter"]
                logger.info(
                    f"✅ 找到 cited_sources_in_chapter，数量: {len(cited_sources)}")
                if cited_sources:
                    logger.info(
                        f"📚 引用源示例: {cited_sources[0].title if hasattr(cited_sources[0], 'title') else '无标题'}"
                    )
            else:
                logger.warning("⚠️  未找到 cited_sources_in_chapter 字段")

            cited_sources_in_chapter = chapter_result.get(
                "cited_sources_in_chapter", [])

            # 安全地计算最大引用索引
            if cited_sources_in_chapter and len(cited_sources_in_chapter) > 0:
                max_citation_index = max(
                    [source.id for source in cited_sources_in_chapter])
            else:
                max_citation_index = 0  # 如果没有引用源，使用默认值

            # 从结果中提取章节内容和引用源
            chapter_content = chapter_result.get("final_document", "")
            state["all_sources"].extend(cited_sources_in_chapter)

            if not chapter_content:
                logger.warning("⚠️  章节工作流未返回内容，使用默认内容")
                chapter_content = f"## {chapter_title}\n\n章节内容生成失败。"

            logger.info(f"✅ 章节处理完成，内容长度: {len(chapter_content)} 字符")
            logger.info(
                f"📚 章节引用源数量: {len(chapter_result.get('cited_sources_in_chapter', []))}"
            )

            # 生成章节摘要
            logger.info(f"📝 开始生成章节摘要: {chapter_title}")
            try:
                # 获取 LLM 客户端
                llm_client = get_llm_client()

                # 创建摘要提示
                summary_prompt = f"""请为以下章节内容生成一个简洁的摘要，控制在200字以内：

章节标题：{chapter_title}

章节内容：
{chapter_content}

请生成一个简洁的摘要，突出章节的主要观点和关键信息："""

                # 调用 LLM 生成摘要
                current_chapter_summary = llm_client.invoke(summary_prompt,
                                                            temperature=0.3,
                                                            max_tokens=300)

                logger.info(
                    f"✅ 章节摘要生成完成，长度: {len(current_chapter_summary)} 字符")

            except Exception as e:
                logger.warning(f"⚠️  章节摘要生成失败: {str(e)}")
                current_chapter_summary = f"章节摘要生成失败: {str(e)}"

            # 更新章节索引
            state['current_citation_index'] = max_citation_index

            # 创建新完成的章节字典
            newly_completed_chapter = {
                "title": chapter_title,
                "content": chapter_content,
                "summary": current_chapter_summary
            }

            # 获取现有的已完成章节列表
            completed_chapters = state.get("completed_chapters", [])
            updated_completed_chapters = completed_chapters.copy()
            updated_completed_chapters.append(newly_completed_chapter)

            # 更新 writer_steps 计数器
            current_writer_steps = state.get("writer_steps", 0)
            updated_writer_steps = current_writer_steps + 1

            logger.info(
                f"📊 进度: {state['current_chapter_index']}/{len(chapters_to_process)} 章节已完成"
            )
            logger.info(f"📚 全局引用源总数: {len(state['all_sources'])}")
            logger.info(f"✍️  Writer步骤计数: {updated_writer_steps}")

            return {
                "completed_chapters": updated_completed_chapters,
                "current_citation_index": state['current_citation_index'],
                "current_chapter_index":
                state['current_chapter_index'] + 1,  # 🔧 修复：递增章节索引
                "cited_sources": state["all_sources"],
                "writer_steps": updated_writer_steps
            }

        except Exception as e:
            logger.error(f"❌ 章节处理失败: {str(e)}")
            # 失败时仍然推进索引，避免无限循环
            # 更新 writer_steps 计数器（即使失败也计数）
            current_writer_steps = state.get("writer_steps", 0)
            updated_writer_steps = current_writer_steps + 1

            # 创建失败章节的字典
            failed_chapter = {
                "title": chapter_title,
                "content": f"## {chapter_title}\n\n章节处理失败: {str(e)}",
                "summary": f"章节处理失败: {str(e)}"
            }

            # 获取现有的已完成章节列表
            completed_chapters = state.get("completed_chapters", [])
            updated_completed_chapters = completed_chapters.copy()
            updated_completed_chapters.append(failed_chapter)

            return {
                "completed_chapters": updated_completed_chapters,
                "current_citation_index": state['current_citation_index'],
                "current_chapter_index":
                state['current_chapter_index'] + 1,  # 🔧 修复：失败时也要递增索引
                "cited_sources": state["all_sources"],
                "writer_steps": updated_writer_steps
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
    completed_chapters = state.get("completed_chapters", [])

    logger.info(f"\n📑 开始生成最终文档")

    # 获取文档标题和摘要
    doc_title = document_outline.get("title", topic)
    doc_summary = document_outline.get("summary", "")

    # 从新的 completed_chapters 结构中提取内容
    completed_chapters_content = []
    for chapter in completed_chapters:
        if isinstance(chapter, dict):
            completed_chapters_content.append(chapter.get("content", ""))
        else:
            completed_chapters_content.append(str(chapter))

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
        # 兼容新旧格式
        chapter_title = chapter.get('title',
                                    chapter.get('chapter_title', f'第{i+1}章'))
        chapter_number = chapter.get('number',
                                     chapter.get('chapter_number', i + 1))
        final_document_parts.append(f"{chapter_number}. {chapter_title}\n")

    final_document_parts.append("\n---\n")

    # 添加所有章节内容（进行格式清理）
    for i, chapter_content in enumerate(completed_chapters_content):
        # 获取章节信息用于标题编号
        chapter_info = chapters[i] if i < len(chapters) else {}
        chapter_number = chapter_info.get(
            'number', chapter_info.get('chapter_number', i + 1))
        chapter_title = chapter_info.get(
            'title', chapter_info.get('chapter_title', f'第{i+1}章'))

        cleaned_content = _clean_chapter_content(chapter_content,
                                                 chapter_number, chapter_title)
        final_document_parts.append(f"\n{cleaned_content}\n")
        final_document_parts.append("\n---\n")

    # 参考文献将由 bibliography_node 在后续步骤中添加
    logger.info("📚 参考文献将在后续步骤中由 bibliography_node 添加")

    # 合并为最终文档
    final_document = "\n".join(final_document_parts)

    logger.info(f"✅ 最终文档生成完成，总长度: {len(final_document)} 字符")
    logger.info(f"📖 包含 {len(completed_chapters_content)} 个章节")

    return {"final_document": final_document}


def _clean_chapter_content(content: str,
                           chapter_number: int = None,
                           chapter_title: str = "") -> str:
    """
    清理章节内容格式
    
    Args:
        content: 原始章节内容
        chapter_number: 章节编号
        chapter_title: 章节标题
        
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
        # 处理章节标题：将 ## 章节标题 转换为 ## 编号. 章节标题
        if line.startswith('## ') and not line.startswith('### '):
            # 这是章节标题，需要添加编号
            if chapter_number and chapter_title:
                # 如果标题已经包含编号，保持不变
                if line.strip() == f"## {chapter_title}":
                    line = f"## {chapter_number}. {chapter_title}"
                else:
                    # 否则使用提供的编号和标题
                    line = f"## {chapter_number}. {chapter_title}"
            # 保持二级标题层级不变

        # 处理子节标题：将 ### 子节标题 转换为 ### 编号. 子节标题
        elif line.startswith('### ') and not line.startswith('#### '):
            # 这是子节标题，保持三级标题层级
            pass

        # 处理子节的子节标题：将 #### 子节标题 转换为 #### 编号. 子节标题
        elif line.startswith('#### ') and not line.startswith('##### '):
            # 这是子节的子节标题，保持四级标题层级
            pass

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
                                  fusion_editor_node=None,
                                  finalize_document_node_func=None,
                                  bibliography_node_func=None):
    """
    构建主编排器图
    
    主工作流程：
    1. 初始研究 -> 生成大纲 -> 拆分章节
    2. 循环处理每个章节（调用章节子工作流）
    3. 所有章节完成后，进入融合编辑器进行润色
    4. 融合编辑后，生成最终文档
    5. 生成参考文献
    
    Args:
        initial_research_node: 已绑定依赖的初始研究节点
        outline_generation_node: 已绑定依赖的大纲生成节点
        split_chapters_node: 章节拆分节点
        chapter_workflow_graph: 编译后的章节工作流图
        fusion_editor_node: 可选的融合编辑器节点函数
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

    # 使用提供的或默认的融合编辑器节点
    if fusion_editor_node is None:
        fusion_editor_node = nodes.fusion_editor_node

    # 使用提供的或默认的参考文献生成节点
    if bibliography_node_func is None:
        bibliography_node_func = nodes.bibliography_node

    # 注册所有节点
    workflow.add_node("initial_research", initial_research_node)
    workflow.add_node("outline_generation", outline_generation_node)
    workflow.add_node("split_chapters", split_chapters_node)
    workflow.add_node("chapter_processing", chapter_processing_node)
    workflow.add_node("finalize_document", finalize_document_node_func)
    workflow.add_node("fusion_editor", fusion_editor_node)
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
            "finalize_document": "fusion_editor"  # 所有章节完成，进入融合编辑
        })

    # 融合编辑后进入文档最终化
    workflow.add_edge("fusion_editor", "finalize_document")

    # 文档最终化后进入参考文献生成
    workflow.add_edge("finalize_document", "generate_bibliography")

    # 参考文献生成后结束
    workflow.add_edge("generate_bibliography", END)

    # 编译并返回图
    logger.info("🏗️  主编排器图构建完成")
    return workflow.compile()


def build_outline_graph(initial_research_node, outline_generation_node):
    """
    构建大纲生成图
    
    流程：entry -> initial_research_node -> outline_generation_node -> END
    
    Args:
        initial_research_node: 已绑定依赖的初始研究节点
        outline_generation_node: 已绑定依赖的大纲生成节点
        
    Returns:
        CompiledGraph: 编译后的大纲生成图
    """
    # 创建状态图
    workflow = StateGraph(ResearchState)

    # 注册节点
    workflow.add_node("initial_research", initial_research_node)
    workflow.add_node("outline_generation", outline_generation_node)

    # 设置入口点
    workflow.set_entry_point("initial_research")

    # 添加顺序边
    workflow.add_edge("initial_research", "outline_generation")
    workflow.add_edge("outline_generation", END)

    # 编译并返回图
    logger.info("🏗️  大纲生成图构建完成")
    return workflow.compile()


def build_document_graph(chapter_workflow_graph,
                         split_chapters_node,
                         fusion_editor_node=None,
                         finalize_document_node_func=None,
                         bibliography_node_func=None):
    """
    构建文档生成图
    
    流程：entry -> split_chapters_node -> (章节处理循环) -> fusion_editor_node -> finalize_document_node -> bibliography_node -> END
    
    Args:
        chapter_workflow_graph: 编译后的章节工作流图
        split_chapters_node: 章节拆分节点
        fusion_editor_node: 可选的融合编辑器节点函数
        finalize_document_node_func: 可选的文档最终化节点函数
        bibliography_node_func: 可选的参考文献生成节点函数
        
    Returns:
        CompiledGraph: 编译后的文档生成图
    """
    # 创建状态图
    workflow = StateGraph(ResearchState)

    # 创建章节处理节点
    chapter_processing_node = create_chapter_processing_node(
        chapter_workflow_graph)

    # 使用提供的或默认的节点函数
    if fusion_editor_node is None:
        fusion_editor_node = nodes.fusion_editor_node

    if finalize_document_node_func is None:
        finalize_document_node_func = finalize_document_node

    if bibliography_node_func is None:
        bibliography_node_func = nodes.bibliography_node

    # 注册所有节点
    workflow.add_node("split_chapters", split_chapters_node)
    workflow.add_node("chapter_processing", chapter_processing_node)
    workflow.add_node("fusion_editor", fusion_editor_node)
    workflow.add_node("finalize_document", finalize_document_node_func)
    workflow.add_node("generate_bibliography", bibliography_node_func)

    # 设置入口点
    workflow.set_entry_point("split_chapters")

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
            "finalize_document": "fusion_editor"  # 所有章节完成，进入融合编辑
        })

    # 融合编辑后进入文档最终化
    workflow.add_edge("fusion_editor", "finalize_document")

    # 最终化后进入参考文献生成
    workflow.add_edge("finalize_document", "generate_bibliography")

    # 参考文献生成后结束
    workflow.add_edge("generate_bibliography", END)

    # 编译并返回图
    logger.info("🏗️  文档生成图构建完成")
    return workflow.compile()
