#!/usr/bin/env python3
"""
简单的Celery任务测试
"""

import asyncio
import json
from doc_agent.core.logger import logger
# 导入Celery任务
from workers.tasks import generate_document_from_outline_task


def test_celery_task():
    """测试Celery任务"""
    logger.info("开始测试Celery任务")

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
        # 直接调用Celery任务
        result = generate_document_from_outline_task.delay(
            job_id="test_celery_job_001",
            outline=test_outline,
            session_id="test_celery_session_001")

        logger.success(f"Celery任务已提交，Task ID: {result.id}")
        logger.info(f"任务状态: {result.status}")

        # 等待任务完成
        task_result = result.get(timeout=30)
        logger.info(f"任务结果: {task_result}")

    except Exception as e:
        logger.error(f"Celery任务测试失败: {e}")


if __name__ == "__main__":
    logger.info("=== Celery任务测试 ===")
    test_celery_task()
    logger.info("测试完成")
