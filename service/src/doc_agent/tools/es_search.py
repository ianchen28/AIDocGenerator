"""
Elasticsearch搜索工具
基于底层ES服务模块，提供简洁有效的搜索接口，支持KNN向量搜索
"""

from typing import Optional, List, Dict, Any
from loguru import logger
from .es_service import ESService, ESSearchResult
from .es_discovery import ESDiscovery


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
        logger.info("初始化ES搜索工具")

    async def _ensure_initialized(self):
        """确保已初始化"""
        if not self._initialized:
            logger.info("开始初始化ES搜索工具")
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

    async def search(
            self,
            query: str,
            query_vector: Optional[List[float]] = None,
            top_k: int = 10,
            filters: Optional[Dict[str, Any]] = None,
            use_multiple_indices: bool = True,
            config: Optional[Dict[str, Any]] = None) -> List[ESSearchResult]:
        """
        执行Elasticsearch搜索
        
        Args:
            query: 搜索查询字符串
            query_vector: 查询向量（可选）
            top_k: 返回结果数量
            filters: 过滤条件
            use_multiple_indices: 是否使用多索引搜索

        Returns:
            List[ESSearchResult]: 搜索结果列表
        """
        logger.info(f"开始ES搜索，查询: {query[:50]}...")
        logger.debug(
            f"搜索参数 - top_k: {top_k}, use_multiple_indices: {use_multiple_indices}"
        )
        if query_vector:
            logger.debug(f"查询向量维度: {len(query_vector)}")
        if filters:
            logger.debug(f"过滤条件: {filters}")

        try:
            # 确保已初始化
            await self._ensure_initialized()

            # 如果没有可用索引，返回空列表
            if not self._indices_list:
                logger.warning("没有可用的知识库索引")
                return []

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

            # 使用配置参数或默认值
            if config:
                vector_recall_size = config.get('vector_recall_size', top_k)
                min_score = config.get('min_score', 0.3)
                logger.debug(
                    f"使用配置参数 - vector_recall_size: {vector_recall_size}, min_score: {min_score}"
                )
            else:
                vector_recall_size = top_k
                min_score = 0.3

            # 执行搜索
            if use_multiple_indices and len(self._indices_list) > 1:
                # 多索引搜索
                logger.info(f"执行多索引搜索，索引数量: {len(self._indices_list)}")
                results = await self._es_service.search_multiple_indices(
                    indices=self._indices_list,
                    query=query,
                    top_k=vector_recall_size,
                    query_vector=query_vector,
                    filters=filters)
            else:
                # 单索引搜索
                index_to_use = self._current_index or self._indices_list[
                    0] if self._indices_list else None
                if not index_to_use:
                    logger.warning("没有可用的索引")
                    return []

                logger.info(f"执行单索引搜索，索引: {index_to_use}")
                results = await self._es_service.search(
                    index=index_to_use,
                    query=query,
                    top_k=vector_recall_size,
                    query_vector=query_vector,
                    filters=filters)

            # 根据最小分数过滤结果
            if min_score > 0:
                original_count = len(results)
                results = [r for r in results if r.score >= min_score]
                logger.info(
                    f"根据最小分数 {min_score} 过滤后，剩余 {len(results)} 个结果（原始: {original_count}）"
                )

            logger.info(f"ES搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            return []

    async def search_with_hybrid(
            self,
            query: str,
            query_vector: Optional[List[float]] = None,
            top_k: int = 10,
            filters: Optional[Dict[str, Any]] = None,
            config: Optional[Dict[str, Any]] = None) -> List[ESSearchResult]:
        """
        执行混合搜索（文本+向量）
        
        Args:
            query: 搜索查询字符串
            query_vector: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            List[ESSearchResult]: 搜索结果列表
        """
        logger.info(f"开始混合搜索，查询: {query[:50]}...")
        logger.debug(f"混合搜索参数 - top_k: {top_k}")
        if query_vector:
            logger.debug(f"查询向量维度: {len(query_vector)}")
        if filters:
            logger.debug(f"过滤条件: {filters}")

        if not query_vector:
            # 如果没有向量，回退到普通搜索
            logger.info("没有查询向量，回退到普通搜索")
            return await self.search(query,
                                     None,
                                     top_k,
                                     filters,
                                     config=config)

        try:
            await self._ensure_initialized()

            if not self._indices_list:
                logger.warning("没有可用的知识库索引")
                return []

            # 准备查询向量
            if len(query_vector) != self._vector_dims:
                if len(query_vector) > self._vector_dims:
                    query_vector = query_vector[:self._vector_dims]
                else:
                    query_vector.extend(
                        [0.0] * (self._vector_dims - len(query_vector)))
                logger.info(f"调整向量维度到 {self._vector_dims}")

            # 使用配置参数或默认值
            if config:
                hybrid_recall_size = config.get('hybrid_recall_size', top_k)
                min_score = config.get('min_score', 0.3)
                logger.debug(
                    f"使用配置参数 - hybrid_recall_size: {hybrid_recall_size}, min_score: {min_score}"
                )
            else:
                hybrid_recall_size = top_k
                min_score = 0.3

            # 执行混合搜索
            index_to_use = self._current_index or self._indices_list[
                0] if self._indices_list else None
            if not index_to_use:
                logger.warning("没有可用的索引")
                return []

            logger.info(f"执行混合搜索，索引: {index_to_use}")
            results = await self._es_service.search(index=index_to_use,
                                                    query=query,
                                                    top_k=hybrid_recall_size,
                                                    query_vector=query_vector,
                                                    filters=filters)

            # 根据最小分数过滤结果
            if min_score > 0:
                original_count = len(results)
                results = [r for r in results if r.score >= min_score]
                logger.info(
                    f"根据最小分数 {min_score} 过滤后，剩余 {len(results)} 个结果（原始: {original_count}）"
                )

            logger.info(f"混合搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            return []

    async def get_available_indices(self) -> List[str]:
        """获取可用索引列表"""
        await self._ensure_initialized()
        logger.debug(f"获取可用索引列表，共 {len(self._indices_list)} 个")
        return self._indices_list.copy()

    async def get_current_index(self) -> Optional[str]:
        """获取当前使用的索引"""
        await self._ensure_initialized()
        logger.debug(f"获取当前索引: {self._current_index}")
        return self._current_index

    async def __aenter__(self):
        """异步上下文管理器入口"""
        logger.debug("进入ES搜索工具异步上下文")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，自动关闭连接"""
        logger.debug("退出ES搜索工具异步上下文")
        await self.close()

    async def close(self):
        """关闭连接"""
        logger.info("关闭ES搜索工具连接")
        try:
            await self._es_service.close()
            self._initialized = False

            # 从全局注册表移除（如果存在）
            try:
                from . import unregister_es_tool
                unregister_es_tool(self)
                logger.debug("从全局注册表移除ES工具")
            except ImportError:
                # 如果导入失败，说明不在测试环境中，忽略
                logger.debug("不在测试环境中，跳过注册表移除")
                pass
        except Exception as e:
            logger.error(f"关闭ES搜索工具时出错: {e}")

    # 兼容性方法，用于工具工厂
    async def _discover_available_indices(self):
        """发现可用索引（兼容性方法）"""
        await self._ensure_initialized()
        logger.debug("调用兼容性方法 _discover_available_indices")
        return self._indices_list

    @property
    def _available_indices(self):
        """获取可用索引（兼容性属性）"""
        logger.debug("调用兼容性属性 _available_indices")
        return self._indices_list
