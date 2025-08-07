#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本 (优化版)
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认端口
DEFAULT_PORT=8000
PORT=${1:-$DEFAULT_PORT}

echo -e "${GREEN}🚀 启动 AI 文档生成器服务...${NC}"
echo "=========================================="
echo "端口: $PORT"
echo ""

# --- 步骤 0: 清理旧的进程 ---
echo -e "${YELLOW}🔵 步骤 0: 正在清理可能残留的旧服务...${NC}"
# 执行停止脚本，确保环境干净
./stop_dev_server.sh
echo ""


# --- 步骤 1: 检查系统依赖 ---
echo -e "${YELLOW}🔵 步骤 1: 检查系统依赖...${NC}"

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo -e "   - ${RED}conda 未安装，请先安装 conda${NC}"
    exit 1
fi

# 检查Redis服务
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "   - ${RED}错误: Redis 服务未运行或无法访问。${NC}"
    echo "   - 请先在另一个终端中启动你的 Redis 服务。"
    exit 1
fi
echo "   - ✅ Redis 服务正常运行"


# --- 步骤 2: 激活 conda 环境 ---
echo -e "\n${YELLOW}🔵 步骤 2: 激活 conda 环境...${NC}"
# 检查当前环境是否为 ai-doc
if [[ "$CONDA_DEFAULT_ENV" != "ai-doc" ]]; then
    echo "   - ⚠️  当前环境不是 'ai-doc'，尝试激活..."
    if ! conda activate ai-doc; then
        echo "   - ${RED}无法激活 ai-doc 环境。${NC}"
        echo "   - 请确保已创建环境: conda create -n ai-doc python=3.11"
        exit 1
    fi
fi
echo "   - ✅ 当前环境是 'ai-doc'"


# --- 步骤 3: 启动 Celery Worker ---
echo -e "\n${YELLOW}🔵 步骤 3: 在后台启动 Celery Worker...${NC}"
(cd service && python -m workers.celery_worker worker --loglevel=info) > celery_worker.log 2>&1 &
CELERY_PID=$!
echo "   - ✅ Celery Worker 已在后台启动，PID: $CELERY_PID"
echo "   - 日志正在写入 celery_worker.log"
# 简短等待，确保 worker 完成初始化
sleep 3
# 检查进程是否存在
if ! ps -p $CELERY_PID > /dev/null; then
    echo "   - ${RED}Celery Worker 启动失败，请检查 celery_worker.log 文件。${NC}"
    exit 1
fi


# --- 步骤 4: 启动 FastAPI 服务 ---
echo -e "\n${YELLOW}🔵 步骤 4: 在前台启动 FastAPI 服务...${NC}"
echo "   - 服务地址: http://127.0.0.1:$PORT"
echo "   - API文档: http://127.0.0.1:$PORT/docs"
echo -e "   - ${YELLOW}按 Ctrl+C 可停止所有服务。${NC}"

# 定义一个函数用于优雅地关闭后台进程
cleanup() {
    echo -e "\n${YELLOW}🔴 收到关闭信号，正在停止所有服务...${NC}"
    # 调用我们的标准停止脚本
    ./stop_dev_server.sh
    exit 0
}

# 设置 trap，当脚本接收到退出信号时（比如按下了 Ctrl+C），调用 cleanup 函数
trap cleanup SIGINT SIGTERM

# 在 service 目录中启动 uvicorn
(cd service && uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --reload)