"""
Redis Streams 消费者组实现

支持多消费者负载均衡、故障恢复和消息确认机制。
"""

import asyncio
import json
from typing import Any, Callable, Union

import redis.asyncio as redis
from doc_agent.core.logger import logger


class RedisStreamConsumer:
    """
    Redis Streams 消费者
    
    支持消费者组模式，提供负载均衡和故障恢复功能。
    """

    def __init__(self, redis_url: str, group_name: str, consumer_name: str):
        """
        初始化消费者
        
        Args:
            redis_url: Redis 连接 URL
            group_name: 消费者组名称
            consumer_name: 消费者名称（在组内唯一）
        """
        self.redis_url = redis_url
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.redis_client = None
        self.is_running = False
        self.handlers: dict[str, Callable] = {}

    async def connect(self):
        """连接到 Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True)
            await self.redis_client.ping()
            logger.info(f"✅ Redis 消费者连接成功: {self.consumer_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Redis 消费者连接失败: {e}")
            return False

    async def create_consumer_group(self,
                                    stream_name: str,
                                    start_id: str = "0"):
        """
        创建消费者组
        
        Args:
            stream_name: Stream 名称
            start_id: 起始消息 ID，默认为 "0"（从开始读取）
        """
        try:
            # 检查 Stream 是否存在
            stream_exists = await self.redis_client.exists(stream_name)

            if not stream_exists:
                # 如果 Stream 不存在，先创建一个空消息
                await self.redis_client.xadd(stream_name, {"init": "true"})
                logger.info(f"📝 创建 Stream: {stream_name}")

            # 创建消费者组
            await self.redis_client.xgroup_create(stream_name,
                                                  self.group_name,
                                                  id=start_id,
                                                  mkstream=True)
            logger.info(f"✅ 消费者组创建成功: {self.group_name} -> {stream_name}")

        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"ℹ️ 消费者组已存在: {self.group_name}")
            else:
                logger.error(f"❌ 创建消费者组失败: {e}")
                raise

    async def register_handler(self, event_type: str, handler: Callable):
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数，接收 (job_id, event_data) 参数
        """
        self.handlers[event_type] = handler
        logger.info(f"📝 注册事件处理器: {event_type}")

    async def start_consuming(self, stream_name: str, block_ms: int = 5000):
        """
        开始消费消息
        
        Args:
            stream_name: Stream 名称
            block_ms: 阻塞等待时间（毫秒）
        """
        if not self.redis_client:
            raise Exception("Redis 客户端未连接")

        self.is_running = True
        logger.info(f"🚀 开始消费消息: {self.consumer_name} -> {stream_name}")

        try:
            while self.is_running:
                try:
                    # 从消费者组读取消息
                    messages = await self.redis_client.xreadgroup(
                        self.group_name,
                        self.consumer_name, {stream_name: ">"},
                        count=10,
                        block=block_ms)

                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            await self._process_message(
                                stream, message_id, fields)

                except asyncio.CancelledError:
                    logger.info(f"🛑 消费者被取消: {self.consumer_name}")
                    break
                except Exception as e:
                    logger.error(f"❌ 消费消息时出错: {e}")
                    await asyncio.sleep(1)  # 短暂等待后重试

        finally:
            self.is_running = False
            logger.info(f"🔚 消费者停止: {self.consumer_name}")

    async def _process_message(self, stream: str, message_id: str,
                               fields: dict[str, Any]):
        """
        处理单个消息
        
        Args:
            stream: Stream 名称
            message_id: 消息 ID
            fields: 消息字段
        """
        try:
            # 解析事件数据
            event_data = json.loads(fields.get("data", "{}"))
            # 兼容两种事件类型键名
            event_type = event_data.get(
                "eventType", event_data.get("event_type", "unknown"))

            # 从 Stream 名称提取 job_id - 现在stream名称就是job_id
            job_id = stream

            logger.debug(
                f"📨 收到消息: {message_id} -> {event_type} (job_id: {job_id})")

            # 调用对应的处理器
            if event_type in self.handlers:
                await self.handlers[event_type](job_id, event_data)
            else:
                logger.warning(f"⚠️ 未找到事件处理器: {event_type}")

            # 确认消息已处理
            await self.redis_client.xack(stream, self.group_name, message_id)
            logger.debug(f"✅ 消息已确认: {message_id}")

        except Exception as e:
            logger.error(f"❌ 处理消息失败 {message_id}: {e}")
            # 注意：这里可以选择是否确认消息，取决于错误类型

    async def stop(self):
        """停止消费者"""
        self.is_running = False
        logger.info(f"🛑 停止消费者: {self.consumer_name}")

    async def close(self):
        """关闭连接"""
        await self.stop()
        if self.redis_client:
            await self.redis_client.close()
            logger.info(f"🔌 Redis 消费者连接已关闭: {self.consumer_name}")


class RedisStreamConsumerGroup:
    """
    Redis Streams 消费者组管理器
    
    管理多个消费者实例，提供负载均衡和故障恢复。
    """

    def __init__(self,
                 redis_url: str,
                 group_name: str,
                 consumer_count: int = 3):
        """
        初始化消费者组管理器
        
        Args:
            redis_url: Redis 连接 URL
            group_name: 消费者组名称
            consumer_count: 消费者数量
        """
        self.redis_url = redis_url
        self.group_name = group_name
        self.consumer_count = consumer_count
        self.consumers: dict[str, RedisStreamConsumer] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.handlers: dict[str, Callable] = {}
        self.is_running = False

    async def start(self, stream_name: str):
        """
        启动消费者组
        
        Args:
            stream_name: Stream 名称
        """
        if self.is_running:
            logger.warning("⚠️ 消费者组已在运行")
            return

        self.is_running = True
        logger.info(
            f"🚀 启动消费者组: {self.group_name} (消费者数量: {self.consumer_count})")

        # 创建消费者组
        temp_consumer = RedisStreamConsumer(self.redis_url, self.group_name,
                                            "temp")
        await temp_consumer.connect()
        await temp_consumer.create_consumer_group(stream_name)
        await temp_consumer.close()

        # 启动多个消费者
        for i in range(self.consumer_count):
            consumer_name = f"{self.group_name}-consumer-{i+1}"
            consumer = RedisStreamConsumer(self.redis_url, self.group_name,
                                           consumer_name)

            # 注册处理器
            for event_type, handler in self.handlers.items():
                await consumer.register_handler(event_type, handler)

            # 启动消费者
            await consumer.connect()
            task = asyncio.create_task(consumer.start_consuming(stream_name))

            self.consumers[consumer_name] = consumer
            self.tasks[consumer_name] = task

            logger.info(f"✅ 消费者启动: {consumer_name}")

    async def stop(self):
        """停止消费者组"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info(f"🛑 停止消费者组: {self.group_name}")

        # 停止所有消费者
        for _consumer_name, consumer in self.consumers.items():
            await consumer.stop()

        # 等待所有任务完成
        for task_name, task in self.tasks.items():
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info(f"✅ 消费者任务完成: {task_name}")

        # 关闭所有连接
        for consumer in self.consumers.values():
            await consumer.close()

        self.consumers.clear()
        self.tasks.clear()

    def register_handler(self, event_type: str, handler: Callable):
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self.handlers[event_type] = handler
        logger.info(f"📝 注册全局事件处理器: {event_type}")

    async def get_consumer_status(self) -> dict[str, Any]:
        """
        获取消费者组状态
        
        Returns:
            dict: 状态信息
        """
        status = {
            "group_name": self.group_name,
            "is_running": self.is_running,
            "consumer_count": len(self.consumers),
            "consumers": {}
        }

        for consumer_name, consumer in self.consumers.items():
            status["consumers"][consumer_name] = {
                "is_running": consumer.is_running
            }

        return status


# 预定义的事件处理器
async def default_task_started_handler(job_id: Union[str, int],
                                       event_data: dict):
    """默认的任务开始处理器"""
    task_type = event_data.get("task_type", "unknown")
    logger.info(f"🚀 任务开始: {job_id} -> {task_type}")


async def default_task_progress_handler(job_id: Union[str, int],
                                        event_data: dict):
    """默认的任务进度处理器"""
    task_type = event_data.get("task_type", "unknown")
    progress = event_data.get("progress", "")
    logger.info(f"🔄 任务进度: {job_id} -> {task_type} - {progress}")


async def default_task_completed_handler(job_id: Union[str, int],
                                         event_data: dict):
    """默认的任务完成处理器"""
    task_type = event_data.get("task_type", "unknown")
    logger.info(f"✅ 任务完成: {job_id} -> {task_type}")


async def default_task_failed_handler(job_id: Union[str, int],
                                      event_data: dict):
    """默认的任务失败处理器"""
    task_type = event_data.get("task_type", "unknown")
    error = event_data.get("error", "")
    logger.error(f"❌ 任务失败: {job_id} -> {task_type} - {error}")


async def default_outline_generated_handler(job_id: Union[str, int],
                                            event_data: dict):
    """默认的大纲生成完成处理器"""
    outline = event_data.get("outline", {})
    title = outline.get("title", "Unknown")
    logger.info(f"📋 大纲生成完成: {job_id} -> {title}")


async def default_document_generated_handler(job_id: Union[str, int],
                                             event_data: dict):
    """默认的文档生成完成处理器"""
    document = event_data.get("document", {})
    title = document.get("title", "Unknown")
    logger.info(f"📄 文档生成完成: {job_id} -> {title}")


def create_default_consumer_group(
        redis_url: str,
        group_name: str = "doc_gen_consumers") -> RedisStreamConsumerGroup:
    """
    创建默认的消费者组
    
    Args:
        redis_url: Redis 连接 URL
        group_name: 消费者组名称
        
    Returns:
        RedisStreamConsumerGroup: 配置好的消费者组
    """
    consumer_group = RedisStreamConsumerGroup(redis_url, group_name)

    # 注册默认处理器
    consumer_group.register_handler("task_started",
                                    default_task_started_handler)
    consumer_group.register_handler("task_progress",
                                    default_task_progress_handler)
    consumer_group.register_handler("task_completed",
                                    default_task_completed_handler)
    consumer_group.register_handler("task_failed", default_task_failed_handler)
    consumer_group.register_handler("outline_generated",
                                    default_outline_generated_handler)
    consumer_group.register_handler("document_generated",
                                    default_document_generated_handler)

    return consumer_group
