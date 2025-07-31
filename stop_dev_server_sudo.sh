#!/bin/bash

# =================================================================
# AIDocGenerator - 停止开发环境脚本 (sudo 版本)
# =================================================================

echo "🔴 正在停止 AI 文档生成器服务 (使用 sudo 权限)..."

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 此脚本需要 sudo 权限运行"
    echo "💡 请使用: sudo ./stop_dev_server_sudo.sh"
    exit 1
fi

# 查找并停止所有 uvicorn 进程
echo "📋 查找所有 uvicorn 进程..."
UVICORN_PIDS=$(ps aux | grep "uvicorn api.main:app" | grep -v grep | awk '{print $2}')

if [ -n "$UVICORN_PIDS" ]; then
    echo "   - 找到 uvicorn 进程: $UVICORN_PIDS"
    for pid in $UVICORN_PIDS; do
        echo "   - 停止 uvicorn 进程 (PID: $pid)..."
        if kill $pid 2>/dev/null; then
            echo "   - ✅ uvicorn 进程 (PID: $pid) 已停止"
        else
            echo "   - ❌ 无法停止 uvicorn 进程 (PID: $pid)"
        fi
        sleep 1
    done
else
    echo "   - ⚠️  未找到 uvicorn 进程"
fi

# 查找并停止所有 Celery Worker 进程
echo "📋 查找所有 Celery Worker 进程..."
CELERY_PIDS=$(ps aux | grep "celery.*worker" | grep -v grep | awk '{print $2}')

if [ -n "$CELERY_PIDS" ]; then
    echo "   - 找到 Celery Worker 进程: $CELERY_PIDS"
    for pid in $CELERY_PIDS; do
        echo "   - 停止 Celery Worker 进程 (PID: $pid)..."
        if kill $pid 2>/dev/null; then
            echo "   - ✅ Celery Worker 进程 (PID: $pid) 已停止"
        else
            echo "   - ❌ 无法停止 Celery Worker 进程 (PID: $pid)"
        fi
        sleep 1
    done
else
    echo "   - ⚠️  未找到 Celery Worker 进程"
fi

# 查找并停止所有启动脚本进程
echo "📋 查找所有启动脚本进程..."
SCRIPT_PIDS=$(ps aux | grep "start_dev_server_alt_port.sh" | grep -v grep | awk '{print $2}')

if [ -n "$SCRIPT_PIDS" ]; then
    echo "   - 找到启动脚本进程: $SCRIPT_PIDS"
    for pid in $SCRIPT_PIDS; do
        echo "   - 停止启动脚本进程 (PID: $pid)..."
        if kill $pid 2>/dev/null; then
            echo "   - ✅ 启动脚本进程 (PID: $pid) 已停止"
        else
            echo "   - ❌ 无法停止启动脚本进程 (PID: $pid)"
        fi
        sleep 1
    done
else
    echo "   - ⚠️  未找到启动脚本进程"
fi

# 检查端口占用情况
echo "📋 检查端口占用情况..."
PORT_8001=$(netstat -tlnp 2>/dev/null | grep :8001 || echo "")
if [ -n "$PORT_8001" ]; then
    echo "   - ⚠️  端口 8001 仍被占用:"
    echo "     $PORT_8001"
    echo "   - 💡 尝试强制释放端口..."
    # 尝试强制终止占用端口的进程
    PORT_PID=$(echo "$PORT_8001" | awk '{print $7}' | cut -d'/' -f1)
    if [ -n "$PORT_PID" ] && [ "$PORT_PID" != "-" ]; then
        echo "   - 强制终止占用端口的进程 (PID: $PORT_PID)..."
        kill -9 $PORT_PID 2>/dev/null
    fi
else
    echo "   - ✅ 端口 8001 已释放"
fi

# 显示当前状态
echo ""
echo "📊 服务状态检查:"
echo "   - uvicorn 进程: $(ps aux | grep "uvicorn api.main:app" | grep -v grep | wc -l) 个"
echo "   - Celery Worker 进程: $(ps aux | grep "celery.*worker" | grep -v grep | wc -l) 个"
echo "   - 启动脚本进程: $(ps aux | grep "start_dev_server_alt_port.sh" | grep -v grep | wc -l) 个"

echo ""
echo "✅ 服务停止完成！"
echo "📝 日志文件位置: output.log"
echo "🔍 查看日志: tail -f output.log" 