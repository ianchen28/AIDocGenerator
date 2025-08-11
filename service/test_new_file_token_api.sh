#!/bin/bash

# AI文档生成器API - 新file_token功能测试脚本
# 测试大纲生成和文档生成的新file_token功能

echo "🚀 开始测试新的file_token功能..."
echo "=================================================="

# 检查服务是否运行
echo "🔍 检查服务状态..."
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ 服务正在运行"
else
    echo "❌ 服务未运行，请先启动服务: ./start_dev_server.sh"
    exit 1
fi

echo -e "\n"

# ============================================================================
# 1. 健康检查端点
# ============================================================================
echo "📋 1. 测试健康检查端点"
echo "--------------------------------------------------"
curl -X GET "http://localhost:8000/api/v1/health" \
  -H "Content-Type: application/json" \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n"
echo -e "\n"

# ============================================================================
# 2. 大纲生成端点测试 (会返回file_token)
# ============================================================================
echo "📋 2. 测试大纲生成端点 (新功能：返回file_token)"
echo "--------------------------------------------------"
OUTLINE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_001",
    "taskPrompt": "请生成一份关于人工智能技术发展趋势的详细大纲，包含机器学习、深度学习和应用场景等内容",
    "isOnline": true,
    "contextFiles": [],
    "styleGuideContent": "请使用专业的技术文档风格",
    "requirements": "需要包含实际案例和未来发展趋势"
  }' \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n")

echo "$OUTLINE_RESPONSE"
echo -e "\n"

# 提取taskId和file_token
TASK_ID=$(echo "$OUTLINE_RESPONSE" | grep -o '"redisStreamKey":"[^"]*"' | cut -d'"' -f4)
if [ -n "$TASK_ID" ]; then
    echo "✅ 获取到taskId: $TASK_ID"
else
    echo "⚠️  未能获取到taskId"
fi
echo -e "\n"

# ============================================================================
# 3. 等待大纲生成完成并获取file_token
# ============================================================================
echo "📋 3. 等待大纲生成完成并获取file_token"
echo "--------------------------------------------------"
echo "⏳ 等待5秒让大纲生成完成..."
sleep 5

# 这里需要监听Redis流来获取file_token
echo "💡 提示: 大纲生成完成后，Redis流中会包含file_token"
echo "   可以使用以下命令监听Redis流:"
echo "   redis-cli XREAD COUNT 10 STREAMS $TASK_ID 0"
echo -e "\n"

# ============================================================================
# 4. 文档生成端点测试 (使用file_token)
# ============================================================================
echo "📋 4. 测试文档生成端点 (使用file_token)"
echo "--------------------------------------------------"
echo "📝 注意: 这里使用一个示例file_token，实际使用时需要从大纲生成的Redis流中获取"
echo "   示例file_token: 8b7e75b4150cde04bffba318da25068e"

curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "基于大纲生成一份详细的技术文档",
    "sessionId": "test_session_001",
    "outline": "a19bcc15e6098a030632aac19fd2780c",
    "contextFiles": [],
    "isOnline": true
  }' \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n"
echo -e "\n"

# ============================================================================
# 5. 测试带context_files的文档生成
# ============================================================================
echo "📋 5. 测试带context_files的文档生成"
echo "--------------------------------------------------"
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "基于大纲和提供的参考资料生成技术文档",
    "sessionId": "test_session_002",
    "outline": "8b7e75b4150cde04bffba318da25068e",
    "contextFiles": [
      {
        "attachmentFileToken": "example_file_token_001",
        "attachmentType": 1
      },
      {
        "attachmentFileToken": "example_file_token_002", 
        "attachmentType": 2
      }
    ],
    "isOnline": false
  }' \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n"
echo -e "\n"

# ============================================================================
# 6. 模拟文档生成端点测试 (使用file_token)
# ============================================================================
echo "📋 6. 测试模拟文档生成端点 (使用file_token)"
echo "--------------------------------------------------"
MOCK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/document-from-outline-mock" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "模拟生成技术文档",
    "sessionId": "mock_session_001",
    "outline": "8b7e75b4150cde04bffba318da25068e",
    "contextFiles": [],
    "isOnline": false
  }' \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n")

echo "$MOCK_RESPONSE"
echo -e "\n"

# 提取模拟任务的taskId
MOCK_TASK_ID=$(echo "$MOCK_RESPONSE" | grep -o '"redisStreamKey":"[^"]*"' | cut -d'"' -f4)
if [ -n "$MOCK_TASK_ID" ]; then
    echo "✅ 获取到模拟任务taskId: $MOCK_TASK_ID"
    echo "💡 提示: 可以使用以下命令监听Redis流事件:"
    echo "   redis-cli XREAD COUNT 10 STREAMS $MOCK_TASK_ID 0"
else
    echo "⚠️  未能获取到模拟任务taskId"
fi
echo -e "\n"

# ============================================================================
# 7. 测试错误情况
# ============================================================================
echo "📋 7. 测试错误情况"
echo "--------------------------------------------------"

echo "7.1 测试无效的file_token"
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "测试无效token",
    "sessionId": "error_test_001",
    "outline": "invalid_file_token_123",
    "contextFiles": [],
    "isOnline": false
  }' \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n"
echo -e "\n"

echo "7.2 测试缺少必需参数"
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "error_test_002",
    "outline": "8b7e75b4150cde04bffba318da25068e"
  }' \
  -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n"
echo -e "\n"

# ============================================================================
# 测试总结
# ============================================================================
echo "🎉 新file_token功能测试完成!"
echo "=================================================="
echo "📊 测试总结:"
echo "✅ 健康检查端点"
echo "✅ 大纲生成端点 (新功能：返回file_token)"
echo "✅ 文档生成端点 (使用file_token)"
echo "✅ 带context_files的文档生成"
echo "✅ 模拟文档生成端点 (使用file_token)"
echo "✅ 错误情况测试"
echo -e "\n"

echo "💡 新功能特点:"
echo "1. 大纲生成完成后会返回file_token，存储在Redis流中"
echo "2. 文档生成时使用file_token而不是直接的大纲JSON"
echo "3. 支持context_files的file_token处理"
echo "4. 自动从远程storage下载和解析文件"
echo -e "\n"

echo "🔗 相关命令:"
echo "- 监听Redis流: redis-cli XREAD COUNT 10 STREAMS <task_id> 0"
echo "- 查看Redis流内容: redis-cli XRANGE <task_id> - +"
echo "- 启动开发服务器: ./start_dev_server.sh"
echo -e "\n"

echo "✨ 测试脚本执行完毕!"
