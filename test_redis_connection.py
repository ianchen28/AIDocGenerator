#!/usr/bin/env python3
"""
测试 Redis 连接
"""

import sys
import os
import asyncio
import redis.asyncio as redis

# 添加项目路径到 sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'service', 'src'))

# 导入配置
from doc_agent.core.config import settings

async def test_redis_connection():
    """测试 Redis 连接"""
    try:
        redis_url = settings.redis_url
        print(f"Redis URL: {redis_url}")
        
        client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
        print("✅ Redis 连接成功")
        
        # 测试写入和读取
        test_key = "test_connection"
        test_value = "hello_world"
        await client.set(test_key, test_value)
        result = await client.get(test_key)
        print(f"✅ 读写测试成功: {result}")
        
        # 清理测试数据
        await client.delete(test_key)
        
        return True
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 测试 Redis 连接")
    print("=" * 30)
    
    success = asyncio.run(test_redis_connection())
    if success:
        print("\n✅ Redis 连接测试通过")
    else:
        print("\n❌ Redis 连接测试失败")
