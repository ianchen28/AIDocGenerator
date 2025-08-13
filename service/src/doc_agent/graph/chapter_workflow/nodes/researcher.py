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
from doc_agent.tools.es_service import ESSearchResult
from doc_agent.tools.reranker import RerankedSearchResult, RerankerTool
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.utils.search_utils import format_search_results, search_and_rerank
from doc_agent.graph.callbacks import publish_event, safe_serialize


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
    job_id = state.get("job_id", "")
    is_online = state.get("is_online", True)

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

    publish_event(
        job_id, "信息收集", "document_generation", "RUNNING", {
            "search_queries": search_queries,
            "description": f"开始信息收集，共需搜索{len(search_queries)}个查询"
        })
    user_data_reference_files = state.get("user_data_reference_files", [])
    user_style_guide_content = state.get("user_style_guide_content", [])
    user_requirements_content = state.get("user_requirements_content", [])

    # 执行搜索
    for i, query in enumerate(search_queries, 1):
        # 生成向量
        if embedding_client:
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
                        f"⚠️  无法解析embedding响应格式: {type(embedding_data)}")
                    query_vector = None
            except json.JSONDecodeError:
                logger.warning("⚠️  JSON解析失败！无法进行 ES 检索")
                query_vector = None

        logger.info(f"执行搜索查询 {i}/{len(search_queries)}: {query}")
        # ============================
        # 用户上传的文件搜索
        # ============================
        user_data_raw_results: list[RerankedSearchResult] = []
        user_style_raw_results: list[RerankedSearchResult] = []
        user_requirement_raw_results: list[RerankedSearchResult] = []
        user_str_results = ""

        # 检查是否有用户上传的文档
        has_user_documents = (user_data_reference_files
                              or user_style_guide_content
                              or user_requirements_content)

        if has_user_documents:
            logger.info(
                f"🔍 在用户上传文档范围内搜索，参考文档数量: {len(user_data_reference_files) if user_data_reference_files else 0}，风格指南数量: {len(user_style_guide_content) if user_style_guide_content else 0}，需求文档数量: {len(user_requirements_content) if user_requirements_content else 0}"
            )

            try:
                # 在指定文档范围内执行ES搜索
                user_data_es_results = []
                user_style_es_results = []
                user_requirement_es_results = []

                if user_data_reference_files:
                    logger.info(
                        f"🔍 搜索用户参考文档，文档token: {user_data_reference_files[:3]}..."
                    )
                    user_data_es_results = await es_search_tool.search_within_documents(
                        query=query,
                        query_vector=query_vector,
                        file_tokens=user_data_reference_files,
                        top_k=initial_top_k,
                        config={
                            'min_score':
                            complexity_config.get('min_score', 0.3)
                        })

                if user_style_guide_content:
                    logger.info(
                        f"🔍 搜索用户风格指南，文档token: {user_style_guide_content[:3]}..."
                    )
                    user_style_es_results = await es_search_tool.search_within_documents(
                        query=query,
                        query_vector=query_vector,
                        file_tokens=user_style_guide_content,
                        top_k=initial_top_k,
                        config={
                            'min_score':
                            complexity_config.get('min_score', 0.3)
                        })

                if user_requirements_content:
                    logger.info(
                        f"🔍 搜索用户需求文档，文档token: {user_requirements_content[:3]}..."
                    )
                    user_requirement_es_results = await es_search_tool.search_within_documents(
                        query=query,
                        query_vector=query_vector,
                        file_tokens=user_requirements_content,
                        top_k=initial_top_k,
                        config={
                            'min_score':
                            complexity_config.get('min_score', 0.3)
                        })

                # 对用户文档搜索结果进行重排序
                if user_data_es_results and reranker_tool:
                    logger.info(
                        f"🔄 对用户文档搜索结果进行重排序，原始结果数: {len(user_data_es_results)}")

                    # 转换为重排序工具需要的格式
                    user_search_results = []
                    for result in user_data_es_results:
                        user_search_results.append({
                            'content':
                            result.original_content or result.div_content,
                            'score':
                            result.score,
                            'metadata': {
                                'source': result.source,
                                'doc_id': result.doc_id,
                                'file_token': result.file_token,
                                'alias_name': result.alias_name
                            }
                        })

                    # 执行重排序
                    reranked_user_results = await reranker_tool.rerank(
                        query=query,
                        documents=user_search_results,
                        top_k=final_top_k)

                    # 转换为RerankedSearchResult格式
                    for reranked_result in reranked_user_results:
                        user_data_raw_results.append(
                            RerankedSearchResult(
                                content=reranked_result['content'],
                                score=reranked_result['score'],
                                metadata=reranked_result.get('metadata', {})))

                    logger.info(
                        f"✅ 用户文档重排序完成，结果数: {len(user_data_raw_results)}")

                    # style 重排序
                    if user_style_es_results and reranker_tool:
                        logger.info(
                            f"🔄 对用户风格指南搜索结果进行重排序，原始结果数: {len(user_style_es_results)}"
                        )

                        # 转换为重排序工具需要的格式
                        user_style_search_results = []
                        for result in user_style_es_results:
                            user_style_search_results.append({
                                'content':
                                result.original_content or result.div_content,
                                'score':
                                result.score,
                                'metadata': {
                                    'source': result.source,
                                    'doc_id': result.doc_id,
                                    'file_token': result.file_token,
                                    'alias_name': result.alias_name
                                }
                            })

                        # 执行重排序
                        reranked_user_style_results = await reranker_tool.rerank(
                            query=query,
                            documents=user_style_search_results,
                            top_k=final_top_k)

                        # 转换为RerankedSearchResult格式
                        for reranked_result in reranked_user_style_results:
                            user_style_raw_results.append(
                                RerankedSearchResult(
                                    content=reranked_result['content'],
                                    score=reranked_result['score'],
                                    metadata=reranked_result.get(
                                        'metadata', {})))

                    # requirement 重排序
                    if user_requirement_es_results and reranker_tool:
                        logger.info(
                            f"🔄 对用户需求搜索结果进行重排序，原始结果数: {len(user_requirement_es_results)}"
                        )

                        # 转换为重排序工具需要的格式
                        user_requirement_search_results = []
                        for result in user_requirement_es_results:
                            user_requirement_search_results.append({
                                'content':
                                result.original_content or result.div_content,
                                'score':
                                result.score,
                                'metadata': {
                                    'source': result.source,
                                    'doc_id': result.doc_id,
                                    'file_token': result.file_token,
                                    'alias_name': result.alias_name
                                }
                            })

                        # 执行重排序
                        reranked_user_requirement_results = await reranker_tool.rerank(
                            query=query,
                            documents=user_requirement_search_results,
                            top_k=final_top_k)

                        # 转换为RerankedSearchResult格式
                        for reranked_result in reranked_user_requirement_results:
                            user_requirement_raw_results.append(
                                RerankedSearchResult(
                                    content=reranked_result['content'],
                                    score=reranked_result['score'],
                                    metadata=reranked_result.get(
                                        'metadata', {})))
                else:
                    # 如果没有重排序工具，直接使用原始结果
                    for result in user_data_es_results:
                        user_data_raw_results.append(
                            RerankedSearchResult(
                                content=result.original_content
                                or result.div_content,
                                score=result.score,
                                metadata={
                                    'source': result.source,
                                    'doc_id': result.doc_id,
                                    'file_token': result.file_token,
                                    'alias_name': result.alias_name
                                }))
                    logger.info(
                        f"✅ 用户文档搜索完成，结果数: {len(user_data_raw_results)}")

                # 格式化用户文档搜索结果
                user_results_combined = []
                if user_data_raw_results:
                    user_results_combined.extend(user_data_raw_results)
                if user_style_raw_results:
                    user_results_combined.extend(user_style_raw_results)
                if user_requirement_raw_results:
                    user_results_combined.extend(user_requirement_raw_results)

                if user_results_combined:
                    user_str_results = format_search_results(
                        user_results_combined, query)
                    logger.info(
                        f"📝 用户文档搜索结果格式化完成，总结果数: {len(user_results_combined)}，格式化长度: {len(user_str_results)}"
                    )
                else:
                    logger.warning("⚠️ 未找到有效的用户文档搜索结果")

            except Exception as e:
                logger.error(f"❌ 用户文档搜索失败: {str(e)}")
                user_data_raw_results = []
                user_str_results = ""

        # ============================
        # ES搜索
        # ============================
        es_raw_results: list[RerankedSearchResult] = []
        es_str_results = ""
        try:
            if query_vector and len(query_vector) == 1536:
                logger.debug(
                    f"✅ 向量维度: {len(query_vector)}，前5: {query_vector[:5]}")
                # 使用新的搜索和重排序功能
                search_query = query if query.strip() else "相关文档"

                _, reranked_es_results, formatted_es_results = await search_and_rerank(
                    es_search_tool=es_search_tool,
                    query=search_query,
                    query_vector=query_vector,
                    reranker_tool=reranker_tool,
                    initial_top_k=initial_top_k,
                    final_top_k=final_top_k,
                    config={
                        'min_score': complexity_config.get('min_score', 0.3)
                    })
                # 添加新的结果
                es_raw_results.extend(reranked_es_results)
                es_str_results = formatted_es_results
                logger.info(
                    f"✅ 向量检索+重排序执行成功，结果长度: {len(formatted_es_results)}")
            else:
                # 报错返回
                raise ValueError("向量维度不正确")
        except Exception as e:
            logger.error(f"❌ 向量检索异常: {str(e)}！ 请检查embedding客户端配置")
            raise e

        # ============================
        # 网络搜索
        # ============================
        web_raw_results: list[RerankedSearchResult] = []
        web_str_results = ""
        if is_online:
            try:
                # 使用异步搜索方法
                web_raw_results, web_str_results = await web_search_tool.search_async(
                    query)
                if "模拟" in web_str_results or "mock" in web_str_results.lower(
                ):
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

        # ============================
        # 处理用户文档搜索结果
        # ============================
        user_data_sources = []
        user_requirement_sources = []
        user_style_sources = []

        if user_str_results and user_str_results.strip():
            try:
                # 解析用户文档搜索结果，创建 Source 对象
                user_data_sources = _parse_es_search_results(
                    user_data_raw_results, query, source_id_counter)
                user_requirement_sources = _parse_es_search_results(
                    user_requirement_raw_results, query, 1)
                user_style_sources = _parse_es_search_results(
                    user_style_raw_results, query, 1)

                all_sources.extend(user_data_sources)
                source_id_counter += len(user_data_sources)
                logger.info(f"✅ 从用户文档搜索中提取到 {len(user_data_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析用户文档搜索结果失败: {str(e)}")

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

    publish_event(
        job_id, "信息收集", "document_generation", "SUCCESS", {
            "web_sources":
            [safe_serialize(source) for source in web_raw_results],
            "es_sources":
            [safe_serialize(source) for source in es_raw_results],
            "user_data_reference_sources":
            [safe_serialize(source) for source in user_data_sources],
            "user_requirement_sources":
            [safe_serialize(source) for source in user_requirement_sources],
            "user_style_guide_sources":
            [safe_serialize(source) for source in user_style_sources],
            "description":
            f"信息收集完成，搜索到{len(all_sources)}个信息源，其中网络搜索结果 {len(web_raw_results)} 个，ES搜索结果 {len(es_raw_results)} 个，用户文档搜索结果 {len(user_data_sources)} 个"
        })

    logger.info(
        f"🔍 信息收集完成，搜索到{len(all_sources)}个信息源，其中网络搜索结果 {len(web_raw_results)} 个，ES搜索结果 {len(es_raw_results)} 个，用户文档搜索结果 {len(user_data_sources)} 个"
    )
    if es_raw_results:
        logger.info(f"ES搜索结果示例：{es_raw_results[0]}")
    if user_data_sources:
        logger.info(f"用户文档搜索结果示例：{user_data_sources[0]}")

    return {
        "gathered_sources": all_sources,
        "researcher_retry_count": new_retry_count,
        "user_requirement_sources": user_requirement_sources,
        "user_style_guide_sources": user_style_sources,
        "user_data_reference_sources": user_data_sources
    }
