#!/usr/bin/env python3
"""
测试FastAPI后台任务
"""
import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.core.outline_generator import generate_outline_async
from doc_agent.core.logging_config import logger


async def test_background_task():
    """测试后台任务"""
    logger.info("=== 测试FastAPI后台任务 ===")

    try:
        # 模拟后台任务调用
        await generate_outline_async(task_id="test_job_999",
                                     session_id="test_session_999",
                                     task_prompt="请生成一个关于人工智能发展趋势的大纲",
                                     is_online=False,
                                     context_files=[],
                                     style_guide_content=None,
                                     requirements=None)

        logger.success("✅ 后台任务测试成功！")
        return True

    except Exception as e:
        logger.error(f"❌ 后台任务测试失败: {e}")
        import traceback
        logger.error(f"完整错误信息: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_background_task())
    if success:
        logger.info("🎉 后台任务测试通过！")
    else:
        logger.error("❌ 后台任务测试失败！")
