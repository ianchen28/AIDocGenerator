"""
Elasticsearch 底层服务模块
提供基础的ES连接和搜索功能，支持KNN向量搜索
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

from elasticsearch import AsyncElasticsearch

from doc_agent.core.logger import logger


@dataclass
class ESSearchResult:
    """ES搜索结果"""
    id: str
    doc_id: str
    file_token: str
    original_content: str  # 原始内容
    div_content: str = ""  # 切分后的内容
    source: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = None
    alias_name: str = ""  # 来源索引别名

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ESService:
    """ES底层服务类"""

    def __init__(self,
                 hosts: list[str],
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
        self._initialized = False
        logger.info("初始化ES服务")

    async def connect(self) -> bool:
        """连接ES服务"""
        logger.info("开始连接ES服务")
        try:
            es_kwargs = {
                "hosts": self.hosts,
                "verify_certs": False,
                "ssl_show_warn": False,
                "request_timeout": self.timeout,
                "max_retries": 3,
                "retry_on_timeout": True
            }

            if self.username and self.password:
                es_kwargs["basic_auth"] = (self.username, self.password)
                logger.debug("使用基本认证连接ES")

            self._client = AsyncElasticsearch(**es_kwargs)

            # 测试连接
            await self._client.ping()
            logger.info("ES连接成功")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"ES连接失败: {str(e)}")
            self._initialized = False
            return False

    async def _ensure_connected(self):
        """确保已连接"""
        if not self._initialized or not self._client:
            logger.debug("ES客户端未连接，尝试连接")
            await self.connect()

    async def search(
            self,
            index: str,
            query: str,
            top_k: int = 10,
            query_vector: Optional[list[float]] = None,
            filters: Optional[dict[str, Any]] = None) -> list[ESSearchResult]:
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
        logger.info(f"开始ES搜索，索引: {index}, 查询: {query[:50]}...")
        logger.debug(f"搜索参数 - top_k: {top_k}")
        if query_vector:
            logger.debug(f"查询向量维度: {len(query_vector)}")
        if filters:
            logger.debug(f"过滤条件: {filters}")

        await self._ensure_connected()

        if not self._client:
            logger.error("ES客户端未连接")
            return []

        try:
            # 构建搜索查询
            search_body = self._build_search_body(query, query_vector, filters,
                                                  top_k)
            logger.debug(f"搜索查询体: {search_body}")

            # 执行搜索
            response = await self._client.search(index=index, body=search_body)

            # 解析结果
            results = []
            for hit in response['hits']['hits']:
                doc_data = hit['_source']

                # 获取原始内容和切分后的内容
                original_content = (doc_data.get('content_view')
                                    or doc_data.get('content')
                                    or doc_data.get('text')
                                    or doc_data.get('title') or '')

                div_content = (doc_data.get('content') or doc_data.get('text')
                               or doc_data.get('title') or '')

                # 灵活获取来源字段
                source = (doc_data.get('meta_data', {}).get('file_name')
                          or doc_data.get('file_name') or doc_data.get('name')
                          or '')

                # 安全获取 doc_id，如果不存在则使用 _id
                doc_id = doc_data.get('doc_id', "")

                result = ESSearchResult(id=hit['_id'],
                                        doc_id=doc_id,
                                        file_token=doc_data.get(
                                            'file_token', ""),
                                        original_content=original_content,
                                        div_content=div_content,
                                        source=source,
                                        score=hit['_score'],
                                        metadata=doc_data.get('meta_data', {}),
                                        alias_name=index)
                results.append(result)

            logger.info(f"ES搜索成功，返回 {len(results)} 个文档")
            return results

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            return []

    def _build_search_body(self,
                           query: str,
                           query_vector: Optional[list[float]] = None,
                           filters: Optional[dict[str, Any]] = None,
                           top_k: int = 10) -> dict[str, Any]:
        """
        构建搜索查询体

        Args:
            query: 搜索查询
            query_vector: 查询向量
            filters: 过滤条件
            top_k: 返回结果数量

        Returns:
            Dict[str, Any]: 搜索查询体
        """
        # 如果有向量查询，优先使用KNN搜索
        if query_vector:
            logger.debug("使用KNN向量搜索")
            return self._build_knn_search_body(query_vector, query, filters,
                                               top_k)
        else:
            logger.debug("使用文本搜索")
            return self._build_text_search_body(query, filters, top_k)

    def _build_knn_search_body(self,
                               query_vector: list[float],
                               query: str = "",
                               filters: Optional[dict[str, Any]] = None,
                               top_k: int = 10) -> dict[str, Any]:
        """
        构建KNN向量搜索查询体

        Args:
            query_vector: 查询向量
            query: 文本查询（可选，用于混合搜索）
            filters: 过滤条件
            top_k: 返回结果数量

        Returns:
            Dict[str, Any]: KNN搜索查询体
        """
        # 确保向量维度正确
        if len(query_vector) != 1536:
            if len(query_vector) > 1536:
                query_vector = query_vector[:1536]
                logger.debug("截断向量维度到 1536")
            else:
                query_vector.extend([0.0] * (1536 - len(query_vector)))
                logger.debug("扩展向量维度到 1536")

        # 构建基础KNN查询
        search_body = {
            "size": top_k,
            "_source": {
                "excludes": ["content"]  # 排除大字段以提高性能
            },
            "knn": {
                "field": "context_vector",
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": top_k * 2
            }
        }

        # 如果有文本查询，使用混合搜索
        if query:
            logger.debug("构建混合搜索查询")
            search_body = {
                "size": top_k,
                "_source": {
                    "excludes": ["content"]
                },
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "should": [{
                                    "multi_match": {
                                        "query":
                                        query,
                                        "fields": [
                                            "content^2", "file_name",
                                            "title^2", "text^2", "name"
                                        ],
                                        "type":
                                        "best_fields"
                                    }
                                }],
                                "minimum_should_match":
                                1
                            }
                        },
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

        # 添加过滤条件
        if filters:
            logger.debug(f"添加过滤条件: {filters}")
            filter_conditions = self._build_filter_conditions(filters)
            if "knn" in search_body:
                search_body["knn"]["filter"] = filter_conditions
            elif "query" in search_body:
                # 对于混合搜索，将过滤条件添加到bool查询中
                if "bool" in search_body["query"]["script_score"]["query"]:
                    search_body["query"]["script_score"]["query"]["bool"][
                        "filter"] = filter_conditions["bool"]["must"]

        return search_body

    def _build_text_search_body(self,
                                query: str,
                                filters: Optional[dict[str, Any]] = None,
                                top_k: int = 10) -> dict[str, Any]:
        """
        构建文本搜索查询体

        Args:
            query: 搜索查询
            filters: 过滤条件
            top_k: 返回结果数量

        Returns:
            Dict[str, Any]: 文本搜索查询体
        """
        # 基础文本查询
        search_body = {
            "size": top_k,
            "query": {
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
        }

        # 添加过滤条件
        if filters:
            logger.debug(f"添加过滤条件: {filters}")
            filter_conditions = self._build_filter_conditions(filters)
            search_body["query"]["bool"]["filter"] = filter_conditions["bool"][
                "must"]

        return search_body

    def _build_filter_conditions(self, filters: dict[str,
                                                     Any]) -> dict[str, Any]:
        """
        构建过滤条件

        Args:
            filters: 过滤条件字典

        Returns:
            Dict[str, Any]: 过滤条件查询体
        """
        filter_conditions = {"bool": {"must": [], "must_not": []}}

        for key, value in filters.items():
            if isinstance(value, list):
                if value:  # 非空列表
                    filter_conditions["bool"]["must"].append(
                        {"terms": {
                            key: value
                        }})
            elif value is not None:
                filter_conditions["bool"]["must"].append(
                    {"term": {
                        key: value
                    }})

        logger.debug(f"构建的过滤条件: {filter_conditions}")
        return filter_conditions

    async def search_multiple_indices(
            self,
            indices: list[str],
            query: str,
            top_k: int = 10,
            query_vector: Optional[list[float]] = None,
            filters: Optional[dict[str, Any]] = None) -> list[ESSearchResult]:
        """
        在多个索引中搜索

        Args:
            indices: 索引列表
            query: 搜索查询
            top_k: 返回结果数量
            query_vector: 查询向量
            filters: 过滤条件

        Returns:
            List[ESSearchResult]: 搜索结果列表
        """
        logger.info(f"开始多索引搜索，索引数量: {len(indices)}")
        logger.debug(f"索引列表: {indices}")
        logger.debug(f"搜索参数 - top_k: {top_k}")
        if query_vector:
            logger.debug(f"查询向量维度: {len(query_vector)}")
        if filters:
            logger.debug(f"过滤条件: {filters}")

        if not indices:
            logger.warning("索引列表为空")
            return []

        await self._ensure_connected()

        if not self._client:
            logger.error("ES客户端未连接")
            return []

        try:
            # 构建msearch请求体
            msearch_body = []
            search_body = self._build_search_body(query, query_vector, filters,
                                                  top_k)

            for index in indices:
                msearch_body.append({"index": index})
                msearch_body.append(search_body)

            logger.debug(f"构建msearch请求体，包含 {len(indices)} 个索引")

            # 执行msearch
            response = await self._client.msearch(body=msearch_body)

            # 处理结果
            all_results = []
            for i, search_response in enumerate(response["responses"]):
                if "hits" in search_response and "hits" in search_response[
                        "hits"]:
                    for hit in search_response["hits"]["hits"]:
                        doc_data = hit["_source"]

                        # 获取内容
                        original_content = (doc_data.get('content_view')
                                            or doc_data.get('content')
                                            or doc_data.get('text')
                                            or doc_data.get('title') or '')

                        div_content = (doc_data.get('content')
                                       or doc_data.get('text')
                                       or doc_data.get('title') or '')

                        # 获取来源
                        source = (doc_data.get('meta_data',
                                               {}).get('file_name')
                                  or doc_data.get('file_name')
                                  or doc_data.get('name') or '')

                        # 安全获取 doc_id，如果不存在则使用 _id
                        doc_id = doc_data.get('doc_id', "")

                        result = ESSearchResult(
                            id=hit["_id"],
                            doc_id=doc_id,
                            file_token=doc_data.get('file_token', ""),
                            original_content=original_content,
                            div_content=div_content,
                            source=source,
                            score=hit["_score"],
                            metadata=doc_data.get('meta_data', {}),
                            alias_name=indices[i] if i < len(indices) else "")
                        all_results.append(result)

            logger.info(f"多索引搜索成功，返回 {len(all_results)} 个文档")
            return all_results

        except Exception as e:
            logger.error(f"多索引搜索失败: {str(e)}")
            return []

    async def search_by_file_token(self,
                                   index: str,
                                   file_token: str,
                                   top_k: int = 100) -> list[ESSearchResult]:
        """
        根据file_token查询文档内容
        
        Args:
            index: 索引名称
            file_token: 文件token
            top_k: 返回结果数量
            
        Returns:
            List[ESSearchResult]: 搜索结果列表
        """
        logger.info(f"开始按file_token查询，索引: {index}, file_token: {file_token}")

        await self._ensure_connected()

        if not self._client:
            logger.error("ES客户端未连接")
            return []

        try:
            search_body = {
                "size": top_k * 2,  # 设置更大的size
                "query": {
                    "term": {
                        "doc_id": file_token
                    }
                }
                # 移除排序，避免字段不存在的问题
            }

            logger.debug(f"file_token查询体: {search_body}")

            # 执行搜索
            response = await self._client.search(index=index, body=search_body)

            # 解析结果
            results = []
            for hit in response['hits']['hits']:
                doc_data = hit['_source']

                # 获取原始内容和切分后的内容
                original_content = (doc_data.get('content_view')
                                    or doc_data.get('content')
                                    or doc_data.get('text')
                                    or doc_data.get('title') or '')

                div_content = (doc_data.get('content') or doc_data.get('text')
                               or doc_data.get('title') or '')

                # 灵活获取来源字段
                source = (doc_data.get('meta_data', {}).get('file_name')
                          or doc_data.get('file_name') or doc_data.get('name')
                          or '')

                # 安全获取 doc_id
                doc_id = doc_data.get('doc_id', "")

                result = ESSearchResult(id=hit['_id'],
                                        doc_id=doc_id,
                                        file_token=doc_data.get(
                                            'file_token', ""),
                                        original_content=original_content,
                                        div_content=div_content,
                                        source=source,
                                        score=hit['_score'],
                                        metadata=doc_data.get('meta_data', {}),
                                        alias_name=index)
                results.append(result)

            logger.info(f"file_token查询成功，返回 {len(results)} 个文档")
            return results

        except Exception as e:
            logger.error(f"file_token查询失败: {str(e)}")
            return []

    async def close(self):
        """关闭连接"""
        logger.info("开始关闭ES连接")
        if self._client:
            try:
                await self._client.close()
                self._client = None
                self._initialized = False
                logger.info("ES连接已关闭")

                # 等待一小段时间确保连接完全关闭
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"关闭ES连接失败: {str(e)}")
                self._client = None
                self._initialized = False

    async def get_indices(self) -> list[dict[str, Any]]:
        """获取所有索引信息"""
        logger.debug("获取所有索引信息")
        await self._ensure_connected()

        if not self._client:
            logger.error("ES客户端未连接")
            return []

        try:
            indices = await self._client.cat.indices(format='json')
            logger.debug(f"获取到 {len(indices)} 个索引")
            return indices
        except Exception as e:
            logger.error(f"获取索引失败: {str(e)}")
            return []

    async def get_index_mapping(self, index: str) -> Optional[dict[str, Any]]:
        """获取索引映射"""
        logger.debug(f"获取索引 {index} 的映射信息")
        await self._ensure_connected()

        if not self._client:
            logger.error("ES客户端未连接")
            return None

        try:
            mapping = await self._client.indices.get_mapping(index=index)
            logger.debug(f"成功获取索引 {index} 的映射")
            return mapping[index]['mappings']
        except Exception as e:
            logger.error(f"获取索引映射失败: {str(e)}")
            return None

    async def __aenter__(self):
        logger.debug("进入ES服务异步上下文")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("退出ES服务异步上下文")
        await self.close()
