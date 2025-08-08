#!/usr/bin/env python3
"""
测试原始问题是否已修复
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.graph.callbacks import RedisCallbackHandler
from doc_agent.core.logging_config import logger


def test_original_issue():
    """测试原始问题是否已修复"""
    logger.info("=== 测试原始问题修复 ===")

    try:
        # 创建一个回调处理器（模拟原始错误场景）
        callback_handler = RedisCallbackHandler("test_job_789")

        # 尝试发布事件（这应该不会再报"主事件循环不可用"的错误）
        callback_handler._publish_event("phase_update", {
            "phase": "TESTING",
            "message": "测试事件发布",
            "status": "running"
        })

        logger.success("✅ 原始问题已修复！不再出现'主事件循环不可用'错误。")
        return True

    except Exception as e:
        logger.error(f"❌ 原始问题仍然存在: {e}")
        return False


if __name__ == "__main__":
    success = test_original_issue()
    if success:
        logger.info("🎉 修复成功！")
    else:
        logger.error("❌ 修复失败！")
