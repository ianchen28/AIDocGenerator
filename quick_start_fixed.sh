#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本 (修复版 - 确保app.log始终存在)
# 功能：清理环境 -> 检查依赖 -> 启动 Celery -> 启动 Uvicorn -> 后台运行
# 所有日志统一输出到 logs/app.log，确保文件始终存在并实时更新
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- 获取脚本所在目录 ---
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- 后台运行相关文件 ---
PID_FILE="$DIR/service.pid"
LOG_DIR="$DIR/logs"
UNIFIED_LOG="$LOG_DIR/app.log"

# --- 日志轮转配置 ---
LOG_SIZE="10M"  # 日志文件大小限制
LOG_ROTATE_COUNT=5  # 保留的日志文件数量

# --- 创建日志目录和初始日志文件 ---
mkdir -p "$LOG_DIR"
touch "$UNIFIED_LOG"

# --- 检查是否已经在运行 ---
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  检测到服务可能已在运行 (PID文件存在)${NC}"
    echo -e "   - PID文件: $PID_FILE"
    echo -e "   - 统一日志: $UNIFIED_LOG"
    echo ""
    read -p "是否要停止现有服务并重新启动? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}正在停止现有服务...${NC}"
        "$DIR/stop_dev_server.sh"
        rm -f "$PID_FILE"
    else
        echo -e "${GREEN}保持现有服务运行。${NC}"
        echo -e "   - 服务地址: http://127.0.0.1:8000"
        echo -e "   - API文档: http://127.0.0.1:8000/docs"
        echo -e "   - 统一日志: $UNIFIED_LOG"
        echo -e "   - 使用 './stop_dev_server.sh' 停止服务"
        exit 0
    fi
fi

# --- 步骤 0: 强制清理 ---
echo -e "${YELLOW}🔵 步骤 0: 正在强制清理可能残留的旧服务...${NC}"
"$DIR/stop_dev_server.sh"
echo ""

# --- 后续步骤 ---
DEFAULT_PORT=8000
PORT=${1:-$DEFAULT_PORT}

echo -e "${GREEN}🚀 准备启动 AI 文档生成器服务 (修复版 - 确保app.log始终存在)...${NC}"
echo "=========================================="
echo "端口: $PORT"
echo "统一日志: $UNIFIED_LOG"
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

# --- 步骤 3: 启动 Celery Worker (确保app.log始终存在) ---
echo -e "\n${YELLOW}🔵 步骤 3: 在后台启动 Celery Worker (确保app.log始终存在)...${NC}"
# 使用简单的重定向，确保app.log始终存在
(cd service && nohup celery -A workers.celery_worker worker --loglevel=INFO --concurrency=1 >> "$UNIFIED_LOG" 2>&1) &
CELERY_PID=$!
sleep 3 # 等待进程启动
if ! ps -p $CELERY_PID > /dev/null; then
   echo "   - ${RED}Celery Worker 启动失败，请检查日志文件: $UNIFIED_LOG${NC}"
   exit 1
fi
echo "   - ✅ Celery Worker 已在后台启动，PID: $CELERY_PID"
echo "   - 统一日志文件: $UNIFIED_LOG"

# --- 步骤 4: 启动 FastAPI (确保app.log始终存在) ---
echo -e "\n${YELLOW}🔵 步骤 4: 在后台启动 FastAPI 服务 (确保app.log始终存在)...${NC}"
# 使用简单的重定向，确保app.log始终存在
(cd service && nohup uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --reload >> "$UNIFIED_LOG" 2>&1) &
UVICORN_PID=$!
sleep 5 # 等待服务启动

# 检查服务是否成功启动
if ! ps -p $UVICORN_PID > /dev/null; then
   echo "   - ${RED}FastAPI 服务启动失败，请检查日志文件: $UNIFIED_LOG${NC}"
   # 清理已启动的 Celery
   kill $CELERY_PID 2>/dev/null
   exit 1
fi

# 等待端口可用
echo "   - ⏳ 等待服务完全启动..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 保存PID到文件
echo "$CELERY_PID $UVICORN_PID" > "$PID_FILE"

echo ""
echo -e "${GREEN}🎉 服务启动成功！${NC}"
echo "=========================================="
echo -e "   - ${BLUE}服务地址:${NC} http://127.0.0.1:$PORT"
echo -e "   - ${BLUE}API文档:${NC} http://127.0.0.1:$PORT/docs"
echo -e "   - ${BLUE}Celery PID:${NC} $CELERY_PID"
echo -e "   - ${BLUE}Uvicorn PID:${NC} $UVICORN_PID"
echo -e "   - ${BLUE}统一日志:${NC} $UNIFIED_LOG"
echo -e "   - ${BLUE}PID文件:${NC} $PID_FILE"
echo ""
echo -e "${YELLOW}💡 管理命令:${NC}"
echo -e "   - 查看日志: tail -f $UNIFIED_LOG"
echo -e "   - 实时监控: python view_unified_logs.py monitor"
echo -e "   - 搜索日志: python view_unified_logs.py search '关键词'"
echo -e "   - 停止服务: $DIR/stop_dev_server.sh"
echo -e "   - 查看状态: ps aux | grep -E '(celery|uvicorn)'"
echo -e "   - 手动轮转日志: $DIR/log_rotate.sh"
echo ""
echo -e "${GREEN}✅ 服务已在后台运行，所有日志统一输出到 $UNIFIED_LOG${NC}"
echo -e "${GREEN}✅ app.log 文件始终存在并实时更新${NC}"
echo -e "${YELLOW}💡 建议设置定时任务自动轮转日志: $DIR/setup_log_rotation.sh${NC}"
echo -e "${GREEN}✅ 可以安全关闭终端。${NC}"
