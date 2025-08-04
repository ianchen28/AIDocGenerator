#!/usr/bin/env python3
"""
Celery 应用程序配置
"""

from celery import Celery
from urllib.parse import urlparse

from doc_agent.core.config import settings


def build_redis_url():
    """动态构建 Redis URL，支持密码"""
    from doc_agent.core.config import settings

    # 从 config.yaml 中读取 Redis 配置
    if hasattr(settings, '_yaml_config') and settings._yaml_config:
        redis_config = settings._yaml_config.get('redis', {})
        redis_host = redis_config.get('host', 'localhost')
        redis_port = redis_config.get('port', 6379)
        redis_db = redis_config.get('db', 0)
        redis_password = redis_config.get('password', None)

        # 按照要求的逻辑构建 URL
        if redis_password:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

        return redis_url

    # 如果无法从 YAML 读取，使用环境变量中的 URL
    import os
    return os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


# 构建 Redis URL
redis_url = build_redis_url()

# 创建 Celery 实例
celery_app = Celery(
    "aidocgenerator",
    broker=redis_url,
    backend=redis_url,
    include=["workers.tasks"],
)

# 配置 Celery
celery_app.config_from_object({
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
    'broker_connection_timeout': 30,
    'broker_connection_retry': True,
    'broker_connection_max_retries': 10,
    'task_default_queue': 'default',  # 设置默认队列
    'task_default_exchange': 'default',
    'task_default_routing_key': 'default',
})

# 自动发现任务
celery_app.autodiscover_tasks(['workers.tasks'])

# 可选：配置任务路由
celery_app.conf.task_routes = {
    'workers.tasks.*': {
        'queue': 'default'
    },
}

if __name__ == '__main__':
    celery_app.start()
