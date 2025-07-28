#!/usr/bin/env python3
"""
测试 Celery 配置
"""

import sys
from pathlib import Path

# 添加 service 目录到 Python 路径
current_file = Path(__file__)
service_dir = current_file / "service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 导入 Celery 应用
from service.workers.celery_app import celery_app


def test_celery_config():
    """测试 Celery 配置"""
    print("=== 测试 Celery 配置 ===")

    print(f"1. Celery 应用名称: {celery_app.main}")
    print(f"2. Broker URL: {celery_app.conf.broker_url}")
    print(f"3. Result Backend: {celery_app.conf.result_backend}")

    print("\n4. 注册的任务:")
    for task_name in celery_app.tasks.keys():
        print(f"   - {task_name}")

    print("\n5. 测试任务提交...")
    try:
        from service.workers.tasks import test_celery_task
        result = test_celery_task.delay("test")
        print(f"   任务已提交: {result.id}")
        print(f"   任务状态: {result.status}")
    except Exception as e:
        print(f"   任务提交失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_celery_config()
