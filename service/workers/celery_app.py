#!/usr/bin/env python3
"""
Celery 应用程序配置
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
root_dir = service_dir.parent  # AIDocGenerator 根目录

# 添加 service 目录到 Python 路径
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 添加根目录到 Python 路径（用于从根目录运行）
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from celery import Celery

from core.config import AppSettings

# 获取配置
settings = AppSettings()

# 创建 Celery 实例
celery_app = Celery('workers')

# 配置 Celery
celery_app.config_from_object({
    'broker_url': settings.redis_url,
    'result_backend': settings.redis_url,
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30分钟
    'task_soft_time_limit': 25 * 60,  # 25分钟
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    'broker_connection_retry_on_startup': True,
    'task_default_queue': 'default',  # 设置默认队列
    'task_default_exchange': 'default',
    'task_default_routing_key': 'default',
})

# 自动发现任务 - 支持从根目录和 service 目录运行
celery_app.autodiscover_tasks(['service.workers', 'workers'])

# 可选：配置任务路由 - 支持从根目录和 service 目录运行
celery_app.conf.task_routes = {
    'workers.tasks.*': {
        'queue': 'default'
    },
    'service.workers.tasks.*': {
        'queue': 'default'
    },
}

if __name__ == '__main__':
    celery_app.start()
