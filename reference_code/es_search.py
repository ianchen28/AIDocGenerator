import sys
sys.path.append(r"E:\project\cyber-rag")
from typing import Dict, List, Any, Optional, Union
from elasticsearch import AsyncElasticsearch
from nacos_config import get_online_es_config, get_config
from service.rag.es_query.es_queries import build_knn_vector_search_query
from service.base.embeddings import gte_qwen2_embedding
from service.base.logger import get_logger
from service.base.timer_utils import timer
# 使用自定义logger替代标准logging
logger = get_logger("es_search")

class ESSearchService:
    """ES搜索服务，处理RAG查询操作"""
    
    def __init__(self):
        self.es_client = None
        self.type_alias_mapping = {}
        self.index_aliases = {}  # 新增：存储索引别名映射
    
    async def initialize(self):
        """初始化ES客户端"""
        try:
            # 获取ES配置
            es_config = get_online_es_config()
            
            # 获取类型到别名的映射配置
            self.type_alias_mapping = get_config()["type_index_mapping"]
            logger.info(f"加载类型别名映射: {self.type_alias_mapping}")
            
            # 创建ES客户端
            self.es_client = AsyncElasticsearch(
                hosts=es_config['es_host'].split(','),
                http_auth=(es_config['es_user'], es_config['es_password']) if es_config['es_user'] else None,
                verify_certs=False if es_config['es_use_ssl'] else None,
                ssl_show_warn=False
            )
            
            # 尝试ping服务器确认连接有效
            await self.es_client.info()
            logger.info("ES客户端连接成功")
            
            # 获取并存储索引别名
            await self.get_all_aliases()
        except Exception as e:
            logger.error(f"初始化ES客户端失败: {str(e)}")
            # 如果初始化失败，确保客户端被设为None
            self.es_client = None
            raise
    
    async def search_general(self, types: List[str], question: str, top_k: int, knowledge_base_ids: List[str]
                     , exclude_doc_ids: List[str], include_doc_ids: List[str]) -> Dict:
        """根据查询参数和类型进行搜索
        
        Args:
            types: 搜索类型列表
            question: 查询问题
            top_k: 返回结果数量
            knowledge_base_ids: 知识库ID列表
            exclude_doc_ids: 排除的文档ID列表
            include_doc_ids: 包含的文档ID列表
            
        Returns:
            搜索结果
        """
        if not self.es_client:
            try:
                await self.initialize()
                if not self.es_client:
                    return {
                        "message": "无法初始化ES客户端",
                        "errors": True,
                        "hits": []
                    }
            except Exception as e:
                logger.error(f"初始化ES客户端失败: {str(e)}")
                return {
                    "message": f"初始化ES客户端失败: {str(e)}",
                    "errors": True,
                    "hits": []
                }
        
        try:
            # 获取查询类型
            search_types = types
            if isinstance(search_types, str):
                search_types = [search_types]
            
            if not search_types:
                return []
            
            # 根据类型获取对应的别名
            aliases = []
            for search_type in search_types:
                alias_name = self.type_alias_mapping.get(search_type)
                if alias_name:
                    aliases.append(alias_name)
                else:
                    logger.warning(f"未找到类型 '{search_type}' 对应的别名")
            
            if not aliases:
                return {
                  
                }
            
            # 构建查询
            embedding = (await gte_qwen2_embedding(question))[0]
            search_query = build_knn_vector_search_query(embedding
                                                         , top_k
                                                         , knowledge_base_ids
                                                         , include_doc_ids
                                                         , exclude_doc_ids)
            
            
            # 执行搜索
            search_result_hits = await self.search_multiple_aliases_msearch(aliases, search_query, size=10)
            search_result_hits=[ x["_source"] for x in search_result_hits ]
            return search_result_hits
            
        except Exception as e:
            logger.error(f"执行搜索时出错: {str(e)}")
            return []
    
    async def search_multiple_aliases_msearch(self, aliases, search_query, size=10):
        # 准备msearch请求体
        msearch_body = []
        
        for alias in aliases:
            # 添加别名信息行
            msearch_body.append({"index": alias})
            
            # 复制并确保查询中有size参数
            alias_query = search_query.copy()
            if "size" not in alias_query:
                alias_query["size"] = size
                
            # 添加查询行
            msearch_body.append(alias_query)
        
        # 执行msearch请求
        results = await self.es_client.msearch(body=msearch_body)
        
        # 处理结果
        all_hits = []
        for i, response in enumerate(results["responses"]):
            if "hits" in response and "hits" in response["hits"]:
                # 为每个结果添加来源别名信息
                for hit in response["hits"]["hits"]:
                    hit["_source"]["_alias_name"] = aliases[i]
                all_hits.extend(response["hits"]["hits"])
        
        return all_hits
    
    async def close(self):
        """关闭ES客户端连接"""
        if self.es_client:
            await self.es_client.close()
            self.es_client = None
            logger.info("ES客户端已关闭")

    @timer(log_level="info",logger_name="es_search")
    async def msearch_general(self, msearch_body:List[dict]):
        """根据搜索信息进行搜索"""
        # print(msearch_body)
        if not self.es_client:
            try:
                await self.initialize()
                if not self.es_client:
                    logger.error("无法初始化ES客户端")
                    return []
            except Exception as e:
                logger.error(f"初始化ES客户端失败: {str(e)}")
                return []
        
        try:
            results = await self.es_client.msearch(body=msearch_body)
            all_hits = []
            
            # 记录每个查询的耗时信息
            for i, response in enumerate(results["responses"]):
                # 获取当前查询的索引名称
                index_name = msearch_body[i*2].get("index", "未知索引") if i*2 < len(msearch_body) else "未知索引"
                
                if "took" in response:
                    logger.info(f"ES查询 #{i+1} 索引: {index_name} 耗时: {response['took']}ms")
                if "hits" in response and "hits" in response["hits"]:
                    all_hits.extend(response["hits"]["hits"])
            
            # 记录整体msearch请求的耗时
            if "took" in results:
                logger.info(f"ES msearch 总耗时: {results['took']}ms")
                
            return all_hits
        except Exception as e:
            logger.error(f"执行msearch搜索时出错: {str(e)}")
            return []

    async def get_all_aliases(self) -> Dict[str, List[str]]:
        """获取所有索引的别名映射
        
        Returns:
            Dict[str, List[str]]: 索引名到别名列表的映射
        """
        if not self.es_client:
            logger.error("ES客户端未初始化，无法获取别名")
            return {}
            
        try:
            # 获取所有别名信息
            aliases_info = await self.es_client.indices.get_alias(index="*")
            
            # 构建索引到别名的映射
            index_aliases = {}
            for index_name, info in aliases_info.items():
                if 'aliases' in info:
                    index_aliases[index_name] = list(info['aliases'].keys())
                else:
                    index_aliases[index_name] = []
            
            self.index_aliases = index_aliases
            logger.info(f"成功获取索引别名映射，共 {len(index_aliases)} 个索引")
            return index_aliases
            
        except Exception as e:
            logger.error(f"获取索引别名时出错: {str(e)}")
            return {}

    @timer(log_level="info",logger_name="es_search")
    async def update_es_query(self, index: str, update_query: Dict[str, Any]) -> Dict[str, Any]:
        """更新ES中的文档
        
        Args:
            index: 索引名称或别名
            update_query: 更新查询，包含查询条件和更新内容
            
        Returns:
            Dict[str, Any]: 更新操作的结果
        """
        if not self.es_client:
            try:
                await self.initialize()
                if not self.es_client:
                    logger.error("无法初始化ES客户端")
                    return {"error": "无法初始化ES客户端", "updated": 0}
            except Exception as e:
                logger.error(f"初始化ES客户端失败: {str(e)}")
                return {"error": f"初始化ES客户端失败: {str(e)}", "updated": 0}
        
        try:
            # 执行更新操作
            result = await self.es_client.update_by_query(
                index=index,
                body=update_query,
                refresh=True  # 确保更新立即可见
            )
            
            logger.info(f"ES更新操作完成: 索引={index}, 更新文档数={result.get('updated', 0)}")
            return {"status":"ok","code":200}
        except Exception as e:
            logger.error(f"执行ES更新操作时出错: {str(e)}")
            return {"status":"error str(e)","code":-1}


    async def delete_es_query(self, index: str, delete_query: Dict[str, Any]) -> Dict[str, Any]:
        """删除ES中的文档
        
        Args:
            index: 索引名称或别名
            delete_query: 删除查询，包含查询条件
            
        Returns:
            Dict[str, Any]: 删除操作的结果
        """
        if not self.es_client:
            try:
                await self.initialize()
                if not self.es_client:
                    logger.error("无法初始化ES客户端")
                    return {"error": "无法初始化ES客户端", "deleted": 0}
            except Exception as e:
                logger.error(f"初始化ES客户端失败: {str(e)}")
                return {"error": f"初始化ES客户端失败: {str(e)}", "deleted": 0}
        
        try:
            # 执行删除操作
            result = await self.es_client.delete_by_query(
                index=index,
                body=delete_query,
                refresh=True  # 确保删除立即可见
            )
            
            logger.info(f"ES删除操作完成: 索引={index}, 删除文档数={result.get('deleted', 0)}")
            return {"status":"ok","code":200}   
        except Exception as e:
            logger.error(f"执行ES删除操作时出错: {str(e)}")
            return {"status":"error str(e)","code":-1}
    

es_search_service = ESSearchService()
