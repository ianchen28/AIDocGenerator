#!/bin/bash

# =================================================================
# AIDocGenerator - 停止开发环境脚本 (终极优化版)
# 功能：查找并强制杀死所有 uvicorn, celery 和 mock 服务进程。
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 正在强制停止所有 AIDocGenerator 相关服务...${NC}"
echo "=================================================="

# --- 查找并杀死 Uvicorn (FastAPI) 服务 ---
# 使用 pgrep -f 可以通过完整的进程命令来查找，更精确
echo "🔍 正在查找 Uvicorn (FastAPI) 服务..."
PIDS_UVICORN=$(pgrep -f "uvicorn.*api.main:app")
if [ -z "$PIDS_UVICORN" ]; then
    echo -e "   - ${GREEN}没有找到正在运行的 Uvicorn 服务。${NC}"
else
    # -9 信号是强制杀死 (SIGKILL)
    kill -9 $PIDS_UVICORN
    echo -e "   - ✅ Uvicorn 服务进程 (PID: ${PIDS_UVICORN}) 已被强制终止。${NC}"
fi
echo "--------------------------------------------------"

# --- 查找并杀死 Celery Worker ---
# 匹配 'workers.celery_worker'，这比 'python -m' 更特定
echo "🔍 正在查找 Celery Worker..."
PIDS_CELERY=$(pgrep -f "workers.celery_worker worker")
if [ -z "$PIDS_CELERY" ]; then
    echo -e "   - ${GREEN}没有找到正在运行的 Celery Worker。${NC}"
else
    kill -9 $PIDS_CELERY
    echo -e "   - ✅ Celery Worker 进程 (PIDs: ${PIDS_CELERY}) 已被强制终止。${NC}"
fi
echo "--------------------------------------------------"

# --- 查找并杀死 Mock 服务 (如果存在) ---
echo "🔍 正在查找 Mock 服务..."
PIDS_MOCK=$(pgrep -f "mock_service/")
if [ -z "$PIDS_MOCK" ]; then
    echo -e "   - ${GREEN}没有找到正在运行的 Mock 服务。${NC}"
else
    kill -9 $PIDS_MOCK
    echo -e "   - ✅ Mock 服务进程 (PIDs: ${PIDS_MOCK}) 已被强制终止。${NC}"
fi
echo "--------------------------------------------------"

echo -e "${GREEN}✅ 所有服务关闭流程执行完毕。${NC}"