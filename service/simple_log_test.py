#!/usr/bin/env python3
"""
简单的日志测试
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 导入项目日志配置
from doc_agent.core.config import settings
from doc_agent.core.logging_config import setup_logging
from doc_agent.core.logger import logger

# 确保使用项目的统一日志配置
setup_logging(settings)

if __name__ == "__main__":
    print("开始测试...")
    logger.info("🔍 这是一条测试日志")
    logger.warning("⚠️ 这是一条警告日志")
    logger.error("❌ 这是一条错误日志")
    print("测试完成")
