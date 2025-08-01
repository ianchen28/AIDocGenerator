#!/usr/bin/env python3
"""
Redis Stream 消费者组启动脚本

启动消费者组来处理文档生成任务的事件流。
"""

import asyncio
import signal

from loguru import logger

from doc_agent.core.config import settings

# 导入我们的消费者组实现
from doc_agent.core.redis_stream_consumer import create_default_consumer_group


class ConsumerGroupManager:
    """消费者组管理器"""

    def __init__(self):
        self.consumer_group = None
        self.is_running = False

    async def start(self):
        """启动消费者组"""
        try:
            # 使用配置中的 Redis URL
            redis_url = settings.redis_url
            logger.info(f"🔗 连接到 Redis: {redis_url}")

            # 创建消费者组
            self.consumer_group = create_default_consumer_group(
                redis_url, "doc_gen_consumers")

            # 启动消费者组，监听所有作业事件
            stream_name = "job_events:*"  # 通配符模式，监听所有作业
            await self.consumer_group.start(stream_name)

            self.is_running = True
            logger.info("✅ 消费者组启动成功")

            # 保持运行
            while self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ 启动消费者组失败: {e}")
            raise

    async def stop(self):
        """停止消费者组"""
        self.is_running = False
        if self.consumer_group:
            await self.consumer_group.stop()
            logger.info("🛑 消费者组已停止")

    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"📡 收到信号 {signum}，准备停止...")
        asyncio.create_task(self.stop())


async def main():
    """主函数"""
    # 配置日志
    logger.add("logs/redis_consumers.log", rotation="1 day", level="INFO")

    # 创建管理器
    manager = ConsumerGroupManager()

    # 注册信号处理器
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)

    try:
        logger.info("🚀 启动 Redis Stream 消费者组...")
        await manager.start()
    except KeyboardInterrupt:
        logger.info("🛑 收到中断信号")
    except Exception as e:
        logger.error(f"❌ 运行时错误: {e}")
    finally:
        await manager.stop()
        logger.info("👋 消费者组已退出")


if __name__ == "__main__":
    asyncio.run(main())
