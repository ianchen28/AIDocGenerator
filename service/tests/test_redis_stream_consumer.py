#!/usr/bin/env python3
"""
Redis Stream 消费者组测试脚本

测试消费者组的负载均衡、故障恢复和消息处理功能。
"""

import asyncio
import json
from datetime import datetime

import redis.asyncio as redis
from loguru import logger

# 导入我们的消费者组实现
from doc_agent.core.redis_stream_consumer import (
    RedisStreamConsumerGroup,
    create_default_consumer_group,
)
from doc_agent.core.redis_stream_publisher import RedisStreamPublisher


class RedisStreamTester:
    """Redis Stream 测试器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.publisher = None
        self.consumer_group = None

    async def setup(self):
        """设置测试环境"""
        # 创建发布器
        redis_client = redis.from_url(self.redis_url, decode_responses=True)
        await redis_client.ping()
        self.publisher = RedisStreamPublisher(redis_client)

        # 创建消费者组
        self.consumer_group = create_default_consumer_group(self.redis_url)

        logger.info("✅ 测试环境设置完成")

    async def test_single_consumer(self):
        """测试单个消费者"""
        logger.info("🧪 测试单个消费者...")

        # 创建单个消费者
        from doc_agent.core.redis_stream_consumer import RedisStreamConsumer
        consumer = RedisStreamConsumer(self.redis_url, "test_group",
                                       "test_consumer")
        await consumer.connect()

        # 注册测试处理器
        async def test_handler(job_id: str, event_data: dict):
            logger.info(
                f"📨 收到消息: {job_id} -> {event_data.get('event_type', 'unknown')}"
            )

        await consumer.register_handler("test_event", test_handler)

        # 创建消费者组
        stream_name = "test_stream"
        await consumer.create_consumer_group(stream_name)

        # 发布测试消息
        await self.publisher.publish_event(
            "test_job", {
                "event_type": "test_event",
                "message": "Hello from publisher",
                "timestamp": datetime.now().isoformat()
            })

        # 启动消费者（运行5秒）
        logger.info("🚀 启动消费者...")
        consumer_task = asyncio.create_task(
            consumer.start_consuming(stream_name))

        try:
            await asyncio.wait_for(consumer_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.info("⏰ 消费者测试完成")

        await consumer.stop()
        await consumer.close()

    async def test_consumer_group(self):
        """测试消费者组"""
        logger.info("🧪 测试消费者组...")

        # 启动消费者组
        stream_name = "job_events:test_group_job"
        await self.consumer_group.start(stream_name)

        # 发布多个测试消息
        for i in range(10):
            await self.publisher.publish_event(
                "test_group_job", {
                    "event_type": "task_progress",
                    "task_type": "test_task",
                    "progress": f"步骤 {i+1}/10",
                    "timestamp": datetime.now().isoformat()
                })
            await asyncio.sleep(0.1)  # 短暂间隔

        # 等待消息处理
        logger.info("⏳ 等待消息处理...")
        await asyncio.sleep(3)

        # 获取消费者组状态
        status = await self.consumer_group.get_consumer_status()
        logger.info(
            f"📊 消费者组状态: {json.dumps(status, indent=2, ensure_ascii=False)}")

        # 停止消费者组
        await self.consumer_group.stop()

    async def test_fault_tolerance(self):
        """测试故障恢复"""
        logger.info("🧪 测试故障恢复...")

        # 创建自定义处理器，模拟故障
        async def faulty_handler(job_id: str, event_data: dict):
            if event_data.get("message") == "crash":
                raise Exception("模拟故障")
            logger.info(f"✅ 正常处理: {job_id} -> {event_data.get('event_type')}")

        # 创建测试消费者组
        test_group = RedisStreamConsumerGroup(self.redis_url,
                                              "fault_test_group", 2)
        test_group.register_handler("test_event", faulty_handler)

        stream_name = "job_events:fault_test_job"
        await test_group.start(stream_name)

        # 发布正常消息
        await self.publisher.publish_event(
            "fault_test_job", {
                "event_type": "test_event",
                "message": "normal",
                "timestamp": datetime.now().isoformat()
            })

        # 发布故障消息
        await self.publisher.publish_event(
            "fault_test_job", {
                "event_type": "test_event",
                "message": "crash",
                "timestamp": datetime.now().isoformat()
            })

        # 发布更多正常消息
        for i in range(3):
            await self.publisher.publish_event(
                "fault_test_job", {
                    "event_type": "test_event",
                    "message": f"normal_{i}",
                    "timestamp": datetime.now().isoformat()
                })
            await asyncio.sleep(0.1)

        # 等待处理
        await asyncio.sleep(2)

        # 停止测试组
        await test_group.stop()

    async def test_load_balancing(self):
        """测试负载均衡"""
        logger.info("🧪 测试负载均衡...")

        # 创建多个消费者组
        groups = []
        for i in range(3):
            group = RedisStreamConsumerGroup(self.redis_url, f"lb_group_{i}",
                                             2)

            # 注册处理器，记录处理者
            async def create_handler(group_id: int):

                async def handler(job_id: str, event_data: dict):
                    logger.info(
                        f"📨 组 {group_id} 处理: {job_id} -> {event_data.get('event_type')}"
                    )

                return handler

            group.register_handler("test_event", await create_handler(i))
            groups.append(group)

        # 启动所有组
        stream_name = "job_events:lb_test_job"
        for group in groups:
            await group.start(stream_name)

        # 发布大量消息
        logger.info("📤 发布测试消息...")
        for i in range(20):
            await self.publisher.publish_event(
                "lb_test_job", {
                    "event_type": "test_event",
                    "message": f"message_{i}",
                    "timestamp": datetime.now().isoformat()
                })
            await asyncio.sleep(0.05)

        # 等待处理
        await asyncio.sleep(3)

        # 获取所有组的状态
        for i, group in enumerate(groups):
            status = await group.get_consumer_status()
            logger.info(f"📊 组 {i} 状态: {status['consumer_count']} 个消费者")

        # 停止所有组
        for group in groups:
            await group.stop()

    async def test_real_events(self):
        """测试真实事件"""
        logger.info("🧪 测试真实事件...")

        # 创建消费者组，处理真实事件
        real_group = create_default_consumer_group(self.redis_url,
                                                   "real_events_group")
        stream_name = "job_events:real_test_job"
        await real_group.start(stream_name)

        # 发布真实事件序列
        events = [("task_started", {
            "task_type": "outline_generation"
        }),
                  ("task_progress", {
                      "task_type": "outline_generation",
                      "progress": "开始研究主题"
                  }),
                  ("task_progress", {
                      "task_type": "outline_generation",
                      "progress": "收集相关资料"
                  }),
                  ("task_progress", {
                      "task_type": "outline_generation",
                      "progress": "生成大纲结构"
                  }),
                  ("outline_generated", {
                      "outline": {
                          "title": "测试大纲",
                          "nodes": []
                      }
                  }), ("task_started", {
                      "task_type": "document_generation"
                  }),
                  ("task_progress", {
                      "task_type": "document_generation",
                      "progress": "开始文档生成"
                  }),
                  ("task_progress", {
                      "task_type": "document_generation",
                      "progress": "编写章节内容"
                  }),
                  ("document_generated", {
                      "document": {
                          "title": "测试文档",
                          "content": "..."
                      }
                  }), ("task_completed", {
                      "task_type": "document_generation"
                  })]

        for event_type, event_data in events:
            await self.publisher.publish_event(
                "real_test_job", {
                    "event_type": event_type,
                    **event_data, "timestamp": datetime.now().isoformat()
                })
            await asyncio.sleep(0.2)

        # 等待处理
        await asyncio.sleep(3)

        # 停止组
        await real_group.stop()

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始 Redis Stream 消费者组测试")

        try:
            await self.setup()

            # 运行各种测试
            await self.test_single_consumer()
            await asyncio.sleep(1)

            await self.test_consumer_group()
            await asyncio.sleep(1)

            await self.test_fault_tolerance()
            await asyncio.sleep(1)

            await self.test_load_balancing()
            await asyncio.sleep(1)

            await self.test_real_events()

            logger.info("🎉 所有测试完成！")

        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
        finally:
            if self.consumer_group:
                await self.consumer_group.stop()


async def main():
    """主函数"""
    # 配置日志
    logger.add("logs/redis_stream_test.log", rotation="1 day", level="INFO")

    tester = RedisStreamTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
