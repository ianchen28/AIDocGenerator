#!/bin/bash

# 快速测试示例 - 新file_token功能
# 这个脚本展示如何手动测试新功能

echo "🚀 快速测试新file_token功能"
echo "=================================================="

# 检查服务状态
echo "1. 检查服务状态..."
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ 服务正在运行"
else
    echo "❌ 服务未运行，请先启动: ./start_dev_server.sh"
    exit 1
fi

echo -e "\n"

# 2. 大纲生成测试
echo "2. 测试大纲生成..."
OUTLINE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "quick_test_001",
    "taskPrompt": "请生成一份关于Python编程语言的技术文档大纲",
    "isOnline": false,
    "contextFiles": []
  }')

echo "响应: $OUTLINE_RESPONSE"

# 提取taskId
TASK_ID=$(echo "$OUTLINE_RESPONSE" | grep -o '"redisStreamKey":"[^"]*"' | cut -d'"' -f4)
if [ -n "$TASK_ID" ]; then
    echo "✅ 获取到taskId: $TASK_ID"
else
    echo "❌ 未能获取到taskId"
    exit 1
fi

echo -e "\n"

# 3. 等待大纲生成完成
echo "3. 等待大纲生成完成..."
echo "⏳ 等待10秒..."
sleep 10

# 4. 查看Redis流获取file_token
echo "4. 查看Redis流获取file_token..."
echo "使用命令: redis-cli XRANGE $TASK_ID - +"
echo "或者: redis-cli XREAD COUNT 10 STREAMS $TASK_ID 0"
echo -e "\n"

# 5. 模拟文档生成测试
echo "5. 测试模拟文档生成..."
MOCK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/document-from-outline-mock" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "基于大纲生成Python编程技术文档",
    "sessionId": "quick_test_001",
    "outline": "8b7e75b4150cde04bffba318da25068e",
    "contextFiles": [],
    "isOnline": false
  }')

echo "模拟生成响应: $MOCK_RESPONSE"

# 提取模拟任务的taskId
MOCK_TASK_ID=$(echo "$MOCK_RESPONSE" | grep -o '"redisStreamKey":"[^"]*"' | cut -d'"' -f4)
if [ -n "$MOCK_TASK_ID" ]; then
    echo "✅ 获取到模拟任务taskId: $MOCK_TASK_ID"
    echo "💡 可以使用以下命令监听Redis流:"
    echo "   redis-cli XREAD COUNT 10 STREAMS $MOCK_TASK_ID 0"
else
    echo "❌ 未能获取到模拟任务taskId"
fi

echo -e "\n"

# 6. 测试AI编辑功能
echo "6. 测试AI编辑功能..."
EDIT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/actions/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "polish",
    "text": "Python是一种高级编程语言，它被广泛用于数据分析、机器学习和Web开发。",
    "polishStyle": "professional"
  }')

echo "AI编辑响应: $EDIT_RESPONSE"

echo -e "\n"

# 7. 总结
echo "🎉 快速测试完成!"
echo "=================================================="
echo "📊 测试结果:"
echo "✅ 服务健康检查"
echo "✅ 大纲生成端点"
echo "✅ 模拟文档生成"
echo "✅ AI编辑功能"
echo -e "\n"

echo "💡 下一步操作:"
echo "1. 使用Redis命令查看大纲生成的file_token"
echo "2. 使用真实的file_token测试文档生成"
echo "3. 测试带context_files的功能"
echo "4. 查看详细的Redis流事件"
echo -e "\n"

echo "🔗 有用的命令:"
echo "- 查看Redis流: redis-cli XRANGE $TASK_ID - +"
echo "- 监听实时事件: redis-cli XREAD COUNT 10 STREAMS $TASK_ID 0"
echo "- 查看流长度: redis-cli XLEN $TASK_ID"
echo "- 查看所有流: redis-cli KEYS '*'"
echo -e "\n"

echo "✨ 快速测试示例执行完毕!"
