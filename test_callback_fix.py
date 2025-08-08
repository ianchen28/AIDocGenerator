#!/usr/bin/env python3
"""
测试回调修复的脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.graph.callbacks import RedisCallbackHandler
from doc_agent.core.logging_config import logger


def test_callback_without_main_loop():
    """测试在没有主事件循环的情况下回调是否正常工作"""
    logger.info("开始测试回调修复...")

    try:
        # 创建一个回调处理器
        callback_handler = RedisCallbackHandler("test_job_123")

        # 测试发布事件
        callback_handler._publish_event("test_event", {
            "message": "这是一个测试事件",
            "status": "testing"
        })

        logger.success("✅ 回调测试成功！事件发布正常。")
        return True

    except Exception as e:
        logger.error(f"❌ 回调测试失败: {e}")
        return False


async def test_callback_with_main_loop():
    """测试在有主事件循环的情况下回调是否正常工作"""
    logger.info("开始测试有主事件循环的回调...")

    try:
        # 创建一个回调处理器
        callback_handler = RedisCallbackHandler("test_job_456")

        # 测试发布事件
        callback_handler._publish_event("test_event_async", {
            "message": "这是一个异步测试事件",
            "status": "testing_async"
        })

        logger.success("✅ 异步回调测试成功！事件发布正常。")
        return True

    except Exception as e:
        logger.error(f"❌ 异步回调测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("=== 开始回调修复测试 ===")

    # 测试1: 没有主事件循环的情况
    logger.info("测试1: 没有主事件循环的情况")
    result1 = test_callback_without_main_loop()

    # 测试2: 有主事件循环的情况
    logger.info("测试2: 有主事件循环的情况")
    result2 = asyncio.run(test_callback_with_main_loop())

    if result1 and result2:
        logger.success("🎉 所有测试都通过了！回调修复成功。")
    else:
        logger.error("❌ 部分测试失败，需要进一步检查。")

    logger.info("=== 回调修复测试完成 ===")


if __name__ == "__main__":
    main()
