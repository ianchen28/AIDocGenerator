#!/usr/bin/env python3
"""
查看ES中实际的字段结构
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService
from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)


async def test_es_field_structure():
    """查看ES中实际的字段结构"""
    logger.info("🚀 开始查看ES中实际的字段结构")

    try:
        # 1. 初始化ES服务
        logger.info("📡 初始化ES服务...")
        es_config = settings.elasticsearch_config
        es_hosts = es_config.hosts
        es_username = es_config.username
        es_password = es_config.password

        es_service = ESService(hosts=es_hosts,
                               username=es_username,
                               password=es_password)

        await es_service._ensure_connected()
        logger.info("✅ ES服务连接成功")

        # 2. 查看包含file_token的文档结构
        logger.info("🔍 查看包含file_token的文档结构...")

        # 使用通配符搜索
        search_body = {"size": 3, "query": {"exists": {"field": "file_token"}}}

        response = await es_service._client.search(index="*", body=search_body)
        hits = response['hits']['hits']

        if hits:
            logger.info(f"✅ 发现 {len(hits)} 个包含file_token的文档:")
            for i, hit in enumerate(hits, 1):
                doc_data = hit['_source']
                logger.info(f"  {i}. 文档ID: {hit['_id']}")
                logger.info(
                    f"     File Token: {doc_data.get('file_token', 'N/A')}")
                logger.info(f"     Doc ID: {doc_data.get('doc_id', 'N/A')}")
                logger.info(
                    f"     Content Preview: {doc_data.get('content', 'N/A')[:200]}..."
                )
                logger.info(f"     Title: {doc_data.get('title', 'N/A')}")
                logger.info(
                    f"     File Name: {doc_data.get('file_name', 'N/A')}")
                logger.info(
                    f"     Meta Data: {doc_data.get('meta_data', 'N/A')}")
                logger.info("")
        else:
            logger.warning("⚠️ 没有找到包含file_token的文档")

        # 3. 关闭连接
        await es_service.close()
        logger.info("✅ 测试完成")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_es_field_structure())
