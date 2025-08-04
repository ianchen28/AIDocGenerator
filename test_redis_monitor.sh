#!/bin/bash

# Redis 配置
REDIS_HOST="10.215.149.74"
REDIS_PORT="26379"
REDIS_PASSWORD="xJrhp*4mnHxbBWN2grqq"
JOB_ID="1951106983556190200"

echo "🔍 Redis 流监控工具"
echo "=================="
echo "服务器: $REDIS_HOST:$REDIS_PORT"
echo "任务ID: $JOB_ID"
echo ""

# 检查流是否存在
echo "📊 检查流信息..."
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" xlen "job_events:$JOB_ID"

echo ""
echo "📋 查看所有事件..."
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" xrange "job_events:$JOB_ID" - +

echo ""
echo "🔄 实时监控新事件 (按 Ctrl+C 停止)..."
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" xread block 0 count 10 streams "job_events:$JOB_ID" $ 