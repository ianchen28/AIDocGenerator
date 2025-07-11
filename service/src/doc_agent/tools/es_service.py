"""
Elasticsearch 底层服务模块
提供基础的ES连接和搜索功能
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from elasticsearch import AsyncElasticsearch

logger = logging.getLogger(__name__)


@dataclass
class ESSearchResult:
    """ES搜索结果"""
    id: str
    original_content: str  # 原始内容
    div_content: str = ""  # 切分后的内容
    source: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ESService:
    """ES底层服务类"""

    def __init__(self,
                 hosts: List[str],
                 username: str = "",
                 password: str = "",
                 timeout: int = 30):
        """
        初始化ES服务
        
        Args:
            hosts: ES服务器地址列表
            username: 用户名
            password: 密码
            timeout: 超时时间
        """
        self.hosts = hosts
        self.username = username
        self.password = password
        self.timeout = timeout
        self._client: Optional[AsyncElasticsearch] = None

    async def connect(self) -> bool:
        """连接ES服务"""
        try:
            es_kwargs = {
                "hosts": self.hosts,
                "verify_certs": False,
                "ssl_show_warn": False,
                "timeout": self.timeout,
                "max_retries": 3,
                "retry_on_timeout": True
            }

            if self.username and self.password:
                es_kwargs["basic_auth"] = (self.username, self.password)

            self._client = AsyncElasticsearch(**es_kwargs)

            # 测试连接
            await self._client.ping()
            logger.info("ES连接成功")
            return True

        except Exception as e:
            logger.error(f"ES连接失败: {str(e)}")
            return False

    async def search(
            self,
            index: str,
            query: str,
            top_k: int = 10,
            query_vector: Optional[List[float]] = None,
            filters: Optional[Dict[str, Any]] = None) -> List[ESSearchResult]:
        """
        执行ES搜索
        
        Args:
            index: 索引名称
            query: 搜索查询
            top_k: 返回结果数量
            query_vector: 查询向量（可选）
            filters: 过滤条件（可选）
            
        Returns:
            List[ESSearchResult]: 搜索结果列表
        """
        if not self._client:
            logger.error("ES客户端未连接")
            return []

        try:
            # 构建搜索查询
            search_body = self._build_search_body(query, query_vector, filters)

            # 执行搜索
            response = await self._client.search(index=index,
                                                 body=search_body,
                                                 size=top_k)

            # 解析结果
            results = []
            for hit in response['hits']['hits']:
                doc_data = hit['_source']

                # 获取原始内容和切分后的内容
                # 原始内容
                original_content = (doc_data.get('content_view') or '')
                # 切分后的内容
                div_content = (doc_data.get('content') or doc_data.get('text')
                               or doc_data.get('title') or '')

                # 灵活获取来源字段
                source = (doc_data.get('meta_data', {}).get('file_name')
                          or doc_data.get('file_name') or doc_data.get('name')
                          or '')

                result = ESSearchResult(id=hit['_id'],
                                        original_content=original_content,
                                        div_content=div_content,
                                        source=source,
                                        score=hit['_score'],
                                        metadata=doc_data.get('meta_data', {}))
                results.append(result)

            logger.info(f"ES搜索成功，返回 {len(results)} 个文档")
            return results

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            return []

    def _build_search_body(
            self,
            query: str,
            query_vector: Optional[List[float]] = None,
            filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        构建搜索查询体
        
        Args:
            query: 搜索查询
            query_vector: 查询向量
            filters: 过滤条件
            
        Returns:
            Dict[str, Any]: 搜索查询体
        """
        # 基础文本查询 - 只使用确实被索引的字段
        base_query = {
            "bool": {
                "should": [{
                    "multi_match": {
                        "query":
                        query,
                        "fields": [
                            "content^2", "file_name", "title^2", "text^2",
                            "name"
                        ],
                        "type":
                        "best_fields"
                    }
                }],
                "minimum_should_match":
                1
            }
        }

        # 添加过滤条件
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_conditions.append({"terms": {key: value}})
                else:
                    filter_conditions.append({"term": {key: value}})

            if filter_conditions:
                base_query["bool"]["filter"] = filter_conditions

        # 如果有向量查询，使用script_score
        if query_vector:
            # 确保向量维度正确
            if len(query_vector) != 1536:  # 假设使用1536维向量
                if len(query_vector) > 1536:
                    query_vector = query_vector[:1536]
                else:
                    query_vector.extend([0.0] * (1536 - len(query_vector)))

            search_body = {
                "query": {
                    "script_score": {
                        "query": base_query,
                        "script": {
                            "source":
                            "cosineSimilarity(params.query_vector, 'context_vector') + 1.0",
                            "params": {
                                "query_vector": query_vector
                            }
                        }
                    }
                }
            }
        else:
            # 纯文本搜索
            search_body = {"query": base_query}

        return search_body

    async def close(self):
        """关闭连接"""
        if self._client:
            try:
                # 先关闭客户端
                await self._client.close()
                self._client = None
                logger.info("ES连接已关闭")

                # 等待一小段时间确保连接完全关闭
                import asyncio
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"关闭ES连接失败: {str(e)}")
                # 即使出错也要清空客户端引用
                self._client = None

    async def get_indices(self) -> List[Dict[str, Any]]:
        """获取所有索引信息"""
        if not self._client:
            return []

        try:
            indices = await self._client.cat.indices(format='json')
            return indices
        except Exception as e:
            logger.error(f"获取索引失败: {str(e)}")
            return []

    async def get_index_mapping(self, index: str) -> Optional[Dict[str, Any]]:
        """获取索引映射"""
        if not self._client:
            return None

        try:
            mapping = await self._client.indices.get_mapping(index=index)
            return mapping[index]['mappings']
        except Exception as e:
            logger.error(f"获取索引映射失败: {str(e)}")
            return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
