#!/usr/bin/env python3
"""
简单的 Redis Stream 接收脚本
实时显示 AI 文档生成器的流式内容
"""

import asyncio
import json
import sys
import time

import redis.asyncio as redis


async def receive_stream_simple(job_id: str,
                                redis_url: str = "redis://localhost:6379"):
    """
    简单接收流数据
    
    Args:
        job_id: 任务ID
        redis_url: Redis 连接URL
    """
    # 连接 Redis
    client = redis.from_url(redis_url, decode_responses=True)

    try:
        await client.ping()
        print(f"✅ Redis 连接成功")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return

    stream_name = f"job:{job_id}"
    last_id = "0"

    print(f"🎯 开始监听: {stream_name}")
    print(f"📋 任务ID: {job_id}")
    print("=" * 60)
    print("实时内容:")
    print("-" * 40)

    try:
        while True:
            # 读取新消息
            messages = await client.xread(
                {stream_name: last_id},
                count=10,
                block=1000  # 阻塞1秒
            )

            if not messages:
                continue

            # 处理消息
            for stream, stream_messages in messages:
                for message_id, fields in stream_messages:
                    # 提取数据
                    data_str = fields.get("data", "{}")
                    try:
                        event_data = json.loads(data_str)
                        event_type = event_data.get("eventType", "")

                        # 处理 token 事件
                        if event_type == "on_llm_token":
                            token = event_data.get("token", "")
                            if token:
                                print(token, end="", flush=True)

                        # 处理其他事件
                        elif event_type in [
                                "task_started", "task_completed", "task_failed"
                        ]:
                            task_type = event_data.get("taskType", "unknown")
                            if event_type == "task_started":
                                print(f"\n🚀 任务开始: {task_type}")
                            elif event_type == "task_completed":
                                print(f"\n✅ 任务完成: {task_type}")
                            elif event_type == "task_failed":
                                error = event_data.get("error", "unknown")
                                print(f"\n❌ 任务失败: {task_type} - {error}")

                    except json.JSONDecodeError:
                        print(f"\n⚠️ 无法解析消息: {data_str}")

                    last_id = message_id

    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"\n❌ 接收出错: {e}")
    finally:
        await client.close()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python receive_stream_simple.py <job_id>")
        print("示例: python receive_stream_simple.py test_job_001")
        return

    job_id = sys.argv[1]
    await receive_stream_simple(job_id)


if __name__ == "__main__":
    asyncio.run(main())
