#!/bin/bash

# 监听Redis流的脚本

echo "🔍 Redis流监听器"
echo "================"

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <redis_stream_key>"
    echo "示例: $0 outline_generation:test_session_001"
    echo ""
    echo "可用的测试流:"
    echo "- outline_generation:test_session_001"
    echo "- outline_generation:test_session_002" 
    echo "- outline_generation:test_session_003"
    exit 1
fi

STREAM_KEY="$1"

echo "正在监听流: $STREAM_KEY"
echo "按 Ctrl+C 停止监听"
echo ""

# 使用redis-cli监听流
echo "监听流: $STREAM_KEY"
echo "按 Ctrl+C 停止监听"
echo ""

# 如果流key是outline_generation格式，直接使用session_id
if [[ "$STREAM_KEY" == outline_generation:* ]]; then
    JOB_ID=$(echo "$STREAM_KEY" | sed 's/outline_generation://')
    STREAM_KEY="$JOB_ID"
    echo "转换后的流key: $STREAM_KEY"
fi

# 使用远程Redis连接
redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" --raw XREAD COUNT 10 BLOCK 5000 STREAMS "$STREAM_KEY" 0 