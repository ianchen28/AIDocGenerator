#!/usr/bin/env python3
"""
调试远程Redis连接
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis.asyncio as redis
from loguru import logger


async def test_remote_redis_connection():
    """测试远程Redis连接"""
    logger.info("🧪 测试远程Redis连接")

    # 使用远程Redis配置
    remote_redis_url = "redis://:xJrhp*4mnHxbBWN2grqq@10.215.149.74:26379/0"

    try:
        # 连接远程Redis
        logger.info(f"远程Redis URL: {remote_redis_url}")
        client = redis.from_url(remote_redis_url,
                                encoding="utf-8",
                                decode_responses=True)

        # 测试连接
        await client.ping()
        logger.info("✅ 远程Redis连接成功")

        # 测试Stream操作
        test_stream = "test_stream_remote_debug"

        # 添加消息到Stream
        msg_id = await client.xadd(test_stream, {
            "test": "remote_data",
            "timestamp": "2025-08-04"
        })
        logger.info(f"✅ 消息添加到远程Stream，ID: {msg_id}")

        # 读取Stream长度
        stream_length = await client.xlen(test_stream)
        logger.info(f"📊 远程Stream长度: {stream_length}")

        # 读取Stream内容
        stream_data = await client.xrange(test_stream, "-", "+")
        logger.info(f"📋 远程Stream内容: {stream_data}")

        # 清理测试数据
        await client.delete(test_stream)
        logger.info("🧹 清理远程测试数据")

        await client.close()

    except Exception as e:
        logger.error(f"❌ 远程Redis连接测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


async def test_remote_redis_stream_publisher():
    """测试远程Redis Stream Publisher"""
    logger.info("🧪 测试远程Redis Stream Publisher")

    # 使用远程Redis配置
    remote_redis_url = "redis://:xJrhp*4mnHxbBWN2grqq@10.215.149.74:26379/0"

    try:
        # 连接远程Redis
        client = redis.from_url(remote_redis_url,
                                encoding="utf-8",
                                decode_responses=True)

        from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher(client)

        # 测试发布事件
        job_id = "test_remote_publisher_debug"

        # 发布任务开始事件
        event_id = await publisher.publish_task_started(job_id=job_id,
                                                        task_type="test_task",
                                                        task_prompt="远程测试任务")
        logger.info(f"✅ 远程任务开始事件已发布，ID: {event_id}")

        # 发布任务进度事件
        event_id = await publisher.publish_task_progress(job_id=job_id,
                                                         task_type="test_task",
                                                         progress="远程测试进度")
        logger.info(f"✅ 远程任务进度事件已发布，ID: {event_id}")

        # 发布任务完成事件
        event_id = await publisher.publish_task_completed(
            job_id=job_id,
            task_type="test_task",
            result={"test": "remote_result"})
        logger.info(f"✅ 远程任务完成事件已发布，ID: {event_id}")

        # 检查Stream
        stream_key = f"job_events:{job_id}"
        stream_length = await client.xlen(stream_key)
        logger.info(f"📊 远程Stream长度: {stream_length}")

        if stream_length > 0:
            stream_data = await client.xrange(stream_key, "-", "+")
            logger.info(f"📋 远程Stream内容: {stream_data}")

        await client.close()

    except Exception as e:
        logger.error(f"❌ 远程Redis Stream Publisher测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


async def test_celery_with_remote_redis():
    """使用远程Redis测试Celery任务"""
    logger.info("🧪 使用远程Redis测试Celery任务")

    try:
        # 测试远程Redis连接
        remote_redis_url = "redis://:xJrhp*4mnHxbBWN2grqq@10.215.149.74:26379/0"
        logger.info(f"远程Redis URL: {remote_redis_url}")

        client = redis.from_url(remote_redis_url,
                                encoding="utf-8",
                                decode_responses=True)
        await client.ping()
        logger.info("✅ 远程Redis连接成功")
        await client.close()

        # 提交Celery任务
        logger.info("📤 提交Celery任务到远程Redis...")
        from workers.tasks import generate_outline_from_query_task

        result = generate_outline_from_query_task.apply_async(kwargs={
            'job_id':
            'test_remote_redis_001',
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
            'outline_generation:test_remote_redis_001'
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
        client = redis.from_url(remote_redis_url,
                                encoding="utf-8",
                                decode_responses=True)
        stream_key = "job_events:test_remote_redis_001"
        stream_length = await client.xlen(stream_key)
        logger.info(f"📊 远程Redis流长度: {stream_length}")

        if stream_length > 0:
            logger.info("✅ 远程Redis流中有数据！")
            # 显示流内容
            stream_data = await client.xrange(stream_key, "-", "+")
            for msg_id, fields in stream_data:
                logger.info(f"消息ID: {msg_id}")
                for field, value in fields.items():
                    logger.info(f"  {field}: {value}")
        else:
            logger.warning("⚠️ 远程Redis流中无数据")

        await client.close()

    except Exception as e:
        logger.error(f"❌ 远程Redis测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


async def main():
    """主函数"""
    await test_remote_redis_connection()
    print("\n" + "=" * 50 + "\n")
    await test_remote_redis_stream_publisher()
    print("\n" + "=" * 50 + "\n")
    await test_celery_with_remote_redis()


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
