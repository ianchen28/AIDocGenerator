#!/usr/bin/env python3
"""
详细的Celery任务测试
"""

import asyncio
import json
from doc_agent.core.logger import logger
# 导入Celery任务
from workers.tasks import generate_document_from_outline_task


def test_celery_task_detailed():
    """详细测试Celery任务"""
    logger.info("开始详细测试Celery任务")

    # 准备测试数据
    test_outline = {
        "title":
        "详细测试文档",
        "nodes": [{
            "id": "node_1",
            "title": "测试章节1",
            "content_summary": "这是一个测试章节"
        }]
    }

    try:
        # 直接调用Celery任务
        result = generate_document_from_outline_task.delay(
            job_id="test_celery_detailed_001",
            outline=test_outline,
            session_id="test_celery_session_001")

        logger.success(f"Celery任务已提交，Task ID: {result.id}")
        logger.info(f"任务状态: {result.status}")

        # 等待任务完成并获取详细信息
        try:
            task_result = result.get(timeout=60)
            logger.info(f"任务结果: {task_result}")
        except Exception as task_error:
            logger.error(f"任务执行失败: {task_error}")

            # 获取任务的详细信息
            if hasattr(result, 'info'):
                logger.error(f"任务信息: {result.info}")
            if hasattr(result, 'traceback'):
                logger.error(f"任务错误堆栈: {result.traceback}")

    except Exception as e:
        logger.error(f"Celery任务测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")


def test_simple_task():
    """测试简单的Celery任务"""
    from workers.tasks import test_celery_task

    logger.info("开始测试简单Celery任务")

    try:
        result = test_celery_task.delay("Hello Celery!")
        logger.success(f"简单任务已提交，Task ID: {result.id}")

        task_result = result.get(timeout=10)
        logger.info(f"简单任务结果: {task_result}")

    except Exception as e:
        logger.error(f"简单任务测试失败: {e}")


if __name__ == "__main__":
    logger.info("=== 详细Celery任务测试 ===")

    # 测试简单任务
    test_simple_task()

    # 测试复杂任务
    test_celery_task_detailed()

    logger.info("测试完成")
