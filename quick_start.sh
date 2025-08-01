#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本
# =================================================================

echo "🚀 启动 AI 文档生成器服务..."

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
nohup ./start_dev_server_alt_port.sh > output.log 2>&1 &
SERVER_PID=$!
echo "   - ✅ 服务已启动，PID: $SERVER_PID"
echo "   - 服务地址: http://127.0.0.1:8001"
echo "   - 查看日志: tail -f output.log"

echo ""
echo "🎉 启动完成！"