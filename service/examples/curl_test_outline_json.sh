#!/bin/bash

# 测试outline JSON API端点的curl脚本

echo "🚀 开始测试outline JSON API端点"

# API基础URL
BASE_URL="http://localhost:8000"

# 测试健康检查
echo "📋 测试健康检查端点..."
curl -X GET "${BASE_URL}/health" \
  -H "Content-Type: application/json" \
  -w "\n状态码: %{http_code}\n"

echo -e "\n"

# 准备outline JSON数据
OUTLINE_JSON='{
  "title": "人工智能技术发展报告",
  "nodes": [
    {
      "id": "node_1",
      "title": "引言",
      "content_summary": "介绍人工智能的基本概念和发展背景"
    },
    {
      "id": "node_2",
      "title": "人工智能发展历史", 
      "content_summary": "从图灵测试到深度学习的演进历程"
    },
    {
      "id": "node_3",
      "title": "当前技术现状",
      "content_summary": "机器学习、深度学习、自然语言处理等技术的现状"
    },
    {
      "id": "node_4",
      "title": "未来发展趋势",
      "content_summary": "AI技术的未来发展方向和挑战"
    }
  ]
}'

# 准备请求数据
REQUEST_DATA='{
  "job_id": "test_outline_json_001",
  "outline_json": '"$(echo "$OUTLINE_JSON" | jq -c .)"',
  "session_id": "session_001"
}'

echo "📋 测试outline JSON文档生成端点..."
echo "请求数据:"
echo "$REQUEST_DATA" | jq .

echo -e "\n发送请求..."

# 发送POST请求
curl -X POST "${BASE_URL}/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_DATA" \
  -w "\n状态码: %{http_code}\n"

echo -e "\n✅ 测试完成！" 