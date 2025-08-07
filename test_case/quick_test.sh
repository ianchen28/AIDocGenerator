#!/bin/bash

# 快速API测试脚本
# 使用方法: ./quick_test.sh

echo "🚀 快速API测试开始..."
echo "=================================================="

# 检查服务状态
echo "🔍 检查服务状态..."
if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "❌ 服务未运行，请先启动: ./start_dev_server.sh"
    exit 1
fi
echo "✅ 服务正在运行"
echo -e "\n"

# 1. 健康检查
echo "📋 1. 健康检查"
curl -s -X GET "http://localhost:8000/api/v1/health" | jq .
echo -e "\n"

# 2. 大纲生成
echo "📋 2. 大纲生成"
OUTLINE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "123456789",
    "taskPrompt": "请生成一份关于人工智能技术发展趋势的详细大纲",
    "isOnline": true,
    "contextFiles": [],
    "attachmentType": 0,
    "attachmentFileToken": null,
    "isContentRefer": 0,
    "isStyleImitative": 0,
    "isWritingRequirement": 0
  }')
echo "$OUTLINE_RESPONSE" | jq .
echo -e "\n"

# 3. 模拟文档生成
echo "📋 3. 模拟文档生成"
MOCK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/document-from-outline/mock" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "999888777",
    "outline_json": "{\"title\":\"人工智能技术发展趋势\",\"nodes\":[{\"title\":\"人工智能概述\",\"contentSummary\":\"介绍人工智能的基本概念和发展历程\",\"children\":[]},{\"title\":\"核心技术发展\",\"contentSummary\":\"分析机器学习、深度学习等核心技术的最新进展\",\"children\":[{\"title\":\"机器学习技术\",\"contentSummary\":\"传统机器学习算法的发展\",\"children\":[]},{\"title\":\"深度学习技术\",\"contentSummary\":\"神经网络和深度学习的最新突破\",\"children\":[]}]},{\"title\":\"应用领域拓展\",\"contentSummary\":\"探讨AI在各个行业的应用现状和前景\",\"children\":[]}]}",
    "session_id": "999888777"
  }')
echo "$MOCK_RESPONSE" | jq .
echo -e "\n"

# 4. AI文本编辑 (润色)
echo "📋 4. AI文本编辑 (润色)"
curl -s -X POST "http://localhost:8000/api/v1/actions/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "polish",
    "text": "人工智能技术正在快速发展。",
    "polish_style": "professional"
  }' | head -c 200
echo "..."
echo -e "\n"

echo "🎉 快速测试完成!"
echo "💡 提示: 使用 ./run_api_tests.sh 进行完整测试"
