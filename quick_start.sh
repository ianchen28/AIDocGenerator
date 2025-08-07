#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本 (终极优化版)
# 功能：清理环境 -> 检查依赖 -> 启动 Celery -> 启动 Uvicorn -> 统一管理
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- 步骤 0: 强制清理 ---
# 每次启动前都调用停止脚本，确保端口和进程都是干净的
echo -e "${YELLOW}🔵 步骤 0: 正在强制清理可能残留的旧服务...${NC}"
# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# 执行同目录下的 stop_dev_server.sh
"$DIR/stop_dev_server.sh"
echo ""

# --- 后续步骤 ---
DEFAULT_PORT=8000
PORT=${1:-$DEFAULT_PORT}

echo -e "${GREEN}🚀 准备启动 AI 文档生成器服务...${NC}"
echo "=========================================="
echo "端口: $PORT"
echo ""

# --- 步骤 1: 检查依赖 ---
echo -e "${YELLOW}🔵 步骤 1: 检查系统依赖...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "   - ${RED}错误: Redis 服务未运行或无法访问。请先启动 Redis。${NC}"
    exit 1
fi
echo "   - ✅ Redis 服务正常运行"

# --- 步骤 2: 激活 conda 环境 ---
echo -e "\n${YELLOW}🔵 步骤 2: 激活 conda 环境...${NC}"
if [[ "$CONDA_DEFAULT_ENV" != "ai-doc" ]]; then
    echo "   - ⚠️  当前环境不是 'ai-doc'，请先运行 'conda activate ai-doc'"
    exit 1
fi
echo "   - ✅ 当前环境是 'ai-doc'"

# --- 步骤 3: 启动 Celery Worker (后台) ---
echo -e "\n${YELLOW}🔵 步骤 3: 在后台启动 Celery Worker...${NC}"
(cd service && python -m workers.celery_worker worker --loglevel=INFO) > celery_worker.log 2>&1 &
CELERY_PID=$!
sleep 2 # 等待一下，让进程PID稳定
if ! ps -p $CELERY_PID > /dev/null; then
   echo "   - ${RED}Celery Worker 启动失败，请检查 celery_worker.log 文件。${NC}"
   exit 1
fi
echo "   - ✅ Celery Worker 已在后台启动，PID: $CELERY_PID"
echo "   - 日志正在写入 celery_worker.log"


# --- 步骤 4: 启动 FastAPI (前台) ---
echo -e "\n${YELLOW}🔵 步骤 4: 在前台启动 FastAPI 服务...${NC}"
echo "   - 服务地址: http://127.0.0.1:$PORT"
echo "   - API文档: http://127.0.0.1:$PORT/docs"
echo -e "   - ${YELLOW}按 Ctrl+C 可停止所有服务。${NC}"

# 定义一个函数用于捕获 Ctrl+C 并优雅地关闭后台进程
cleanup() {
    echo -e "\n${YELLOW}🔴 收到关闭信号，正在停止所有服务...${NC}"
    # 再次调用我们的终极停止脚本
    "$DIR/stop_dev_server.sh"
    exit 0
}

# 设置 trap，当脚本接收到退出信号时（比如按下了 Ctrl+C），调用 cleanup 函数
trap cleanup SIGINT SIGTERM

# 在 service 目录中启动 uvicorn
# 使用 exec 可以让 uvicorn 进程替换掉当前的 shell 进程，信号处理更直接
(cd service && exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --reload)