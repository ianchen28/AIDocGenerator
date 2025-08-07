#!/usr/bin/env python3
"""
Celery Worker 启动脚本 (统一日志版)
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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

# 导入 Celery 应用
from workers.celery_app import celery_app

# 显式导入 tasks 模块以确保任务被注册
import workers.tasks

if __name__ == '__main__':
    logger.info("🚀 启动 Celery Worker (统一日志版)")

    # 设置环境变量，让Celery使用我们的日志配置
    os.environ['CELERY_WORKER_LOG_FORMAT'] = 'json'

    # 启动 Celery worker
    # 传递命令行参数给 Celery
    celery_app.worker_main(sys.argv[1:] if len(sys.argv) > 1 else
                           ['worker', '--loglevel=info', '--concurrency=1'])
