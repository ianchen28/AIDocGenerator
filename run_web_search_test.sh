#!/bin/bash

# Web搜索服务可用性测试运行脚本

echo "=== Web搜索服务可用性测试 ==="
echo "时间: $(date)"
echo ""

# 检查是否在正确的环境中
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到conda命令，请确保已安装conda"
    exit 1
fi

# 激活conda环境
echo "激活conda环境: ai-doc"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ai-doc

if [ $? -ne 0 ]; then
    echo "❌ 激活conda环境失败"
    exit 1
fi

echo "✅ 环境激活成功"
echo ""

# 检查Python路径
echo "检查Python环境:"
echo "  Python版本: $(python --version)"
echo "  当前目录: $(pwd)"
echo ""

# 创建logs目录（如果不存在）
mkdir -p logs

# 运行测试
echo "开始运行Web搜索可用性测试..."
echo ""

python test_web_search_availability.py

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 测试完成，服务运行正常"
else
    echo ""
    echo "❌ 测试完成，存在问题，请查看日志文件"
    echo "日志文件位置: logs/web_search_availability_test.log"
    echo "测试报告: web_search_test_report.json"
fi

echo ""
echo "测试完成时间: $(date)"
