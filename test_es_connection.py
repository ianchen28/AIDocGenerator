#!/usr/bin/env python3
"""
测试ES连接
"""
import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.tools.es_service import ESService
from doc_agent.core.logging_config import logger


async def test_es_connection():
    """测试ES连接"""
    logger.info("=== 测试ES连接 ===")

    # ES配置
    hosts = ["https://10.238.130.44:9200"]
    username = "devops"
    password = "mQxMg8wEKnN1WExz"

    try:
        # 创建ES服务
        es_service = ESService(hosts=hosts,
                               username=username,
                               password=password)

        # 测试连接
        logger.info("🔍 测试ES连接...")
        connected = await es_service.connect()

        if connected:
            logger.success("✅ ES连接成功！")

            # 测试获取索引
            logger.info("🔍 获取索引列表...")
            indices = await es_service.get_indices()
            logger.info(f"📊 找到 {len(indices)} 个索引")

            # 显示前几个索引
            for i, index in enumerate(indices[:5]):
                logger.info(f"  {i+1}. {index.get('index', 'unknown')}")

            # 测试搜索
            if indices:
                test_index = indices[0].get('index', 'standard_index_base')
                logger.info(f"🔍 测试搜索索引: {test_index}")

                results = await es_service.search(index=test_index,
                                                  query="人工智能",
                                                  top_k=3)

                logger.info(f"📊 搜索返回 {len(results)} 个结果")
                for i, result in enumerate(results[:3]):
                    logger.info(
                        f"  结果 {i+1}: {result.original_content[:100]}...")

            # 关闭连接
            await es_service.close()
            logger.success("✅ ES测试完成！")
            return True

        else:
            logger.error("❌ ES连接失败！")
            return False

    except Exception as e:
        logger.error(f"❌ ES测试失败: {e}")
        import traceback
        logger.error(f"完整错误: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_es_connection())
    if success:
        logger.info("🎉 ES连接测试通过！")
    else:
        logger.error("❌ ES连接测试失败！")
