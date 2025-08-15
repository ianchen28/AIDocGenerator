#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本 (集成自动日志轮转版)
# 功能：清理环境 -> 检查依赖 -> 设置日志轮转 -> 启动 Celery -> 启动 Uvicorn -> 后台运行
# 所有日志统一输出到 logs/app.log，自动按大小轮转
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

echo -e "${GREEN}🚀 准备启动 AI 文档生成器服务 (集成自动日志轮转版)...${NC}"
echo "=========================================="
echo "端口: $PORT"
echo "统一日志: $UNIFIED_LOG"
echo "日志轮转: 自动按 $LOG_SIZE 大小轮转"
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

# --- 步骤 3: 设置日志轮转 ---
echo -e "\n${YELLOW}🔵 步骤 3: 设置自动日志轮转...${NC}"

# 创建自定义的日志轮转函数
setup_log_rotation() {
    local log_file="$1"
    local max_size="$2"
    local backup_count="$3"
    
    # 检查当前日志文件大小
    if [ -f "$log_file" ]; then
        local current_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
        local max_size_bytes
        if [[ "$max_size" == *K ]]; then
            max_size_bytes=$(echo "$max_size" | sed 's/K$//' | awk '{print $1 * 1024}')
        elif [[ "$max_size" == *M ]]; then
            max_size_bytes=$(echo "$max_size" | sed 's/M$//' | awk '{print $1 * 1024 * 1024}')
        elif [[ "$max_size" == *G ]]; then
            max_size_bytes=$(echo "$max_size" | sed 's/G$//' | awk '{print $1 * 1024 * 1024 * 1024}')
        else
            max_size_bytes=$(echo "$max_size" | awk '{print $1 * 1024 * 1024}')  # 默认按M处理
        fi
        
        if [ "$current_size" -gt "$max_size_bytes" ]; then
            echo "   - 🔄 当前日志文件超过 $max_size，执行轮转..."
            
            # 轮转日志文件
            for i in $(seq $((backup_count-1)) -1 1); do
                if [ -f "${log_file}.$i" ]; then
                    mv "${log_file}.$i" "${log_file}.$((i+1))"
                fi
            done
            
            # 备份当前日志文件
            if [ -f "$log_file" ]; then
                mv "$log_file" "${log_file}.1"
                echo "   - ✅ 已备份当前日志文件为 ${log_file}.1"
            fi
            
            # 创建新的空日志文件
            touch "$log_file"
            echo "   - ✅ 已创建新的日志文件"
            
            # 清理旧的备份文件
            for i in $(seq $((backup_count+1)) 10); do
                if [ -f "${log_file}.$i" ]; then
                    rm -f "${log_file}.$i"
                fi
            done
        else
            echo "   - ✅ 当前日志文件大小正常"
        fi
    fi
}

# 设置日志轮转
setup_log_rotation "$UNIFIED_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"

# --- 步骤 4: 启动 Celery Worker (集成日志轮转) ---
echo -e "\n${YELLOW}🔵 步骤 4: 在后台启动 Celery Worker (集成日志轮转)...${NC}"

# 创建带日志轮转的启动函数
start_service_with_log_rotation() {
    local service_name="$1"
    local command="$2"
    local log_file="$3"
    local max_size="$4"
    local backup_count="$5"
    
    # 启动服务并监控日志大小
    (
        # 启动服务并重定向输出到日志文件
        eval "$command >> $log_file 2>&1" &
        local service_pid=$!
        
        # 监控日志文件大小
        while kill -0 $service_pid 2>/dev/null; do
            sleep 30  # 每30秒检查一次
            
            # 检查日志文件大小
            if [ -f "$log_file" ]; then
                local current_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
                local max_size_bytes
                if [[ "$max_size" == *K ]]; then
                    max_size_bytes=$(echo "$max_size" | sed 's/K$//' | awk '{print $1 * 1024}')
                elif [[ "$max_size" == *M ]]; then
                    max_size_bytes=$(echo "$max_size" | sed 's/M$//' | awk '{print $1 * 1024 * 1024}')
                elif [[ "$max_size" == *G ]]; then
                    max_size_bytes=$(echo "$max_size" | sed 's/G$//' | awk '{print $1 * 1024 * 1024 * 1024}')
                else
                    max_size_bytes=$(echo "$max_size" | awk '{print $1 * 1024 * 1024}')  # 默认按M处理
                fi
                
                if [ "$current_size" -gt "$max_size_bytes" ]; then
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 $service_name 日志文件超过 $max_size，执行轮转..." >> "$log_file"
                    
                    # 轮转日志文件
                    for i in $(seq $((backup_count-1)) -1 1); do
                        if [ -f "${log_file}.$i" ]; then
                            mv "${log_file}.$i" "${log_file}.$((i+1))"
                        fi
                    done
                    
                    # 备份当前日志文件
                    if [ -f "$log_file" ]; then
                        mv "$log_file" "${log_file}.1"
                    fi
                    
                    # 创建新的空日志文件
                    touch "$log_file"
                    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $service_name 日志轮转完成" >> "$log_file"
                    
                    # 清理旧的备份文件
                    for i in $(seq $((backup_count+1)) 10); do
                        if [ -f "${log_file}.$i" ]; then
                            rm -f "${log_file}.$i"
                        fi
                    done
                fi
            fi
        done
    ) &
    
    echo $!
}

# 启动 Celery Worker
echo "   - 启动 Celery Worker..."
(cd service && nohup celery -A workers.celery_worker worker --loglevel=INFO --concurrency=1 >> "$UNIFIED_LOG" 2>&1) &
CELERY_PID=$!

sleep 3 # 等待进程启动
if ! ps -p $CELERY_PID > /dev/null; then
   echo "   - ${RED}Celery Worker 启动失败，请检查日志文件: $UNIFIED_LOG${NC}"
   exit 1
fi
echo "   - ✅ Celery Worker 已在后台启动，PID: $CELERY_PID"
echo "   - 统一日志文件: $UNIFIED_LOG (自动轮转)"

# --- 步骤 5: 启动 FastAPI (集成日志轮转) ---
echo -e "\n${YELLOW}🔵 步骤 5: 在后台启动 FastAPI 服务 (集成日志轮转)...${NC}"

# 启动 FastAPI
echo "   - 启动 FastAPI 服务..."
(cd service && nohup uvicorn api.main:app --host 0.0.0.0 --port $PORT --reload >> "$UNIFIED_LOG" 2>&1) &
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

# 启动后台日志轮转监控进程
echo "   - 启动日志轮转监控进程..."
(
    while true; do
        sleep 30  # 每30秒检查一次
        if [ -f "$UNIFIED_LOG" ]; then
            current_size=$(stat -f%z "$UNIFIED_LOG" 2>/dev/null || stat -c%s "$UNIFIED_LOG" 2>/dev/null)
            if [[ "$LOG_SIZE" == *K ]]; then
                max_size_bytes=$(echo "$LOG_SIZE" | sed 's/K$//' | awk '{print $1 * 1024}')
            elif [[ "$LOG_SIZE" == *M ]]; then
                max_size_bytes=$(echo "$LOG_SIZE" | sed 's/M$//' | awk '{print $1 * 1024 * 1024}')
            elif [[ "$LOG_SIZE" == *G ]]; then
                max_size_bytes=$(echo "$LOG_SIZE" | sed 's/G$//' | awk '{print $1 * 1024 * 1024 * 1024}')
            else
                max_size_bytes=$(echo "$LOG_SIZE" | awk '{print $1 * 1024 * 1024}')  # 默认按M处理
            fi
            
            if [ "$current_size" -gt "$max_size_bytes" ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 日志文件超过 $LOG_SIZE，执行轮转..." >> "$UNIFIED_LOG"
                
                # 轮转日志文件
                for i in $(seq $((LOG_ROTATE_COUNT-1)) -1 1); do
                    if [ -f "${UNIFIED_LOG}.$i" ]; then
                        mv "${UNIFIED_LOG}.$i" "${UNIFIED_LOG}.$((i+1))"
                    fi
                done
                
                # 备份当前日志文件
                if [ -f "$UNIFIED_LOG" ]; then
                    mv "$UNIFIED_LOG" "${UNIFIED_LOG}.1"
                fi
                
                # 创建新的空日志文件
                touch "$UNIFIED_LOG"
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 日志轮转完成" >> "$UNIFIED_LOG"
                
                # 清理旧的备份文件
                for i in $(seq $((LOG_ROTATE_COUNT+1)) 10); do
                    if [ -f "${UNIFIED_LOG}.$i" ]; then
                        rm -f "${UNIFIED_LOG}.$i"
                    fi
                done
            fi
        fi
    done
) &
LOG_ROTATION_PID=$!

# 保存PID到文件
echo "$CELERY_PID $UVICORN_PID $LOG_ROTATION_PID" > "$PID_FILE"

echo ""
echo -e "${GREEN}🎉 服务启动成功！${NC}"
echo "=========================================="
echo -e "   - ${BLUE}服务地址:${NC} http://127.0.0.1:$PORT"
echo -e "   - ${BLUE}API文档:${NC} http://127.0.0.1:$PORT/docs"
echo -e "   - ${BLUE}Celery PID:${NC} $CELERY_PID"
echo -e "   - ${BLUE}Uvicorn PID:${NC} $UVICORN_PID"
echo -e "   - ${BLUE}统一日志:${NC} $UNIFIED_LOG"
echo -e "   - ${BLUE}PID文件:${NC} $PID_FILE"
echo -e "   - ${BLUE}日志轮转:${NC} 自动按 $LOG_SIZE 大小轮转"
echo -e "   - ${BLUE}保留备份:${NC} $LOG_ROTATE_COUNT 个文件"
echo ""
echo -e "${YELLOW}💡 管理命令:${NC}"
echo -e "   - 查看日志: tail -f $UNIFIED_LOG"
echo -e "   - 查看备份: ls -lh ${UNIFIED_LOG}*"
echo -e "   - 实时监控: python view_unified_logs.py monitor"
echo -e "   - 搜索日志: python view_unified_logs.py search '关键词'"
echo -e "   - 停止服务: $DIR/stop_dev_server.sh"
echo -e "   - 查看状态: ps aux | grep -E '(celery|uvicorn)'"
echo -e "   - 手动轮转日志: $DIR/log_rotate.sh"
echo ""
echo -e "${GREEN}✅ 服务已在后台运行，日志自动轮转功能已启用${NC}"
echo -e "${GREEN}✅ 日志文件大小超过 $LOG_SIZE 时会自动轮转${NC}"
echo -e "${GREEN}✅ 可以安全关闭终端。${NC}"
