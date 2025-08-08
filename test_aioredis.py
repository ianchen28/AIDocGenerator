#!/usr/bin/env python3
"""
使用aioredis的Redis连接测试
"""
import asyncio
import aioredis


async def simple_test():
    """简单的Redis连接测试"""
    print("开始aioredis Redis连接测试...")

    # 使用你的Redis配置
    redis_url = "redis://:xJrhp*4mnHxbBWN2grqq@10.215.149.74:26379/0"
    print(f"连接URL: {redis_url}")

    try:
        print("创建Redis客户端...")
        redis_client = aioredis.from_url(redis_url)

        print("尝试PING...")
        response = await redis_client.ping()

        if response:
            print("✅ Redis连接成功！")
        else:
            print("❌ PING没有返回预期响应")

        # 关闭连接
        await redis_client.close()

    except Exception as e:
        print(f"❌ 连接失败: {type(e).__name__}")
        print(f"错误信息: {e}")
        import traceback
        print(f"完整堆栈: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(simple_test())
