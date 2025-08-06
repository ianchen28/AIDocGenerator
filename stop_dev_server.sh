#!/bin/bash

# =================================================================
# AIDocGenerator - 停止开发环境脚本
# =================================================================

echo "🛑 停止 AIDocGenerator 开发环境..."
echo "=================================="

# 查找并停止相关进程
echo "🔍 查找相关进程..."

# 停止 Celery Worker 进程
CELERY_PIDS=$(ps aux | grep "celery_worker" | grep -v grep | awk '{print $2}')
if [ -n "$CELERY_PIDS" ]; then
    echo "   - 找到 Celery Worker 进程: $CELERY_PIDS"
    echo "$CELERY_PIDS" | xargs kill -TERM
    sleep 2
    # 强制终止仍在运行的进程
    echo "$CELERY_PIDS" | xargs kill -KILL 2>/dev/null
    echo "   - ✅ Celery Worker 已停止"
else
    echo "   - ℹ️  未找到 Celery Worker 进程"
fi

# 停止 uvicorn 进程
UVICORN_PIDS=$(ps aux | grep "uvicorn" | grep -v grep | awk '{print $2}')
if [ -n "$UVICORN_PIDS" ]; then
    echo "   - 找到 uvicorn 进程: $UVICORN_PIDS"
    echo "$UVICORN_PIDS" | xargs kill -TERM
    sleep 2
    # 强制终止仍在运行的进程
    echo "$UVICORN_PIDS" | xargs kill -KILL 2>/dev/null
    echo "   - ✅ uvicorn 服务已停止"
else
    echo "   - ℹ️  未找到 uvicorn 进程"
fi

# 停止 Python 进程（可能的后台进程）
PYTHON_PIDS=$(ps aux | grep "python.*api.main" | grep -v grep | awk '{print $2}')
if [ -n "$PYTHON_PIDS" ]; then
    echo "   - 找到 Python API 进程: $PYTHON_PIDS"
    echo "$PYTHON_PIDS" | xargs kill -TERM
    sleep 2
    echo "$PYTHON_PIDS" | xargs kill -KILL 2>/dev/null
    echo "   - ✅ Python API 进程已停止"
else
    echo "   - ℹ️  未找到 Python API 进程"
fi

# 清理日志文件（可选）
echo ""
echo "🧹 清理选项:"
echo "   - 保留日志文件 (默认)"
echo "   - 清理日志文件 (输入 'clean')"
read -p "   选择操作 [默认保留]: " choice

if [[ "$choice" == "clean" ]]; then
    echo "   - 清理日志文件..."
    rm -f output.log celery_worker.log
    echo "   - ✅ 日志文件已清理"
else
    echo "   - 保留日志文件"
fi

echo ""
echo "✅ 所有服务已停止"
echo "📝 日志文件位置:"
echo "   - 主日志: output.log"
echo "   - Celery日志: celery_worker.log" 