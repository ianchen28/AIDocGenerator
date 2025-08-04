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

# --- 步骤 1: 激活 conda 环境 ---
echo "🔵 Step 1: 激活 conda 环境..."
if ! conda activate ai-doc 2>/dev/null; then
    echo "   - ⚠️  尝试手动激活环境..."
    source ~/miniforge3/etc/profile.d/conda.sh
    conda activate ai-doc
fi
echo "   - ✅ ai-doc 环境已激活"

# --- 步骤 2: 安装依赖 ---
echo "🔵 Step 2: 安装项目依赖..."
cd service
pip install -e . -i https://mirrors.aliyun.com/pypi/simple/
cd ..
echo "   - ✅ 依赖安装完成"

# --- 步骤 3: 启动服务 ---
echo "🔵 Step 3: 启动开发服务器..."
echo "   - 使用端口: $PORT"
echo "   - 服务地址: http://127.0.0.1:$PORT"
echo "   - API文档: http://127.0.0.1:$PORT/docs"

# 启动服务并传递端口参数
nohup ./start_dev_server.sh $PORT > output.log 2>&1 &
SERVER_PID=$!
echo "   - ✅ 服务已启动，PID: $SERVER_PID"
echo "   - 查看日志: tail -f output.log"

echo ""
echo "🎉 启动完成！"
echo "📝 使用说明:"
echo "   - 测试API: curl http://127.0.0.1:$PORT/api/v1/jobs/outline"
echo "   - 查看文档: http://127.0.0.1:$PORT/docs"
echo "   - 停止服务: kill $SERVER_PID"