#!/bin/bash

# 启动模拟文档生成服务

echo "启动模拟文档生成服务..."

# 检查是否在正确的目录
if [ ! -f "mock_document_service.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Redis 是否运行
echo "检查 Redis 连接..."
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "警告: Redis 可能未运行，请确保 Redis 服务已启动"
    echo "可以使用以下命令启动 Redis:"
    echo "  brew services start redis  # macOS"
    echo "  sudo systemctl start redis  # Linux"
fi

# 创建日志目录
mkdir -p logs

# 启动服务
echo "启动模拟服务在端口 8001..."
python mock_document_service.py 