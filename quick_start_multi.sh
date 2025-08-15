#!/bin/bash

# 一键启动多 Worker + 负载均衡器
# 使用方法: ./quick_start_multi.sh <worker_num> [lb_port]
# 示例: ./quick_start_multi.sh 4 8082

set -e

# 默认配置 - 只需要修改这里的端口即可
DEFAULT_WORKERS=2
BASE_PORT=8000
LB_PORT=8081  # 负载均衡器端口，可以改为 8082, 8083, 9000 等
UNIFIED_LOG="logs/app.log"

# 获取参数
NUM_WORKERS=${1:-$DEFAULT_WORKERS}
LB_PORT=${2:-$LB_PORT}  # 支持命令行指定负载均衡器端口

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

echo "🚀 一键启动多 Worker + 负载均衡器"
echo "=================================================="
echo "Worker 数量: $NUM_WORKERS"
echo "Worker 端口范围: $BASE_PORT - $((BASE_PORT + NUM_WORKERS - 1))"
echo "负载均衡器端口: $LB_PORT"
echo ""

# 创建必要的目录
mkdir -p logs output

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
if [ -f "logs/multi_worker.pid" ]; then
    echo "   - 停止旧的 Worker 进程..."
    while read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
            echo "     🛑 终止 Worker 进程 PID: $pid"
        fi
    done < "logs/multi_worker.pid"
    rm -f "logs/multi_worker.pid"
fi

if [ -f "logs/load_balancer.pid" ]; then
    echo "   - 停止旧的负载均衡器进程..."
    read -r pid < "logs/load_balancer.pid"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null
        echo "     🛑 终止负载均衡器进程 PID: $pid"
    fi
    rm -f "logs/load_balancer.pid"
fi

# 清理残留进程
echo "   - 清理残留进程..."
pkill -f "uvicorn.*api.main:app" 2>/dev/null || true
pkill -f "uvicorn api.main:app" 2>/dev/null || true
pkill -f "load_balancer.py" 2>/dev/null || true
pkill -f "load_balancer:app" 2>/dev/null || true

# 如果进程仍然存在，使用更强力的终止
sleep 3
if pgrep -f "uvicorn.*api.main:app\|uvicorn api.main:app\|api.main:app" > /dev/null 2>&1; then
    echo "     🔴 强制终止 Worker 进程..."
    pkill -9 -f "uvicorn.*api.main:app" 2>/dev/null || true
    pkill -9 -f "uvicorn api.main:app" 2>/dev/null || true
    pkill -9 -f "api.main:app" 2>/dev/null || true
fi

if pgrep -f "load_balancer.py\|load_balancer:app" > /dev/null 2>&1; then
    echo "     🔴 强制终止负载均衡器进程..."
    pkill -9 -f "load_balancer.py" 2>/dev/null || true
    pkill -9 -f "load_balancer:app" 2>/dev/null || true
fi

sleep 2

# 启动 Worker 进程
echo "🔵 启动 $NUM_WORKERS 个 Worker..."
WORKER_PIDS=()

for ((i=0; i<NUM_WORKERS; i++)); do
    WORKER_PORT=$((BASE_PORT + i))
    echo "   - 启动 Worker $((i+1))/$NUM_WORKERS (端口: $WORKER_PORT)..."
    
    # 启动 worker 进程
    (cd service && nohup uvicorn api.main:app --host 0.0.0.0 --port "$WORKER_PORT" --workers 1 >> "../$UNIFIED_LOG" 2>&1) &
    WORKER_PID=$!
    WORKER_PIDS+=($WORKER_PID)
    
    echo "   ✅ Worker $((i+1)) 已启动，PID: $WORKER_PID"
    sleep 2
done

# 保存 Worker PID
echo "${WORKER_PIDS[@]}" > "logs/multi_worker.pid"

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

nohup python load_balancer.py >> "$UNIFIED_LOG" 2>&1 &
LB_PID=$!

# 保存负载均衡器 PID
echo "$LB_PID" > "logs/load_balancer.pid"

echo "   ✅ 负载均衡器已启动，PID: $LB_PID"

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
echo ""
echo "💡 管理命令:"
echo "   - 查看日志: tail -f $UNIFIED_LOG"
echo "   - 查看进程: ps aux | grep -E '(uvicorn|load_balancer)'"
echo "   - 停止服务: ./stop_multi.sh"
echo "   - 性能测试: python simple_log_test.py"
echo ""
echo "✅ 所有服务已在后台运行，支持高并发处理"
echo "✅ 可以安全关闭终端。"
