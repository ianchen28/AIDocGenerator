#!/bin/bash

# 停止多 Worker + 负载均衡器服务
# 使用方法: ./stop_multi.sh

set -e

LOG_DIR="../logs"

echo "🛑 停止多 Worker + 负载均衡器服务"
echo "=================================================="

# 停止 Worker 进程
if [ -f "$LOG_DIR/multi_worker.pid" ]; then
    echo "🔵 停止 Worker 进程..."
    while read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "   - 终止 Worker 进程 PID: $pid"
            kill -TERM "$pid" 2>/dev/null
        fi
    done < "$LOG_DIR/multi_worker.pid"
    rm -f "$LOG_DIR/multi_worker.pid"
    echo "   ✅ Worker 进程已停止"
else
    echo "   ℹ️  未找到 Worker PID 文件"
fi

# 停止负载均衡器进程
if [ -f "$LOG_DIR/load_balancer.pid" ]; then
    echo "🔵 停止负载均衡器进程..."
    read -r pid < "$LOG_DIR/load_balancer.pid"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "   - 终止负载均衡器进程 PID: $pid"
        kill -TERM "$pid" 2>/dev/null
    fi
    rm -f "$LOG_DIR/load_balancer.pid"
    echo "   ✅ 负载均衡器进程已停止"
else
    echo "   ℹ️  未找到负载均衡器 PID 文件"
fi

# 停止日志轮转监控进程
if [ -f "$LOG_DIR/log_rotation.pid" ]; then
    echo "🔵 停止日志轮转监控进程..."
    read -r pid < "$LOG_DIR/log_rotation.pid"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "   - 终止日志轮转监控进程 PID: $pid"
        kill -TERM "$pid" 2>/dev/null
    fi
    rm -f "$LOG_DIR/log_rotation.pid"
    echo "   ✅ 日志轮转监控进程已停止"
else
    echo "   ℹ️  未找到日志轮转监控 PID 文件"
fi

# 清理残留进程
echo "🔵 清理残留进程..."
pkill -f "uvicorn.*api.main:app" 2>/dev/null || true
pkill -f "load_balancer.py" 2>/dev/null || true

# 如果进程仍然存在，使用更强力的终止
sleep 3
if pgrep -f "uvicorn.*api.main:app\|load_balancer.py" > /dev/null 2>&1; then
    echo "   🔴 强制终止残留进程..."
    pkill -9 -f "uvicorn.*api.main:app" 2>/dev/null || true
    pkill -9 -f "load_balancer.py" 2>/dev/null || true
fi

# 清理日志文件（可选）
echo ""
echo "🔵 日志文件管理..."
echo "   当前日志文件:"

# 显示统一日志
if [ -f "$LOG_DIR/app.log" ]; then
    echo "   - $LOG_DIR/app.log ($(du -h "$LOG_DIR/app.log" | cut -f1))"
fi

# 显示负载均衡器日志
if [ -f "$LOG_DIR/load_balancer.log" ]; then
    echo "   - $LOG_DIR/load_balancer.log ($(du -h "$LOG_DIR/load_balancer.log" | cut -f1))"
fi

# 显示 Worker 日志
for i in $(seq 1 20); do
    if [ -f "$LOG_DIR/worker_$i.log" ]; then
        echo "   - $LOG_DIR/worker_$i.log ($(du -h "$LOG_DIR/worker_$i.log" | cut -f1))"
    fi
done

# 显示备份日志文件
echo ""
echo "   备份日志文件:"
for i in $(seq 1 10); do
    if [ -f "$LOG_DIR/app.log.$i" ]; then
        echo "   - $LOG_DIR/app.log.$i ($(du -h "$LOG_DIR/app.log.$i" | cut -f1))"
    fi
done

echo ""
echo "💡 日志管理选项:"
echo "   - 查看统一日志: tail -f $LOG_DIR/app.log"
echo "   - 查看 Worker 日志: tail -f $LOG_DIR/worker_1.log"
echo "   - 查看负载均衡器日志: tail -f $LOG_DIR/load_balancer.log"
echo "   - 查看所有日志: ls -lh $LOG_DIR/*.log"
echo "   - 查看备份日志: ls -lh $LOG_DIR/*.log.*"
echo "   - 清理旧日志: find $LOG_DIR -name '*.log.*' -mtime +7 -delete"
echo "   - 手动轮转: ./log_rotate.sh"

echo ""
echo "✅ 所有服务已停止"
echo "✅ 可以安全关闭终端"
