#!/bin/bash

# 手动日志轮转脚本
# 使用方法: ./log_rotate.sh [worker_num]
# 示例: ./log_rotate.sh 8

set -e

LOG_DIR="../logs"
UNIFIED_LOG="$LOG_DIR/app.log"
LB_LOG="$LOG_DIR/load_balancer.log"
WORKER_LOG_PREFIX="$LOG_DIR/worker"
LOG_SIZE="10M"
LOG_ROTATE_COUNT=5

# 获取 worker 数量
NUM_WORKERS=${1:-8}

echo "🔄 手动执行日志轮转"
echo "=================================================="
echo "Worker 数量: $NUM_WORKERS"
echo "统一日志: $UNIFIED_LOG"
echo "负载均衡器日志: $LB_LOG"
echo "Worker 日志: ${WORKER_LOG_PREFIX}_1.log - ${WORKER_LOG_PREFIX}_${NUM_WORKERS}.log"
echo "最大大小: $LOG_SIZE"
echo "保留备份: $LOG_ROTATE_COUNT 个"
echo ""

# 日志轮转函数
rotate_log() {
    local log_file="$1"
    local max_size="$2"
    local backup_count="$3"
    
    if [ ! -f "$log_file" ]; then
        echo "   ℹ️  日志文件不存在: $log_file"
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
    
    local current_size_mb=$(echo "scale=2; $current_size / 1024 / 1024" | bc -l 2>/dev/null || echo "未知")
    local max_size_mb=$(echo "scale=2; $max_size_bytes / 1024 / 1024" | bc -l 2>/dev/null || echo "未知")
    
    echo "   📊 当前大小: ${current_size_mb}MB, 限制: ${max_size_mb}MB"
    
    if [ "$current_size" -gt "$max_size_bytes" ]; then
        echo "   🔄 日志文件超过限制，开始轮转..."
        
        # 轮转日志文件
        for i in $(seq $((backup_count-1)) -1 1); do
            if [ -f "${log_file}.$i" ]; then
                mv "${log_file}.$i" "${log_file}.$((i+1))"
                echo "     - 移动 ${log_file}.$i -> ${log_file}.$((i+1))"
            fi
        done
        
        # 备份当前日志文件
        if [ -f "$log_file" ]; then
            mv "$log_file" "${log_file}.1"
            echo "     - 备份当前日志文件为 ${log_file}.1"
        fi
        
        # 创建新的空日志文件
        touch "$log_file"
        echo "     - 创建新的日志文件"
        
        # 清理旧的备份文件并移动到archive
        for i in $(seq $((backup_count+1)) 10); do
            if [ -f "${log_file}.$i" ]; then
                # 创建archive目录（如果不存在）
                local archive_dir="$LOG_DIR/archive/$(date '+%Y-%m')"
                mkdir -p "$archive_dir"
                
                # 移动文件到archive目录
                local archive_file="$archive_dir/$(basename "$log_file").$i"
                mv "${log_file}.$i" "$archive_file"
                echo "     - 归档: ${log_file}.$i → $archive_file"
            fi
        done
        
        echo "   ✅ 日志轮转完成"
    else
        echo "   ℹ️  日志文件大小正常，无需轮转"
    fi
}

# 轮转所有日志文件
echo "🔵 开始轮转所有日志文件..."
echo ""

# 轮转统一日志
echo "📄 轮转统一日志: $UNIFIED_LOG"
rotate_log "$UNIFIED_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"
echo ""

# 轮转负载均衡器日志
echo "📄 轮转负载均衡器日志: $LB_LOG"
rotate_log "$LB_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"
echo ""

# 轮转所有 worker 日志
echo "📄 轮转 Worker 日志..."
for ((i=1; i<=NUM_WORKERS; i++)); do
    WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
    echo "   - Worker $i: $WORKER_LOG"
    rotate_log "$WORKER_LOG" "$LOG_SIZE" "$LOG_ROTATE_COUNT"
    echo ""
done

echo "📁 当前日志文件列表:"
echo "   统一日志:"
ls -lh "$LOG_DIR"/app.log* 2>/dev/null || echo "   无统一日志文件"

echo "   负载均衡器日志:"
ls -lh "$LOG_DIR"/load_balancer.log* 2>/dev/null || echo "   无负载均衡器日志文件"

echo "   Worker 日志:"
for ((i=1; i<=NUM_WORKERS; i++)); do
    WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
    if [ -f "$WORKER_LOG" ]; then
        echo "   - Worker $i:"
        ls -lh "$WORKER_LOG"* 2>/dev/null || echo "     无日志文件"
    fi
done
