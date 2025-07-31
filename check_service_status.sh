#!/bin/bash

# =================================================================
# AIDocGenerator - 检查服务状态脚本
# =================================================================

echo "🔍 检查 AI 文档生成器服务状态..."
echo ""

# 检查 uvicorn 进程
echo "📋 uvicorn 进程状态:"
UVICORN_PIDS=$(ps aux | grep "uvicorn api.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$UVICORN_PIDS" ]; then
    echo "   - ✅ 运行中 (PID: $UVICORN_PIDS)"
    ps aux | grep "uvicorn api.main:app" | grep -v grep | awk '{print "     " $2 " " $11 " " $12 " " $13}'
else
    echo "   - ❌ 未运行"
fi

echo ""

# 检查 Celery Worker 进程
echo "📋 Celery Worker 进程状态:"
CELERY_PIDS=$(ps aux | grep "celery.*worker" | grep -v grep | awk '{print $2}')
if [ -n "$CELERY_PIDS" ]; then
    echo "   - ✅ 运行中 (PID: $CELERY_PIDS)"
    ps aux | grep "celery.*worker" | grep -v grep | awk '{print "     " $2 " " $11 " " $12 " " $13}'
else
    echo "   - ❌ 未运行"
fi

echo ""

# 检查启动脚本进程
echo "📋 启动脚本进程状态:"
SCRIPT_PIDS=$(ps aux | grep "start_dev_server_alt_port.sh" | grep -v grep | awk '{print $2}')
if [ -n "$SCRIPT_PIDS" ]; then
    echo "   - ✅ 运行中 (PID: $SCRIPT_PIDS)"
    ps aux | grep "start_dev_server_alt_port.sh" | grep -v grep | awk '{print "     " $2 " " $11 " " $12 " " $13}'
else
    echo "   - ❌ 未运行"
fi

echo ""

# 检查端口占用
echo "📋 端口占用情况:"
PORT_8001=$(netstat -tlnp 2>/dev/null | grep :8001 || echo "")
if [ -n "$PORT_8001" ]; then
    echo "   - ✅ 端口 8001 被占用:"
    echo "     $PORT_8001"
else
    echo "   - ❌ 端口 8001 未被占用"
fi

echo ""

# 检查 Redis 服务
echo "📋 Redis 服务状态:"
if redis-cli ping > /dev/null 2>&1; then
    echo "   - ✅ Redis 服务运行正常"
else
    echo "   - ❌ Redis 服务未运行或无法连接"
fi

echo ""

# 检查日志文件
echo "📋 日志文件状态:"
if [ -f "output.log" ]; then
    LOG_SIZE=$(ls -lh output.log | awk '{print $5}')
    LOG_LINES=$(wc -l < output.log)
    echo "   - ✅ output.log 存在 (大小: $LOG_SIZE, 行数: $LOG_LINES)"
    echo "   - 📝 最后 5 行日志:"
    tail -5 output.log | sed 's/^/     /'
else
    echo "   - ❌ output.log 不存在"
fi

echo ""

# 测试 API 连接
echo "📋 API 连接测试:"
if curl -s http://10.215.58.199:8001/api/v1/health > /dev/null 2>&1; then
    echo "   - ✅ API 服务响应正常"
    HEALTH_RESPONSE=$(curl -s http://10.215.58.199:8001/api/v1/health)
    echo "   - 📊 健康检查响应: $HEALTH_RESPONSE"
else
    echo "   - ❌ API 服务无响应"
fi

echo ""
echo "✅ 状态检查完成！" 