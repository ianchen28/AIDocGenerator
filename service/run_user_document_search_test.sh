#!/bin/bash

# 用户文档范围搜索功能测试脚本

echo "🧪 开始测试用户文档范围搜索功能"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "src/doc_agent/core/config.py" ]; then
    echo "❌ 错误：请在service目录下运行此脚本"
    exit 1
fi

# 激活conda环境
echo "🔧 激活conda环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate ai-doc

if [ $? -ne 0 ]; then
    echo "❌ 激活conda环境失败"
    exit 1
fi

echo "✅ conda环境激活成功"

# 运行测试
echo "🚀 运行用户文档范围搜索测试..."
python examples/test_user_document_search.py

if [ $? -eq 0 ]; then
    echo "✅ 测试完成！"
else
    echo "❌ 测试失败！"
    exit 1
fi
