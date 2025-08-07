#!/usr/bin/env python3
"""
测试日志输出是否实时可见
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doc_agent.core.logger import logger

# 配置loguru输出到app.log文件和控制台
logger.remove()  # 移除默认处理器

# 添加控制台输出
logger.add(
    sys.stderr,
    level="DEBUG",
    format=
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    colorize=True)

# 添加文件输出
logger.add(
    "logs/app.log",
    level="DEBUG",
    format=
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    rotation="10 MB",
    retention="7 days",
    enqueue=False)  # 同步写入，确保实时输出


def test_log_output():
    """测试日志输出"""
    logger.info("🚀 开始测试日志输出")

    for i in range(5):
        logger.info(f"📝 测试日志消息 {i+1}")
        time.sleep(2)  # 每2秒输出一条日志

    logger.info("✅ 测试完成")


if __name__ == "__main__":
    test_log_output()
