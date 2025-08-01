#!/bin/bash

# =================================================================
# AIDocGenerator - 一键启动开发环境脚本
# =================================================================

# 定义一个函数用于优雅地关闭后台进程
cleanup() {
    echo " " # 换行
    echo "🔴 Shutting down services..."
    # 检查 Celery Worker 进程是否存在，如果存在则终止
    if [ -n "$CELERY_PID" ]; then
        echo "   - Stopping Celery Worker (PID: $CELERY_PID)..."
        kill $CELERY_PID
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

# --- 步骤 2: 激活 conda 环境 ---
echo "🔵 Step 2: Activating conda environment..."
# 尝试激活 ai-doc 环境
if command -v conda &> /dev/null; then
    # 尝试直接激活
    if conda activate ai-doc 2>/dev/null; then
        echo "   - ✅ ai-doc environment activated"
    else
        # 如果直接激活失败，尝试使用 source 方式
        echo "   - ⚠️ 无法直接激活 ai-doc 环境，尝试使用 source 方式..."
        if [ -f ~/miniforge3/etc/profile.d/conda.sh ]; then
            source ~/miniforge3/etc/profile.d/conda.sh
        elif [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
            source ~/miniconda3/etc/profile.d/conda.sh
        elif [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
            source ~/anaconda3/etc/profile.d/conda.sh
        fi
        if conda activate ai-doc; then
            echo "   - ✅ ai-doc 环境已激活"
        else
            echo "   - ❌ 无法激活 ai-doc 环境，请手动激活后重新运行脚本"
            exit 1
        fi
    fi
else
    echo "   - ❌ conda 命令未找到，请确保已安装 conda"
    exit 1
fi

# --- 步骤 3: 启动 Celery Worker ---
echo "🔵 Step 3: Starting Celery Worker in the background..."

# 设置正确的 Redis URL
export REDIS_URL=redis://10.215.149.74:26379/0

# 调用 service/workers 目录中的 start_celery.sh 脚本，并在后台运行
# `&` 符号让命令在后台执行
# `2>&1` 将标准错误重定向到标准输出
# `>` 将输出重定向到日志文件
(cd service && REDIS_URL=redis://:xJrhp*4mnHxbBWN2grqq@10.215.149.74:26379/0 python -m workers.celery_worker worker --loglevel=info) > celery_worker.log 2>&1 &

# 获取刚刚启动的后台进程的 PID (Process ID)
CELERY_PID=$!
echo "   - ✅ Celery Worker started in background with PID: $CELERY_PID"
echo "   - Logs are being written to celery_worker.log"

# 等待几秒钟，确保 Celery Worker 完成初始化
sleep 5

# --- 步骤 4: 启动 FastAPI 服务 ---
echo "🔵 Step 4: Starting FastAPI server in the foreground..."
echo "   - FastAPI will be available at http://127.0.0.1:8000"
echo "   - Press Ctrl+C to stop all services."

# 进入 service 目录运行 uvicorn
# 这样 uvicorn 就能正确找到模块
(cd service && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000)

# 脚本会在这里阻塞，直到 uvicorn 进程被终止 (Ctrl+C)
# 当 uvicorn 结束后，trap 会被触发，调用 cleanup 函数