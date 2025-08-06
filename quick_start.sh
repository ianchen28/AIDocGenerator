#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本
# =================================================================

# 默认端口
DEFAULT_PORT=8000

# 解析命令行参数
PORT=${1:-$DEFAULT_PORT}

echo "🚀 启动 AI 文档生成器服务..."
echo "端口: $PORT"
echo ""

# --- 步骤 1: 检查系统依赖 ---
echo "🔵 Step 1: 检查系统依赖..."

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "   - ❌ conda 未安装，请先安装 conda"
    exit 1
fi

# 检查Redis配置
echo "   - 📋 检查Redis配置..."
REDIS_CONFIG=$(cd service && python -c "
import sys
sys.path.append('src')
from doc_agent.core.config import settings
config = settings.redis_config
print(f'{config[\"host\"]}:{config[\"port\"]}')
" 2>/dev/null)

if [ $? -eq 0 ]; then
    IFS=':' read -r REDIS_HOST REDIS_PORT <<< "$REDIS_CONFIG"
    echo "   - 📍 当前Redis配置: $REDIS_HOST:$REDIS_PORT"
    
    if [[ "$REDIS_HOST" == "127.0.0.1" || "$REDIS_HOST" == "localhost" ]]; then
        echo "   - ℹ️  使用本地Redis (如需远程Redis，请运行: ./config_redis.sh)"
    else
        echo "   - ℹ️  使用远程Redis (如需本地Redis，请运行: ./config_redis.sh)"
    fi
else
    echo "   - ⚠️  无法读取Redis配置，使用默认配置"
fi

# 检查Redis是否运行（只检查本地Redis，远程Redis在服务启动时检查）
if ! redis-cli ping > /dev/null 2>&1; then
    echo "   - ⚠️  本地Redis未运行（不影响远程Redis使用）"
else
    echo "   - ✅ 本地Redis服务正常运行"
fi

# --- 步骤 2: 激活 conda 环境 ---
echo "🔵 Step 2: 激活 conda 环境..."
if ! conda activate ai-doc 2>/dev/null; then
    echo "   - ⚠️  尝试手动激活环境..."
    source ~/miniforge3/etc/profile.d/conda.sh
    if ! conda activate ai-doc; then
        echo "   - ❌ 无法激活 ai-doc 环境"
        echo "   - 请确保已创建 ai-doc 环境: conda create -n ai-doc python=3.12"
        exit 1
    fi
fi
echo "   - ✅ ai-doc 环境已激活"

# --- 步骤 3: 安装依赖 ---
echo "🔵 Step 3: 安装项目依赖..."
cd service
if ! pip install -e . -i https://mirrors.aliyun.com/pypi/simple/ > /dev/null 2>&1; then
    echo "   - ❌ 依赖安装失败"
    exit 1
fi
cd ..
echo "   - ✅ 依赖安装完成"

# --- 步骤 4: 启动服务 ---
echo "🔵 Step 4: 启动开发服务器..."
echo "   - 使用端口: $PORT"
echo "   - 服务地址: http://127.0.0.1:$PORT"
echo "   - API文档: http://127.0.0.1:$PORT/docs"

# 启动服务并传递端口参数
nohup ./start_dev_server.sh $PORT > output.log 2>&1 &
SERVER_PID=$!
echo "   - ✅ 服务已启动，PID: $SERVER_PID"
echo "   - 查看日志: tail -f output.log"

# 等待服务启动
echo "   - ⏳ 等待服务启动..."
sleep 3

# 检查服务是否成功启动
if curl -s http://127.0.0.1:$PORT/ > /dev/null; then
    echo "   - ✅ 服务启动成功"
else
    echo "   - ⚠️  服务可能还在启动中，请稍等片刻"
fi

echo ""
echo "🎉 启动完成！"
echo "📝 使用说明:"
echo "   - 测试API: curl http://127.0.0.1:$PORT/api/v1/health"
echo "   - 查看文档: http://127.0.0.1:$PORT/docs"
echo "   - 停止服务: kill $SERVER_PID"
echo "   - 查看日志: tail -f output.log"