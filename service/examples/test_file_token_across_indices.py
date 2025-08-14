#!/usr/bin/env python3
"""
测试特定file_token在哪些索引中存在
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from loguru import logger
from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService


async def test_file_token_across_indices():
    """测试特定file_token在哪些索引中存在"""
    logger.info("🚀 开始测试特定file_token在哪些索引中存在")

    # 测试用的file_token
    test_file_token = "49d31f012ab81b584124369ec0657e42"

    try:
        # 1. 初始化ES服务
        es_config = settings.elasticsearch_config
        es_hosts = es_config.hosts
        es_username = es_config.username
        es_password = es_config.password

        es_service = ESService(hosts=es_hosts,
                               username=es_username,
                               password=es_password)
        logger.info("✅ ES服务初始化成功")

        # 2. 连接ES
        await es_service._ensure_connected()
        logger.info("✅ ES服务连接成功")

        # 3. 获取所有索引
        indices = await es_service.get_indices()
        logger.info(f"✅ 获取到 {len(indices)} 个索引")

        # 4. 测试每个索引
        found_indices = []
        for i, index_info in enumerate(indices):
            if isinstance(index_info, dict):
                index_name = index_info.get('index', str(index_info))
            else:
                index_name = str(index_info)

            logger.info(f"🔍 测试索引 {i+1}/{len(indices)}: {index_name}")

            try:
                # 在每个索引中搜索这个file_token
                search_body = {
                    "size": 1,
                    "query": {
                        "term": {
                            "file_token": test_file_token
                        }
                    }
                }

                response = await es_service._client.search(index=index_name,
                                                           body=search_body)

                hits = response['hits']['hits']
                if hits:
                    found_indices.append(index_name)
                    logger.info(f"✅ 在索引 {index_name} 中找到 {len(hits)} 个文档")

                    # 显示第一个文档的信息
                    doc_data = hits[0]['_source']
                    logger.info(f"   文档ID: {hits[0]['_id']}")
                    logger.info(
                        f"   File Token: {doc_data.get('file_token', 'N/A')}")
                    logger.info(f"   Doc ID: {doc_data.get('doc_id', 'N/A')}")
                    logger.info(
                        f"   内容预览: {doc_data.get('content', 'N/A')[:100]}...")
                else:
                    logger.debug(f"❌ 在索引 {index_name} 中未找到")

            except Exception as e:
                logger.warning(f"⚠️ 测试索引 {index_name} 时出错: {str(e)}")

        # 5. 总结
        logger.info("📊 搜索结果总结:")
        logger.info(f"  目标file_token: {test_file_token}")
        logger.info(f"  总索引数: {len(indices)}")
        logger.info(f"  包含该file_token的索引数: {len(found_indices)}")

        if found_indices:
            logger.info("✅ 包含该file_token的索引:")
            for idx in found_indices:
                logger.info(f"  - {idx}")
        else:
            logger.error("❌ 没有找到包含该file_token的索引")

        # 6. 关闭连接
        await es_service.close()
        logger.info("✅ 测试完成")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_file_token_across_indices())
