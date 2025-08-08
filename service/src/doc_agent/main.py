#!/usr/bin/env python3
"""
AI文档生成器 - 主入口点
"""

import asyncio
from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from fastapi import FastAPI
from doc_agent.api import endpoints
from doc_agent.graph.main_orchestrator.builder import MainOrchestratorBuilder
from doc_agent.core.redis_health_check import init_redis_pool, close_redis_pool
from doc_agent.core import redis_health_check

app = FastAPI(title="Doc Agent API")


@app.on_event("startup")
async def startup_event():
    """
    应用启动事件处理
    """
    logger.info("应用开始启动...")
    # 2. 在应用启动时调用初始化函数
    await init_redis_pool()
    # 4. 获取当前正在运行的事件循环，并存到全局变量中
    redis_health_check.main_event_loop = asyncio.get_running_loop()
    logger.info("应用启动完成，并已捕获主事件循环。")
    logger.info("应用启动完成。")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件处理
    """
    logger.info("应用开始关闭...")
    # 3. 在应用关闭时调用关闭函数
    await close_redis_pool()
    logger.info("应用关闭完成。")


app.include_router(endpoints.router)


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
