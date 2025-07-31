#!/bin/bash

# =================================================================
# AIDocGenerator - 停止开发环境脚本
# =================================================================

echo "🔴 正在停止 AI 文档生成器服务..."

# 获取当前用户
CURRENT_USER=$(whoami)
echo "👤 当前用户: $CURRENT_USER"

# 查找并停止 uvicorn 进程（只处理当前用户的进程）
echo "📋 查找 uvicorn 进程..."
UVICORN_PIDS=$(ps aux | grep "uvicorn api.main:app" | grep -v grep | awk -v user="$CURRENT_USER" '$1 == user {print $2}')

if [ -n "$UVICORN_PIDS" ]; then
    echo "   - 找到当前用户的 uvicorn 进程: $UVICORN_PIDS"
    for pid in $UVICORN_PIDS; do
        echo "   - 停止 uvicorn 进程 (PID: $pid)..."
        if kill $pid 2>/dev/null; then
            echo "   - ✅ uvicorn 进程 (PID: $pid) 已停止"
        else
            echo "   - ❌ 无法停止 uvicorn 进程 (PID: $pid) - 权限不足"
        fi
        sleep 1
    done
else
    echo "   - ⚠️  未找到当前用户的 uvicorn 进程"
fi

# 查找并停止 Celery Worker 进程（只处理当前用户的进程）
echo "📋 查找 Celery Worker 进程..."
CELERY_PIDS=$(ps aux | grep "celery.*worker" | grep -v grep | awk -v user="$CURRENT_USER" '$1 == user {print $2}')

if [ -n "$CELERY_PIDS" ]; then
    echo "   - 找到当前用户的 Celery Worker 进程: $CELERY_PIDS"
    for pid in $CELERY_PIDS; do
        echo "   - 停止 Celery Worker 进程 (PID: $pid)..."
        if kill $pid 2>/dev/null; then
            echo "   - ✅ Celery Worker 进程 (PID: $pid) 已停止"
        else
            echo "   - ❌ 无法停止 Celery Worker 进程 (PID: $pid) - 权限不足"
        fi
        sleep 1
    done
else
    echo "   - ⚠️  未找到当前用户的 Celery Worker 进程"
fi

# 查找并停止启动脚本进程（只处理当前用户的进程）
echo "📋 查找启动脚本进程..."
SCRIPT_PIDS=$(ps aux | grep "start_dev_server_alt_port.sh" | grep -v grep | awk -v user="$CURRENT_USER" '$1 == user {print $2}')

if [ -n "$SCRIPT_PIDS" ]; then
    echo "   - 找到当前用户的启动脚本进程: $SCRIPT_PIDS"
    for pid in $SCRIPT_PIDS; do
        echo "   - 停止启动脚本进程 (PID: $pid)..."
        if kill $pid 2>/dev/null; then
            echo "   - ✅ 启动脚本进程 (PID: $pid) 已停止"
        else
            echo "   - ❌ 无法停止启动脚本进程 (PID: $pid) - 权限不足"
        fi
        sleep 1
    done
else
    echo "   - ⚠️  未找到当前用户的启动脚本进程"
fi

# 检查端口占用情况
echo "📋 检查端口占用情况..."
PORT_8001=$(netstat -tlnp 2>/dev/null | grep :8001 || echo "")
if [ -n "$PORT_8001" ]; then
    echo "   - ⚠️  端口 8001 仍被占用:"
    echo "     $PORT_8001"
    echo "   - 💡 提示: 如果端口仍被占用，可能需要使用 sudo 权限"
else
    echo "   - ✅ 端口 8001 已释放"
fi

# 显示当前状态
echo ""
echo "📊 服务状态检查:"
echo "   - 当前用户的 uvicorn 进程: $(ps aux | grep "uvicorn api.main:app" | grep -v grep | awk -v user="$CURRENT_USER" '$1 == user' | wc -l) 个"
echo "   - 当前用户的 Celery Worker 进程: $(ps aux | grep "celery.*worker" | grep -v grep | awk -v user="$CURRENT_USER" '$1 == user' | wc -l) 个"
echo "   - 当前用户的启动脚本进程: $(ps aux | grep "start_dev_server_alt_port.sh" | grep -v grep | awk -v user="$CURRENT_USER" '$1 == user' | wc -l) 个"

echo ""
echo "✅ 服务停止完成！"
echo "📝 日志文件位置: output.log"
echo "🔍 查看日志: tail -f output.log"

# 如果有其他用户的进程，给出提示
OTHER_UVICORN=$(ps aux | grep "uvicorn api.main:app" | grep -v grep | awk -v user="$CURRENT_USER" '$1 != user' | wc -l)
OTHER_CELERY=$(ps aux | grep "celery.*worker" | grep -v grep | awk -v user="$CURRENT_USER" '$1 != user' | wc -l)

if [ $OTHER_UVICORN -gt 0 ] || [ $OTHER_CELERY -gt 0 ]; then
    echo ""
    echo "⚠️  发现其他用户的进程:"
    echo "   - 其他用户的 uvicorn 进程: $OTHER_UVICORN 个"
    echo "   - 其他用户的 Celery Worker 进程: $OTHER_CELERY 个"
    echo "   - 💡 如需停止所有进程，请使用: sudo ./stop_dev_server.sh"
fi 