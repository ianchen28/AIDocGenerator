#!/usr/bin/env python3
"""
使用本地Redis测试Celery任务
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis.asyncio as redis
from loguru import logger

from workers.tasks import generate_outline_from_query_task


async def test_celery_with_local_redis():
    """使用本地Redis测试Celery任务"""
    logger.info("🧪 使用本地Redis测试Celery任务")

    try:
        # 测试本地Redis连接
        local_redis_url = "redis://localhost:6379/0"
        logger.info(f"本地Redis URL: {local_redis_url}")

        client = redis.from_url(local_redis_url,
                                encoding="utf-8",
                                decode_responses=True)
        await client.ping()
        logger.info("✅ 本地Redis连接成功")
        await client.close()

        # 提交Celery任务
        logger.info("📤 提交Celery任务...")
        result = generate_outline_from_query_task.apply_async(kwargs={
            'job_id':
            'test_local_redis_001',
            'task_prompt':
            '生成一份关于Python编程的大纲',
            'is_online':
            False,
            'context_files': [],
            'style_guide_content':
            None,
            'requirements':
            None,
            'redis_stream_key':
            'outline_generation:test_local_redis_001'
        },
                                                              countdown=0,
                                                              expires=300)

        logger.info(f"✅ 任务已提交，ID: {result.id}")
        logger.info(f"📊 任务状态: {result.status}")

        # 等待任务完成
        logger.info("⏳ 等待任务完成...")
        task_result = result.get(timeout=60)

        logger.info(f"✅ 任务完成，结果: {task_result}")

        # 检查Redis流
        client = redis.from_url(local_redis_url,
                                encoding="utf-8",
                                decode_responses=True)
        stream_key = "job_events:test_local_redis_001"
        stream_length = await client.xlen(stream_key)
        logger.info(f"📊 Redis流长度: {stream_length}")

        if stream_length > 0:
            logger.info("✅ Redis流中有数据！")
            # 显示流内容
            stream_data = await client.xrange(stream_key, "-", "+")
            for msg_id, fields in stream_data:
                logger.info(f"消息ID: {msg_id}")
                for field, value in fields.items():
                    logger.info(f"  {field}: {value}")
        else:
            logger.warning("⚠️ Redis流中无数据")

        await client.close()

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO")

    # 运行测试
    asyncio.run(test_celery_with_local_redis())
