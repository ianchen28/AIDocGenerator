#!/usr/bin/env python3
"""
简单的 loguru 测试脚本
"""

from loguru import logger
import pprint


def test_loguru():
    """测试 loguru 日志系统"""
    print("=== 测试 loguru 日志系统 ===")

    # 测试不同级别的日志
    logger.info("这是一条信息日志")
    logger.debug("这是一条调试日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")

    # 测试格式化日志
    test_data = {
        "name": "测试数据",
        "value": 123,
        "items": ["item1", "item2", "item3"]
    }

    logger.debug(f"测试数据结构:\n{pprint.pformat(test_data)}")

    # 测试异常日志
    try:
        raise ValueError("这是一个测试异常")
    except Exception as e:
        logger.error(f"捕获到异常: {e}")

    print("✅ loguru 日志系统测试完成")
    print("请检查控制台输出和日志文件")


if __name__ == "__main__":
    test_loguru()
