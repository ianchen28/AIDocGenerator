#!/usr/bin/env python3
"""
测试特定file_token能否被限定范围搜索搜到
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from loguru import logger
from doc_agent.core.config import settings
from doc_agent.tools.es_search import ESSearchTool


async def test_file_token_search():
    """测试特定file_token的搜索"""
    logger.info("🚀 开始测试特定file_token的搜索")

    # 测试用的file_token
    test_file_token = "49d31f012ab81b584124369ec0657e42"
    test_query = "人工智能技术发展"

    try:
        # 1. 初始化ES搜索工具
        es_config = settings.elasticsearch_config
        es_hosts = es_config.hosts
        es_username = es_config.username
        es_password = es_config.password

        es_search_tool = ESSearchTool(hosts=es_hosts,
                                      username=es_username,
                                      password=es_password)
        logger.info("✅ ES搜索工具初始化成功")

        # 2. 测试普通搜索（不限定范围）
        logger.info(f"🔍 测试普通搜索，查询: {test_query}")
        normal_results = await es_search_tool.search(query=test_query,
                                                     top_k=10)
        logger.info(f"✅ 普通搜索结果数量: {len(normal_results)}")

        # 检查普通搜索结果中是否包含我们的file_token
        found_in_normal = False
        for result in normal_results:
            if result.file_token == test_file_token:
                found_in_normal = True
                logger.info(f"✅ 在普通搜索结果中找到目标file_token: {test_file_token}")
                logger.info(f"   分数: {result.score}")
                logger.info(f"   内容预览: {result.original_content[:100]}...")
                break

        if not found_in_normal:
            logger.warning(f"⚠️ 在普通搜索结果中未找到目标file_token: {test_file_token}")

        # 3. 测试限定范围搜索
        logger.info(f"🔍 测试限定范围搜索，file_token: {test_file_token}")
        limited_results = await es_search_tool.search_within_documents(
            query=test_query,
            file_tokens=[test_file_token],
            top_k=10,
            config={'min_score': 0.0}  # 设置最小分数为0
        )
        logger.info(f"✅ 限定范围搜索结果数量: {len(limited_results)}")

        if limited_results:
            logger.info("✅ 限定范围搜索成功找到结果:")
            for i, result in enumerate(limited_results, 1):
                logger.info(f"  {i}. File Token: {result.file_token}")
                logger.info(f"     分数: {result.score}")
                logger.info(f"     内容预览: {result.original_content[:100]}...")
                logger.info(f"     标题: {result.metadata.get('title', 'N/A')}")
        else:
            logger.warning("⚠️ 限定范围搜索未找到结果")

        # 4. 测试直接通过file_token搜索
        logger.info(f"🔍 测试直接通过file_token搜索: {test_file_token}")
        direct_results = await es_search_tool.search_by_file_token(
            file_token=test_file_token, top_k=5)
        logger.info(f"✅ 直接搜索file_token结果数量: {len(direct_results)}")

        if direct_results:
            logger.info("✅ 直接搜索file_token成功:")
            for i, result in enumerate(direct_results, 1):
                logger.info(f"  {i}. File Token: {result.file_token}")
                logger.info(f"     分数: {result.score}")
                logger.info(f"     内容预览: {result.original_content[:100]}...")
                logger.info(f"     标题: {result.metadata.get('title', 'N/A')}")
        else:
            logger.warning("⚠️ 直接搜索file_token未找到结果")

        # 5. 总结
        logger.info("📊 搜索结果总结:")
        logger.info(f"  普通搜索: {'找到' if found_in_normal else '未找到'}")
        logger.info(f"  限定范围搜索: {'找到' if limited_results else '未找到'}")
        logger.info(f"  直接file_token搜索: {'找到' if direct_results else '未找到'}")

        if limited_results:
            logger.info("🎉 限定范围搜索正常工作！")
        else:
            logger.error("❌ 限定范围搜索存在问题，需要进一步调试")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_file_token_search())
