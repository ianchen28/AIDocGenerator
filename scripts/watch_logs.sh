#!/bin/bash

# 日志聚合查看脚本
# 使用方法: ./watch_logs.sh [worker_num]
# 示例: ./watch_logs.sh 8

set -e

LOG_DIR="../logs"
UNIFIED_LOG="$LOG_DIR/app.log"
LB_LOG="$LOG_DIR/load_balancer.log"
WORKER_LOG_PREFIX="$LOG_DIR/worker"

# 获取 worker 数量
NUM_WORKERS=${1:-8}

echo "📊 日志聚合查看器"
echo "=================================================="
echo "Worker 数量: $NUM_WORKERS"
echo "统一日志: $UNIFIED_LOG"
echo "负载均衡器日志: $LB_LOG"
echo "Worker 日志: ${WORKER_LOG_PREFIX}_1.log - ${WORKER_LOG_PREFIX}_${NUM_WORKERS}.log"
echo ""

# 检查日志文件是否存在
echo "🔵 检查日志文件..."
if [ ! -f "$UNIFIED_LOG" ]; then
    echo "❌ 统一日志文件不存在: $UNIFIED_LOG"
    exit 1
fi

if [ ! -f "$LB_LOG" ]; then
    echo "❌ 负载均衡器日志文件不存在: $LB_LOG"
    exit 1
fi

# 检查 worker 日志文件
missing_workers=()
for ((i=1; i<=NUM_WORKERS; i++)); do
    WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
    if [ ! -f "$WORKER_LOG" ]; then
        missing_workers+=($i)
    fi
done

if [ ${#missing_workers[@]} -gt 0 ]; then
    echo "⚠️  以下 Worker 日志文件不存在: ${missing_workers[*]}"
    echo "   可能的原因："
    echo "   - Worker 数量不正确"
    echo "   - 服务未启动"
    echo "   - 日志文件被删除"
    echo ""
    echo "💡 建议："
    echo "   - 检查服务状态: ps aux | grep uvicorn"
    echo "   - 重新启动服务: ./quick_start_multi.sh $NUM_WORKERS"
    echo ""
fi

echo "✅ 日志文件检查完成"
echo ""

# 显示日志文件大小
echo "📊 当前日志文件大小:"
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
echo "💡 查看选项:"
echo "   1. 查看统一日志: tail -f $UNIFIED_LOG"
echo "   2. 查看负载均衡器日志: tail -f $LB_LOG"
echo "   3. 查看特定 Worker 日志: tail -f ${WORKER_LOG_PREFIX}_1.log"
echo "   4. 聚合查看所有日志: tail -f $UNIFIED_LOG $LB_LOG ${WORKER_LOG_PREFIX}_*.log"
echo "   5. 查看错误日志: grep -i error $LOG_DIR/*.log"
echo "   6. 查看警告日志: grep -i warn $LOG_DIR/*.log"
echo ""

# 提供交互式选择
echo "🔵 选择查看模式:"
echo "   [1] 统一日志 (推荐)"
echo "   [2] 负载均衡器日志"
echo "   [3] Worker 1 日志"
echo "   [4] 聚合查看所有日志"
echo "   [5] 错误日志"
echo "   [6] 警告日志"
echo "   [q] 退出"
echo ""
read -p "请输入选择 (1-6, q): " choice

case $choice in
    1)
        echo "📖 查看统一日志..."
        tail -f "$UNIFIED_LOG"
        ;;
    2)
        echo "📖 查看负载均衡器日志..."
        tail -f "$LB_LOG"
        ;;
    3)
        echo "📖 查看 Worker 1 日志..."
        tail -f "${WORKER_LOG_PREFIX}_1.log"
        ;;
    4)
        echo "📖 聚合查看所有日志..."
        # 构建日志文件列表
        log_files="$UNIFIED_LOG $LB_LOG"
        for ((i=1; i<=NUM_WORKERS; i++)); do
            WORKER_LOG="${WORKER_LOG_PREFIX}_${i}.log"
            if [ -f "$WORKER_LOG" ]; then
                log_files="$log_files $WORKER_LOG"
            fi
        done
        tail -f $log_files
        ;;
    5)
        echo "📖 查看错误日志..."
        grep -i error "$LOG_DIR"/*.log | tail -20
        ;;
    6)
        echo "📖 查看警告日志..."
        grep -i warn "$LOG_DIR"/*.log | tail -20
        ;;
    q|Q)
        echo "👋 退出日志查看器"
        exit 0
        ;;
    *)
        echo "❌ 无效选择，退出"
        exit 1
        ;;
esac
