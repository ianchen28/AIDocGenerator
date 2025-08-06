#!/bin/bash

# =================================================================
# AIDocGenerator - 统一启动开发环境脚本
# =================================================================

# 默认端口
DEFAULT_PORT=8000

# 解析命令行参数
PORT=${1:-$DEFAULT_PORT}

# 显示启动信息
echo "🚀 AIDocGenerator 开发环境启动脚本"
echo "=================================="
echo "端口: $PORT"
echo ""

# 定义一个函数用于优雅地关闭后台进程
cleanup() {
    echo " " # 换行
    echo "🔴 Shutting down services..."
    # 检查 Celery Worker 进程是否存在，如果存在则终止
    if [ -n "$CELERY_PID" ]; then
        echo "   - Stopping Celery Worker (PID: $CELERY_PID)..."
        kill $CELERY_PID 2>/dev/null
    fi
    echo "✅ All services stopped."
    exit 0
}

# 设置一个 trap，当脚本接收到退出信号时（比如按下了 Ctrl+C），调用 cleanup 函数
trap cleanup SIGINT SIGTERM

# --- 步骤 1: 检查 Redis 服务 ---
echo "🔵 Step 1: Checking Redis server status..."
# 使用 redis-cli ping 命令来检查服务是否可用
if ! redis-cli ping > /dev/null 2>&1; then
    echo "   - ❌ Error: Redis server is not running or not accessible."
    echo "   - Please start your Redis server in a separate terminal first."
    echo "   - Common commands:"
    echo "     - Docker:    docker start <your-redis-container>"
    echo "     - Homebrew:  brew services start redis"
    echo "     - Linux:     sudo systemctl start redis-server"
    exit 1
else
    echo "   - ✅ Redis server is running."
fi

# --- 步骤 2: 检查 conda 环境 ---
echo "🔵 Step 2: Checking conda environment..."
# 检查当前是否在正确的环境中
if [[ "$CONDA_DEFAULT_ENV" != "ai-doc" ]]; then
    echo "   - ⚠️  Warning: Not in ai-doc environment (current: $CONDA_DEFAULT_ENV)"
    echo "   - Please ensure you're in the ai-doc environment before running this script"
    echo "   - Run: conda activate ai-doc"
    exit 1
else
    echo "   - ✅ Running in ai-doc environment"
fi

# --- 步骤 3: 启动 Celery Worker ---
echo "🔵 Step 3: Starting Celery Worker in the background..."

# 从配置文件读取Redis配置
REDIS_CONFIG=$(python -c "
import sys
sys.path.append('service/src')
from doc_agent.core.config import settings
config = settings.redis_config
print(f'{config[\"host\"]}:{config[\"port\"]}:{config[\"db\"]}:{config.get(\"password\", \"\")}')
")

if [ $? -ne 0 ]; then
    echo "   - ❌ 无法读取Redis配置，使用默认配置"
    REDIS_HOST="127.0.0.1"
    REDIS_PORT="6379"
    REDIS_DB="0"
    REDIS_PASSWORD=""
else
    IFS=':' read -r REDIS_HOST REDIS_PORT REDIS_DB REDIS_PASSWORD <<< "$REDIS_CONFIG"
    echo "   - 📋 Redis配置: $REDIS_HOST:$REDIS_PORT (DB: $REDIS_DB)"
fi

# 构建Redis URL
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_URL="redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/$REDIS_DB"
else
    REDIS_URL="redis://$REDIS_HOST:$REDIS_PORT/$REDIS_DB"
fi

# 启动Celery Worker
(cd service && REDIS_URL="$REDIS_URL" python -m workers.celery_worker worker --loglevel=info) > celery_worker.log 2>&1 &

# 获取刚刚启动的后台进程的 PID (Process ID)
CELERY_PID=$!
echo "   - ✅ Celery Worker started in background with PID: $CELERY_PID"
echo "   - Logs are being written to celery_worker.log"

# 等待几秒钟，确保 Celery Worker 完成初始化
sleep 5

# 检查 Celery Worker 是否成功启动
if ps -p $CELERY_PID > /dev/null; then
    echo "   - ✅ Celery Worker is running"
else
    echo "   - ❌ Celery Worker failed to start"
    echo "   - Check celery_worker.log for details"
    exit 1
fi

# --- 步骤 4: 启动 FastAPI 服务 ---
echo "🔵 Step 4: Starting FastAPI server in the foreground..."
echo "   - FastAPI will be available at http://127.0.0.1:$PORT"
echo "   - API Documentation: http://127.0.0.1:$PORT/docs"
echo "   - Press Ctrl+C to stop all services."

# 进入 service 目录运行 uvicorn
# 这样 uvicorn 就能正确找到模块
(cd service && uvicorn api.main:app --reload --host 0.0.0.0 --port $PORT)

# 脚本会在这里阻塞，直到 uvicorn 进程被终止 (Ctrl+C)
# 当 uvicorn 结束后，trap 会被触发，调用 cleanup 函数