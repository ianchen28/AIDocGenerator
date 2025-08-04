#!/usr/bin/env python3
"""
Redis Streams 测试脚本

演示发布器和消费者的完整工作流程
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis.asyncio as redis
from loguru import logger

from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
from doc_agent.core.redis_stream_consumer import (RedisStreamConsumerGroup,
                                                  create_default_consumer_group
                                                  )
from doc_agent.core.config import settings


class RedisStreamsTester:
    """Redis Streams 测试器"""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.redis_client = None
        self.publisher = None
        self.consumer_group = None

    async def setup(self):
        """初始化连接"""
        try:
            logger.info(f"Redis URL: {self.redis_url}")
            # 连接Redis
            self.redis_client = redis.from_url(self.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Redis连接成功")

            # 初始化发布器
            self.publisher = RedisStreamPublisher(self.redis_client)

            # 初始化消费者组
            self.consumer_group = create_default_consumer_group(
                self.redis_url, "test_consumers")

            logger.info("✅ 组件初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def test_publish_events(self, job_id: str):
        """测试发布事件"""
        logger.info(f"🚀 开始测试发布事件: {job_id}")

        try:
            # 1. 发布任务开始事件
            await self.publisher.publish_task_started(job_id,
                                                      "outline_generation",
                                                      query="测试查询")
            logger.info("📤 发布任务开始事件")

            # 2. 发布任务进度事件
            await self.publisher.publish_task_progress(job_id,
                                                       "outline_generation",
                                                       "正在生成大纲...",
                                                       progress_percent=30)
            logger.info("📤 发布任务进度事件")

            # 3. 发布大纲生成完成事件
            outline_data = {
                "title":
                "测试文档大纲",
                "chapters": [{
                    "title": "第一章",
                    "content": "内容1"
                }, {
                    "title": "第二章",
                    "content": "内容2"
                }]
            }
            await self.publisher.publish_outline_generated(
                job_id, outline_data)
            logger.info("📤 发布大纲生成完成事件")

            # 4. 发布任务完成事件
            await self.publisher.publish_task_completed(
                job_id, "outline_generation", result={"outline": outline_data})
            logger.info("📤 发布任务完成事件")

        except Exception as e:
            logger.error(f"❌ 发布事件失败: {e}")

    async def test_consumer_handlers(self, job_id: str):
        """测试自定义消费者处理器"""

        async def custom_task_started_handler(job_id: str, event_data: dict):
            """自定义任务开始处理器"""
            logger.info(f"🎯 自定义处理器 - 任务开始: {job_id}")
            logger.info(f"   任务类型: {event_data.get('taskType', 'unknown')}")
            logger.info(f"   时间戳: {event_data.get('timestamp', 'unknown')}")

        async def custom_outline_generated_handler(job_id: str,
                                                   event_data: dict):
            """自定义大纲生成处理器"""
            logger.info(f"🎯 自定义处理器 - 大纲生成: {job_id}")
            outline = event_data.get('outline', {})
            logger.info(f"   文档标题: {outline.get('title', 'Unknown')}")
            logger.info(f"   章节数量: {len(outline.get('chapters', []))}")

        # 注册自定义处理器
        self.consumer_group.register_handler("task_started",
                                             custom_task_started_handler)
        self.consumer_group.register_handler("outline_generated",
                                             custom_outline_generated_handler)

        logger.info("📝 注册自定义事件处理器")

    async def run_test(self):
        """运行完整测试"""
        logger.info("🧪 开始Redis Streams测试")

        # 初始化
        if not await self.setup():
            return

        # 生成测试任务ID
        job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stream_name = f"job_events:{job_id}"

        try:
            # 注册自定义处理器
            await self.test_consumer_handlers(job_id)

            # 启动消费者组
            await self.consumer_group.start(stream_name)
            logger.info("👥 消费者组已启动")

            # 等待一下确保消费者准备就绪
            await asyncio.sleep(2)

            # 发布测试事件
            await self.test_publish_events(job_id)

            # 等待事件处理
            logger.info("⏳ 等待事件处理...")
            await asyncio.sleep(5)

            # 获取Stream信息
            stream_info = await self.publisher.get_stream_info(job_id)
            stream_length = await self.publisher.get_stream_length(job_id)

            logger.info(f"📊 Stream信息:")
            logger.info(f"   长度: {stream_length}")
            if stream_info:
                logger.info(
                    f"   第一个ID: {stream_info.get('first-entry', ['N/A'])[0]}")
                logger.info(
                    f"   最后一个ID: {stream_info.get('last-entry', ['N/A'])[0]}")

            # 停止消费者组
            await self.consumer_group.stop()
            logger.info("🛑 消费者组已停止")

        except Exception as e:
            logger.error(f"❌ 测试过程中出错: {e}")

        finally:
            # 清理连接
            if self.redis_client:
                await self.redis_client.close()
            logger.info("🧹 清理完成")


async def main():
    """主函数"""
    tester = RedisStreamsTester()
    await tester.run_test()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO")

    # 运行测试
    asyncio.run(main())
