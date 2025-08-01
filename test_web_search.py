#!/usr/bin/env python3
"""测试网络搜索功能"""

import asyncio
import sys

sys.path.append('service/src')

from doc_agent.tools.web_search import WebSearchTool
from loguru import logger


async def test_web_search():
    """测试网络搜索功能"""
    # 创建搜索工具
    web_search_tool = WebSearchTool()

    # 测试查询
    queries = [
        "Prometheus vs Zabbix vs OpenTelemetry",
        "云原生 可观测性",
        "Prometheus 监控",
    ]

    for query in queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"测试查询: {query}")
        logger.info(f"{'='*60}")

        try:
            # 测试异步搜索
            result = await web_search_tool.search_async(query)
            logger.info(f"搜索结果:\n{result}")

            # 测试获取原始数据
            logger.info("尝试获取原始搜索数据...")
            raw_data = await web_search_tool.get_web_search(query)
            logger.info(f"原始数据: {raw_data}")

            web_docs = await web_search_tool.get_web_docs(query)
            logger.info(f"获取到 {len(web_docs)} 个文档")

            if web_docs:
                for i, doc in enumerate(web_docs[:2]):
                    logger.info(f"\n文档 {i+1}:")
                    logger.info(
                        f"  标题: {doc['meta_data'].get('docName', 'Unknown')}")
                    logger.info(f"  URL: {doc['doc_id']}")
                    logger.info(f"  内容长度: {len(doc['text'])} 字符")

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_web_search())
