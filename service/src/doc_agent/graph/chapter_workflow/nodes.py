# service/src/doc_agent/graph/nodes.py
from loguru import logger
import pprint
from ..state import ResearchState
from ...llm_clients.base import LLMClient
from ...tools.web_search import WebSearchTool
from ...tools.es_search import ESSearchTool
from ...tools.reranker import RerankerTool
from ...llm_clients.providers import EmbeddingClient, RerankerClient

# 添加配置导入
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir and str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.config import settings

# 修复相对导入
# 直接导入utils模块
import sys
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir:
    src_dir = service_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

# 导入utils模块
import sys
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir:
    src_dir = service_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

# 直接导入utils.py文件
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from doc_agent.common import parse_planner_response
from doc_agent.utils.search_utils import search_and_rerank


def planner_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    节点1: 规划研究步骤
    
    从状态中获取 topic 和当前章节信息，创建 prompt 调用 LLM 生成研究计划和搜索查询
    
    Args:
        state: 研究状态，包含 topic 和当前章节信息
        llm_client: LLM客户端实例
        
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

    # 导入提示词模板
    from ...prompts import PLANNER_PROMPT

    # 创建研究计划生成的 prompt，要求 JSON 格式响应
    prompt = PLANNER_PROMPT.format(topic=topic,
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

        # 解析 JSON 响应
        research_plan, search_queries = parse_planner_response(response)

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
                    web_search_tool: WebSearchTool) -> dict:
    raise NotImplementedError("请使用 async_researcher_node")


async def async_researcher_node(state: ResearchState,
                                web_search_tool: WebSearchTool,
                                es_search_tool: ESSearchTool,
                                reranker_tool: RerankerTool = None) -> dict:
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
        dict: 包含 gathered_data 的字典
    """
    logger.info(f"🔍 Researcher节点接收到的完整状态:")
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
        return {"gathered_data": "没有搜索查询需要执行"}

    all_results = []

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

    # 使用传入的ES工具，不再内部创建
    for i, query in enumerate(search_queries, 1):
        logger.info(f"执行搜索查询 {i}/{len(search_queries)}: {query}")

        # 网络搜索
        web_results = ""
        try:
            web_results = web_search_tool.search(query)
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
                        logger.warning(f"⚠️  JSON解析失败，使用文本搜索")
                        query_vector = None

                    if query_vector and len(query_vector) == 1536:
                        logger.debug(
                            f"✅ 向量维度: {len(query_vector)}，前5: {query_vector[:5]}"
                        )
                        # 使用新的搜索和重排序功能
                        search_query = query if query.strip() else "相关文档"

                        # 获取配置参数
                        doc_config = settings.get_document_config(
                            fast_mode=False)
                        initial_top_k = doc_config.get('vector_recall_size',
                                                       10)
                        final_top_k = doc_config.get('rerank_size', 5)

                        _, reranked_results, formatted_es_results = await search_and_rerank(
                            es_search_tool=es_search_tool,
                            query=search_query,
                            query_vector=query_vector,
                            reranker_tool=reranker_tool,
                            initial_top_k=initial_top_k,  # 使用配置的向量召回数量
                            final_top_k=final_top_k,  # 使用配置的重排序数量
                            config=doc_config  # 传递配置参数
                        )
                        es_results = formatted_es_results
                        logger.info(
                            f"✅ 向量检索+重排序执行成功，结果长度: {len(formatted_es_results)}"
                        )
                    else:
                        logger.warning(f"❌ 向量生成失败，使用文本搜索")
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

                # 获取配置参数
                doc_config = settings.get_document_config(fast_mode=False)
                initial_top_k = doc_config.get('hybrid_recall_size', 10)
                final_top_k = doc_config.get('rerank_size', 5)

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

        # 聚合结果
        query_results = f"=== 搜索查询 {i}: {query} ===\n\n"
        if web_results:
            query_results += f"网络搜索结果:\n{web_results}\n\n"
        if es_results:
            query_results += f"知识库搜索结果:\n{es_results}\n\n"
        if not web_results and not es_results:
            query_results += "未找到相关搜索结果\n\n"
        all_results.append(query_results)

    # 合并所有搜索结果
    if all_results:
        gathered_data = "\\n\\n".join(all_results)
        logger.info(f"✅ 收集到 {len(all_results)} 条搜索结果")
        logger.info(f"📊 总数据长度: {len(gathered_data)} 字符")
        # 只显示前200字符作为预览，避免日志过长
        preview = gathered_data[:200] + "..." if len(
            gathered_data) > 200 else gathered_data
        logger.debug(f"📝 数据预览: {preview}")
    else:
        gathered_data = "未收集到任何搜索结果"
        logger.warning("❌ 未收集到任何搜索结果")

    return {"gathered_data": gathered_data}


def writer_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    章节写作节点
    
    基于当前章节的研究数据和已完成章节的上下文，生成当前章节的内容
    
    Args:
        state: 研究状态，包含章节信息、研究数据和已完成章节
        llm_client: LLM客户端实例
        
    Returns:
        dict: 包含当前章节内容的字典
    """
    # 获取基本信息
    topic = state.get("topic", "")
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])
    completed_chapters_content = state.get("completed_chapters_content", [])

    # 验证当前章节索引
    if current_chapter_index >= len(chapters_to_process):
        raise ValueError(f"章节索引 {current_chapter_index} 超出范围")

    # 获取当前章节信息
    current_chapter = chapters_to_process[current_chapter_index]
    chapter_title = current_chapter.get("chapter_title", "")
    chapter_description = current_chapter.get("description", "")

    # 从状态中获取研究数据
    gathered_data = state.get("gathered_data", "")

    if not chapter_title:
        raise ValueError("章节标题不能为空")

    if not gathered_data:
        return {
            "final_document": f"## {chapter_title}\n\n由于没有收集到相关数据，无法生成章节内容。"
        }

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

    # 导入提示词模板
    from ...prompts import WRITER_PROMPT, WRITER_PROMPT_SIMPLE

    # 构建高质量的提示词
    prompt = WRITER_PROMPT.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description,
        chapter_number=current_chapter_index + 1,
        total_chapters=len(chapters_to_process),
        previous_chapters_context=previous_chapters_context
        if previous_chapters_context else "这是第一章，没有前置内容。",
        gathered_data=gathered_data)

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

        # 重新构建prompt
        prompt = WRITER_PROMPT_SIMPLE.format(
            topic=topic,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            chapter_number=current_chapter_index + 1,
            total_chapters=len(chapters_to_process),
            previous_chapters_context=previous_chapters_context
            if previous_chapters_context else "这是第一章，没有前置内容。",
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

        # 返回当前章节的内容
        return {"final_document": response}

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
        return {"final_document": error_content}
