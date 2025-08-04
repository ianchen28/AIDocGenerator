#!/bin/bash

# 测试大纲生成API的curl命令

echo "🧪 测试大纲生成API"
echo "=================="

# 设置API基础URL
API_BASE_URL="http://localhost:8000/api/v1"

# 测试1: 基本大纲生成请求
echo ""
echo "📝 测试1: 基本大纲生成请求"
curl -X POST "${API_BASE_URL}/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_001",
    "taskPrompt": "请为我生成一份关于人工智能在医疗领域应用的详细大纲，包括技术原理、应用场景、发展趋势等内容",
    "isOnline": true,
    "contextFiles": []
  }' \
  -w "\nHTTP状态码: %{http_code}\n响应时间: %{time_total}s\n"

echo ""
echo "=================="

# 测试2: 带上下文文件的大纲生成请求
echo ""
echo "📝 测试2: 带上下文文件的大纲生成请求"
curl -X POST "${API_BASE_URL}/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_002",
    "taskPrompt": "基于提供的参考资料，生成一份关于区块链技术在供应链管理中的应用大纲",
    "isOnline": false,
    "contextFiles": [
      {
        "file_id": "file_001",
        "file_name": "blockchain_guide.pdf",
        "storage_url": "https://example.com/files/blockchain_guide.pdf",
        "file_type": "content"
      }
    ],
    "attachmentType": 1,
    "attachmentFileToken": "token_123456",
    "isContentRefer": 1,
    "isStyleImitative": 0,
    "isWritingRequirement": 1
  }' \
  -w "\nHTTP状态码: %{http_code}\n响应时间: %{time_total}s\n"

echo ""
echo "=================="

# 测试3: 学术论文大纲生成
echo ""
echo "📝 测试3: 学术论文大纲生成"
curl -X POST "${API_BASE_URL}/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_003",
    "taskPrompt": "生成一份关于机器学习在金融风控中的应用研究论文大纲，要求包含文献综述、方法论、实验设计、结果分析等章节",
    "isOnline": true,
    "contextFiles": [],
    "attachmentType": 0,
    "isContentRefer": 0,
    "isStyleImitative": 1,
    "isWritingRequirement": 1
  }' \
  -w "\nHTTP状态码: %{http_code}\n响应时间: %{time_total}s\n"

echo ""
echo "=================="

# 测试4: 健康检查
echo ""
echo "🏥 健康检查"
curl -X GET "http://localhost:8000/" \
  -w "\nHTTP状态码: %{http_code}\n响应时间: %{time_total}s\n"

curl -X GET "${API_BASE_URL}/health" \
  -w "\nHTTP状态码: %{http_code}\n响应时间: %{time_total}s\n"

echo ""
echo "✅ 测试完成！"
echo ""
echo "💡 提示："
echo "1. 确保API服务器正在运行 (默认端口8000)"
echo "2. 确保Celery worker正在运行"
echo "3. 确保Redis服务正在运行"
echo "4. 查看返回的redisStreamKey来监听任务进度" 