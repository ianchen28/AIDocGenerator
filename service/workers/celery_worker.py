#!/usr/bin/env python3
"""
Celery Worker 启动脚本
"""

# 导入 Celery 应用
from workers.celery_app import celery_app

# 显式导入 tasks 模块以确保任务被注册
import workers.tasks

if __name__ == '__main__':
    # 启动 Celery worker
    import sys
    # 传递命令行参数给 Celery
    celery_app.worker_main(sys.argv[1:] if len(sys.argv) > 1 else
                           ['worker', '--loglevel=info', '--concurrency=1'])
