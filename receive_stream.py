#!/usr/bin/env python3
"""
Redis Stream 接收脚本
用于接收和显示 AI 文档生成器的流式数据
"""

import asyncio
import json
import sys
from typing import Optional

import redis.asyncio as redis
from doc_agent.core.logger import logger


class StreamReceiver:
    """Redis Stream 接收器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.is_running = False

    async def connect(self):
        """连接到 Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Redis 连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            return False

    async def receive_stream(self,
                             job_id: str,
                             stream_name: Optional[str] = None):
        """
        接收指定 job_id 的流数据
        
        Args:
            job_id: 任务ID
            stream_name: Stream 名称，如果为 None 则使用默认格式
        """
        if stream_name is None:
            stream_name = f"job:{job_id}"

        logger.info(f"🎯 开始监听 Stream: {stream_name}")
        logger.info(f"📋 任务ID: {job_id}")
        logger.info("=" * 60)

        # 记录最后读取的位置
        last_id = "0"

        try:
            while self.is_running:
                # 读取新消息
                messages = await self.redis_client.xread(
                    {stream_name: last_id},
                    count=10,
                    block=5000  # 阻塞5秒
                )

                if not messages:
                    continue

                # 处理消息
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        await self._process_message(job_id, message_id, fields)
                        last_id = message_id

        except KeyboardInterrupt:
            logger.info("🛑 用户中断，停止接收")
        except Exception as e:
            logger.error(f"❌ 接收流数据时出错: {e}")

    async def _process_message(self, job_id: str, message_id: str,
                               fields: dict):
        """处理接收到的消息"""
        try:
            # 提取数据
            data_str = fields.get("data", "{}")
            event_data = json.loads(data_str)

            # 获取事件类型
            event_type = event_data.get("eventType", "unknown")

            # 根据事件类型处理
            if event_type == "on_llm_token":
                await self._handle_token_event(job_id, message_id, event_data)
            elif event_type == "task_started":
                await self._handle_task_started(job_id, message_id, event_data)
            elif event_type == "task_completed":
                await self._handle_task_completed(job_id, message_id,
                                                  event_data)
            elif event_type == "task_failed":
                await self._handle_task_failed(job_id, message_id, event_data)
            else:
                await self._handle_generic_event(job_id, message_id,
                                                 event_data)

        except Exception as e:
            logger.error(f"❌ 处理消息失败: {e}")

    async def _handle_token_event(self, job_id: str, message_id: str,
                                  event_data: dict):
        """处理 token 事件"""
        token = event_data.get("token", "")
        if token:
            print(token, end="", flush=True)

    async def _handle_task_started(self, job_id: str, message_id: str,
                                   event_data: dict):
        """处理任务开始事件"""
        task_type = event_data.get("taskType", "unknown")
        print(f"\n🚀 任务开始: {task_type}")
        print(f"📋 任务ID: {job_id}")
        print(f"⏰ 时间: {event_data.get('timestamp', 'unknown')}")
        print("-" * 40)

    async def _handle_task_completed(self, job_id: str, message_id: str,
                                     event_data: dict):
        """处理任务完成事件"""
        task_type = event_data.get("taskType", "unknown")
        print(f"\n✅ 任务完成: {task_type}")
        print(f"📋 任务ID: {job_id}")
        print(f"⏰ 时间: {event_data.get('timestamp', 'unknown')}")
        print("=" * 60)

    async def _handle_task_failed(self, job_id: str, message_id: str,
                                  event_data: dict):
        """处理任务失败事件"""
        task_type = event_data.get("taskType", "unknown")
        error = event_data.get("error", "unknown")
        print(f"\n❌ 任务失败: {task_type}")
        print(f"📋 任务ID: {job_id}")
        print(f"💥 错误: {error}")
        print(f"⏰ 时间: {event_data.get('timestamp', 'unknown')}")
        print("=" * 60)

    async def _handle_generic_event(self, job_id: str, message_id: str,
                                    event_data: dict):
        """处理通用事件"""
        event_type = event_data.get("eventType", "unknown")
        print(f"\n📡 事件: {event_type}")
        print(f"📋 任务ID: {job_id}")
        print(f"📄 数据: {json.dumps(event_data, ensure_ascii=False, indent=2)}")
        print("-" * 40)

    async def start(self, job_id: str):
        """开始接收流数据"""
        if not await self.connect():
            return

        self.is_running = True
        await self.receive_stream(job_id)

    async def stop(self):
        """停止接收"""
        self.is_running = False
        if self.redis_client:
            await self.redis_client.close()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python receive_stream.py <job_id>")
        print("示例: python receive_stream.py test_job_001")
        return

    job_id = sys.argv[1]

    # 创建接收器
    receiver = StreamReceiver()

    try:
        print(f"🎯 开始接收任务 {job_id} 的流数据...")
        print("按 Ctrl+C 停止接收")
        print("=" * 60)

        await receiver.start(job_id)

    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        logger.error(f"❌ 运行出错: {e}")
    finally:
        await receiver.stop()


if __name__ == "__main__":
    asyncio.run(main())
