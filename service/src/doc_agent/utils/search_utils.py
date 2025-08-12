"""
搜索工具函数
提供搜索结果格式化和重排序功能
"""

from typing import Any, Optional

from doc_agent.core.logger import logger

from doc_agent.tools.es_service import ESSearchResult
from doc_agent.tools.reranker import RerankedSearchResult, RerankerTool


def format_search_results(results: list[ESSearchResult],
                          query: str,
                          indices_list: list[str] = None) -> str:
    """
    格式化搜索结果
    
    Args:
        results: 搜索结果列表
        query: 搜索查询
        indices_list: 索引列表（用于显示来源）
        
    Returns:
        str: 格式化后的搜索结果字符串
    """
    logger.debug(f"格式化搜索结果，结果数量: {len(results)}")

    if not results:
        logger.warning(f"没有找到与 '{query}' 相关的文档")
        return f"未找到与 '{query}' 相关的文档。"

    result = f"搜索查询: {query}\n"
    result += f"找到 {len(results)} 个相关文档:\n\n"

    for i, doc in enumerate(results, 1):
        # 显示来源索引（如果有多索引）
        if doc.alias_name and indices_list and len(indices_list) > 1:
            result += f"{i}. [{doc.alias_name}] {doc.source or '未知来源'}\n"
        else:
            result += f"{i}. {doc.source or '未知来源'}\n"

        result += f"   评分: {doc.score:.3f}\n"

        # 显示原始内容（如果存在）
        if doc.original_content:
            content_preview = doc.original_content[:300]
            result += f"   原始内容: {content_preview}"
            if len(doc.original_content) > 300:
                result += "..."
            result += "\n"

        # 显示切分后的内容（如果存在且与原始内容不同）
        if doc.div_content and doc.div_content != doc.original_content:
            div_preview = doc.div_content[:200]
            result += f"   切分内容: {div_preview}"
            if len(doc.div_content) > 200:
                result += "..."
            result += "\n"

        result += "\n"

    logger.debug(f"格式化完成，结果长度: {len(result)} 字符")
    return result


async def rerank_search_results(search_results: list[ESSearchResult],
                                query: str,
                                reranker_tool: RerankerTool,
                                top_k: int = 5) -> list[RerankedSearchResult]:
    """
    对搜索结果进行重排序
    
    Args:
        search_results: 原始搜索结果列表
        query: 搜索查询
        reranker_tool: 重排序工具
        top_k: 返回结果数量
        
    Returns:
        List[RerankedSearchResult]: 重排序后的结果列表
    """
    logger.info(f"开始重排序搜索结果，查询: '{query[:50]}...'")
    logger.debug(f"重排序参数 - 原始结果数量: {len(search_results)}, top_k: {top_k}")

    if not search_results:
        logger.warning("没有搜索结果需要重排序")
        return []

    try:
        logger.info(f"开始重排序，原始结果数量: {len(search_results)}")

        # 执行重排序
        reranked_results = reranker_tool.rerank_search_results(
            query=query, search_results=search_results, top_k=top_k)

        logger.info(f"重排序完成，返回 {len(reranked_results)} 个结果")

        # 分析重排序效果
        analysis = reranker_tool.analyze_rerank_effectiveness(
            reranked_results, query)
        logger.info(f"重排序效果分析: {analysis}")

        return reranked_results

    except Exception as e:
        logger.error(f"重排序失败: {str(e)}")
        # 如果重排序失败，返回原始结果的前top_k个
        fallback_results = []
        for result in search_results[:top_k]:
            fallback_result = RerankedSearchResult(
                id=result.id,
                doc_id=result.doc_id,
                original_content=result.original_content,
                div_content=result.div_content,
                source=result.source,
                score=result.score,
                rerank_score=result.score,  # 使用原始评分
                metadata=result.metadata,
                alias_name=result.alias_name)
            fallback_results.append(fallback_result)

        logger.info(f"使用原始结果作为后备，返回 {len(fallback_results)} 个结果")
        return fallback_results


def format_reranked_results(reranked_results: list[RerankedSearchResult],
                            query: str,
                            indices_list: list[str] = None) -> str:
    """
    格式化重排序后的搜索结果
    Args:
        reranked_results: 重排序后的结果列表
        query: 搜索查询
        indices_list: 索引列表
    Returns:
        str: 格式化后的重排序结果字符串
    """
    logger.debug(f"格式化重排序结果，结果数量: {len(reranked_results)}")

    if not reranked_results:
        logger.warning(f"没有找到与 '{query}' 相关的文档")
        return f"未找到与 '{query}' 相关的文档。"

    result = f"搜索查询: {query}\n"
    result += f"重排序后找到 {len(reranked_results)} 个最相关文档:\n\n"

    for i, doc in enumerate(reranked_results, 1):
        # 显示来源索引
        if doc.alias_name and indices_list and len(indices_list) > 1:
            result += f"{i}. [{doc.alias_name}] {doc.source or '未知来源'}\n"
        else:
            result += f"{i}. {doc.source or '未知来源'}\n"

        result += f"   原始评分: {doc.score:.3f}\n"
        result += f"   重排序评分: {doc.rerank_score:.3f}\n"

        # 显示内容
        content_to_show = doc.div_content if doc.div_content else doc.original_content
        if content_to_show:
            content_preview = content_to_show[:300]
            result += f"   内容: {content_preview}"
            if len(content_to_show) > 300:
                result += "..."
            result += "\n"

        result += "\n"

    logger.debug(f"重排序结果格式化完成，结果长度: {len(result)} 字符")
    return result


async def search_and_rerank(
    es_search_tool,
    query: str,
    query_vector: Optional[list[float]] = None,
    reranker_tool: Optional[RerankerTool] = None,
    initial_top_k: int = 10,
    final_top_k: int = 5,
    filters: Optional[dict[str, Any]] = None,
    config: Optional[dict[str, Any]] = None
) -> tuple[list[ESSearchResult], list[RerankedSearchResult], str]:
    """
    执行搜索并进行重排序
    Args:
        es_search_tool: ES搜索工具
        query: 搜索查询
        query_vector: 查询向量
        reranker_tool: 重排序工具
        initial_top_k: 初始搜索返回结果数量
        final_top_k: 重排序后返回结果数量
        filters: 过滤条件
    Returns:
        tuple: (原始搜索结果, 重排序结果, 格式化字符串)
    """
    logger.info(f"开始搜索和重排序流程，查询: '{query[:50]}...'")
    logger.debug(
        f"搜索参数 - initial_top_k: {initial_top_k}, final_top_k: {final_top_k}")
    if query_vector:
        logger.debug(f"查询向量维度: {len(query_vector)}")
    if filters:
        logger.debug(f"过滤条件: {filters}")
    if config:
        logger.debug(f"配置参数: {config}")

    # 执行搜索
    logger.info(f"执行搜索: {query}")
    search_results = await es_search_tool.search(query=query,
                                                 query_vector=query_vector,
                                                 top_k=initial_top_k,
                                                 filters=filters,
                                                 config=config)

    logger.info(f"搜索完成，获得 {len(search_results)} 个原始结果")

    # 如果没有搜索结果，返回空结果
    if not search_results:
        logger.warning("搜索未返回任何结果")
        return [], [], f"未找到与 '{query}' 相关的文档。"

    # 安全地显示第一个结果示例
    if search_results:
        logger.info(f"es result example: {search_results[0]}")

    # 如果没有重排序工具，直接格式化原始结果
    if not reranker_tool:
        logger.info("未提供重排序工具，使用原始结果")
        # 安全地获取索引列表
        indices_list = getattr(es_search_tool, '_indices_list', [])
        if not isinstance(indices_list, list):
            indices_list = []
        formatted_result = format_search_results(search_results, query,
                                                 indices_list)
        return search_results, [], formatted_result

    # 执行重排序
    logger.info("开始执行重排序")
    reranked_results = await rerank_search_results(search_results, query,
                                                   reranker_tool, final_top_k)

    # 格式化重排序结果
    logger.info("格式化重排序结果")
    # 安全地获取索引列表
    indices_list = getattr(es_search_tool, '_indices_list', [])
    if not isinstance(indices_list, list):
        indices_list = []
    formatted_result = format_reranked_results(reranked_results, query,
                                               indices_list)

    logger.info(
        f"搜索和重排序流程完成，原始结果: {len(search_results)}, 重排序结果: {len(reranked_results)}"
    )
    return search_results, reranked_results, formatted_result
