#!/usr/bin/env python3
"""
测试ES中的file_token搜索
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


async def test_es_file_token_search():
    """测试ES中的file_token搜索"""
    logger.info("🚀 开始测试ES中的file_token搜索")

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

        # 2. 获取可用索引
        logger.info("📋 获取可用索引...")
        indices = await es_service.get_indices()
        logger.info(f"✅ 发现 {len(indices)} 个索引")

        # 3. 测试file_token搜索
        test_file_token = "2135fc8eff8aa40e5b0957c96caae252"
        logger.info(f"🔍 测试file_token搜索: {test_file_token}")

        # 使用通配符索引搜索
        results = await es_service.search_by_file_token(
            index="*", file_token=test_file_token, top_k=10)

        logger.info(f"✅ file_token搜索完成，返回 {len(results)} 个结果")

        if results:
            logger.info("📄 搜索结果详情:")
            for i, result in enumerate(results[:3], 1):  # 只显示前3个
                logger.info(f"  {i}. ID: {result.id}")
                logger.info(f"     Doc ID: {result.doc_id}")
                logger.info(f"     File Token: {result.file_token}")
                logger.info(f"     Source: {result.source}")
                logger.info(f"     Score: {result.score}")
                logger.info(
                    f"     Content Preview: {result.original_content[:100]}..."
                )
                logger.info("")
        else:
            logger.warning("⚠️ 没有找到匹配的文档")

            # 4. 检查ES中是否有任何包含file_token的文档
            logger.info("🔍 检查ES中是否有任何包含file_token的文档...")

            # 使用通配符搜索
            search_body = {
                "size": 5,
                "query": {
                    "exists": {
                        "field": "file_token"
                    }
                }
            }

            response = await es_service._client.search(index="*",
                                                       body=search_body)
            hits = response['hits']['hits']

            if hits:
                logger.info(f"✅ 发现 {len(hits)} 个包含file_token的文档:")
                for i, hit in enumerate(hits, 1):
                    doc_data = hit['_source']
                    file_token = doc_data.get('file_token', 'N/A')
                    logger.info(f"  {i}. File Token: {file_token}")
                    logger.info(
                        f"     Source: {doc_data.get('meta_data', {}).get('file_name', 'N/A')}"
                    )
            else:
                logger.warning("⚠️ ES中没有找到任何包含file_token的文档")

        # 5. 关闭连接
        await es_service.close()
        logger.info("✅ 测试完成")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_es_file_token_search())
