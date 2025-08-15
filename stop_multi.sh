#!/bin/bash

# 停止多 Worker + 负载均衡器
# 使用方法: ./stop_multi.sh

set -e

echo "🛑 正在停止多 Worker + 负载均衡器..."

# 停止 Worker 进程
echo "🔵 停止 Worker 进程..."
if [ -f "logs/multi_worker.pid" ]; then
    echo "   - 读取 Worker PID 文件..."
    while read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
            echo "     🛑 终止 Worker 进程 PID: $pid"
        else
            echo "     ⚠️  Worker 进程 PID: $pid 不存在"
        fi
    done < "logs/multi_worker.pid"
    rm -f "logs/multi_worker.pid"
    echo "   ✅ Worker PID 文件已删除"
else
    echo "   ⚠️  未找到 Worker PID 文件"
fi

# 停止负载均衡器进程
echo "🔵 停止负载均衡器进程..."
if [ -f "logs/load_balancer.pid" ]; then
    echo "   - 读取负载均衡器 PID 文件..."
    read -r pid < "logs/load_balancer.pid"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null
        echo "     🛑 终止负载均衡器进程 PID: $pid"
    else
        echo "     ⚠️  负载均衡器进程 PID: $pid 不存在"
    fi
    rm -f "logs/load_balancer.pid"
    echo "   ✅ 负载均衡器 PID 文件已删除"
else
    echo "   ⚠️  未找到负载均衡器 PID 文件"
fi

# 等待进程优雅关闭
echo "🔵 等待进程优雅关闭..."
sleep 3

# 清理残留进程
echo "🔵 清理残留进程..."
pkill -f "uvicorn.*api.main:app" 2>/dev/null || true
pkill -f "uvicorn api.main:app" 2>/dev/null || true
pkill -f "load_balancer.py" 2>/dev/null || true
pkill -f "load_balancer:app" 2>/dev/null || true

# 如果进程仍然存在，使用更强力的终止
sleep 3
if pgrep -f "uvicorn.*api.main:app\|uvicorn api.main:app\|api.main:app" > /dev/null 2>&1; then
    echo "   🔴 强制终止 Worker 进程..."
    pkill -9 -f "uvicorn.*api.main:app" 2>/dev/null || true
    pkill -9 -f "uvicorn api.main:app" 2>/dev/null || true
    pkill -9 -f "api.main:app" 2>/dev/null || true
fi

if pgrep -f "load_balancer.py\|load_balancer:app" > /dev/null 2>&1; then
    echo "   🔴 强制终止负载均衡器进程..."
    pkill -9 -f "load_balancer.py" 2>/dev/null || true
    pkill -9 -f "load_balancer:app" 2>/dev/null || true
fi

# 最后尝试终止所有可能的 uvicorn 进程
if pgrep -f "uvicorn" > /dev/null 2>&1; then
    echo "   🔴 终止所有 uvicorn 进程..."
    pkill -9 -f "uvicorn" 2>/dev/null || true
fi

sleep 2

# 最终检查
echo "🔵 最终检查..."
if pgrep -f "uvicorn.*api.main:app\|uvicorn api.main:app\|api.main:app" > /dev/null 2>&1; then
    echo "   ❌ 仍有 Worker 进程在运行:"
    pgrep -f "uvicorn.*api.main:app\|uvicorn api.main:app\|api.main:app" | while read -r pid; do
        echo "     Worker 进程: $pid"
    done
    echo "   ⚠️  请手动检查并终止这些进程"
    echo "   💡 可以运行: ps aux | grep -E '(uvicorn|api.main)' | grep -v grep"
else
    echo "   ✅ 所有 Worker 进程已停止"
fi

if pgrep -f "load_balancer.py\|load_balancer:app" > /dev/null 2>&1; then
    echo "   ❌ 仍有负载均衡器进程在运行:"
    pgrep -f "load_balancer.py\|load_balancer:app" | while read -r pid; do
        echo "     负载均衡器进程: $pid"
    done
    echo "   ⚠️  请手动检查并终止这些进程"
    echo "   💡 可以运行: ps aux | grep -E '(load_balancer)' | grep -v grep"
else
    echo "   ✅ 所有负载均衡器进程已停止"
fi

# 检查是否还有其他相关进程
if pgrep -f "uvicorn" > /dev/null 2>&1; then
    echo "   ⚠️  发现其他 uvicorn 进程:"
    pgrep -f "uvicorn" | while read -r pid; do
        echo "     uvicorn 进程: $pid"
    done
    echo "   💡 这些可能是其他服务的进程，请确认是否需要终止"
fi

echo ""
echo "🎉 多 Worker + 负载均衡器停止完成！"
