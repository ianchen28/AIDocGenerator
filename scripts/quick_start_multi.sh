#!/bin/bash

# 一键启动多 Worker + 负载均衡器 (统一日志系统版)
# 使用方法: ./quick_start_multi.sh <worker_num> [lb_port]
# 示例: ./quick_start_multi.sh 4 8082

set -e

# 默认配置
DEFAULT_WORKERS=2
BASE_PORT=8000
LB_PORT=8081

# 统一日志系统配置
LOG_DIR="logs"
UNIFIED_LOG="$LOG_DIR/app.log"
WORKER_LOG_PREFIX="$LOG_DIR/worker"
LB_LOG="$LOG_DIR/load_balancer.log"
LOG_SIZE="10M"  # 10MB 文件大小限制
LOG_ROTATE_COUNT=5  # 保留5个备份文件

# 获取参数
NUM_WORKERS=${1:-$DEFAULT_WORKERS}
LB_PORT=${2:-$LB_PORT}

# 参数验证
if ! [[ "$NUM_WORKERS" =~ ^[0-9]+$ ]]; then
    echo "❌ Worker 数量必须是整数"
    echo "使用方法: ./quick_start_multi.sh <worker_num> [lb_port]"
    echo "示例: ./quick_start_multi.sh 4 8082"
    exit 1
fi

if [ "$NUM_WORKERS" -lt 1 ] || [ "$NUM_WORKERS" -gt 20 ]; then
    echo "❌ Worker 数量必须在 1-20 之间"
    exit 1
fi

if ! [[ "$LB_PORT" =~ ^[0-9]+$ ]]; then
    echo "❌ 负载均衡器端口必须是整数"
    echo "使用方法: ./quick_start_multi.sh <worker_num> [lb_port]"
    echo "示例: ./quick_start_multi.sh 4 8082"
    exit 1
fi

if [ "$LB_PORT" -lt 1024 ] || [ "$LB_PORT" -gt 65535 ]; then
    echo "❌ 负载均衡器端口必须在 1024-65535 之间"
    exit 1
fi

echo "🚀 一键启动多 Worker + 负载均衡器 (统一日志系统版)"
echo "=================================================="
echo "Worker 数量: $NUM_WORKERS"
echo "Worker 端口范围: $BASE_PORT - $((BASE_PORT + NUM_WORKERS - 1))"
echo "负载均衡器端口: $LB_PORT"
echo "统一日志: $UNIFIED_LOG"
echo "日志轮转: 自动按 $LOG_SIZE 大小轮转，保留 $LOG_ROTATE_COUNT 个备份"
echo ""

# 创建日志目录并清理旧日志
echo "🔵 初始化日志系统..."
mkdir -p "$LOG_DIR"
mkdir -p "$LOG_DIR/archive"

# 清理旧的日志文件（保留最近的文件）
echo "   - 清理旧日志文件..."
# 清理过老的备份文件（超过7天）
find "$LOG_DIR" -maxdepth 1 -name "*.log.*" -type f -mtime +7 -delete 2>/dev/null || true
# 清理过老的归档文件（超过30天）
find "$LOG_DIR/archive" -name "*.log.*" -type f -mtime +30 -delete 2>/dev/null || true
# 清理空的归档目录
find "$LOG_DIR/archive" -type d -empty -delete 2>/dev/null || true

# 创建日志文件
touch "$UNIFIED_LOG"
touch "$LB_LOG"

# 日志轮转函数
rotate_log() {
    local log_file="$1"
    local max_size="$2"
    local backup_count="$3"
    
    if [ ! -f "$log_file" ]; then
        return
    fi
    
    # 获取文件大小（字节）
    local current_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
    
    # 转换最大大小到字节
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
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 日志文件超过 $max_size，执行轮转..." >> "$log_file"
        
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
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 日志轮转完成" >> "$log_file"
        
        # 清理旧的备份文件并移动到archive
        for i in $(seq $((backup_count+1)) 10); do
            if [ -f "${log_file}.$i" ]; then
                # 创建archive目录（如果不存在）
                local archive_dir="$LOG_DIR/archive/$(date '+%Y-%m')"
                mkdir -p "$archive_dir"
                
                # 移动文件到archive目录
                local archive_file="$archive_dir/$(basename "$log_file").$i"
                mv "${log_file}.$i" "$archive_file"
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📦 已归档: ${log_file}.$i → $archive_file" >> "$log_file"
            fi
        done
    fi
}

# 检查 conda 环境
if [ "$CONDA_DEFAULT_ENV" != "ai-doc" ]; then
    echo "❌ 当前环境不是 'ai-doc'，请先运行 'conda activate ai-doc'"
    exit 1
fi
echo "✅ 当前环境是 'ai-doc'"

# 检查 Redis
echo "🔵 检查 Redis 服务..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis 服务未运行或无法访问"
    exit 1
fi
echo "✅ Redis 服务正常运行"

# 检查端口占用
echo "🔵 检查端口占用..."
if lsof -i :$LB_PORT > /dev/null 2>&1; then
    echo "❌ 负载均衡器端口 $LB_PORT 已被占用"
    echo "   请选择其他端口，例如: ./quick_start_multi.sh $NUM_WORKERS 8082"
    exit 1
fi
echo "✅ 负载均衡器端口 $LB_PORT 可用"

# 清理旧进程
echo "🔵 清理旧进程..."
if [ -f "$LOG_DIR/multi_worker.pid" ]; then
    echo "   - 停止旧的 Worker 进程..."
    while read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
            echo "     🛑 终止 Worker 进程 PID: $pid"
        fi
    done < "$LOG_DIR/multi_worker.pid"
    rm -f "$LOG_DIR/multi_worker.pid"
fi

if [ -f "$LOG_DIR/load_balancer.pid" ]; then
    echo "   - 停止旧的负载均衡器进程..."
    read -r pid < "$LOG_DIR/load_balancer.pid"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null
        echo "     🛑 终止负载均衡器进程 PID: $pid"
    fi
    rm -f "$LOG_DIR/load_balancer.pid"
fi

# 清理残留进程
echo "   - 清理残留进程..."
pkill -f "uvicorn.*api.main:app" 2>/dev/null || true
pkill -f "load_balancer.py" 2>/dev/null || true

# 如果进程仍然存在，使用更强力的终止
sleep 3
if pgrep -f "uvicorn.*api.main:app\|load_balancer.py" > /dev/null 2>&1; then
    echo "     🔴 强制终止残留进程..."
    pkill -9 -f "uvicorn.*api.main:app" 2>/dev/null || true
    pkill -9 -f "load_balancer.py" 2>/dev/null || true
fi

sleep 2

# 启动 Worker 进程
echo "🔵 启动 $NUM_WORKERS 个 Worker..."
WORKER_PIDS=()

for ((i=0; i<NUM_WORKERS; i++)); do
    WORKER_PORT=$((BASE_PORT + i))
    WORKER_LOG="${WORKER_LOG_PREFIX}_$((i+1)).log"
    echo "   - 启动 Worker $((i+1))/$NUM_WORKERS (端口: $WORKER_PORT, 日志: $WORKER_LOG)..."
    
    # 创建 worker 专用日志文件
    touch "$WORKER_LOG"
    
    # 启动 worker 进程，输出到专用日志文件
    (cd service && nohup uvicorn api.main:app --host 0.0.0.0 --port $WORKER_PORT --workers 1 --reload >> "../$WORKER_LOG" 2>&1) &
    WORKER_PID=$!
    WORKER_PIDS+=($WORKER_PID)
    
    echo "   ✅ Worker $((i+1)) 已启动，PID: $WORKER_PID"
    sleep 2
done

# 保存 Worker PID
echo "${WORKER_PIDS[@]}" > "$LOG_DIR/multi_worker.pid"

# 等待 Worker 启动
echo "   ⏳ 等待 Worker 完全启动..."
sleep 5

# 检查 Worker 状态
for ((i=0; i<NUM_WORKERS; i++)); do
    WORKER_PORT=$((BASE_PORT + i))
    if curl -s "http://127.0.0.1:$WORKER_PORT/" > /dev/null 2>&1; then
        echo "   ✅ Worker $((i+1)) 运行正常 (端口: $WORKER_PORT)"
    else
        echo "   ❌ Worker $((i+1)) 启动失败"
        exit 1
    fi
done

# 启动负载均衡器
echo "🔵 启动负载均衡器..."
export LB_BASE_PORT=$BASE_PORT
export LB_NUM_WORKERS=$NUM_WORKERS
export LB_PORT=$LB_PORT

# 启动负载均衡器，输出到专用日志文件
nohup python load_balancer.py >> "$LB_LOG" 2>&1 &
LB_PID=$!

# 保存负载均衡器 PID
echo "$LB_PID" > "$LOG_DIR/load_balancer.pid"

echo "   ✅ 负载均衡器已启动，PID: $LB_PID"

# 启动后台日志轮转监控进程
echo "   - 启动日志轮转监控进程..."
(
    while true; do
        sleep 30  # 每30秒检查一次
        # 轮转统一日志
        rotate_log "$UNIFIED_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"
        # 轮转负载均衡器日志
        rotate_log "$LB_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"
        # 轮转所有 worker 日志
        for ((i=1; i<=NUM_WORKERS; i++)); do
            WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
            rotate_log "$WORKER_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"
        done
    done
) &
LOG_ROTATION_PID=$!

# 保存日志轮转监控进程 PID
echo "$LOG_ROTATION_PID" > "$LOG_DIR/log_rotation.pid"

# 等待负载均衡器启动
echo "   ⏳ 等待负载均衡器完全启动..."
sleep 5

# 检查负载均衡器状态
if curl -s "http://127.0.0.1:$LB_PORT/health" > /dev/null 2>&1; then
    echo "   ✅ 负载均衡器运行正常"
else
    echo "   ⚠️  负载均衡器健康检查失败，但进程正在运行"
fi

# 显示服务信息
echo ""
echo "🎉 多 Worker + 负载均衡器启动成功！"
echo "=================================================="
echo "   Worker 数量: $NUM_WORKERS"
echo "   Worker 端口范围: $BASE_PORT - $((BASE_PORT + NUM_WORKERS - 1))"
echo "   负载均衡器端口: $LB_PORT"
echo "   服务地址: http://127.0.0.1:$LB_PORT"
echo "   API文档: http://127.0.0.1:$LB_PORT/docs"
echo "   健康检查: http://127.0.0.1:$LB_PORT/health"
echo "   统一日志: $UNIFIED_LOG"
echo "   Worker 日志: ${WORKER_LOG_PREFIX}_1.log - ${WORKER_LOG_PREFIX}_${NUM_WORKERS}.log"
echo "   负载均衡器日志: $LB_LOG"
echo "   日志轮转: 自动按 $LOG_SIZE 大小轮转"
echo "   保留备份: $LOG_ROTATE_COUNT 个文件"
echo ""
echo "💡 管理命令:"
echo "   - 查看统一日志: tail -f $UNIFIED_LOG"
echo "   - 查看 Worker 日志: tail -f ${WORKER_LOG_PREFIX}_1.log"
echo "   - 查看负载均衡器日志: tail -f $LB_LOG"
echo "   - 查看所有日志: ls -lh $LOG_DIR/*.log"
echo "   - 查看进程: ps aux | grep -E '(uvicorn|load_balancer)'"
echo "   - 停止服务: ./stop_multi.sh"
echo "   - 手动轮转日志: ./log_rotate.sh"
echo "   - 清理过老日志: ./cleanup_logs.sh"
echo "   - 查看归档日志: ls -lh $LOG_DIR/archive/"
echo ""
echo "✅ 所有服务已在后台运行，支持高并发处理"
echo "✅ 分离式日志系统已启用，避免并发写入冲突"
echo "✅ 自动轮转功能已启用"
echo "✅ 可以安全关闭终端。"
