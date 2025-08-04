#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的Redis Stream格式
验证流名称直接使用session_id而不是job_events:session_id
"""

import redis
import json
import time
from datetime import datetime

# Redis配置
REDIS_HOST = "10.215.149.74"
REDIS_PORT = 26379
REDIS_PASSWORD = "xJrhp*4mnHxbBWN2grqq"

def test_new_stream_format():
    """测试新的流格式"""
    print("🧪 测试新的Redis Stream格式")
    print("=" * 50)
    
    # 连接Redis
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    
    # 测试session_id
    test_session_id = "1951106983556190200"
    
    print(f"📊 测试session_id: {test_session_id}")
    print()
    
    # 1. 检查流是否存在
    print("1️⃣ 检查流是否存在...")
    stream_length = r.xlen(test_session_id)
    print(f"   流长度: {stream_length}")
    
    if stream_length > 0:
        print("   ✅ 流存在且有数据")
    else:
        print("   ⚠️ 流不存在或为空")
    
    print()
    
    # 2. 查看流内容
    print("2️⃣ 查看流内容...")
    messages = r.xrange(test_session_id, "-", "+")
    
    if messages:
        print(f"   找到 {len(messages)} 条消息:")
        for i, (msg_id, fields) in enumerate(messages, 1):
            print(f"   📨 消息 {i}: {msg_id}")
            
            # 解析事件数据
            if 'data' in fields:
                try:
                    data = json.loads(fields['data'])
                    event_type = data.get('eventType', 'unknown')
                    print(f"      事件类型: {event_type}")
                    
                    if event_type == 'outline_generated':
                        outline = data.get('outline', {})
                        title = outline.get('title', 'N/A')
                        nodes = outline.get('nodes', [])
                        print(f"      大纲标题: {title}")
                        print(f"      节点数量: {len(nodes)}")
                        
                        for j, node in enumerate(nodes[:3], 1):  # 只显示前3个节点
                            print(f"        节点{j}: {node.get('title', 'N/A')}")
                        
                        if len(nodes) > 3:
                            print(f"        ... 还有 {len(nodes) - 3} 个节点")
                    
                except json.JSONDecodeError:
                    print(f"      ❌ JSON解析失败: {fields['data']}")
            else:
                print(f"      📄 原始数据: {fields}")
            
            print()
    else:
        print("   ⚠️ 流中没有消息")
    
    print()
    
    # 3. 实时监控测试
    print("3️⃣ 实时监控测试 (5秒)...")
    print("   按 Ctrl+C 停止监控")
    print()
    
    try:
        last_id = "0"
        start_time = time.time()
        
        while time.time() - start_time < 5:  # 监控5秒
            # 读取新消息
            messages = r.xread(
                count=10,
                block=1000,  # 1秒超时
                streams={test_session_id: last_id}
            )
            
            if messages:
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        print(f"   📨 新消息: {message_id}")
                        
                        if 'data' in fields:
                            try:
                                data = json.loads(fields['data'])
                                event_type = data.get('eventType', 'unknown')
                                print(f"      事件类型: {event_type}")
                            except json.JSONDecodeError:
                                print(f"      ❌ JSON解析失败")
                        
                        last_id = message_id
            else:
                print(f"   💓 监控中... {datetime.now().strftime('%H:%M:%S')}")
    
    except KeyboardInterrupt:
        print("   🛑 监控已停止")
    
    print()
    
    # 4. 检查所有数字ID的流
    print("4️⃣ 检查所有数字ID的流...")
    all_keys = r.keys("*")
    numeric_keys = [key for key in all_keys if key.isdigit() or (key.startswith('-') and key[1:].isdigit())]
    
    print(f"   找到 {len(numeric_keys)} 个数字ID流:")
    for key in numeric_keys[:10]:  # 只显示前10个
        length = r.xlen(key)
        print(f"     {key}: {length} 条消息")
    
    if len(numeric_keys) > 10:
        print(f"     ... 还有 {len(numeric_keys) - 10} 个流")
    
    print()
    print("✅ 测试完成！")
    
    # 关闭连接
    r.close()

if __name__ == "__main__":
    test_new_stream_format() 