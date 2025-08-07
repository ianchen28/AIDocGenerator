#!/usr/bin/env python3
"""
测试tools和llm_clients的日志输出
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
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.llm_clients import get_llm_client


def test_tools_logging():
    """测试tools的日志输出"""
    logger.info("🚀 开始测试tools日志输出")

    # 测试web_search工具
    try:
        web_search = WebSearchTool()
        logger.info("✅ WebSearchTool初始化成功")
    except Exception as e:
        logger.error(f"❌ WebSearchTool初始化失败: {e}")

    logger.info("✅ tools日志测试完成")


def test_llm_clients_logging():
    """测试llm_clients的日志输出"""
    logger.info("🚀 开始测试llm_clients日志输出")

    # 测试LLM客户端创建
    try:
        llm_client = get_llm_client("qwen_2_5_235b_a22b")
        logger.info("✅ LLM客户端创建成功")
    except Exception as e:
        logger.error(f"❌ LLM客户端创建失败: {e}")

    logger.info("✅ llm_clients日志测试完成")


if __name__ == "__main__":
    logger.info("🔍 开始测试tools和llm_clients的日志输出")

    test_tools_logging()
    test_llm_clients_logging()

    logger.info("🏁 所有测试完成")
