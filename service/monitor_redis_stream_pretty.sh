#!/bin/bash

# 美化显示的Redis流监控脚本

echo "🔍 Redis流监控工具 (美化显示)"
echo "================================"

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <job_id>"
    echo "示例: $0 1951106983556190200"
    exit 1
fi

JOB_ID="$1"
STREAM_KEY="job_events:$JOB_ID"

echo "监控流: $STREAM_KEY"
echo ""

# 检查流是否存在
STREAM_LENGTH=$(redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" XLEN "$STREAM_KEY" 2>/dev/null)

if [ "$STREAM_LENGTH" -eq 0 ]; then
    echo "⚠️ 流中暂无数据"
    echo "等待新消息..."
    echo ""
fi

echo "🔄 实时监控新消息 (按 Ctrl+C 停止)..."
echo ""

# 使用Python脚本来美化显示
python3 -c "
import sys
import json
import redis
import time

# 连接Redis
r = redis.Redis(
    host='10.215.149.74',
    port=26379,
    password='xJrhp*4mnHxbBWN2grqq',
    decode_responses=True
)

stream_key = 'job_events:$JOB_ID'
last_id = '0'

print('开始监控...')
print('=' * 60)

try:
    while True:
        # 读取新消息
        messages = r.xread({stream_key: last_id}, count=10, block=5000)
        
        if messages:
            for stream, stream_messages in messages:
                for msg_id, fields in stream_messages:
                    print(f'📨 消息ID: {msg_id}')
                    print(f'⏰ 时间: {fields.get(\"timestamp\", \"N/A\")}')
                    print(f'📋 事件类型: {fields.get(\"eventType\", \"N/A\")}')
                    
                    # 解析JSON数据
                    if 'data' in fields:
                        try:
                            data = json.loads(fields['data'])
                            print('📄 数据内容:')
                            print(json.dumps(data, ensure_ascii=False, indent=2))
                        except json.JSONDecodeError:
                            print(f'📄 数据内容: {fields[\"data\"]}')
                    
                    print('-' * 40)
                    last_id = msg_id
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print('\\n🛑 监控已停止')
except Exception as e:
    print(f'❌ 错误: {e}')
finally:
    r.close()
" 