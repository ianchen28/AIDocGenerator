#!/usr/bin/env python3
"""
测试Redis事件流功能
"""

import asyncio
import json
import redis.asyncio as redis
from doc_agent.core.logger import logger

# 测试配置
REDIS_URL = "redis://localhost:6379"
TEST_TASK_ID = "1754562374692737577"  # 使用刚才测试中生成的Task ID


async def test_redis_stream_events():
    """测试Redis Stream事件"""
    logger.info("开始测试Redis Stream事件")

    try:
        # 连接Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.success("Redis连接成功")

        # 获取Stream信息
        stream_name = TEST_TASK_ID
        stream_info = await redis_client.xinfo_stream(stream_name)
        logger.info(f"Stream信息: {stream_info}")

        # 读取Stream中的所有事件
        events = await redis_client.xread({stream_name: "0"}, count=100)

        if events:
            logger.info(f"找到 {len(events[0][1])} 个事件")

            for event_id, event_data in events[0][1]:
                try:
                    # 解析事件数据
                    data_str = event_data.get("data", "{}")
                    event_data_parsed = json.loads(data_str)

                    event_type = event_data_parsed.get("eventType", "unknown")
                    logger.info(f"事件ID: {event_id}")
                    logger.info(f"事件类型: {event_type}")
                    logger.info(
                        f"事件数据: {json.dumps(event_data_parsed, ensure_ascii=False, indent=2)}"
                    )
                    logger.info("-" * 50)

                except json.JSONDecodeError as e:
                    logger.error(f"解析事件数据失败: {e}")
                    logger.error(f"原始数据: {data_str}")
        else:
            logger.warning("没有找到事件")

    except Exception as e:
        logger.error(f"测试Redis Stream失败: {e}")


async def monitor_real_time_events(task_id: str, duration: int = 30):
    """实时监控事件流"""
    logger.info(f"开始实时监控任务 {task_id} 的事件流，持续 {duration} 秒")

    try:
        # 连接Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()

        # 获取当前Stream长度作为起始位置
        stream_length = await redis_client.xlen(task_id)
        start_id = f"{task_id}-{stream_length + 1}"

        logger.info(f"从位置 {start_id} 开始监控")

        # 实时监控新事件
        for i in range(duration):
            try:
                # 读取新事件
                events = await redis_client.xread({task_id: start_id},
                                                  count=10,
                                                  block=1000)

                if events:
                    for stream_name, stream_events in events:
                        for event_id, event_data in stream_events:
                            try:
                                data_str = event_data.get("data", "{}")
                                event_data_parsed = json.loads(data_str)

                                event_type = event_data_parsed.get(
                                    "eventType", "unknown")
                                logger.info(
                                    f"[实时] {event_type}: {event_data_parsed.get('progress', '')}"
                                )

                                # 更新起始位置
                                start_id = event_id

                            except json.JSONDecodeError:
                                continue

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"监控过程中出错: {e}")
                await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"实时监控失败: {e}")


def test_document_generation_with_monitoring():
    """测试文档生成并监控事件"""
    import requests

    logger.info("开始测试文档生成并监控事件")

    # 准备测试数据
    test_outline = {
        "title":
        "人工智能技术发展趋势",
        "nodes": [{
            "id": "node_1",
            "title": "人工智能概述",
            "content_summary": "介绍人工智能的基本概念、发展历史和核心原理"
        }, {
            "id": "node_2",
            "title": "核心技术发展",
            "content_summary": "详细分析机器学习、深度学习、自然语言处理等核心技术的最新进展"
        }]
    }

    request_data = {
        "jobId": "test_monitor_job_001",
        "outlineJson": json.dumps(test_outline, ensure_ascii=False),
        "sessionId": "test_monitor_session_001"
    }

    try:
        # 发送文档生成请求
        response = requests.post(
            "http://localhost:8000/api/v1/jobs/document-from-outline",
            json=request_data,
            headers={"Content-Type": "application/json"})

        if response.status_code == 202:
            result = response.json()
            task_id = result.get("redisStreamKey")

            logger.success(f"文档生成任务已提交，Task ID: {task_id}")

            # 监控事件流
            asyncio.run(monitor_real_time_events(task_id, 60))

        else:
            logger.error(f"请求失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")

    except Exception as e:
        logger.error(f"测试失败: {e}")


if __name__ == "__main__":
    logger.info("=== Redis事件流测试 ===")

    # 测试现有的事件流
    asyncio.run(test_redis_stream_events())

    # 测试实时监控
    test_document_generation_with_monitoring()

    logger.info("测试完成")
