#!/usr/bin/env python3
"""
简单的文档生成任务测试
"""

import asyncio
import json
from doc_agent.core.logger import logger


async def test_document_task_simple():
    """简单测试文档生成任务"""
    logger.info("开始简单测试文档生成任务")

    # 准备测试数据
    test_outline = {
        "title":
        "简单测试文档",
        "nodes": [{
            "id": "node_1",
            "title": "测试章节1",
            "content_summary": "这是一个测试章节"
        }]
    }

    try:
        # 直接调用异步函数
        from workers.tasks import _generate_document_from_outline_task_async

        result = await _generate_document_from_outline_task_async(
            job_id="test_simple_async_001",
            outline=test_outline,
            session_id="test_simple_session_001")

        logger.success(f"异步任务执行完成，结果: {result}")

    except Exception as e:
        logger.error(f"异步任务执行失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")


def test_redis_connection():
    """测试Redis连接"""
    logger.info("开始测试Redis连接")

    try:
        from workers.tasks import get_redis_client
        import asyncio

        async def test_redis():
            redis_client = await get_redis_client()
            await redis_client.ping()
            logger.success("Redis连接成功")

            # 测试发布事件
            from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
            publisher = RedisStreamPublisher(redis_client)

            await publisher.publish_task_started(job_id="test_redis_001",
                                                 task_type="test",
                                                 test_message="Hello Redis!")
            logger.success("Redis事件发布成功")

        asyncio.run(test_redis())

    except Exception as e:
        logger.error(f"Redis连接测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")


if __name__ == "__main__":
    logger.info("=== 简单文档生成任务测试 ===")

    # 测试Redis连接
    test_redis_connection()

    # 测试异步任务
    asyncio.run(test_document_task_simple())

    logger.info("测试完成")
