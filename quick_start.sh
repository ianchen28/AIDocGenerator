#!/bin/bash

# =================================================================
# AIDocGenerator - 快速启动脚本
# =================================================================

echo "🚀 启动 AI 文档生成器服务..."

# --- 步骤 1: 激活 conda 环境 ---
echo "🔵 Step 1: 激活 conda 环境..."

# 初始化 conda（如果需要）
if ! command -v conda &> /dev/null; then
    echo "   - ❌ Error: conda 命令未找到"
    echo "   - 请确保已安装 conda 并添加到 PATH"
    exit 1
fi

# 尝试激活环境
if ! conda activate ai-doc 2>/dev/null; then
    echo "   - ⚠️  无法直接激活 ai-doc 环境，尝试使用 source 方式..."
    # 尝试使用 source 方式激活
    if [ -f "$CONDA_PREFIX/etc/profile.d/conda.sh" ]; then
        source "$CONDA_PREFIX/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniforge3/etc/profile.d/conda.sh"
    else
        echo "   - ❌ Error: 无法找到 conda.sh 文件"
        echo "   - 请手动激活环境: conda activate ai-doc"
        exit 1
    fi
    
    # 再次尝试激活
    if ! conda activate ai-doc; then
        echo "   - ❌ Error: 无法激活 ai-doc 环境"
        echo "   - 请确保已创建 ai-doc 环境: conda create -n ai-doc python=3.12"
        echo "   - 或者手动激活环境后运行此脚本"
        exit 1
    fi
fi

echo "   - ✅ ai-doc 环境已激活"

# --- 步骤 2: 安装/更新依赖 ---
echo "🔵 Step 2: 安装/更新项目依赖..."
cd service
if ! pip install -e .; then
    echo "   - ❌ Error: 依赖安装失败"
    exit 1
else
    echo "   - ✅ 依赖安装完成"
fi
cd ..

# --- 步骤 3: 启动开发服务器 ---
echo "🔵 Step 3: 启动开发服务器..."
echo "   - 服务将在后台运行，日志输出到 output.log"
echo "   - 服务地址: http://127.0.0.1:8001"
echo "   - 查看日志: tail -f output.log"

# 启动服务到后台
nohup ./start_dev_server_alt_port.sh > output.log 2>&1 &

# 获取后台进程的 PID
SERVER_PID=$!
echo "   - ✅ 服务已启动，PID: $SERVER_PID"

# 等待几秒钟让服务完全启动
sleep 3

# 检查服务是否成功启动
if curl -s http://127.0.0.1:8001/api/v1/health > /dev/null 2>&1; then
    echo "   - ✅ 服务启动成功！"
    echo "   - 健康检查: http://127.0.0.1:8001/api/v1/health"
    echo "   - API 文档: http://127.0.0.1:8001/docs"
else
    echo "   - ⚠️  服务可能还在启动中，请稍等..."
    echo "   - 查看启动日志: tail -f output.log"
fi

echo ""
echo "🎉 启动完成！"
echo "📝 常用命令:"
echo "   - 查看日志: tail -f output.log"
echo "   - 停止服务: ./stop_dev_server.sh"
echo "   - 重启服务: ./quick_start.sh"