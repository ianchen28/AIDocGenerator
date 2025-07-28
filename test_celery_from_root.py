#!/usr/bin/env python3
"""
测试从根目录运行 Celery 任务
"""

import sys
from pathlib import Path

# 添加 service 目录到 Python 路径
current_file = Path(__file__)
service_dir = current_file / "service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 导入任务
from service.workers.tasks import test_celery_task


def test_celery_from_root():
    """测试从根目录运行 Celery 任务"""
    print("测试从根目录运行 Celery 任务...")

    try:
        # 提交任务
        result = test_celery_task.delay("Hello from root directory!")
        print(f"任务已提交: {result.id}")

        # 等待任务完成
        import time
        time.sleep(3)

        # 获取任务状态和结果
        print(f"任务状态: {result.status}")
        if result.ready():
            print(f"任务结果: {result.get()}")
        else:
            print("任务仍在执行中...")

    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == '__main__':
    test_celery_from_root()
