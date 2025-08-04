from typing import Optional, Any, Union
from loguru import logger

from doc_agent.tools.es_search import ESSearchTool
from doc_agent.schemas import Source
from .base import BaseRetriever


class ESRetriever(BaseRetriever):
    """
    Elasticsearch检索器
    继承自BaseRetriever，提供基于ES的向量搜索功能
    支持同步和异步两种调用方式
    """

    def __init__(self,
                 hosts: list[str],
                 username: str = "",
                 password: str = "",
                 index_prefix: str = "doc_gen",
                 timeout: int = 30):
        """
        初始化ES检索器
        
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
        self._es_tool: Optional[ESSearchTool] = None
        logger.info("初始化ES检索器")

    async def _get_es_tool(self) -> ESSearchTool:
        """获取ES搜索工具实例"""
        if self._es_tool is None:
            self._es_tool = ESSearchTool(
                hosts=self.hosts,
                username=self.username,
                password=self.password,
                index_prefix=self.index_prefix,
                timeout=self.timeout
            )
        return self._es_tool

    def retrieve(self, query: str, **kwargs) -> Union[list[Source], "ESRetriever"]:
        """
        同步检索方法（为了兼容性）
        
        注意：由于ES搜索本质上是异步操作，建议使用 retrieve_async 方法
        此方法会抛出异常，提示使用异步版本
        """
        raise NotImplementedError(
            "ESRetriever 不支持同步调用，请使用 retrieve_async 方法。"
            "ES搜索是异步操作，同步调用会导致性能问题。"
        )

    async def retrieve_async(self, query: str, **kwargs) -> list[Source]:
        """
        异步检索方法（推荐使用）
        
        Args:
            query: 搜索查询字符串
            **kwargs: 其他参数，包括：
                - query_vector: 查询向量（可选）
                - top_k: 返回结果数量（默认10）
                - filters: 过滤条件（可选）
                - use_multiple_indices: 是否使用多索引搜索（默认True）
                - config: 搜索配置（可选）
        
        Returns:
            List[Source]: Source对象列表
        """
        logger.info(f"开始ES检索，查询: {query[:50]}...")
        
        try:
            # 获取ES搜索工具
            es_tool = await self._get_es_tool()
            
            # 提取参数
            query_vector = kwargs.get('query_vector')
            top_k = kwargs.get('top_k', 10)
            filters = kwargs.get('filters')
            use_multiple_indices = kwargs.get('use_multiple_indices', True)
            config = kwargs.get('config')
            
            logger.debug(f"检索参数 - top_k: {top_k}, use_multiple_indices: {use_multiple_indices}")
            if query_vector:
                logger.debug(f"查询向量维度: {len(query_vector)}")
            if filters:
                logger.debug(f"过滤条件: {filters}")
            
            # 执行搜索
            search_results = await es_tool.search(
                query=query,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
                use_multiple_indices=use_multiple_indices,
                config=config
            )
            
            # 转换为Source对象
            sources = []
            for result in search_results:
                source = self._convert_to_source(result)
                sources.append(source)
            
            logger.info(f"ES检索完成，返回 {len(sources)} 个Source对象")
            return sources
            
        except Exception as e:
            logger.error(f"ES检索失败: {str(e)}")
            return []

    def _convert_to_source(self, es_result) -> Source:
        """
        将ES搜索结果转换为Source对象
        
        Args:
            es_result: ESSearchResult对象
            
        Returns:
            Source: 转换后的Source对象
        """
        # 确定数据源类型
        source_type = "db"  # ES属于数据库类型
        
        # 构建URL（如果有的话）
        url = es_result.metadata.get('url', '') or es_result.metadata.get('file_name', '')
        if not url:
            url = f"es://{es_result.alias_name}/{es_result.id}"
        
        # 构建标题
        title = es_result.metadata.get('title', '') or es_result.metadata.get('file_name', '')
        if not title:
            title = f"ES文档_{es_result.id[:8]}"
        
        # 使用div_content作为主要内容，original_content作为原始内容
        content = es_result.div_content or es_result.original_content
        raw_content = es_result.original_content
        
        # 生成摘要（这里简单截取前200字符，实际项目中可能需要更复杂的摘要生成）
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return Source(
            type=source_type,
            title=title,
            url=url,
            content=content,
            raw_content=raw_content,
            summary=summary
        )

    async def close(self):
        """关闭ES连接"""
        if self._es_tool:
            await self._es_tool.close()
            self._es_tool = None
            logger.info("ES检索器连接已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
