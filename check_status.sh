#!/bin/bash

# =================================================================
# AIDocGenerator - 服务状态检查脚本
# =================================================================

echo "🔍 AIDocGenerator 服务状态检查"
echo "=============================="

# 检查 Redis 服务
echo "📊 Redis 服务状态:"

# 从配置文件读取Redis配置
REDIS_CONFIG=$(cd service && python -c "
import sys
sys.path.append('src')
from doc_agent.core.config import settings
config = settings.redis_config
print(f'{config[\"host\"]}:{config[\"port\"]}:{config.get(\"password\", \"\")}')
" 2>/dev/null)

if [ $? -eq 0 ]; then
    IFS=':' read -r REDIS_HOST REDIS_PORT REDIS_PASSWORD <<< "$REDIS_CONFIG"
    echo "   - 📋 配置的Redis: $REDIS_HOST:$REDIS_PORT"
    
    # 判断是本地还是远程Redis
    if [[ "$REDIS_HOST" == "127.0.0.1" || "$REDIS_HOST" == "localhost" ]]; then
        echo "   - 🏠 类型: 本地Redis"
    else
        echo "   - 🌐 类型: 远程Redis"
    fi
    
    # 检查配置的Redis服务器
    if [ -n "$REDIS_PASSWORD" ]; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
            echo "   - ✅ Redis 服务正常运行"
            # 获取 Redis 信息
            REDIS_INFO=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" info server | grep "redis_version\|uptime_in_seconds\|connected_clients")
            echo "   - 📋 Redis 信息:"
            echo "$REDIS_INFO" | while read line; do
                if [[ -n "$line" ]]; then
                    echo "     $line"
                fi
            done
        else
            echo "   - ❌ 配置的Redis服务未运行"
        fi
    else
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
            echo "   - ✅ Redis 服务正常运行"
            # 获取 Redis 信息
            REDIS_INFO=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info server | grep "redis_version\|uptime_in_seconds\|connected_clients")
            echo "   - 📋 Redis 信息:"
            echo "$REDIS_INFO" | while read line; do
                if [[ -n "$line" ]]; then
                    echo "     $line"
                fi
            done
        else
            echo "   - ❌ 配置的Redis服务未运行"
        fi
    fi
else
    echo "   - ⚠️  无法读取Redis配置，检查本地Redis"
    if redis-cli ping > /dev/null 2>&1; then
        echo "   - ✅ 本地Redis服务正常运行"
    else
        echo "   - ❌ 本地Redis服务未运行"
    fi
fi

echo ""

# 检查 conda 环境
echo "📊 Conda 环境状态:"
if command -v conda &> /dev/null; then
    if [[ "$CONDA_DEFAULT_ENV" == "ai-doc" ]]; then
        echo "   - ✅ 当前在 ai-doc 环境"
    else
        echo "   - ⚠️  当前环境: $CONDA_DEFAULT_ENV (建议使用 ai-doc)"
    fi
else
    echo "   - ❌ conda 未安装"
fi

echo ""

# 检查 API 服务
echo "📊 API 服务状态:"
API_PIDS=$(ps aux | grep "uvicorn api.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$API_PIDS" ]; then
    echo "   - ✅ API 服务正在运行 (PID: $API_PIDS)"
    # 检查端口
    for pid in $API_PIDS; do
        PORT=$(netstat -tlnp 2>/dev/null | grep "$pid" | awk '{print $4}' | sed 's/.*://')
        if [ -n "$PORT" ]; then
            echo "   - 📍 端口: $PORT"
            # 测试 API 健康检查
            if curl -s http://127.0.0.1:8080/api/v1/health > /dev/null; then
                echo "   - ✅ API 健康检查通过"
            else
                echo "   - ⚠️  API 健康检查失败"
            fi
        fi
    done
else
    echo "   - ❌ API 服务未运行"
fi

echo ""

# 检查 Celery Worker
echo "📊 Celery Worker 状态:"
CELERY_PIDS=$(ps aux | grep "celery_worker" | grep -v grep | awk '{print $2}')
if [ -n "$CELERY_PIDS" ]; then
    echo "   - ✅ Celery Worker 正在运行 (PID: $CELERY_PIDS)"
    # 统计 worker 数量
    WORKER_COUNT=$(echo "$CELERY_PIDS" | wc -w)
    echo "   - 📊 Worker 数量: $WORKER_COUNT"
else
    echo "   - ❌ Celery Worker 未运行"
fi

echo ""

# 检查日志文件
echo "📊 日志文件状态:"
if [ -f "output.log" ]; then
    LOG_SIZE=$(du -h output.log | cut -f1)
    LOG_LINES=$(wc -l < output.log)
    echo "   - 📄 output.log: $LOG_SIZE, $LOG_LINES 行"
else
    echo "   - ❌ output.log 不存在"
fi

if [ -f "celery_worker.log" ]; then
    LOG_SIZE=$(du -h celery_worker.log | cut -f1)
    LOG_LINES=$(wc -l < celery_worker.log)
    echo "   - 📄 celery_worker.log: $LOG_SIZE, $LOG_LINES 行"
else
    echo "   - ❌ celery_worker.log 不存在"
fi

echo ""

# 检查端口占用
echo "📊 端口占用情况:"
PORTS=$(netstat -tlnp 2>/dev/null | grep "127.0.0.1" | grep "LISTEN" | awk '{print $4}' | sed 's/127.0.0.1://')
if [ -n "$PORTS" ]; then
    echo "   - 📍 本地监听端口:"
    echo "$PORTS" | while read port; do
        if [[ -n "$port" ]]; then
            echo "     $port"
        fi
    done
else
    echo "   - ℹ️  无本地监听端口"
fi

echo ""

# 总体状态
echo "📊 总体状态:"
REDIS_OK=$(redis-cli ping > /dev/null 2>&1 && echo "1" || echo "0")
API_OK=$(ps aux | grep "uvicorn api.main:app" | grep -v grep | wc -l)
CELERY_OK=$(ps aux | grep "celery_worker" | grep -v grep | wc -l)

if [ $REDIS_OK -eq 1 ] && [ $API_OK -gt 0 ] && [ $CELERY_OK -gt 0 ]; then
    echo "   - ✅ 所有服务正常运行"
    echo "   - 🎉 系统状态良好"
elif [ $REDIS_OK -eq 0 ]; then
    echo "   - ❌ Redis 服务异常"
elif [ $API_OK -eq 0 ]; then
    echo "   - ❌ API 服务异常"
elif [ $CELERY_OK -eq 0 ]; then
    echo "   - ❌ Celery Worker 异常"
else
    echo "   - ⚠️  部分服务异常"
fi

echo ""
echo "📝 常用命令:"
echo "   - 启动服务: ./quick_start.sh"
echo "   - 停止服务: ./stop_dev_server.sh"
echo "   - 查看日志: tail -f output.log"
echo "   - 健康检查: curl http://127.0.0.1:8080/api/v1/health" 