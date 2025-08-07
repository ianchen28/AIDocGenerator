#!/bin/bash

# 统一日志启动脚本
# 所有日志将输出到 logs/app.log

echo "🚀 启动统一日志配置的服务..."

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 确保日志目录存在
mkdir -p logs

# 清理旧的日志文件（可选）
# rm -f logs/celery_worker.log

# 启动 Celery worker（使用统一的日志配置）
echo "📝 启动 Celery worker（统一日志输出到 logs/app.log）..."
conda activate ai-doc && celery -A workers.celery_worker worker --loglevel=INFO --concurrency=1 --logfile=logs/app.log

echo "✅ 服务已启动，所有日志将统一输出到 logs/app.log"
