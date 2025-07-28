#!/bin/bash

# Celery Worker 启动脚本
# 从service/workers目录运行

echo "启动 Celery Worker..."

# 检查是否在正确的目录
if [ ! -f "celery_worker.py" ]; then
    echo "错误: 请在 service/workers 目录下运行此脚本"
    exit 1
fi

# 启动 Celery worker
python celery_worker.py worker --loglevel=info --concurrency=1 -Q default 