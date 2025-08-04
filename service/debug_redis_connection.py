#!/usr/bin/env python3
"""
调试Redis连接
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis.asyncio as redis
from loguru import logger

from doc_agent.core.config import settings


async def test_redis_connection():
    """测试Redis连接"""
    logger.info("🧪 测试Redis连接")

    try:
        # 连接Redis
        logger.info(f"Redis URL: {settings.redis_url}")
        client = redis.from_url(settings.redis_url,
                                encoding="utf-8",
                                decode_responses=True)

        # 测试连接
        await client.ping()
        logger.info("✅ Redis连接成功")

        # 测试Stream操作
        test_stream = "test_stream_debug"

        # 添加消息到Stream
        msg_id = await client.xadd(test_stream, {
            "test": "data",
            "timestamp": "2025-08-04"
        })
        logger.info(f"✅ 消息添加到Stream，ID: {msg_id}")

        # 读取Stream长度
        stream_length = await client.xlen(test_stream)
        logger.info(f"📊 Stream长度: {stream_length}")

        # 读取Stream内容
        stream_data = await client.xrange(test_stream, "-", "+")
        logger.info(f"📋 Stream内容: {stream_data}")

        # 清理测试数据
        await client.delete(test_stream)
        logger.info("🧹 清理测试数据")

        await client.close()

    except Exception as e:
        logger.error(f"❌ Redis连接测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


async def test_redis_stream_publisher():
    """测试Redis Stream Publisher"""
    logger.info("🧪 测试Redis Stream Publisher")

    try:
        # 连接Redis
        client = redis.from_url(settings.redis_url,
                                encoding="utf-8",
                                decode_responses=True)

        from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher(client)

        # 测试发布事件
        job_id = "test_publisher_debug"

        # 发布任务开始事件
        event_id = await publisher.publish_task_started(job_id=job_id,
                                                        task_type="test_task",
                                                        task_prompt="测试任务")
        logger.info(f"✅ 任务开始事件已发布，ID: {event_id}")

        # 发布任务进度事件
        event_id = await publisher.publish_task_progress(job_id=job_id,
                                                         task_type="test_task",
                                                         progress="测试进度")
        logger.info(f"✅ 任务进度事件已发布，ID: {event_id}")

        # 发布任务完成事件
        event_id = await publisher.publish_task_completed(
            job_id=job_id, task_type="test_task", result={"test": "result"})
        logger.info(f"✅ 任务完成事件已发布，ID: {event_id}")

        # 检查Stream
        stream_key = f"job_events:{job_id}"
        stream_length = await client.xlen(stream_key)
        logger.info(f"📊 Stream长度: {stream_length}")

        if stream_length > 0:
            stream_data = await client.xrange(stream_key, "-", "+")
            logger.info(f"📋 Stream内容: {stream_data}")

        await client.close()

    except Exception as e:
        logger.error(f"❌ Redis Stream Publisher测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


async def main():
    """主函数"""
    await test_redis_connection()
    print("\n" + "=" * 50 + "\n")
    await test_redis_stream_publisher()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO")

    # 运行测试
    asyncio.run(main())
