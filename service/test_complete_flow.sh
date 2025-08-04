#!/bin/bash

echo "🧪 完整流程测试"
echo "================"

# 1. 提交API请求
echo "📤 1. 提交API请求..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "complete_test_001",
    "taskPrompt": "生成一份关于机器学习基础的大纲",
    "isOnline": false,
    "contextFiles": []
  }')

echo "📥 API响应:"
echo "$RESPONSE" | jq '.'

# 提取session_id和redis_stream_key
SESSION_ID=$(echo "$RESPONSE" | jq -r '.sessionId')
REDIS_STREAM_KEY=$(echo "$RESPONSE" | jq -r '.redisStreamKey')

echo ""
echo "🔍 提取的信息:"
echo "  Session ID: $SESSION_ID"
echo "  Redis Stream Key: $REDIS_STREAM_KEY"

# 2. 转换Redis流key
JOB_EVENTS_KEY="$SESSION_ID"  # 直接使用session_id作为流名称
echo "  Job Events Key: $JOB_EVENTS_KEY"

# 3. 等待任务开始
echo ""
echo "⏳ 2. 等待任务开始..."
sleep 5

# 4. 检查Redis流
echo ""
echo "📊 3. 检查Redis流状态..."
STREAM_LENGTH=$(redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" XLEN "$JOB_EVENTS_KEY")
echo "  流长度: $STREAM_LENGTH"

if [ "$STREAM_LENGTH" -gt 0 ]; then
    echo "✅ 流中有数据！"
    echo ""
    echo "📋 流内容:"
    redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" XRANGE "$JOB_EVENTS_KEY" - + | head -20
else
    echo "⚠️ 流中暂无数据"
    echo ""
    echo "🔍 检查所有相关的流:"
    redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" KEYS "*$SESSION_ID*"
fi

# 5. 检查Celery任务状态
echo ""
echo "🔍 4. 检查Celery任务状态..."
echo "  检查是否有Celery worker进程:"
ps aux | grep "celery.*worker" | grep -v grep | wc -l

echo ""
echo "✅ 测试完成！" 