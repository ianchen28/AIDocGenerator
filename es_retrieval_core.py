"""
Elasticsearch 检索核心逻辑
独立可复用的ES检索代码段
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from elasticsearch import AsyncElasticsearch

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档数据模型"""
    id: str
    content: str
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def get_score(self) -> float:
        """获取文档评分"""
        return self.metadata.get('score', 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'source': self.source,
            'metadata': self.metadata,
            'created_at':
            self.created_at.isoformat() if self.created_at else None,
            'updated_at':
            self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class SearchRequest:
    """搜索请求模型"""
    query_vector: List[float]
    query_text: str = ""
    top_k: int = 10
    index_name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


@dataclass
class SearchResponse:
    """搜索响应模型"""
    documents: List[Document]
    total_count: int = 0
    query: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.total_count == 0:
            self.total_count = len(self.documents)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'documents': [doc.to_dict() for doc in self.documents],
            'total_count': self.total_count,
            'query': self.query,
            'metadata': self.metadata
        }


class ESClientManager:
    """ES客户端管理器"""

    def __init__(self, client_name: str = "default"):
        self.client: Optional[AsyncElasticsearch] = None
        self.current_config: Dict[str, Any] = {}
        self.client_name = client_name

    def create_client(self, config: Dict[str, Any]) -> AsyncElasticsearch:
        """根据配置创建ES客户端"""
        try:
            # 构建连接地址
            if isinstance(config.get('hosts'), list):
                hosts = config['hosts']
            elif isinstance(config.get('hosts'), str):
                hosts = config['hosts'].split(',')
            else:
                host = config.get('host', 'localhost')
                port = config.get('port', 9200)
                scheme = config.get('scheme', 'http')
                hosts = [f"{scheme}://{host}:{port}"]

            es_kwargs = {
                "hosts": hosts,
                "verify_certs": config.get('verify_certs', False),
                "ssl_show_warn": False,
                "timeout": config.get('timeout', 30),
                "max_retries": config.get('max_retries', 3),
                "retry_on_timeout": config.get('retry_on_timeout', True)
            }

            # 添加认证信息
            username = config.get('username') or config.get('user')
            password = config.get('password')
            if username and password:
                es_kwargs["basic_auth"] = (username, password)

            logger.info(f"创建{self.client_name} ES客户端，连接地址: {hosts[0]}")
            self.client = AsyncElasticsearch(**es_kwargs)
            self.current_config = config.copy()
            return self.client

        except Exception as e:
            logger.error(f"创建{self.client_name} ES客户端失败: {str(e)}")
            raise

    async def test_connection(self) -> bool:
        """测试ES连接"""
        if not self.client:
            return False

        try:
            await self.client.info()
            return True
        except Exception as e:
            logger.error(f"{self.client_name} ES连接测试失败: {str(e)}")
            return False

    async def is_client_valid(self) -> bool:
        """检查客户端是否有效"""
        if not self.client:
            return False

        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def get_valid_client(self) -> Optional[AsyncElasticsearch]:
        """获取有效的ES客户端"""
        if not await self.is_client_valid():
            if self.current_config:
                try:
                    if self.client:
                        try:
                            await self.client.close()
                        except:
                            pass
                    self.create_client(self.current_config)
                except Exception as e:
                    logger.error(f"重新创建{self.client_name} ES客户端失败: {str(e)}")
                    return None
            else:
                return None

        return self.client

    async def close(self):
        """关闭ES客户端"""
        if self.client:
            try:
                await self.client.close()
                self.client = None
            except Exception as e:
                logger.error(f"关闭{self.client_name} ES客户端时出错: {str(e)}")


class ESRetrieverCore:
    """ES检索核心逻辑"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化ES检索器
        
        Args:
            config: ES配置字典，包含以下字段：
                - hosts: ES服务器地址列表或字符串
                - port: ES端口（可选）
                - username: 用户名（可选）
                - password: 密码（可选）
                - timeout: 超时时间（可选，默认30）
                - default_index: 默认索引名（可选）
        """
        self.config = config
        self.default_index = config.get('default_index', 'knowledge_base')
        self.timeout = config.get('timeout', 30)
        self.es_manager = ESClientManager()

    async def initialize(self) -> bool:
        """
        初始化ES客户端
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            es_config = {
                'hosts': self.config.get('hosts', ['localhost:9200']),
                'port': self.config.get('port', 9200),
                'username': self.config.get('username', ''),
                'password': self.config.get('password', ''),
                'timeout': self.timeout
            }

            self.es_manager.create_client(es_config)

            if await self.es_manager.test_connection():
                logger.info("ES客户端初始化成功")
                return True
            else:
                logger.error("ES连接测试失败")
                return False

        except Exception as e:
            logger.error(f"初始化ES客户端失败: {str(e)}")
            return False

    async def search_documents(self, request: SearchRequest) -> SearchResponse:
        """
        搜索文档
        
        Args:
            request: 搜索请求对象
            
        Returns:
            SearchResponse: 搜索响应对象
        """
        client = await self.es_manager.get_valid_client()
        if not client:
            logger.error("无法获取有效的ES客户端")
            return SearchResponse(documents=[], query=request.query_text)

        index = request.index_name or self.default_index

        try:
            # 构建搜索查询
            search_query = self._build_search_query(request.query_vector,
                                                    request.query_text,
                                                    request.top_k,
                                                    request.filters)

            # 执行搜索
            response = await client.search(index=index,
                                           body=search_query,
                                           size=request.top_k)

            # 解析结果
            documents = []
            for hit in response['hits']['hits']:
                doc_data = hit['_source']

                # 创建Document对象
                source = doc_data.get('meta_data', {}).get('file_name', '')
                document = Document(id=hit['_id'],
                                    content=doc_data.get(
                                        'content_view',
                                        doc_data.get('content', '')),
                                    source=source,
                                    metadata={
                                        'score': hit['_score'],
                                        'index': hit['_index'],
                                        **doc_data.get('meta_data', {})
                                    })
                documents.append(document)

            logger.info(f"ES搜索成功，返回 {len(documents)} 个文档")
            return SearchResponse(documents=documents,
                                  query=request.query_text,
                                  metadata={'index': index})

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            return SearchResponse(documents=[], query=request.query_text)

    def _build_search_query(
            self,
            query_vector: List[float],
            query_text: str = "",
            top_k: int = 10,
            filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        构建混合搜索查询
        
        Args:
            query_vector: 查询向量
            query_text: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            Dict[str, Any]: ES查询体
        """
        # 基础查询
        base_query = {"match_all": {}}
        if query_text:
            base_query = {
                "bool": {
                    "should": [{
                        "multi_match": {
                            "query": query_text,
                            "fields": ["content^2", "file_name"],
                            "type": "best_fields"
                        }
                    }],
                    "minimum_should_match":
                    1
                }
            }

        # 增加 context_vector 存在性过滤，避免 NaN
        exists_filter = {"exists": {"field": "context_vector"}}
        if isinstance(base_query, dict) and "bool" in base_query:
            if "filter" in base_query["bool"]:
                if isinstance(base_query["bool"]["filter"], list):
                    base_query["bool"]["filter"].append(exists_filter)
                else:
                    base_query["bool"]["filter"] = [
                        base_query["bool"]["filter"], exists_filter
                    ]
            else:
                base_query["bool"]["filter"] = [exists_filter]
        else:
            base_query = {
                "bool": {
                    "must": [base_query],
                    "filter": [exists_filter]
                }
            }

        # 使用script_score进行向量相似度计算
        query = {
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

        # 添加过滤条件
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_conditions.append({"terms": {key: value}})
                else:
                    filter_conditions.append({"term": {key: value}})

            if filter_conditions:
                if isinstance(base_query, dict) and "bool" in base_query:
                    if "filter" in base_query["bool"]:
                        base_query["bool"]["filter"].extend(filter_conditions)
                    else:
                        base_query["bool"]["filter"] = filter_conditions
                else:
                    base_query = {
                        "bool": {
                            "must": [base_query],
                            "filter": filter_conditions
                        }
                    }
                query["query"]["script_score"]["query"] = base_query

        return query

    async def create_index(self,
                           index_name: str,
                           vector_dims: int = 1024) -> bool:
        """
        创建索引
        
        Args:
            index_name: 索引名称
            vector_dims: 向量维度
            
        Returns:
            bool: 创建是否成功
        """
        client = await self.es_manager.get_valid_client()
        if not client:
            logger.error("无法获取有效的ES客户端")
            return False

        try:
            # 检查索引是否已存在
            if await client.indices.exists(index=index_name):
                logger.info(f"索引已存在: {index_name}")
                return True

            # 创建索引映射
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "source": {
                            "type": "keyword"
                        },
                        "meta_data": {
                            "type": "object"
                        },
                        "context_vector": {
                            "type": "dense_vector",
                            "dims": vector_dims,
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }

            await client.indices.create(index=index_name, body=mapping)
            logger.info(f"索引创建成功: {index_name}")
            return True

        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            return False

    async def index_document(self,
                             document: Document,
                             index_name: Optional[str] = None) -> bool:
        """
        索引文档
        
        Args:
            document: 文档对象
            index_name: 索引名称（可选）
            
        Returns:
            bool: 索引是否成功
        """
        client = await self.es_manager.get_valid_client()
        if not client:
            logger.error("无法获取有效的ES客户端")
            return False

        index = index_name or self.default_index

        try:
            # 准备文档数据
            doc_data = {
                'content': document.content,
                'source': document.source,
                'meta_data': document.metadata
            }

            # 索引文档
            await client.index(index=index, id=document.id, body=doc_data)
            logger.info(f"文档索引成功: {document.id}")
            return True

        except Exception as e:
            logger.error(f"文档索引失败: {str(e)}")
            return False

    async def close(self):
        """关闭连接"""
        await self.es_manager.close()


# 使用示例和接口定义
async def create_es_retriever(config: Dict[str, Any]) -> ESRetrieverCore:
    """
    创建ES检索器实例
    
    Args:
        config: ES配置字典
        
    Returns:
        ESRetrieverCore: ES检索器实例
    """
    retriever = ESRetrieverCore(config)
    success = await retriever.initialize()
    if not success:
        raise ConnectionError("ES客户端初始化失败")
    return retriever


# 输入输出接口定义
"""
输入接口:
1. SearchRequest - 搜索请求
   - query_vector: List[float] - 查询向量
   - query_text: str - 查询文本
   - top_k: int - 返回结果数量
   - index_name: Optional[str] - 索引名称
   - filters: Optional[Dict[str, Any]] - 过滤条件

2. Document - 文档对象
   - id: str - 文档ID
   - content: str - 文档内容
   - source: str - 文档来源
   - metadata: Dict[str, Any] - 元数据

输出接口:
1. SearchResponse - 搜索响应
   - documents: List[Document] - 文档列表
   - total_count: int - 总数量
   - query: str - 查询文本
   - metadata: Dict[str, Any] - 元数据

配置接口:
1. ES配置字典
   - hosts: Union[List[str], str] - ES服务器地址
   - port: int - ES端口（可选）
   - username: str - 用户名（可选）
   - password: str - 密码（可选）
   - timeout: int - 超时时间（可选）
   - default_index: str - 默认索引名（可选）

核心方法:
1. search_documents(request: SearchRequest) -> SearchResponse
2. create_index(index_name: str, vector_dims: int = 1024) -> bool
3. index_document(document: Document, index_name: Optional[str] = None) -> bool
4. close() -> None
"""
