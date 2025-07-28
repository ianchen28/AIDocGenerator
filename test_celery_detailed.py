#!/usr/bin/env python3
"""
详细的 Celery 测试脚本
"""

import sys
import time
from pathlib import Path

# 添加 service 目录到 Python 路径
current_file = Path(__file__)
service_dir = current_file / "service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 导入任务
from service.workers.tasks import test_celery_task


def test_celery_detailed():
    """详细的 Celery 测试"""
    print("=== 详细的 Celery 测试 ===")

    try:
        # 提交任务
        print("1. 提交任务...")
        result = test_celery_task.delay("Hello from root directory!")
        print(f"   任务ID: {result.id}")
        print(f"   任务状态: {result.status}")

        # 等待并检查状态
        print("\n2. 等待任务执行...")
        for i in range(10):
            time.sleep(1)
            status = result.status
            print(f"   第{i+1}秒 - 状态: {status}")

            if status == "SUCCESS":
                print(f"   任务完成! 结果: {result.get()}")
                break
            elif status == "FAILURE":
                print(f"   任务失败! 错误: {result.info}")
                break
            elif status == "PENDING":
                print("   任务仍在等待中...")
            else:
                print(f"   任务状态: {status}")

        if result.status == "PENDING":
            print("\n3. 任务仍在等待中，可能 worker 没有正确处理任务")
            print("   检查 worker 日志以获取更多信息")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_celery_detailed()
