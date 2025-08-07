#!/bin/bash

# =================================================================
# AIDocGenerator - 服务状态检查脚本
# 功能：检查服务运行状态、端口占用、日志文件等
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- 获取脚本所在目录 ---
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PID_FILE="$DIR/service.pid"
LOG_DIR="$DIR/logs"

echo -e "${BLUE}🔍 AIDocGenerator 服务状态检查${NC}"
echo "=========================================="

# --- 检查PID文件 ---
if [ -f "$PID_FILE" ]; then
    echo -e "${GREEN}✅ PID文件存在: $PID_FILE${NC}"
    PIDS=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "   - 记录的PID: $PIDS"
        
        # 检查进程是否还在运行
        for pid in $PIDS; do
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "   - ${GREEN}PID $pid: 正在运行${NC}"
            else
                echo -e "   - ${RED}PID $pid: 已停止${NC}"
            fi
        done
    fi
else
    echo -e "${YELLOW}⚠️  PID文件不存在${NC}"
fi
echo ""

# --- 检查端口占用 ---
echo -e "${BLUE}🌐 端口状态检查${NC}"
PORT_8000_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PORT_8000_PID" ]; then
    echo -e "   - ${GREEN}端口 8000: 被占用 (PID: $PORT_8000_PID)${NC}"
else
    echo -e "   - ${RED}端口 8000: 未被占用${NC}"
fi
echo ""

# --- 检查进程 ---
echo -e "${BLUE}🔧 进程状态检查${NC}"
UVICORN_PIDS=$(pgrep -f "uvicorn.*api.main:app")
if [ -n "$UVICORN_PIDS" ]; then
    echo -e "   - ${GREEN}Uvicorn 进程: 运行中 (PIDs: $UVICORN_PIDS)${NC}"
else
    echo -e "   - ${RED}Uvicorn 进程: 未运行${NC}"
fi

CELERY_PIDS=$(pgrep -f "workers.celery_worker worker")
if [ -n "$CELERY_PIDS" ]; then
    echo -e "   - ${GREEN}Celery Worker 进程: 运行中 (PIDs: $CELERY_PIDS)${NC}"
else
    echo -e "   - ${RED}Celery Worker 进程: 未运行${NC}"
fi
echo ""

# --- 检查日志文件 ---
echo -e "${BLUE}📋 日志文件检查${NC}"
if [ -d "$LOG_DIR" ]; then
    echo -e "   - ${GREEN}日志目录存在: $LOG_DIR${NC}"
    
    CELERY_LOG="$LOG_DIR/celery_worker.log"
    UVICORN_LOG="$LOG_DIR/uvicorn.log"
    
    if [ -f "$CELERY_LOG" ]; then
        CELERY_SIZE=$(du -h "$CELERY_LOG" | cut -f1)
        echo -e "   - Celery日志: $CELERY_LOG (大小: $CELERY_SIZE)"
    else
        echo -e "   - ${YELLOW}Celery日志文件不存在${NC}"
    fi
    
    if [ -f "$UVICORN_LOG" ]; then
        UVICORN_SIZE=$(du -h "$UVICORN_LOG" | cut -f1)
        echo -e "   - Uvicorn日志: $UVICORN_LOG (大小: $UVICORN_SIZE)"
    else
        echo -e "   - ${YELLOW}Uvicorn日志文件不存在${NC}"
    fi
else
    echo -e "   - ${YELLOW}日志目录不存在${NC}"
fi
echo ""

# --- 检查服务可用性 ---
echo -e "${BLUE}🌐 服务可用性检查${NC}"
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "   - ${GREEN}FastAPI 服务: 可访问${NC}"
    echo -e "   - 服务地址: http://127.0.0.1:8000"
    echo -e "   - API文档: http://127.0.0.1:8000/docs"
else
    echo -e "   - ${RED}FastAPI 服务: 不可访问${NC}"
fi
echo ""

# --- 总结 ---
echo -e "${BLUE}📊 状态总结${NC}"
if [ -f "$PID_FILE" ] && [ -n "$PORT_8000_PID" ] && [ -n "$UVICORN_PIDS" ] && [ -n "$CELERY_PIDS" ]; then
    echo -e "   - ${GREEN}✅ 所有服务正常运行${NC}"
elif [ -f "$PID_FILE" ] || [ -n "$PORT_8000_PID" ] || [ -n "$UVICORN_PIDS" ] || [ -n "$CELERY_PIDS" ]; then
    echo -e "   - ${YELLOW}⚠️  部分服务运行中${NC}"
else
    echo -e "   - ${RED}❌ 没有服务在运行${NC}"
fi 