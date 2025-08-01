#!/bin/bash

# 测试 Redis 流输出的驼峰格式
echo "测试 Redis 流输出的驼峰格式..."

# 1. 触发大纲生成任务
echo "1. 触发大纲生成任务"
curl --location 'http://127.0.0.1:8000/api/v1/jobs/outline' \
--header 'Content-Type: application/json' \
--data '{
    "sessionId": "test-camelcase-001",
    "taskPrompt": "生成一篇关于人工智能技术发展趋势的详细报告",
    "isOnline": true,
    "contextFiles": []
}'

echo -e "\n\n"

# 2. 等待几秒钟让任务开始
echo "2. 等待任务开始..."
sleep 3

# 3. 检查 Redis 流中的数据格式
echo "3. 检查 Redis 流中的数据格式"
echo "使用 redis-cli 查看流数据:"
echo "redis-cli xread count 10 streams job_events:test-camelcase-001 0"

echo -e "\n\n"

# 4. 提供手动检查命令
echo "4. 手动检查命令:"
echo "redis-cli xread count 10 streams job_events:test-camelcase-001 0"
echo "redis-cli xlen job_events:test-camelcase-001"
echo "redis-cli xinfo stream job_events:test-camelcase-001"

echo -e "\n\n测试完成！" 