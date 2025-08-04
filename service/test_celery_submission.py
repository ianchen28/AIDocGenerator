#!/usr/bin/env python3
"""
测试Celery任务提交
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from workers.tasks import generate_outline_from_query_task
from loguru import logger


def test_celery_submission():
    """测试Celery任务提交"""
    logger.info("🧪 测试Celery任务提交")
    
    try:
        # 直接提交任务
        logger.info("📤 提交大纲生成任务...")
        result = generate_outline_from_query_task.apply_async(
            kwargs={
                'job_id': 'test_submission_001',
                'task_prompt': '生成一份关于Python编程的大纲',
                'is_online': False,
                'context_files': [],
                'style_guide_content': None,
                'requirements': None,
                'redis_stream_key': 'outline_generation:test_submission_001'
            },
            countdown=0,
            expires=300
        )
        
        logger.info(f"✅ 任务已提交，ID: {result.id}")
        logger.info(f"📊 任务状态: {result.status}")
        
        # 等待任务完成
        logger.info("⏳ 等待任务完成...")
        task_result = result.get(timeout=60)
        
        logger.info(f"✅ 任务完成，结果: {task_result}")
        
        # 检查Redis流
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        stream_key = "job_events:test_submission_001"
        stream_length = r.xlen(stream_key)
        logger.info(f"📊 Redis流长度: {stream_length}")
        
        if stream_length > 0:
            logger.info("✅ Redis流中有数据！")
            # 显示流内容
            stream_data = r.xrange(stream_key, '-', '+')
            for msg_id, fields in stream_data:
                logger.info(f"消息ID: {msg_id}")
                for field, value in fields.items():
                    logger.info(f"  {field}: {value}")
        else:
            logger.warning("⚠️ Redis流中无数据")
        
    except Exception as e:
        logger.error(f"❌ 任务提交失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    test_celery_submission() 