# service/src/doc_agent/graph/chapter_workflow/nodes.py
import pprint
import sys
import re
from pathlib import Path
from typing import Any

from loguru import logger

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir and str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 添加src目录到Python路径
if service_dir:
    src_dir = service_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

# 导入项目内部模块
from core.config import settings

from ...common import parse_planner_response
from ...common.prompt_selector import PromptSelector
from ...llm_clients.base import LLMClient
from ...llm_clients.providers import EmbeddingClient
from ...tools.es_search import ESSearchTool
from ...tools.reranker import RerankerTool
from ...tools.web_search import WebSearchTool
from ...utils.search_utils import search_and_rerank
from ..state import ResearchState
from ...schemas import Source


def planner_node(state: ResearchState,
                 llm_client: LLMClient,
                 prompt_selector: PromptSelector,
                 genre: str = "default") -> dict[str, Any]:
    """
    节点1: 规划研究步骤
    从状态中获取 topic 和当前章节信息，创建 prompt 调用 LLM 生成研究计划和搜索查询
    Args:
        state: 研究状态，包含 topic 和当前章节信息
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
    Returns:
        dict: 包含 research_plan 和 search_queries 的字典
    """
    topic = state.get("topic", "")
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])

    if not topic:
        raise ValueError("Topic is required in state")

    # 获取当前章节信息
    current_chapter = None
    if current_chapter_index < len(chapters_to_process):
        current_chapter = chapters_to_process[current_chapter_index]

    chapter_title = current_chapter.get("chapter_title",
                                        "") if current_chapter else ""
    chapter_description = current_chapter.get("description",
                                              "") if current_chapter else ""

    logger.info(f"📋 规划章节研究: {chapter_title}")
    logger.info(f"📝 章节描述: {chapter_description}")

    # 获取任务规划器配置
    task_planner_config = settings.get_agent_component_config("task_planner")
    if not task_planner_config:
        raise ValueError("Task planner configuration not found")

    # 使用 PromptSelector 获取 prompt 模板
    try:
        prompt_template = prompt_selector.get_prompt("chapter_workflow",
                                                     "planner", genre)
        logger.debug(f"✅ 成功获取 planner prompt 模板，genre: {genre}")
    except Exception as e:
        logger.error(f"❌ 获取 planner prompt 模板失败: {e}")
        # 使用 prompts/planner.py 中的备用模板
        try:
            from ...prompts.planner import PROMPTS
            prompt_template = PROMPTS.get("v1_fallback", PROMPTS["v1_default"])
            logger.debug("✅ 成功获取 planner 备用模板")
        except Exception as e2:
            logger.error(f"❌ 获取 planner 备用模板也失败: {e2}")
            # 最后的备用方案
            prompt_template = """
你是一个专业的研究规划专家。请为以下章节制定详细的研究计划和搜索策略。

**文档主题:** {topic}

**当前章节信息:**
- 章节标题: {chapter_title}
- 章节描述: {chapter_description}

**任务要求:**
1. 分析章节主题，确定研究重点和方向
2. 制定详细的研究计划，包括研究步骤和方法
3. 生成5-8个高质量的搜索查询，用于收集相关信息
4. 确保搜索查询具有针对性和全面性

**输出格式:**
请以JSON格式返回结果，包含以下字段：
- research_plan: 详细的研究计划
- search_queries: 搜索查询列表（数组）

请立即开始制定研究计划。
"""

    # 创建研究计划生成的 prompt，要求 JSON 格式响应
    prompt = prompt_template.format(topic=topic,
                                    chapter_title=chapter_title,
                                    chapter_description=chapter_description)

    logger.debug(f"Invoking LLM with prompt:\n{pprint.pformat(prompt)}")

    try:
        # 调用 LLM 生成研究计划
        response = llm_client.invoke(
            prompt,
            temperature=task_planner_config.temperature,
            max_tokens=task_planner_config.max_tokens,
            **task_planner_config.extra_params)

        logger.debug(f"🔍 LLM原始响应: {repr(response)}")
        logger.debug(f"📝 响应长度: {len(response)} 字符")
        logger.info(f"🔍 LLM响应内容:\n{response}")

        # 解析 JSON 响应
        research_plan, search_queries = parse_planner_response(response)

        # 应用搜索轮数限制
        max_search_rounds = getattr(settings.search_config,
                                    'max_search_rounds', 5)
        logger.info(f"📊 planner_node 当前搜索轮数配置: {max_search_rounds}")

        if len(search_queries) > max_search_rounds:
            logger.info(
                f"📊 限制搜索查询数量: {len(search_queries)} -> {max_search_rounds}")
            search_queries = search_queries[:max_search_rounds]

        logger.info(f"✅ 生成研究计划: {len(search_queries)} 个搜索查询")
        for i, query in enumerate(search_queries, 1):
            logger.debug(f"  {i}. {query}")

        # 返回完整的状态更新
        result = {
            "research_plan": research_plan,
            "search_queries": search_queries
        }
        logger.debug(f"📤 Planner节点返回结果: {pprint.pformat(result)}")
        return result

    except Exception as e:
        # 如果 LLM 调用失败，返回默认计划
        logger.error(f"Planner node error: {str(e)}")
        default_queries = [
            f"{topic} {chapter_title} 概述", f"{topic} {chapter_title} 主要内容",
            f"{topic} {chapter_title} 关键要点", f"{topic} {chapter_title} 最新发展",
            f"{topic} {chapter_title} 重要性"
        ]
        logger.warning(f"⚠️  使用默认搜索查询: {len(default_queries)} 个")
        for i, query in enumerate(default_queries, 1):
            logger.debug(f"  {i}. {query}")

        result = {
            "research_plan": f"研究计划：对章节 {chapter_title} 进行深入研究，收集相关信息并整理成文档。",
            "search_queries": default_queries
        }
        logger.debug(f"📤 Planner节点返回默认结果: {pprint.pformat(result)}")
        return result


def researcher_node(state: ResearchState,
                    web_search_tool: WebSearchTool) -> dict[str, Any]:
    """已废弃，请使用 async_researcher_node"""
    raise NotImplementedError("请使用 async_researcher_node")


async def async_researcher_node(
        state: ResearchState,
        web_search_tool: WebSearchTool,
        es_search_tool: ESSearchTool,
        reranker_tool: RerankerTool = None) -> dict[str, Any]:
    """
    异步节点2: 执行搜索研究
    从状态中获取 search_queries，使用搜索工具收集相关信息
    优先使用向量检索，如果失败则回退到文本搜索
    使用重排序工具对搜索结果进行优化
    Args:
        state: 研究状态，包含 search_queries
        web_search_tool: 网络搜索工具
        es_search_tool: Elasticsearch搜索工具
        reranker_tool: 重排序工具（可选）
    Returns:
        dict: 包含 gathered_sources 的字典，包含 Source 对象列表
    """
    logger.info("🔍 Researcher节点接收到的完整状态:")
    logger.debug(f"  - topic: {state.get('topic', 'N/A')}")
    logger.debug(
        f"  - current_chapter_index: {state.get('current_chapter_index', 'N/A')}"
    )
    logger.debug(
        f"  - research_plan: {state.get('research_plan', 'N/A')[:100]}...")
    logger.debug(f"  - search_queries: {state.get('search_queries', [])}")
    logger.debug(
        f"  - search_queries类型: {type(state.get('search_queries', []))}")
    logger.debug(
        f"  - search_queries长度: {len(state.get('search_queries', []))}")
    logger.debug(
        f"  - gathered_data: {state.get('gathered_data', 'N/A')[:50]}...")

    search_queries = state.get("search_queries", [])

    if not search_queries:
        logger.warning("❌ 没有搜索查询，返回默认消息")
        return {"gathered_sources": []}

    all_sources = []  # 存储所有 Source 对象
    source_id_counter = 1  # 源ID计数器

    # 获取embedding配置
    embedding_config = settings.supported_models.get("gte_qwen")
    embedding_client = None
    if embedding_config:
        try:
            embedding_client = EmbeddingClient(
                base_url=embedding_config.url,
                api_key=embedding_config.api_key)
            logger.info("✅ Embedding客户端初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  Embedding客户端初始化失败: {str(e)}")
            embedding_client = None
    else:
        logger.warning("❌ 未找到 embedding 配置，将使用文本搜索")

    # 获取配置参数 - 使用快速模式以加快测试
    doc_config = settings.get_document_config(fast_mode=True)
    initial_top_k = doc_config.get('vector_recall_size', 10)
    final_top_k = doc_config.get('rerank_size', 5)

    # 限制搜索查询数量以加快测试
    max_queries = settings.search_config.max_queries
    if len(search_queries) > max_queries:
        logger.info(f"🔧 限制搜索查询数量从 {len(search_queries)} 到 {max_queries}")
        search_queries = search_queries[:max_queries]

    # 使用传入的ES工具，不再内部创建
    for i, query in enumerate(search_queries, 1):
        logger.info(f"执行搜索查询 {i}/{len(search_queries)}: {query}")

        # 网络搜索
        web_results = ""
        try:
            # 使用异步搜索方法
            web_results = await web_search_tool.search_async(query)
            if "模拟" in web_results or "mock" in web_results.lower():
                logger.info(f"网络搜索返回模拟结果，跳过: {query}")
                web_results = ""
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_results = ""

        # ES搜索 - 使用新的搜索和重排序功能
        es_results = ""
        try:
            if embedding_client:
                # 尝试向量检索
                try:
                    embedding_response = embedding_client.invoke(query)
                    import json
                    try:
                        embedding_data = json.loads(embedding_response)
                        if isinstance(embedding_data, list):
                            if len(embedding_data) > 0 and isinstance(
                                    embedding_data[0], list):
                                query_vector = embedding_data[0]
                            else:
                                query_vector = embedding_data
                        elif isinstance(embedding_data,
                                        dict) and 'data' in embedding_data:
                            query_vector = embedding_data['data']
                        else:
                            logger.warning(
                                f"⚠️  无法解析embedding响应格式: {type(embedding_data)}"
                            )
                            query_vector = None
                    except json.JSONDecodeError:
                        logger.warning("⚠️  JSON解析失败，使用文本搜索")
                        query_vector = None

                    if query_vector and len(query_vector) == 1536:
                        logger.debug(
                            f"✅ 向量维度: {len(query_vector)}，前5: {query_vector[:5]}"
                        )
                        # 使用新的搜索和重排序功能
                        search_query = query if query.strip() else "相关文档"

                        _, reranked_results, formatted_es_results = await search_and_rerank(
                            es_search_tool=es_search_tool,
                            query=search_query,
                            query_vector=query_vector,
                            reranker_tool=reranker_tool,
                            initial_top_k=initial_top_k,
                            final_top_k=final_top_k,
                            config=doc_config)
                        es_results = formatted_es_results
                        logger.info(
                            f"✅ 向量检索+重排序执行成功，结果长度: {len(formatted_es_results)}"
                        )
                    else:
                        logger.warning("❌ 向量生成失败，使用文本搜索")
                        # 回退到文本搜索
                        _, reranked_results, formatted_es_results = await search_and_rerank(
                            es_search_tool=es_search_tool,
                            query=query,
                            query_vector=None,
                            reranker_tool=reranker_tool,
                            initial_top_k=initial_top_k,
                            final_top_k=final_top_k,
                            config=doc_config)
                        es_results = formatted_es_results
                        logger.info(
                            f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}"
                        )
                except Exception as e:
                    logger.error(f"❌ 向量检索异常: {str(e)}，使用文本搜索")
                    # 回退到文本搜索
                    _, reranked_results, formatted_es_results = await search_and_rerank(
                        es_search_tool=es_search_tool,
                        query=query,
                        query_vector=None,
                        reranker_tool=reranker_tool,
                        initial_top_k=initial_top_k,
                        final_top_k=final_top_k,
                        config=doc_config)
                    es_results = formatted_es_results
                    logger.info(
                        f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}")
            else:
                # 没有embedding客户端，直接使用文本搜索
                logger.info("📝 使用文本搜索")

                _, reranked_results, formatted_es_results = await search_and_rerank(
                    es_search_tool=es_search_tool,
                    query=query,
                    query_vector=None,
                    reranker_tool=reranker_tool,
                    initial_top_k=initial_top_k,
                    final_top_k=final_top_k,
                    config=doc_config)
                es_results = formatted_es_results
                logger.info(
                    f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}")

        except Exception as e:
            logger.error(f"❌ ES搜索失败: {str(e)}")
            es_results = f"ES搜索失败: {str(e)}"

        # 处理网络搜索结果
        if web_results and web_results.strip():
            try:
                # 解析网络搜索结果，创建 Source 对象
                web_sources = _parse_web_search_results(
                    web_results, query, source_id_counter)
                all_sources.extend(web_sources)
                source_id_counter += len(web_sources)
                logger.info(f"✅ 从网络搜索中提取到 {len(web_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析网络搜索结果失败: {str(e)}")

        # 处理ES搜索结果
        if es_results and es_results.strip():
            try:
                # 解析ES搜索结果，创建 Source 对象
                es_sources = _parse_es_search_results(es_results, query,
                                                      source_id_counter)
                all_sources.extend(es_sources)
                source_id_counter += len(es_sources)
                logger.info(f"✅ 从ES搜索中提取到 {len(es_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析ES搜索结果失败: {str(e)}")

    # 返回结构化的源列表
    logger.info(f"✅ 总共收集到 {len(all_sources)} 个信息源")
    for i, source in enumerate(all_sources[:5], 1):  # 只显示前5个源作为预览
        logger.debug(
            f"  {i}. [{source.id}] {source.title} ({source.source_type})")

    return {"gathered_sources": all_sources}


def writer_node(state: ResearchState,
                llm_client: LLMClient,
                prompt_selector: PromptSelector,
                genre: str = "default",
                prompt_version: str = "v3_context_aware") -> dict[str, Any]:
    """
    章节写作节点
    基于当前章节的研究数据和已完成章节的上下文，生成当前章节的内容
    支持引用工作流，自动处理引用标记和源追踪
    Args:
        state: 研究状态，包含章节信息、研究数据和已完成章节
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
    Returns:
        dict: 包含当前章节内容和引用源的字典
    """
    # 获取基本信息
    topic = state.get("topic", "")
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])
    completed_chapters_content = state.get("completed_chapters_content", [])
    completed_chapters = state.get("completed_chapters", [])

    # 验证当前章节索引
    if current_chapter_index >= len(chapters_to_process):
        raise ValueError(f"章节索引 {current_chapter_index} 超出范围")

    # 获取当前章节信息
    current_chapter = chapters_to_process[current_chapter_index]
    chapter_title = current_chapter.get("chapter_title", "")
    chapter_description = current_chapter.get("description", "")

    # 从状态中获取研究数据
    gathered_sources = state.get("gathered_sources", [])
    gathered_data = state.get("gathered_data", "")  # 保持向后兼容

    if not chapter_title:
        raise ValueError("章节标题不能为空")

    # 构建滑动窗口 + 全局摘要上下文
    context_for_writing = ""
    if completed_chapters:
        # 获取最后一章的完整内容（滑动窗口）
        last_chapter = completed_chapters[-1]
        if isinstance(last_chapter, dict) and "content" in last_chapter:
            context_for_writing += f"**Context from the previous chapter (Full Text):**\n{last_chapter['content']}\n\n"
            logger.info(
                f"📖 添加前一章完整内容到上下文，长度: {len(last_chapter['content'])} 字符")

        # 如果有更多章节，获取早期章节的摘要（全局摘要）
        if len(completed_chapters) > 1:
            earlier_summaries = []
            for chapter in completed_chapters[:-1]:  # 除了最后一章的所有章节
                if isinstance(chapter, dict) and "summary" in chapter:
                    earlier_summaries.append(chapter["summary"])
                elif isinstance(chapter, dict) and "content" in chapter:
                    # 如果没有摘要，使用内容的前200字符作为摘要
                    content = chapter["content"]
                    summary = content[:200] + "..." if len(
                        content) > 200 else content
                    earlier_summaries.append(summary)

            if earlier_summaries:
                context_for_writing += f"**Context from earlier chapters (Summaries):**\n" + "\n\n".join(
                    earlier_summaries)
                logger.info(f"📚 添加 {len(earlier_summaries)} 个早期章节摘要到上下文")

    if not context_for_writing:
        context_for_writing = "这是第一章，没有前置内容。"
        logger.info("📝 这是第一章，使用默认上下文")

    # 如果没有收集到源数据，尝试使用旧的 gathered_data
    if not gathered_sources and not gathered_data:
        return {
            "final_document": f"## {chapter_title}\n\n由于没有收集到相关数据，无法生成章节内容。",
            "cited_sources_in_chapter": []
        }

    # 格式化可用信息源列表
    available_sources_text = ""
    if gathered_sources:
        available_sources_text = "可用信息源列表:\n\n"
        for source in gathered_sources:
            available_sources_text += f"[Source {source.id}] {source.title}\n"
            available_sources_text += f"  类型: {source.source_type}\n"
            if source.url:
                available_sources_text += f"  URL: {source.url}\n"
            available_sources_text += f"  内容: {source.content[:200]}...\n\n"

        # 同时保持向后兼容的 gathered_data
        gathered_data = _format_sources_to_text(gathered_sources)
    elif not gathered_data:
        gathered_data = "没有收集到相关数据"

    # 获取文档生成器配置
    document_writer_config = settings.get_agent_component_config(
        "document_writer")
    if not document_writer_config:
        temperature = 0.7
        max_tokens = 4000
        extra_params = {}
    else:
        temperature = document_writer_config.temperature
        max_tokens = document_writer_config.max_tokens
        extra_params = document_writer_config.extra_params

    # 构建已完成章节的上下文摘要
    previous_chapters_context = ""
    if completed_chapters_content:
        previous_chapters_context = "\n\n".join([
            f"第{i+1}章摘要:\n{content[:500]}..."
            if len(content) > 500 else f"第{i+1}章:\n{content}"
            for i, content in enumerate(completed_chapters_content)
        ])

    # 获取样式指南内容
    style_guide_content = state.get("style_guide_content")

    # 使用 PromptSelector 获取 prompt 模板
    try:
        # 根据指定的 prompt_version 获取模板
        from ...prompts.writer import PROMPTS

        # 如果有样式指南，优先使用 v4_with_style_guide 版本
        if style_guide_content and style_guide_content.strip():
            if "v4_with_style_guide" in PROMPTS:
                prompt_template = PROMPTS["v4_with_style_guide"]
                logger.info(f"✅ 使用 v4_with_style_guide 版本，检测到样式指南")
            else:
                # 如果没有 v4 版本，回退到指定版本
                prompt_template = PROMPTS.get(prompt_version,
                                              PROMPTS.get("v3_context_aware"))
                logger.warning(
                    f"⚠️  v4_with_style_guide 版本不存在，回退到 {prompt_version}")
        else:
            # 没有样式指南，使用指定版本
            if prompt_version in PROMPTS:
                prompt_template = PROMPTS[prompt_version]
                logger.debug(f"✅ 成功获取 writer {prompt_version} prompt 模板")
            elif "v3_context_aware" in PROMPTS:
                prompt_template = PROMPTS["v3_context_aware"]
                logger.debug(f"✅ 回退到 writer v3_context_aware prompt 模板")
            elif "v2_with_citations" in PROMPTS:
                prompt_template = PROMPTS["v2_with_citations"]
                logger.debug(f"✅ 回退到 writer v2_with_citations prompt 模板")
            else:
                raise KeyError(
                    f"指定的 prompt_version '{prompt_version}' 和备用版本都不存在")
    except Exception as e:
        logger.warning(f"⚠️  获取 {prompt_version} prompt 失败: {e}")
        try:
            # 回退到默认版本
            prompt_template = prompt_selector.get_prompt(
                "prompts", "writer", genre)
            logger.debug(f"✅ 成功获取 writer prompt 模板，genre: {genre}")
        except Exception as e2:
            logger.error(f"❌ 获取 writer prompt 模板失败: {e2}")
            # 使用 prompts/writer.py 中的简化备用模板
            try:
                from ...prompts.writer import PROMPTS
                simple_prompt_template = PROMPTS.get("v2_fallback_simple",
                                                     PROMPTS["v1_simple"])
                logger.debug("✅ 成功获取 writer 简化备用模板")
            except Exception as e2:
                logger.error(f"❌ 获取 writer 简化备用模板也失败: {e2}")
                # 最后的备用方案
                simple_prompt_template = """
你是一个专业的文档写作专家。请基于提供的研究数据，为指定章节撰写内容。

**文档主题:** {topic}
**章节标题:** {chapter_title}
**章节描述:** {chapter_description}
**章节编号:** {chapter_number}/{total_chapters}

**可用信息源:**
{available_sources}

**研究数据:**
{gathered_data}

**写作要求:**
1. 基于研究数据撰写内容，确保信息准确性和完整性
2. 保持章节结构清晰，逻辑连贯
3. 使用专业但易懂的语言
4. 在写作时，如果使用了某个信息源的内容，请使用特殊标记：<sources>[源ID]</sources>
5. 例如：<sources>[1]</sources> 这里使用了源1的信息
6. 如果是自己的综合总结，使用：<sources>[]</sources>

请立即开始撰写章节内容。
"""

    # 构建高质量的提示词
    if style_guide_content and style_guide_content.strip():
        # 格式化样式指南内容
        formatted_style_guide = f"""
{style_guide_content}

"""
        prompt = prompt_template.format(
            topic=topic,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            chapter_number=current_chapter_index + 1,
            total_chapters=len(chapters_to_process),
            previous_chapters_context=previous_chapters_context
            if previous_chapters_context else "这是第一章，没有前置内容。",
            gathered_data=gathered_data,
            available_sources=available_sources_text,
            context_for_writing=context_for_writing,
            style_guide_content=formatted_style_guide)
        logger.info(f"📝 包含样式指南的写作，样式指南长度: {len(style_guide_content)} 字符")
    else:
        # 不包含样式指南的版本
        prompt = prompt_template.format(
            topic=topic,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            chapter_number=current_chapter_index + 1,
            total_chapters=len(chapters_to_process),
            previous_chapters_context=previous_chapters_context
            if previous_chapters_context else "这是第一章，没有前置内容。",
            gathered_data=gathered_data,
            available_sources=available_sources_text,
            context_for_writing=context_for_writing)
        logger.info("📝 标准写作，未包含样式指南")

    # 限制 prompt 长度
    max_prompt_length = 30000
    if len(prompt) > max_prompt_length:
        logger.warning(
            f"⚠️  Writer prompt 长度 {len(prompt)} 超过限制 {max_prompt_length}，进行截断"
        )

        # 优先保留当前章节的研究数据，适当缩减已完成章节的上下文
        if len(previous_chapters_context) > 5000:
            # 只保留每章的简短摘要
            previous_chapters_context = "\n\n".join([
                f"第{i+1}章摘要:\n{content[:200]}..."
                for i, content in enumerate(completed_chapters_content)
            ])

        # 如果研究数据也太长，进行截断
        if len(gathered_data) > 15000:
            gathered_data = gathered_data[:15000] + "\n\n... (研究数据已截断)"

        # 重新构建prompt - 优先使用支持引用的版本
        try:
            # 对于长 prompt 截断，优先使用支持引用的简化版本
            from ...prompts.writer import PROMPTS
            if "v2_simple_citations" in PROMPTS:
                simple_prompt_template = PROMPTS["v2_simple_citations"]
                logger.debug("✅ 成功获取 writer v2_simple_citations prompt 模板")
            else:
                # 回退到默认版本
                simple_prompt_template = prompt_selector.get_prompt(
                    "prompts", "writer", "default")
                logger.debug("✅ 成功获取 writer default prompt 模板")
        except Exception as e:
            logger.error(f"❌ 获取 writer prompt 模板失败: {e}")
            # 使用简化的备用模板（支持引用）
            simple_prompt_template = """
你是一个专业的文档写作专家。请基于提供的研究数据，为指定章节撰写内容。

**文档主题:** {topic}
**章节标题:** {chapter_title}
**章节描述:** {chapter_description}
**章节编号:** {chapter_number}/{total_chapters}

**可用信息源:**
{available_sources}

**研究数据:**
{gathered_data}

**写作要求:**
1. 基于研究数据撰写内容，确保信息准确性和完整性
2. 保持章节结构清晰，逻辑连贯
3. 使用专业但易懂的语言
4. 在写作时，如果使用了某个信息源的内容，请使用特殊标记：<sources>[源ID]</sources>
5. 例如：<sources>[1]</sources> 这里使用了源1的信息
6. 如果是自己的综合总结，使用：<sources>[]</sources>

请立即开始撰写章节内容。
"""

        prompt = simple_prompt_template.format(
            topic=topic,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            chapter_number=current_chapter_index + 1,
            total_chapters=len(chapters_to_process),
            gathered_data=gathered_data)
        logger.info(f"📝 截断后 writer prompt 长度: {len(prompt)} 字符")

    logger.debug(f"Invoking LLM with writer prompt:\n{pprint.pformat(prompt)}")

    try:
        # 调用LLM生成章节内容
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        # 确保响应格式正确
        if not response.strip():
            response = f"## {chapter_title}\n\n无法生成章节内容。"
        elif not response.startswith("##"):
            # 如果没有二级标题，添加章节标题
            response = f"## {chapter_title}\n\n{response}"

        # 定义内联引用处理函数
        def _process_citations_inline(
                raw_text: str,
                available_sources: list[Source]) -> tuple[str, list[Source]]:
            """
            处理LLM输出中的引用标记，提取引用的源并格式化文本
            
            Args:
                raw_text: LLM的原始输出文本
                available_sources: 可用的信息源列表
                
            Returns:
                tuple[str, list[Source]]: (处理后的文本, 引用的源列表)
            """
            processed_text = raw_text
            cited_sources = []

            # 创建源ID到源对象的映射
            source_map = {source.id: source for source in available_sources}

            def _replace_sources_tag(match):
                """替换引用标记的辅助函数"""
                try:
                    # 提取源ID列表，例如从 [1, 3] 中提取 [1, 3]
                    content = match.group(1).strip()

                    if not content:  # 空标签 <sources>[]</sources>
                        logger.debug("  📝 处理空引用标记（综合分析）")
                        return ""  # 移除空标签

                    # 解析源ID列表
                    source_ids = []
                    for id_str in content.split(','):
                        id_str = id_str.strip()
                        if id_str.isdigit():
                            source_ids.append(int(id_str))

                    logger.debug(f"  📚 解析到源ID: {source_ids}")

                    # 收集引用的源并生成引用标记
                    citation_markers = []
                    for source_id in source_ids:
                        if source_id in source_map:
                            source = source_map[source_id]
                            cited_sources.append(source)
                            citation_markers.append(f"[{source_id}]")
                            logger.debug(
                                f"    ✅ 添加引用源: [{source_id}] {source.title}")
                        else:
                            logger.warning(f"    ⚠️  未找到源ID: {source_id}")

                    # 返回格式化的引用标记
                    return "".join(citation_markers)

                except Exception as e:
                    logger.error(f"❌ 处理引用标记失败: {e}")
                    return ""  # 移除无效标签

            # 使用正则表达式替换所有引用标记
            sources_pattern = r'<sources>\[([^\]]*)\]</sources>'
            processed_text = re.sub(sources_pattern, _replace_sources_tag,
                                    processed_text)

            logger.info(f"✅ 引用处理完成，引用了 {len(cited_sources)} 个信息源")

            return processed_text, cited_sources

        # 处理引用标记
        processed_response, cited_sources = _process_citations_inline(
            response, gathered_sources)

        logger.info(f"✅ 章节生成完成，引用了 {len(cited_sources)} 个信息源")
        for source in cited_sources:
            logger.debug(f"  📚 引用源: [{source.id}] {source.title}")

        # 返回当前章节的内容和引用源
        return {
            "final_document": processed_response,
            "cited_sources_in_chapter": cited_sources
        }

    except Exception as e:
        # 如果LLM调用失败，返回错误信息
        logger.error(f"Writer node error: {str(e)}")
        error_content = f"""## {chapter_title}

### 章节生成错误

由于技术原因，无法生成本章节的内容。

**错误信息:** {str(e)}

**章节描述:** {chapter_description}

请检查系统配置或稍后重试。
"""
        return {
            "final_document": error_content,
            "cited_sources_in_chapter": []
        }


async def reflection_node(state: ResearchState,
                          llm_client: LLMClient,
                          prompt_selector: PromptSelector,
                          genre: str = "default") -> dict[str, Any]:
    """
    智能查询扩展节点
    分析现有的搜索查询和已收集的数据，生成更精确、更相关的搜索查询

    Args:
        state: 研究状态，包含 topic、search_queries 和 gathered_data
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"

    Returns:
        dict: 包含更新后的 search_queries 的字典
    """
    # 从状态中获取必要信息
    topic = state.get("topic", "")
    original_search_queries = state.get("search_queries", [])
    gathered_data = state.get("gathered_data", "")
    gathered_sources = state.get("gathered_sources", [])
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])

    # 获取当前章节信息
    current_chapter = None
    if current_chapter_index < len(chapters_to_process):
        current_chapter = chapters_to_process[current_chapter_index]

    chapter_title = current_chapter.get("chapter_title",
                                        "") if current_chapter else ""
    chapter_description = current_chapter.get("description",
                                              "") if current_chapter else ""

    # 优先使用 gathered_sources 的数据，如果没有则使用 gathered_data
    if gathered_sources and not gathered_data:
        gathered_data = _format_sources_to_text(gathered_sources)
        logger.info(
            f"📊 从 gathered_sources 转换为 gathered_data，长度: {len(gathered_data)} 字符"
        )

    logger.info("🤔 开始智能查询扩展分析")
    logger.info(f"📋 章节: {chapter_title}")
    logger.info(f"🔍 原始查询数量: {len(original_search_queries)}")
    logger.info(f"📊 已收集数据长度: {len(gathered_data)} 字符")
    logger.info(f"📚 已收集源数量: {len(gathered_sources)}")

    # 验证输入数据
    if not topic:
        logger.warning("❌ 缺少主题信息，无法进行查询扩展")
        return {"search_queries": original_search_queries}

    if not original_search_queries:
        logger.warning("❌ 没有原始查询，无法进行扩展")
        return {"search_queries": []}

    # 检查是否有足够的数据进行分析
    has_sufficient_data = ((gathered_data and len(gathered_data.strip()) >= 50)
                           or (gathered_sources and len(gathered_sources) > 0))

    if not has_sufficient_data:
        logger.warning("❌ 收集的数据不足，无法进行有效分析")
        return {"search_queries": original_search_queries}

    # 获取查询扩展器配置
    query_expander_config = settings.get_agent_component_config(
        "query_expander")
    if not query_expander_config:
        temperature = 0.7
        max_tokens = 2000
        extra_params = {}
    else:
        temperature = query_expander_config.temperature
        max_tokens = query_expander_config.max_tokens
        extra_params = query_expander_config.extra_params

    # 使用 PromptSelector 获取 prompt 模板
    try:
        prompt_template = prompt_selector.get_prompt("chapter_workflow",
                                                     "reflection", genre)
        logger.debug(f"✅ 成功获取 reflection prompt 模板，genre: {genre}")
    except Exception as e:
        logger.error(f"❌ 获取 reflection prompt 模板失败: {e}")
        # 使用 prompts/reflection.py 中的备用模板
        try:
            from ...prompts.reflection import PROMPTS
            prompt_template = PROMPTS.get("v1_fallback", PROMPTS["v1_default"])
            logger.debug("✅ 成功获取 reflection 备用模板")
        except Exception as e2:
            logger.error(f"❌ 获取 reflection 备用模板也失败: {e2}")
            # 最后的备用方案
            prompt_template = """
你是一个专业的研究专家和查询优化师。请分析现有的搜索查询和已收集的数据，生成更精确、更相关的搜索查询。

**文档主题:** {topic}

**当前章节信息:**
- 章节标题: {chapter_title}
- 章节描述: {chapter_description}

**原始搜索查询:**
{original_queries}

**已收集的数据摘要:**
{gathered_data_summary}

**任务要求:**
1. 仔细分析已收集的数据，识别信息缺口、模糊之处或新的有趣方向
2. 考虑原始查询的覆盖范围和深度
3. 生成2-3个新的、高度相关的、更具体的或探索性的搜索查询
4. 新查询应该：
   - 填补信息缺口
   - 深入特定方面
   - 探索新的角度或视角
   - 使用更精确的关键词

**输出格式:**
请以JSON格式返回结果，包含以下字段：
- new_queries: 新的搜索查询列表（数组，2-3个查询）
- reasoning: 简要说明为什么需要这些新查询

请立即开始分析并生成新的查询。
"""

    # 准备数据摘要（避免prompt过长）
    gathered_data_summary = gathered_data
    if len(gathered_data) > 3000:
        gathered_data_summary = gathered_data[:
                                              1500] + "\n\n... (数据已截断) ...\n\n" + gathered_data[
                                                  -1500:]

    # 格式化原始查询
    original_queries_text = "\n".join(
        [f"{i+1}. {query}" for i, query in enumerate(original_search_queries)])

    # 构建 prompt
    prompt = prompt_template.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description,
        original_queries=original_queries_text,
        gathered_data_summary=gathered_data_summary)

    logger.debug(
        f"Invoking LLM with reflection prompt:\n{pprint.pformat(prompt)}")

    try:
        # 调用 LLM 生成新的查询
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        logger.debug(f"🔍 LLM原始响应: {repr(response)}")
        logger.debug(f"📝 响应长度: {len(response)} 字符")

        # 解析响应，提取新的查询
        new_queries = _parse_reflection_response(response)

        if new_queries:
            logger.info(f"✅ 成功生成 {len(new_queries)} 个新查询")
            for i, query in enumerate(new_queries, 1):
                logger.debug(f"  {i}. {query}")

            # 返回更新后的查询列表
            return {"search_queries": new_queries}
        else:
            logger.warning("⚠️ 无法解析新查询，保持原始查询")
            return {"search_queries": original_search_queries}

    except Exception as e:
        logger.error(f"Reflection node error: {str(e)}")
        logger.warning("⚠️ 查询扩展失败，保持原始查询")
        return {"search_queries": original_search_queries}


def _parse_reflection_response(response: str) -> list[str]:
    """
    解析 reflection 节点的 LLM 响应，提取新的搜索查询

    Args:
        response: LLM 的原始响应

    Returns:
        list[str]: 新的搜索查询列表
    """
    try:
        # 尝试解析 JSON 格式
        import json
        import re

        # 清理响应文本
        cleaned_response = response.strip()

        # 尝试提取 JSON 部分
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)

            if 'new_queries' in data and isinstance(data['new_queries'], list):
                queries = data['new_queries']
                # 验证查询质量
                valid_queries = [
                    q.strip() for q in queries
                    if q.strip() and len(q.strip()) > 5
                ]
                if valid_queries:
                    return valid_queries

        # 如果 JSON 解析失败，尝试从文本中提取查询
        # 查找常见的查询模式
        query_patterns = [
            r'(\d+\.\s*)([^\n]+)',  # 1. query
            r'[-•]\s*([^\n]+)',  # - query 或 • query
            r'"([^"]+)"',  # "query"
        ]

        for pattern in query_patterns:
            try:
                matches = re.findall(pattern, cleaned_response, re.MULTILINE)
                if matches:
                    queries = []
                    for match in matches:
                        if isinstance(match, tuple):
                            query = match[1] if len(match) > 1 else match[0]
                        else:
                            query = match

                        query = query.strip()
                        if query and len(query) > 5:
                            queries.append(query)

                    if queries:
                        return queries
            except Exception as e:
                logger.debug(f"正则表达式匹配失败: {e}")
                continue

        # 如果所有方法都失败，尝试简单的行分割
        lines = cleaned_response.split('\n')
        queries = []
        for line in lines:
            line = line.strip()
            # 跳过空行、数字行、标题行等
            if (line and len(line) > 10 and not line.startswith('#')
                    and not re.match(r'^\d+\.?$', line)
                    and not re.match(r'^[A-Z\s]+$', line)):  # 全大写可能是标题
                queries.append(line)

        return queries[:3]  # 最多返回3个查询

    except Exception as e:
        logger.error(f"解析 reflection 响应失败: {e}")
        return []


def _parse_web_search_results(web_results: str, query: str,
                              start_id: int) -> list[Source]:
    """
    解析网络搜索结果，创建 Source 对象列表
    
    Args:
        web_results: 网络搜索的原始结果字符串
        query: 搜索查询
        start_id: 起始ID
        
    Returns:
        list[Source]: Source 对象列表
    """
    sources = []
    current_id = start_id

    try:
        # 简单的解析逻辑：按行分割，提取标题和URL
        lines = web_results.split('\n')
        current_title = ""
        current_url = ""
        current_content = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试提取标题和URL
            if line.startswith('http') or line.startswith('https'):
                # 这是一个URL
                if current_title and current_content:
                    # 创建前一个源
                    source = Source(
                        id=current_id,
                        source_type="webpage",
                        title=current_title,
                        url=current_url,
                        content=current_content[:500] + "..."
                        if len(current_content) > 500 else current_content)
                    sources.append(source)
                    current_id += 1

                current_url = line
                current_title = ""
                current_content = ""
            elif line.startswith('标题:') or line.startswith('Title:'):
                current_title = line.split(':', 1)[1].strip()
            elif line.startswith('内容:') or line.startswith('Content:'):
                current_content = line.split(':', 1)[1].strip()
            elif not current_title and len(
                    line) > 10 and not line.startswith('==='):
                # 可能是标题
                current_title = line
            elif current_title and len(line) > 20:
                # 可能是内容
                current_content += " " + line

        # 处理最后一个源
        if current_title and current_content:
            source = Source(
                id=current_id,
                source_type="webpage",
                title=current_title,
                url=current_url,
                content=current_content[:500] +
                "..." if len(current_content) > 500 else current_content)
            sources.append(source)

        # 如果没有解析到任何源，创建一个默认源
        if not sources:
            source = Source(id=current_id,
                            source_type="webpage",
                            title=f"网络搜索结果 - {query}",
                            url="",
                            content=web_results[:500] +
                            "..." if len(web_results) > 500 else web_results)
            sources.append(source)

    except Exception as e:
        logger.error(f"解析网络搜索结果失败: {str(e)}")
        # 创建默认源
        source = Source(id=start_id,
                        source_type="webpage",
                        title=f"网络搜索结果 - {query}",
                        url="",
                        content=web_results[:500] +
                        "..." if len(web_results) > 500 else web_results)
        sources.append(source)

    return sources


def _process_citations(
        raw_text: str,
        available_sources: list[Source],
        global_cited_sources: dict = None) -> tuple[str, list[Source]]:
    """
    处理LLM输出中的引用标记，提取引用的源并格式化文本
    
    Args:
        raw_text: LLM的原始输出文本
        available_sources: 可用的信息源列表
        global_cited_sources: 全局已引用的源字典，用于连续编号
        
    Returns:
        tuple[str, list[Source]]: (处理后的文本, 引用的源列表)
    """
    processed_text = raw_text
    cited_sources = []

    if global_cited_sources is None:
        global_cited_sources = {}

    try:
        # 创建源ID到源对象的映射
        source_map = {source.id: source for source in available_sources}

        # 查找所有 <sources>[...]</sources> 标签
        sources_pattern = r'<sources>\[([^\]]*)\]</sources>'
        matches = re.findall(sources_pattern, processed_text)

        logger.debug(f"🔍 找到 {len(matches)} 个引用标记")

        for match in matches:
            if not match.strip():  # 空标签 <sources>[]</sources>
                # 替换为空字符串（综合分析，不需要引用）
                processed_text = processed_text.replace(
                    f'<sources>[{match}]</sources>', '', 1)
                logger.debug("  📝 处理空引用标记（综合分析）")
                continue

            # 解析源ID列表
            try:
                source_ids = [
                    int(id.strip()) for id in match.split(',')
                    if id.strip().isdigit()
                ]
                logger.debug(f"  📚 解析到源ID: {source_ids}")

                # 收集引用的源并分配全局编号
                citation_markers = []
                for source_id in source_ids:
                    if source_id in source_map:
                        source = source_map[source_id]
                        cited_sources.append(source)

                        # 分配全局编号
                        if source_id not in global_cited_sources:
                            global_cited_sources[source_id] = source

                        # 使用全局编号
                        global_number = list(
                            global_cited_sources.keys()).index(source_id) + 1
                        citation_markers.append(f"[{global_number}]")

                        logger.debug(
                            f"    ✅ 添加引用源: [{global_number}] {source.title}")
                    else:
                        logger.warning(f"    ⚠️  未找到源ID: {source_id}")

                # 替换为格式化的引用标记
                formatted_citation = "".join(citation_markers)
                processed_text = processed_text.replace(
                    f'<sources>[{match}]</sources>', formatted_citation, 1)

            except ValueError as e:
                logger.error(f"❌ 解析源ID失败: {e}")
                # 移除无效的标签
                processed_text = processed_text.replace(
                    f'<sources>[{match}]</sources>', '', 1)

        logger.info(f"✅ 引用处理完成，引用了 {len(cited_sources)} 个信息源")

    except Exception as e:
        logger.error(f"❌ 处理引用时发生错误: {e}")
        # 如果处理失败，返回原始文本和空列表
        return raw_text, []

    return processed_text, cited_sources


def _format_sources_to_text(sources: list[Source]) -> str:
    """
    将 Source 对象列表格式化为文本格式，用于向后兼容
    
    Args:
        sources: Source 对象列表
        
    Returns:
        str: 格式化的文本
    """
    if not sources:
        return "没有收集到相关数据"

    formatted_text = "收集到的信息源:\n\n"

    for i, source in enumerate(sources, 1):
        formatted_text += f"=== 信息源 {i} ===\n"
        formatted_text += f"标题: {source.title}\n"
        if source.url:
            formatted_text += f"URL: {source.url}\n"
        formatted_text += f"类型: {source.source_type}\n"
        formatted_text += f"内容: {source.content}\n\n"

    return formatted_text


def _parse_es_search_results(es_results: str, query: str,
                             start_id: int) -> list[Source]:
    """
    解析ES搜索结果，创建 Source 对象列表
    
    Args:
        es_results: ES搜索的原始结果字符串
        query: 搜索查询
        start_id: 起始ID
        
    Returns:
        list[Source]: Source 对象列表
    """
    sources = []
    current_id = start_id

    try:
        # 解析ES搜索结果
        lines = es_results.split('\n')
        current_title = ""
        current_content = ""
        current_url = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试提取文档信息
            if line.startswith('文档标题:') or line.startswith('Title:'):
                current_title = line.split(':', 1)[1].strip()
            elif line.startswith('文档内容:') or line.startswith('Content:'):
                current_content = line.split(':', 1)[1].strip()
            elif line.startswith('文档URL:') or line.startswith('URL:'):
                current_url = line.split(':', 1)[1].strip()
            elif line.startswith('---') or line.startswith('==='):
                # 分隔符，处理前一个文档
                if current_title and current_content:
                    source = Source(
                        id=current_id,
                        source_type="es_result",
                        title=current_title,
                        url=current_url,
                        content=current_content[:500] + "..."
                        if len(current_content) > 500 else current_content)
                    sources.append(source)
                    current_id += 1
                    current_title = ""
                    current_content = ""
                    current_url = ""
            elif not current_title and len(line) > 10:
                # 可能是标题
                current_title = line
            elif current_title and len(line) > 20:
                # 可能是内容
                current_content += " " + line

        # 处理最后一个文档
        if current_title and current_content:
            source = Source(
                id=current_id,
                source_type="es_result",
                title=current_title,
                url=current_url,
                content=current_content[:500] +
                "..." if len(current_content) > 500 else current_content)
            sources.append(source)

        # 如果没有解析到任何源，创建一个默认源
        if not sources:
            source = Source(id=start_id,
                            source_type="es_result",
                            title=f"知识库搜索结果 - {query}",
                            url="",
                            content=es_results[:500] +
                            "..." if len(es_results) > 500 else es_results)
            sources.append(source)

    except Exception as e:
        logger.error(f"解析ES搜索结果失败: {str(e)}")
        # 创建默认源
        source = Source(id=start_id,
                        source_type="es_result",
                        title=f"知识库搜索结果 - {query}",
                        url="",
                        content=es_results[:500] +
                        "..." if len(es_results) > 500 else es_results)
        sources.append(source)

    return sources
