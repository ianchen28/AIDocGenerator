"""
RerankerTool 重排序工具
接收 ESSearchResult 列表，调用 RerankerClient 进行重排序
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .es_service import ESSearchResult
from ..llm_clients.providers import RerankerClient

logger = logging.getLogger(__name__)


@dataclass
class RerankedSearchResult:
    """重排序后的搜索结果"""
    id: str
    original_content: str
    div_content: str = ""
    source: str = ""
    score: float = 0.0
    rerank_score: float = 0.0  # 重排序评分
    metadata: Dict[str, Any] = None
    alias_name: str = ""

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RerankerTool:
    """重排序工具类"""

    def __init__(self, base_url: str, api_key: str):
        """
        初始化重排序工具
        
        Args:
            reranker_client: RerankerClient 实例
        """
        self.reranker_client = RerankerClient(base_url=base_url,
                                              api_key=api_key)

    def rerank_search_results(
            self,
            query: str,
            search_results: List[ESSearchResult],
            top_k: Optional[int] = None) -> List[RerankedSearchResult]:
        """
        对搜索结果进行重排序
        
        Args:
            query: 查询文本
            search_results: ESSearchResult 列表
            top_k: 返回结果数量，None表示返回全部
            
        Returns:
            List[RerankedSearchResult]: 重排序后的结果列表
        """
        if not search_results:
            logger.warning("输入搜索结果为空，返回空列表")
            return []

        try:
            # 提取文档文本
            documents = []
            for result in search_results:
                # 优先使用 div_content，如果没有则使用 original_content
                doc_text = result.div_content if result.div_content else result.original_content
                if doc_text:
                    documents.append(doc_text)
                else:
                    logger.warning(f"文档 {result.id} 内容为空，跳过")

            if not documents:
                logger.warning("所有文档内容都为空，无法进行重排序")
                return []

            logger.info(f"开始重排序，查询: '{query}'，文档数量: {len(documents)}")

            # 调用 RerankerClient 进行重排序
            size = top_k if top_k is not None else len(documents)
            rerank_result = self.reranker_client.invoke(prompt=query,
                                                        documents=documents,
                                                        size=size)

            # 解析重排序结果
            reranked_results = self._parse_rerank_result(
                rerank_result, search_results, query)

            logger.info(f"重排序完成，返回 {len(reranked_results)} 个结果")
            return reranked_results

        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            # 如果重排序失败，返回原始结果（按原始评分排序）
            return self._fallback_to_original_results(search_results)

    def _parse_rerank_result(self, rerank_result: Dict[str, Any],
                             original_results: List[ESSearchResult],
                             query: str) -> List[RerankedSearchResult]:
        """
        解析重排序结果
        
        Args:
            rerank_result: RerankerClient 返回的结果
            original_results: 原始搜索结果
            query: 查询文本
            
        Returns:
            List[RerankedSearchResult]: 解析后的重排序结果
        """
        reranked_results = []

        if not isinstance(rerank_result,
                          dict) or 'sorted_doc_list' not in rerank_result:
            logger.error(f"重排序结果格式异常: {rerank_result}")
            return self._fallback_to_original_results(original_results)

        sorted_docs = rerank_result['sorted_doc_list']
        logger.info(f"重排序返回 {len(sorted_docs)} 个文档")

        # 创建原始文档的映射，用于快速查找
        original_doc_map = {}
        for result in original_results:
            doc_text = result.div_content if result.div_content else result.original_content
            if doc_text:
                original_doc_map[doc_text] = result

        # 处理重排序结果
        for i, reranked_doc in enumerate(sorted_docs):
            try:
                doc_text = reranked_doc.get('text', '')
                rerank_score = reranked_doc.get('rerank_score', 0.0)

                # 查找对应的原始结果
                original_result = original_doc_map.get(doc_text)
                if original_result:
                    # 创建重排序结果
                    reranked_result = RerankedSearchResult(
                        id=original_result.id,
                        original_content=original_result.original_content,
                        div_content=original_result.div_content,
                        source=original_result.source,
                        score=original_result.score,  # 保留原始评分
                        rerank_score=rerank_score,  # 添加重排序评分
                        metadata=original_result.metadata,
                        alias_name=original_result.alias_name)
                    reranked_results.append(reranked_result)
                else:
                    logger.warning(f"重排序文档在原始结果中未找到: {doc_text[:50]}...")

            except Exception as e:
                logger.error(f"解析重排序文档失败: {str(e)}")
                continue

        # 如果没有成功解析任何结果，回退到原始结果
        if not reranked_results:
            logger.warning("重排序结果解析失败，回退到原始结果")
            return self._fallback_to_original_results(original_results)

        logger.info(f"成功解析 {len(reranked_results)} 个重排序结果")
        return reranked_results

    def _fallback_to_original_results(
            self, original_results: List[ESSearchResult]
    ) -> List[RerankedSearchResult]:
        """
        回退到原始结果（当重排序失败时）
        
        Args:
            original_results: 原始搜索结果
            
        Returns:
            List[RerankedSearchResult]: 转换后的结果
        """
        fallback_results = []
        for result in original_results:
            fallback_result = RerankedSearchResult(
                id=result.id,
                original_content=result.original_content,
                div_content=result.div_content,
                source=result.source,
                score=result.score,
                rerank_score=result.score,  # 使用原始评分作为重排序评分
                metadata=result.metadata,
                alias_name=result.alias_name)
            fallback_results.append(fallback_result)

        logger.info(f"回退到原始结果，返回 {len(fallback_results)} 个结果")
        return fallback_results

    def get_top_results(self, reranked_results: List[RerankedSearchResult],
                        top_k: int) -> List[RerankedSearchResult]:
        """
        获取前 top_k 个重排序结果
        
        Args:
            reranked_results: 重排序结果列表
            top_k: 返回结果数量
            
        Returns:
            List[RerankedSearchResult]: 前 top_k 个结果
        """
        if not reranked_results:
            return []

        # 按重排序评分降序排列
        sorted_results = sorted(reranked_results,
                                key=lambda x: x.rerank_score,
                                reverse=True)

        return sorted_results[:top_k]

    def analyze_rerank_effectiveness(
            self, reranked_results: List[RerankedSearchResult],
            query: str) -> Dict[str, Any]:
        """
        分析重排序效果
        
        Args:
            reranked_results: 重排序结果列表
            query: 查询文本
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        if not reranked_results:
            return {
                "total_results": 0,
                "score_range": 0.0,
                "top_score": 0.0,
                "bottom_score": 0.0,
                "effectiveness": "no_results"
            }

        # 计算评分统计
        scores = [result.rerank_score for result in reranked_results]
        top_score = max(scores)
        bottom_score = min(scores)
        score_range = top_score - bottom_score

        # 分析效果
        if score_range > 5.0:
            effectiveness = "excellent"
        elif score_range > 2.0:
            effectiveness = "good"
        elif score_range > 0.5:
            effectiveness = "moderate"
        else:
            effectiveness = "poor"

        # 检查最相关文档是否排在前面
        first_doc = reranked_results[0].div_content if reranked_results[
            0].div_content else reranked_results[0].original_content
        query_keywords = query.lower().split()
        first_doc_lower = first_doc.lower()

        keyword_match_count = sum(1 for keyword in query_keywords
                                  if keyword in first_doc_lower)
        relevance_score = keyword_match_count / len(
            query_keywords) if query_keywords else 0.0

        return {
            "total_results": len(reranked_results),
            "score_range": score_range,
            "top_score": top_score,
            "bottom_score": bottom_score,
            "effectiveness": effectiveness,
            "relevance_score": relevance_score,
            "keyword_match_count": keyword_match_count
        }
