#!/usr/bin/env python3
"""
Celery Worker 启动脚本 - 从根目录运行
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

if __name__ == '__main__':
    # 启动 Celery worker
    import sys
    # 传递命令行参数给 Celery
    celery_app.worker_main(sys.argv[1:] if len(sys.argv) > 1 else
                           ['worker', '--loglevel=info', '--concurrency=1'])
