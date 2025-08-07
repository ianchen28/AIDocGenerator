"""
研究节点模块

负责初始研究，收集主题相关的信息源
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.graph.common import (
    parse_es_search_results,
    parse_web_search_results,
)
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.llm_clients.providers import EmbeddingClient
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.reranker import RerankerTool
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.utils.search_utils import search_and_rerank


async def initial_research_node(state: ResearchState,
                                web_search_tool: WebSearchTool,
                                es_search_tool: ESSearchTool,
                                reranker_tool: RerankerTool = None,
                                llm_client: LLMClient = None) -> dict:
    """
    初始研究节点 - 统一版本
    基于主题进行初始研究，收集相关信息源
    根据配置自动调整搜索深度和查询数量
    
    Args:
        state: 研究状态，包含 topic
        web_search_tool: 网络搜索工具
        es_search_tool: ES搜索工具
        reranker_tool: 重排序工具
        llm_client: LLM客户端（可选）
        
    Returns:
        dict: 包含 initial_sources 的字典，包含 Source 对象列表
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("主题不能为空")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()

    logger.info(f"🔍 开始初始研究 (模式: {complexity_config['level']}): {topic}")

    # 根据配置生成查询数量
    num_queries = complexity_config['initial_search_queries']

    # 生成搜索查询
    if num_queries == 2:  # 快速模式
        initial_queries = [f"{topic} 概述", f"{topic} 主要内容"]
    elif num_queries <= 5:  # 标准模式
        initial_queries = [
            f"{topic} 概述", f"{topic} 主要内容", f"{topic} 关键要点", f"{topic} 最新发展",
            f"{topic} 重要性"
        ][:num_queries]
    else:  # 全面模式
        initial_queries = [
            f"{topic} 概述", f"{topic} 主要内容", f"{topic} 关键要点", f"{topic} 最新发展",
            f"{topic} 重要性", f"{topic} 实践案例", f"{topic} 未来趋势", f"{topic} 相关技术"
        ][:num_queries]

    logger.info(f"📊 配置搜索轮数: {num_queries}，实际执行: {len(initial_queries)} 轮")

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

    # 执行搜索
    for i, query in enumerate(initial_queries, 1):
        logger.info(f"执行初始搜索 {i}/{len(initial_queries)}: {query}")

        # 网络搜索
        web_raw_results = []
        web_str_results = ""
        try:
            # 使用异步搜索方法
            web_raw_results, web_str_results = await web_search_tool.search_async(
                query)
            if "模拟" in web_str_results or "mock" in web_str_results.lower():
                web_str_results = ""
                web_raw_results = []
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_str_results = ""
            web_raw_results = []

        # ES搜索
        es_raw_results = []
        es_str_results = ""
        try:
            if embedding_client:
                # 尝试向量检索
                try:
                    embedding_response = embedding_client.invoke(query)
                    embedding_data = json.loads(embedding_response)

                    # 解析向量
                    if isinstance(embedding_data, list):
                        query_vector = embedding_data[0] if len(
                            embedding_data) > 0 and isinstance(
                                embedding_data[0], list) else embedding_data
                    elif isinstance(embedding_data,
                                    dict) and 'data' in embedding_data:
                        query_vector = embedding_data['data']
                    else:
                        query_vector = None

                    if query_vector:
                        # 使用向量检索
                        _, es_raw_results, es_str_results = await search_and_rerank(
                            es_search_tool, query, query_vector, reranker_tool)
                        logger.info(
                            f"✅ 向量检索+重排序执行成功，结果长度: {len(es_raw_results)}")
                    else:
                        # 回退到文本搜索
                        es_raw_results = await es_search_tool.search(query)
                        logger.info(f"✅ 文本搜索执行成功，结果长度: {len(es_raw_results)}")

                except Exception as e:
                    logger.warning(f"⚠️  向量检索失败，使用文本搜索: {str(e)}")
                    es_raw_results = await es_search_tool.search(query)
            else:
                # 直接使用文本搜索
                es_raw_results = await es_search_tool.search(query)

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            es_raw_results = []

        # 处理搜索结果并创建Source对象
        if web_str_results and web_str_results.strip():
            try:
                web_sources = parse_web_search_results(web_raw_results, query,
                                                       source_id_counter)
                all_sources.extend(web_sources)
                source_id_counter += len(web_sources)
                logger.info(f"✅ 从网络搜索中提取到 {len(web_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析网络搜索结果失败: {str(e)}")

        if es_raw_results and len(es_raw_results) > 0:
            try:
                es_sources = parse_es_search_results(es_raw_results, query,
                                                     source_id_counter)
                all_sources.extend(es_sources)
                source_id_counter += len(es_sources)
                logger.info(f"✅ 从ES搜索中提取到 {len(es_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析ES搜索结果失败: {str(e)}")

    # 根据配置决定是否截断数据
    truncate_length = complexity_config.get('data_truncate_length', -1)
    if truncate_length > 0:
        # 限制每个源的内容长度
        for source in all_sources:
            if len(source.content) > truncate_length // len(all_sources):
                source.content = source.content[:truncate_length //
                                                len(all_sources
                                                    )] + "... (内容已截断)"

    logger.info(f"✅ 初始研究完成，收集到 {len(all_sources)} 个信息源")

    return {"initial_sources": all_sources}
