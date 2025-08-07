"""
研究节点模块

负责执行搜索和收集信息
"""

import json
from typing import Any

from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)

from doc_agent.core.config import settings
from doc_agent.graph.common import merge_sources_with_deduplication
from doc_agent.graph.common import parse_es_search_results as _parse_es_search_results
from doc_agent.graph.common import parse_web_search_results as _parse_web_search_results
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.providers import EmbeddingClient
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.reranker import RerankerTool
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.utils.search_utils import search_and_rerank, format_search_results
from doc_agent.tools.es_service import ESSearchResult
from doc_agent.tools.reranker import RerankedSearchResult, RerankerTool


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

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"🔧 使用复杂度级别: {complexity_config['level']}")

    all_sources = []  # 存储所有 Source 对象
    source_id_counter = 1  # 源ID计数器

    # 获取现有的信源列表（从状态中获取）
    existing_sources = state.get("gathered_sources", [])
    if existing_sources:
        logger.info(f"📚 发现现有信源 {len(existing_sources)} 个，将进行去重处理")
        # 更新源ID计数器 - 安全获取，提供默认值
        source_id_counter = state.get("current_citation_index", 0)
    else:
        # 如果没有现有信源，确保有默认的引用索引
        source_id_counter = state.get("current_citation_index", 0)

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

    # 根据复杂度配置获取文档配置参数
    initial_top_k = complexity_config.get('vector_recall_size', 10)
    final_top_k = complexity_config.get('rerank_size', 5)

    # 应用基于复杂度的查询数量限制
    max_queries = complexity_config.get(
        'chapter_search_queries', complexity_config.get('max_queries', 5))
    if len(search_queries) > max_queries:
        logger.info(f"🔧 限制搜索查询数量从 {len(search_queries)} 到 {max_queries}")
        search_queries = search_queries[:max_queries]

    # 执行搜索
    for i, query in enumerate(search_queries, 1):
        logger.info(f"执行搜索查询 {i}/{len(search_queries)}: {query}")

        # ============================
        # ES搜索
        # ============================
        es_raw_results: list[RerankedSearchResult] = []
        es_str_results = ""
        try:
            if embedding_client:
                # 尝试向量检索
                try:
                    embedding_response = embedding_client.invoke(query)
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
                            config={
                                'min_score':
                                complexity_config.get('min_score', 0.3)
                            })
                        # 添加新的结果
                        es_raw_results.extend(reranked_results)
                        es_str_results = formatted_es_results
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
                            config={
                                'min_score':
                                complexity_config.get('min_score', 0.3)
                            })
                        es_str_results = formatted_es_results
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
                        config={
                            'min_score':
                            complexity_config.get('min_score', 0.3)
                        })
                    es_str_results = formatted_es_results
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
                    config={
                        'min_score': complexity_config.get('min_score', 0.3)
                    })
                # 添加新的结果
                es_raw_results.extend(reranked_results)
                es_str_results = formatted_es_results
                logger.info(
                    f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}")

        except Exception as e:
            logger.error(f"❌ ES搜索失败: {str(e)}")
            es_str_results = f"ES搜索失败: {str(e)}"

        # ============================
        # 网络搜索
        # ============================
        web_raw_results = []
        web_str_results = ""
        try:
            # 使用异步搜索方法
            web_raw_results, web_str_results = await web_search_tool.search_async(
                query)
            if "模拟" in web_str_results or "mock" in web_str_results.lower():
                logger.info(f"网络搜索返回模拟结果，跳过: {query}")
                web_str_results = ""
                web_raw_results = []
            if "搜索失败" in web_str_results:
                logger.error(f"网络搜索失败: {web_str_results}")
                web_str_results = ""
                web_raw_results = []
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_str_results = ""

        # 处理ES搜索结果
        if es_str_results and es_str_results.strip():
            try:
                # 解析ES搜索结果，创建 Source 对象
                es_sources = _parse_es_search_results(es_raw_results, query,
                                                      source_id_counter)

                all_sources.extend(es_sources)
                source_id_counter += len(es_sources)
                logger.info(f"✅ 从ES搜索中提取到 {len(es_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析ES搜索结果失败: {str(e)}")

        # 处理网络搜索结果
        if web_str_results and web_str_results.strip():
            try:
                # 解析网络搜索结果，创建 Source 对象
                web_sources = _parse_web_search_results(
                    web_raw_results, query, source_id_counter)

                all_sources.extend(web_sources)
                source_id_counter += len(web_sources)
                logger.info(f"✅ 从网络搜索中提取到 {len(web_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析网络搜索结果失败: {str(e)}")

    # 返回结构化的源列表
    old_source_count = len(existing_sources)
    new_source_count = len(all_sources)
    added_source_count = new_source_count - old_source_count
    logger.info(
        f"✅ 信源数：{old_source_count} -- +{new_source_count} --> {added_source_count}"
    )
    for i, source in enumerate(all_sources[:5], 1):  # 只显示前5个源作为预览
        logger.debug(
            f"  {i}. [{source.id}] {source.title} ({source.source_type})")

    # 🔧 新增：更新重试计数器
    current_retry_count = state.get("researcher_retry_count", 0)
    new_retry_count = current_retry_count + 1
    logger.info(f"📊 更新重试计数器: {current_retry_count} -> {new_retry_count}")

    return {
        "gathered_sources": all_sources,
        "researcher_retry_count": new_retry_count
    }
