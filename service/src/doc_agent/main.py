#!/usr/bin/env python3
"""
AI文档生成器 - 主入口点
"""

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.graph.main_orchestrator.builder import MainOrchestratorBuilder


def main():
    """主函数 - 命令行入口点"""
    try:
        logger.info("AI文档生成器启动中...")

        # 获取配置
        logger.info(f"配置加载完成: {settings}")

        # 这里可以添加命令行参数解析
        # 例如: 解析 --topic, --output-dir 等参数

        # 构建主编排器
        builder = MainOrchestratorBuilder()
        orchestrator = builder.build()

        logger.info("AI文档生成器启动完成")

        # 这里可以启动具体的文档生成流程
        # 或者启动 FastAPI 服务器

    except Exception as e:
        logger.error(f"启动失败: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
