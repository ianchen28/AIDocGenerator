#!/usr/bin/env python3
"""
测试web_search功能
"""
import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.tools.web_search import WebSearchTool
from doc_agent.core.logging_config import logger


async def test_web_search():
    """测试web_search功能"""
    logger.info("=== 测试Web Search功能 ===")

    try:
        # 创建web_search工具
        web_search = WebSearchTool()
        logger.info("✅ WebSearchTool初始化成功")

        # 测试搜索
        query = "人工智能发展趋势"
        logger.info(f"🔍 开始搜索: {query}")

        result = await web_search.search_async(query)

        # 检查返回格式
        if isinstance(result, tuple) and len(result) == 2:
            web_docs, formatted_result = result
            logger.success(f"✅ 搜索成功，返回 {len(web_docs)} 个结果")

            # 显示前3个结果
            for i, doc in enumerate(web_docs[:3]):
                logger.info(f"结果 {i+1}:")
                logger.info(
                    f"  标题: {doc.get('meta_data', {}).get('docName', 'Unknown')}"
                )
                logger.info(f"  URL: {doc.get('url', 'Unknown')}")
                logger.info(f"  内容长度: {len(doc.get('text', ''))} 字符")
                logger.info(f"  内容预览: {doc.get('text', '')[:100]}...")
                logger.info("")
        else:
            logger.warning(f"⚠️ 搜索返回格式异常: {type(result)}")
            logger.info(f"返回内容: {result}")

        return True

    except Exception as e:
        logger.error(f"❌ Web Search测试失败: {e}")
        import traceback
        logger.error(f"完整错误: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_web_search())
    if success:
        logger.info("🎉 Web Search测试通过！")
    else:
        logger.error("❌ Web Search测试失败！")
