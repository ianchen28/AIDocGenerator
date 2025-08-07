#!/bin/bash

# =================================================================
# AIDocGenerator - 停止开发环境脚本 (终极优化版)
# 功能：查找并强制杀死所有 uvicorn, celery 和 mock 服务进程。
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- 获取脚本所在目录 ---
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PID_FILE="$DIR/service.pid"

echo -e "${YELLOW}🛑 正在强制停止所有 AIDocGenerator 相关服务...${NC}"
echo "=================================================="

# --- 安全终止进程的函数 ---
safe_kill_processes() {
    local pids="$1"
    local process_name="$2"
    
    if [ -z "$pids" ]; then
        echo -e "   - ${GREEN}没有找到正在运行的 ${process_name}。${NC}"
        return
    fi
    
    # 先尝试优雅终止 (SIGTERM)
    echo "   - 正在优雅终止 ${process_name} 进程..."
    kill $pids 2>/dev/null
    
    # 等待3秒让进程优雅退出
    sleep 3
    
    # 检查进程是否还存在
    remaining_pids=""
    for pid in $pids; do
        if kill -0 $pid 2>/dev/null; then
            remaining_pids="$remaining_pids $pid"
        fi
    done
    
    # 如果还有进程存在，尝试强制终止
    if [ -n "$remaining_pids" ]; then
        echo "   - 正在强制终止剩余的 ${process_name} 进程..."
        kill -9 $remaining_pids 2>/dev/null
        
        # 最终检查
        final_remaining=""
        for pid in $remaining_pids; do
            if kill -0 $pid 2>/dev/null; then
                final_remaining="$final_remaining $pid"
            fi
        done
        
        if [ -n "$final_remaining" ]; then
            echo -e "   - ${RED}警告: 以下进程无法终止 (可能需要手动处理): ${final_remaining}${NC}"
        else
            echo -e "   - ✅ ${process_name} 进程已被强制终止。${NC}"
        fi
    else
        echo -e "   - ✅ ${process_name} 进程已优雅终止。${NC}"
    fi
}

# --- 处理PID文件中的进程 ---
if [ -f "$PID_FILE" ]; then
    echo "🔍 正在查找PID文件中的进程..."
    PIDS_FROM_FILE=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PIDS_FROM_FILE" ]; then
        safe_kill_processes "$PIDS_FROM_FILE" "PID文件中的进程"
        rm -f "$PID_FILE"
    fi
    echo "--------------------------------------------------"
fi

# --- 查找并杀死 Uvicorn (FastAPI) 服务 ---
echo "🔍 正在查找 Uvicorn (FastAPI) 服务..."
PIDS_UVICORN=$(pgrep -f "uvicorn.*api.main:app")
safe_kill_processes "$PIDS_UVICORN" "Uvicorn 服务"
echo "--------------------------------------------------"

# --- 查找并杀死 Celery Worker ---
echo "🔍 正在查找 Celery Worker..."
PIDS_CELERY=$(pgrep -f "workers.celery_worker worker")
safe_kill_processes "$PIDS_CELERY" "Celery Worker"
echo "--------------------------------------------------"

# --- 查找并杀死 Mock 服务 (如果存在) ---
echo "🔍 正在查找 Mock 服务..."
PIDS_MOCK=$(pgrep -f "mock_service/")
safe_kill_processes "$PIDS_MOCK" "Mock 服务"
echo "--------------------------------------------------"

# --- 检查端口占用情况 ---
echo "🔍 检查端口占用情况..."
PORT_8000_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PORT_8000_PID" ]; then
    echo "   - 发现端口 8000 被占用，正在释放..."
    safe_kill_processes "$PORT_8000_PID" "端口 8000 占用进程"
else
    echo -e "   - ${GREEN}端口 8000 未被占用。${NC}"
fi
echo "--------------------------------------------------"

# --- 等待端口完全释放 ---
echo "⏳ 等待端口完全释放..."
for i in {1..5}; do
    if ! lsof -ti:8000 >/dev/null 2>&1; then
        echo -e "   - ${GREEN}端口 8000 已释放。${NC}"
        break
    fi
    echo "   - 等待中... ($i/5)"
    sleep 1
done

echo -e "${GREEN}✅ 所有服务关闭流程执行完毕。${NC}"