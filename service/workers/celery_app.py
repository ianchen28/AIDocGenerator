#!/usr/bin/env python3
"""
Celery 应用程序配置
统一日志版本
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from celery import Celery

# 导入统一日志配置
from doc_agent.core.logger import logger

# 强制设置loguru为默认日志系统
import logging
import loguru


# 拦截所有logging调用，转发到loguru
class InterceptHandler(logging.Handler):

    def emit(self, record):
        # 获取对应的loguru级别
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage())


# 配置logging使用loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# 移除所有现有的handlers
for name in logging.root.manager.loggerDict.keys():
    logging.getLogger(name).handlers = []
    logging.getLogger(name).propagate = True


def build_redis_url():
    """动态构建 Redis URL，支持密码和集群模式"""
    from doc_agent.core.config import settings

    # 从 config.yaml 中读取 Redis 配置
    if hasattr(settings, '_yaml_config') and settings._yaml_config:
        redis_config = settings._yaml_config.get('redis', {})
        mode = redis_config.get('mode', 'single')

        if mode == 'cluster':
            # 集群模式 - 使用第一个节点作为连接点
            cluster_config = redis_config.get('cluster', {})
            nodes = cluster_config.get('nodes', [])
            if nodes:
                first_node = nodes[0]
                password = cluster_config.get('password', '')
                if password:
                    redis_url = f"redis://:{password}@{first_node}/0"
                else:
                    redis_url = f"redis://{first_node}/0"
                return redis_url
            else:
                # 如果没有节点配置，回退到默认
                return "redis://127.0.0.1:6379/0"
        else:
            # 单节点模式
            single_config = redis_config.get('single', {})
            redis_host = single_config.get('host', 'localhost')
            redis_port = single_config.get('port', 6379)
            redis_db = single_config.get('db', 0)
            redis_password = single_config.get('password', None)

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

# 🔧 新增：记录 Celery 启动信息
logger.info("Celery 应用程序已配置")
logger.info(f"Redis URL: {build_redis_url()}")
logger.info("所有 Celery 任务日志将统一输出到 logs/app.log")

if __name__ == '__main__':
    celery_app.start()
