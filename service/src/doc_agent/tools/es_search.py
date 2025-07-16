"""
Elasticsearch搜索工具
基于底层ES服务模块，提供简洁有效的搜索接口，支持KNN向量搜索
"""

import logging
from typing import Optional, List, Dict, Any
from .es_service import ESService, ESSearchResult
from .es_discovery import ESDiscovery

logger = logging.getLogger(__name__)


class ESSearchTool:
    """
    Elasticsearch搜索工具类
    提供简洁有效的ES搜索功能，支持异步上下文管理器
    """

    def __init__(self,
                 hosts: List[str],
                 username: str = "",
                 password: str = "",
                 index_prefix: str = "doc_gen",
                 timeout: int = 30):
        """
        初始化Elasticsearch搜索工具
        
        Args:
            hosts: ES服务器地址列表
            username: 用户名
            password: 密码
            index_prefix: 索引前缀
            timeout: 超时时间
        """
        self.hosts = hosts
        self.username = username
        self.password = password
        self.index_prefix = index_prefix
        self.timeout = timeout

        # 初始化底层服务
        self._es_service = ESService(hosts, username, password, timeout)
        self._discovery = ESDiscovery(self._es_service)
        self._current_index = None
        self._indices_list = []
        self._vector_dims = 1536
        self._initialized = False

    async def _ensure_initialized(self):
        """确保已初始化"""
        if not self._initialized:
            try:
                # 发现可用索引
                indices = await self._discovery.discover_knowledge_indices()
                if indices:
                    # 提取索引名称列表
                    self._indices_list = [idx['name'] for idx in indices]
                    self._current_index = self._discovery.get_best_index()
                    self._vector_dims = self._discovery.get_vector_dims()
                    self._initialized = True
                    logger.info(f"ES搜索工具初始化成功，使用索引: {self._current_index}")
                    logger.info(f"可用索引: {self._indices_list}")
                else:
                    logger.warning("没有找到可用的知识库索引，将使用降级模式")
                    self._initialized = True
            except Exception as e:
                logger.error(f"ES搜索工具初始化失败: {str(e)}")
                self._initialized = True  # 即使失败也标记为已初始化，避免重复尝试

    async def search(self,
                     query: str,
                     query_vector: Optional[List[float]] = None,
                     top_k: int = 10,
                     filters: Optional[Dict[str, Any]] = None,
                     use_multiple_indices: bool = True) -> str:
        """
        执行Elasticsearch搜索
        
        Args:
            query: 搜索查询字符串
            query_vector: 查询向量（可选）
            top_k: 返回结果数量
            filters: 过滤条件
            use_multiple_indices: 是否使用多索引搜索

        Returns:
            str: 搜索结果
        """
        try:
            # 确保已初始化
            await self._ensure_initialized()

            # 如果没有可用索引，返回降级响应
            if not self._indices_list:
                return self._get_fallback_response(query)

            # 准备查询向量
            if query_vector is not None:
                if len(query_vector) != self._vector_dims:
                    # 调整向量维度
                    if len(query_vector) > self._vector_dims:
                        query_vector = query_vector[:self._vector_dims]
                    else:
                        query_vector.extend(
                            [0.0] * (self._vector_dims - len(query_vector)))
                    logger.info(f"调整向量维度到 {self._vector_dims}")

            # 执行搜索
            if use_multiple_indices and len(self._indices_list) > 1:
                # 多索引搜索
                results = await self._es_service.search_multiple_indices(
                    indices=self._indices_list,
                    query=query,
                    top_k=top_k,
                    query_vector=query_vector,
                    filters=filters)
            else:
                # 单索引搜索
                index_to_use = self._current_index or self._indices_list[
                    0] if self._indices_list else None
                if not index_to_use:
                    return self._get_fallback_response(query)

                results = await self._es_service.search(
                    index=index_to_use,
                    query=query,
                    top_k=top_k,
                    query_vector=query_vector,
                    filters=filters)

            # 格式化结果
            return self._format_search_results(results, query)

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            return self._get_fallback_response(query)

    def _format_search_results(self, results: List[ESSearchResult],
                               query: str) -> str:
        """格式化搜索结果"""
        if not results:
            return f"未找到与 '{query}' 相关的文档。"

        result = f"搜索查询: {query}\n"
        result += f"找到 {len(results)} 个相关文档:\n\n"

        for i, doc in enumerate(results, 1):
            # 显示来源索引（如果有多索引）
            if doc.alias_name and len(self._indices_list) > 1:
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

        return result

    def _get_fallback_response(self, query: str) -> str:
        """获取降级响应（当ES不可用时）"""
        return f"ES搜索服务暂时不可用，查询: {query}\n\n" \
               f"1. 相关文档标题1 - 这是一个模拟的搜索结果\n" \
               f"   摘要: 这是第一个搜索结果的摘要内容，包含了一些相关信息...\n\n" \
               f"2. 相关文档标题2 - 另一个模拟的搜索结果\n" \
               f"   摘要: 这是第二个搜索结果的摘要内容，提供了更多相关的信息...\n\n" \
               f"3. 相关文档标题3 - 第三个模拟的搜索结果\n" \
               f"   摘要: 这是第三个搜索结果的摘要内容，补充了额外的相关信息...\n\n" \
               f"注意: 这是降级响应，实际ES服务不可用。"

    async def search_with_hybrid(
            self,
            query: str,
            query_vector: Optional[List[float]] = None,
            top_k: int = 10,
            filters: Optional[Dict[str, Any]] = None) -> str:
        """
        执行混合搜索（文本+向量）
        
        Args:
            query: 搜索查询字符串
            query_vector: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            str: 搜索结果
        """
        if not query_vector:
            # 如果没有向量，回退到普通搜索
            return await self.search(query, None, top_k, filters)

        try:
            await self._ensure_initialized()

            if not self._indices_list:
                return self._get_fallback_response(query)

            # 准备查询向量
            if len(query_vector) != self._vector_dims:
                if len(query_vector) > self._vector_dims:
                    query_vector = query_vector[:self._vector_dims]
                else:
                    query_vector.extend(
                        [0.0] * (self._vector_dims - len(query_vector)))

            # 执行混合搜索
            index_to_use = self._current_index or self._indices_list[
                0] if self._indices_list else None
            if not index_to_use:
                return self._get_fallback_response(query)

            results = await self._es_service.search(index=index_to_use,
                                                    query=query,
                                                    top_k=top_k,
                                                    query_vector=query_vector,
                                                    filters=filters)

            return self._format_search_results(results, query)

        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            return self._get_fallback_response(query)

    async def get_available_indices(self) -> List[str]:
        """获取可用索引列表"""
        await self._ensure_initialized()
        return self._indices_list.copy()

    async def get_current_index(self) -> Optional[str]:
        """获取当前使用的索引"""
        await self._ensure_initialized()
        return self._current_index

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，自动关闭连接"""
        await self.close()

    async def close(self):
        """关闭连接"""
        try:
            await self._es_service.close()
            self._initialized = False

            # 从全局注册表移除（如果存在）
            try:
                from . import unregister_es_tool
                unregister_es_tool(self)
            except ImportError:
                # 如果导入失败，说明不在测试环境中，忽略
                pass
        except Exception as e:
            logger.error(f"关闭ES搜索工具时出错: {e}")

    # 兼容性方法，用于工具工厂
    async def _discover_available_indices(self):
        """发现可用索引（兼容性方法）"""
        await self._ensure_initialized()
        return self._indices_list

    @property
    def _available_indices(self):
        """获取可用索引（兼容性属性）"""
        return self._indices_list
