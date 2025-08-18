#!/bin/bash

# 多 Worker 日志监控脚本
# 使用方法: ./monitor_all_workers.sh [worker_num] [监控模式]
# 示例: ./monitor_all_workers.sh 8 realtime
# 示例: ./monitor_all_workers.sh 8 errors

set -e

LOG_DIR="../logs"
UNIFIED_LOG="$LOG_DIR/app.log"
LB_LOG="$LOG_DIR/load_balancer.log"
WORKER_LOG_PREFIX="$LOG_DIR/worker"

# 获取参数
NUM_WORKERS=${1:-8}
MONITOR_MODE=${2:-"realtime"}

echo "📊 多 Worker 日志监控器"
echo "=================================================="
echo "Worker 数量: $NUM_WORKERS"
echo "监控模式: $MONITOR_MODE"
echo "日志目录: $LOG_DIR"
echo ""

# 检查日志目录
if [ ! -d "$LOG_DIR" ]; then
    echo "❌ 日志目录不存在: $LOG_DIR"
    echo "请确保在 scripts 目录下运行此脚本"
    exit 1
fi

# 检查日志文件
echo "🔵 检查日志文件..."
missing_files=()

# 检查统一日志
if [ ! -f "$UNIFIED_LOG" ]; then
    missing_files+=("统一日志: $UNIFIED_LOG")
fi

# 检查负载均衡器日志
if [ ! -f "$LB_LOG" ]; then
    missing_files+=("负载均衡器日志: $LB_LOG")
fi

# 检查 worker 日志
for ((i=1; i<=NUM_WORKERS; i++)); do
    WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
    if [ ! -f "$WORKER_LOG" ]; then
        missing_files+=("Worker $i 日志: $WORKER_LOG")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "⚠️  以下日志文件不存在:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "💡 建议："
    echo "   - 检查服务是否已启动"
    echo "   - 运行: ./quick_start_multi.sh $NUM_WORKERS"
    echo ""
fi

echo "✅ 日志文件检查完成"
echo ""

# 显示日志文件状态
echo "📊 当前日志文件状态:"
if [ -f "$UNIFIED_LOG" ]; then
    echo "   - $UNIFIED_LOG ($(du -h "$UNIFIED_LOG" | cut -f1))"
fi

if [ -f "$LB_LOG" ]; then
    echo "   - $LB_LOG ($(du -h "$LB_LOG" | cut -f1))"
fi

for ((i=1; i<=NUM_WORKERS; i++)); do
    WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
    if [ -f "$WORKER_LOG" ]; then
        echo "   - $WORKER_LOG ($(du -h "$WORKER_LOG" | cut -f1))"
    fi
done

echo ""

# 监控模式选择
case $MONITOR_MODE in
    "realtime"|"rt")
        echo "🔍 实时监控模式 - 同时监控所有日志"
        echo "   按 Ctrl+C 停止监控"
        echo ""
        
        # 构建所有日志文件列表
        log_files=""
        if [ -f "$UNIFIED_LOG" ]; then
            log_files="$UNIFIED_LOG"
        fi
        if [ -f "$LB_LOG" ]; then
            log_files="$log_files $LB_LOG"
        fi
        for ((i=1; i<=NUM_WORKERS; i++)); do
            WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
            if [ -f "$WORKER_LOG" ]; then
                log_files="$log_files $WORKER_LOG"
            fi
        done
        
        if [ -n "$log_files" ]; then
            echo "📖 开始实时监控以下文件:"
            echo "$log_files" | tr ' ' '\n' | while read -r file; do
                echo "   - $file"
            done
            echo ""
            echo "🔄 实时日志输出:"
            echo "=================================================="
            tail -f $log_files
        else
            echo "❌ 没有找到可监控的日志文件"
        fi
        ;;
        
    "errors"|"error")
        echo "🔍 错误监控模式 - 监控所有错误日志"
        echo ""
        
        echo "📖 搜索错误日志..."
        echo "=================================================="
        
        # 搜索所有日志文件中的错误
        for file in "$UNIFIED_LOG" "$LB_LOG"; do
            if [ -f "$file" ]; then
                echo "🔍 搜索文件: $file"
                grep -i "error\|exception\|failed\|fail" "$file" | tail -10
                echo ""
            fi
        done
        
        for ((i=1; i<=NUM_WORKERS; i++)); do
            WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
            if [ -f "$WORKER_LOG" ]; then
                echo "🔍 搜索文件: $WORKER_LOG"
                grep -i "error\|exception\|failed\|fail" "$WORKER_LOG" | tail -10
                echo ""
            fi
        done
        ;;
        
    "warnings"|"warn")
        echo "🔍 警告监控模式 - 监控所有警告日志"
        echo ""
        
        echo "📖 搜索警告日志..."
        echo "=================================================="
        
        # 搜索所有日志文件中的警告
        for file in "$UNIFIED_LOG" "$LB_LOG"; do
            if [ -f "$file" ]; then
                echo "🔍 搜索文件: $file"
                grep -i "warn\|warning" "$file" | tail -10
                echo ""
            fi
        done
        
        for ((i=1; i<=NUM_WORKERS; i++)); do
            WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
            if [ -f "$WORKER_LOG" ]; then
                echo "🔍 搜索文件: $WORKER_LOG"
                grep -i "warn\|warning" "$WORKER_LOG" | tail -10
                echo ""
            fi
        done
        ;;
        
    "summary"|"stats")
        echo "🔍 统计监控模式 - 显示日志统计信息"
        echo ""
        
        echo "📊 日志统计信息:"
        echo "=================================================="
        
        # 统计每个日志文件的信息
        for file in "$UNIFIED_LOG" "$LB_LOG"; do
            if [ -f "$file" ]; then
                file_size=$(du -h "$file" | cut -f1)
                line_count=$(wc -l < "$file")
                error_count=$(grep -i "error\|exception\|failed\|fail" "$file" | wc -l)
                warn_count=$(grep -i "warn\|warning" "$file" | wc -l)
                echo "📄 $(basename "$file"):"
                echo "   - 大小: $file_size"
                echo "   - 行数: $line_count"
                echo "   - 错误: $error_count"
                echo "   - 警告: $warn_count"
                echo ""
            fi
        done
        
        for ((i=1; i<=NUM_WORKERS; i++)); do
            WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
            if [ -f "$WORKER_LOG" ]; then
                file_size=$(du -h "$WORKER_LOG" | cut -f1)
                line_count=$(wc -l < "$WORKER_LOG")
                error_count=$(grep -i "error\|exception\|failed\|fail" "$WORKER_LOG" | wc -l)
                warn_count=$(grep -i "warn\|warning" "$WORKER_LOG" | wc -l)
                echo "📄 Worker $i ($(basename "$WORKER_LOG")):"
                echo "   - 大小: $file_size"
                echo "   - 行数: $line_count"
                echo "   - 错误: $error_count"
                echo "   - 警告: $warn_count"
                echo ""
            fi
        done
        ;;
        
    "worker"|"w")
        echo "🔍 Worker 监控模式 - 监控特定 Worker"
        echo ""
        
        read -p "请输入要监控的 Worker 编号 (1-$NUM_WORKERS): " worker_num
        
        if ! [[ "$worker_num" =~ ^[0-9]+$ ]] || [ "$worker_num" -lt 1 ] || [ "$worker_num" -gt "$NUM_WORKERS" ]; then
            echo "❌ 无效的 Worker 编号"
            exit 1
        fi
        
        WORKER_LOG="${WORKER_LOG_PREFIX}_${worker_num}.log"
        if [ -f "$WORKER_LOG" ]; then
            echo "📖 监控 Worker $worker_num 日志: $WORKER_LOG"
            echo "   按 Ctrl+C 停止监控"
            echo ""
            echo "🔄 实时日志输出:"
            echo "=================================================="
            tail -f "$WORKER_LOG"
        else
            echo "❌ Worker $worker_num 日志文件不存在: $WORKER_LOG"
        fi
        ;;
        
    *)
        echo "❌ 无效的监控模式: $MONITOR_MODE"
        echo ""
        echo "💡 可用的监控模式:"
        echo "   - realtime/rt: 实时监控所有日志"
        echo "   - errors/error: 监控错误日志"
        echo "   - warnings/warn: 监控警告日志"
        echo "   - summary/stats: 显示统计信息"
        echo "   - worker/w: 监控特定 Worker"
        echo ""
        echo "示例:"
        echo "   ./monitor_all_workers.sh 8 realtime"
        echo "   ./monitor_all_workers.sh 8 errors"
        echo "   ./monitor_all_workers.sh 8 worker"
        exit 1
        ;;
esac
