#!/usr/bin/env python3
"""
测试Celery任务
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from workers.tasks import test_celery_task
from workers.celery_app import celery_app
from loguru import logger


def test_celery():
    """测试Celery任务"""
    logger.info("🧪 测试Celery任务")
    
    try:
        # 测试简单任务
        logger.info("📤 提交测试任务...")
        result = test_celery_task.delay("Hello from test!")
        
        logger.info(f"✅ 任务已提交，ID: {result.id}")
        logger.info(f"📊 任务状态: {result.status}")
        
        # 等待任务完成
        logger.info("⏳ 等待任务完成...")
        task_result = result.get(timeout=30)
        
        logger.info(f"✅ 任务完成，结果: {task_result}")
        
    except Exception as e:
        logger.error(f"❌ 任务测试失败: {e}")


def test_outline_task():
    """测试大纲生成任务"""
    logger.info("🧪 测试大纲生成任务")
    
    try:
        from workers.tasks import generate_outline_from_query_task
        
        # 提交大纲生成任务
        logger.info("📤 提交大纲生成任务...")
        result = generate_outline_from_query_task.delay(
            job_id="test_celery_001",
            task_prompt="生成一份关于Python编程的大纲",
            is_online=False,
            context_files=[],
            redis_stream_key="outline_generation:test_celery_001"
        )
        
        logger.info(f"✅ 任务已提交，ID: {result.id}")
        logger.info(f"📊 任务状态: {result.status}")
        
        # 等待任务完成
        logger.info("⏳ 等待任务完成...")
        task_result = result.get(timeout=60)
        
        logger.info(f"✅ 任务完成，结果: {task_result}")
        
    except Exception as e:
        logger.error(f"❌ 大纲生成任务测试失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    test_celery()
    print("\n" + "="*50 + "\n")
    test_outline_task() 