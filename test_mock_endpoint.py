#!/usr/bin/env python3
"""
测试新的模拟端点 /jobs/document-from-outline/mock
"""

import asyncio
import json
import redis.asyncio as redis
from loguru import logger
import sys
import os

# 添加项目路径到 sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'service', 'src'))

# 导入配置
from doc_agent.core.config import settings

# 测试用的 outline JSON
TEST_OUTLINE = {
    "title":
    "人工智能技术发展报告",
    "nodes": [{
        "id": "node_1",
        "title": "人工智能概述",
        "content_summary": "介绍人工智能的基本概念和发展历程"
    }, {
        "id": "node_2",
        "title": "机器学习技术",
        "content_summary": "深入探讨机器学习的核心算法和应用"
    }, {
        "id": "node_3",
        "title": "深度学习进展",
        "content_summary": "分析深度学习的最新发展和突破"
    }]
}


async def test_mock_endpoint():
    """测试模拟端点"""

    # 1. 测试 API 调用
    import requests

    url = "http://localhost:8000/api/v1/jobs/document-from-outline/mock"
    # 使用固定的sessionId（纯数字）
    unique_job_id = "999888777"  # 新的sessionId

    payload = {
        "job_id": unique_job_id,
        "outline_json": json.dumps(TEST_OUTLINE),
        "session_id": unique_job_id
    }

    print("发送请求到模拟端点...")
    response = requests.post(url, json=payload)

    if response.status_code == 202:
        print("✅ API 调用成功")
        print(f"响应: {response.json()}")
    else:
        print(f"❌ API 调用失败: {response.status_code}")
        print(f"错误: {response.text}")
        return

    # 2. 监听 Redis 事件流
    print("\n开始监听 Redis 事件流...")

    # 使用配置文件中的 Redis URL
    redis_url = settings.redis_url
    logger.info(f"使用 Redis URL: {redis_url}")

    redis_client = redis.from_url(redis_url,
                                  encoding="utf-8",
                                  decode_responses=True)

    session_id = unique_job_id
    stream_name = session_id

    # 等待并读取事件 - 从当前时刻开始监听新消息
    last_id = "$"  # 使用 $ 表示只监听新消息，不读取历史数据
    event_count = 0

    while event_count < 1000:  # 最多监听1000个事件
        try:
            # 读取新事件
            events = await redis_client.xread({stream_name: last_id},
                                              count=1,
                                              block=5000)

            if events:
                for stream, messages in events:
                    for message_id, data in messages:
                        last_id = message_id
                        event_data = json.loads(data["data"])

                        event_count += 1
                        print(f"\n📡 事件 {event_count}:")
                        print(f"   事件ID: {event_data.get('redis_id', 'N/A')}")
                        print(f"   事件类型: {event_data.get('eventType', 'N/A')}")
                        print(
                            f"   原始数据: {json.dumps(data, ensure_ascii=False, indent=2)}"
                        )

                        # 检查是否是任务完成或失败事件
                        if event_data.get('eventType') == 'task_completed':
                            print("✅ 任务完成!")
                            return
                        elif event_data.get('eventType') == 'task_failed':
                            print("❌ 任务失败!")
                            return
            else:
                print("⏳ 等待事件...")

        except Exception as e:
            print(f"❌ 监听事件时出错: {e}")
            break

    print("\n🎉 测试完成!")


if __name__ == "__main__":
    print("🧪 开始测试模拟端点")
    print("=" * 50)

    asyncio.run(test_mock_endpoint())
