#!/bin/bash

echo "🧪 简单大纲生成测试"
echo "=================="

# 提交任务
echo "📤 提交大纲生成任务..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "simple_test_001",
    "taskPrompt": "生成一份关于Python编程基础的大纲",
    "isOnline": false,
    "contextFiles": []
  }')

echo "📥 API响应:"
echo "$RESPONSE" | jq '.'

# 提取redis stream key
STREAM_KEY=$(echo "$RESPONSE" | jq -r '.redisStreamKey')
echo ""
echo "🔍 Redis流Key: $STREAM_KEY"

# 等待几秒钟让任务开始
echo ""
echo "⏳ 等待任务开始..."
sleep 3

# 检查Redis流
echo ""
echo "📊 检查Redis流状态..."
STREAM_LENGTH=$(redis-cli XLEN "$STREAM_KEY")
echo "流长度: $STREAM_LENGTH"

if [ "$STREAM_LENGTH" -gt 0 ]; then
    echo "✅ 流中有数据，显示内容:"
    redis-cli XRANGE "$STREAM_KEY" - + | head -20
else
    echo "⚠️ 流中暂无数据，可能的原因:"
    echo "1. Celery worker未正确处理任务"
    echo "2. 任务执行时间较长"
    echo "3. Redis连接配置问题"
fi

echo ""
echo "✅ 测试完成！" 