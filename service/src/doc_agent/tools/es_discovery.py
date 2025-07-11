"""
ES可用性检测模块
独立处理索引发现和可用性检测功能
"""

import logging
from typing import List, Dict, Any, Optional
from .es_service import ESService

logger = logging.getLogger(__name__)


class ESDiscovery:
    """ES可用性检测类"""

    def __init__(self, es_service: ESService):
        """
        初始化ES检测器
        
        Args:
            es_service: ES服务实例
        """
        self.es_service = es_service
        self._available_indices = []
        self._vector_dims = 1536  # 默认向量维度

    async def discover_knowledge_indices(self) -> List[Dict[str, Any]]:
        """
        发现可用的知识库索引
        
        Returns:
            List[Dict[str, Any]]: 可用索引列表
        """
        try:
            # 连接ES服务
            if not await self.es_service.connect():
                logger.error("无法连接ES服务")
                return []

            # 获取所有索引
            indices = await self.es_service.get_indices()

            # 筛选知识库索引
            knowledge_indices = []
            for idx in indices:
                index_name = idx.get('index', '')
                docs_count = idx.get('docs.count', '0')

                # 查找包含知识库关键词的索引
                if any(keyword in index_name.lower()
                       for keyword in ['knowledge', 'base', 'index']):
                    if docs_count and docs_count != '0' and docs_count != 'None':
                        knowledge_indices.append({
                            'name':
                            index_name,
                            'docs_count':
                            int(docs_count) if docs_count != 'None' else 0
                        })

            # 按文档数量排序，优先使用文档数量多的索引
            knowledge_indices.sort(key=lambda x: x['docs_count'], reverse=True)
            self._available_indices = knowledge_indices

            # 检测向量维度
            if knowledge_indices:
                await self._detect_vector_dims(knowledge_indices[0]['name'])

            logger.info(f"发现 {len(knowledge_indices)} 个可用知识库索引")
            for idx in knowledge_indices[:5]:  # 只显示前5个
                logger.info(f"  - {idx['name']} ({idx['docs_count']} 文档)")

            return knowledge_indices

        except Exception as e:
            logger.error(f"发现索引失败: {str(e)}")
            return []

    async def _detect_vector_dims(self, index_name: str):
        """检测向量维度"""
        try:
            mapping = await self.es_service.get_index_mapping(index_name)
            if mapping:
                properties = mapping.get('properties', {})
                if 'context_vector' in properties:
                    vector_config = properties['context_vector']
                    if 'dims' in vector_config:
                        self._vector_dims = vector_config['dims']
                        logger.info(f"检测到向量维度: {self._vector_dims}")
        except Exception as e:
            logger.warning(f"检测向量维度失败: {str(e)}")

    def get_best_index(self) -> Optional[str]:
        """获取最佳索引名称"""
        if self._available_indices:
            return self._available_indices[0]['name']
        return None

    def get_vector_dims(self) -> int:
        """获取向量维度"""
        return self._vector_dims

    def get_available_indices(self) -> List[Dict[str, Any]]:
        """获取可用索引列表"""
        return self._available_indices.copy()
