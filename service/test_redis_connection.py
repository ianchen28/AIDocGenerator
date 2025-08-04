#!/usr/bin/env python3
"""
Redis 连接测试脚本
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis.asyncio as redis
from loguru import logger

from doc_agent.core.config import settings


async def test_redis_connection():
    """测试Redis连接"""
    logger.info(f"测试Redis连接: {settings.redis_url}")

    try:
        # 方法1: 使用配置中的URL
        logger.info("方法1: 使用配置URL")
        client1 = redis.from_url(settings.redis_url,
                                 encoding="utf-8",
                                 decode_responses=True,
                                 socket_connect_timeout=10,
                                 socket_timeout=10)

        result = await client1.ping()
        logger.info(f"✅ 连接成功: {result}")
        await client1.close()

    except Exception as e:
        logger.error(f"❌ 方法1失败: {e}")

    try:
        # 方法2: 手动构建连接
        logger.info("方法2: 手动构建连接")
        client2 = redis.Redis(host="10.215.149.74",
                              port=26379,
                              password="xJrhp*4mnHxbBWN2grqq",
                              db=0,
                              encoding="utf-8",
                              decode_responses=True,
                              socket_connect_timeout=10,
                              socket_timeout=10)

        result = await client2.ping()
        logger.info(f"✅ 连接成功: {result}")
        await client2.close()

    except Exception as e:
        logger.error(f"❌ 方法2失败: {e}")

    try:
        # 方法3: 不使用密码
        logger.info("方法3: 不使用密码")
        client3 = redis.Redis(host="10.215.149.74",
                              port=26379,
                              db=0,
                              encoding="utf-8",
                              decode_responses=True,
                              socket_connect_timeout=10,
                              socket_timeout=10)

        result = await client3.ping()
        logger.info(f"✅ 连接成功: {result}")
        await client3.close()

    except Exception as e:
        logger.error(f"❌ 方法3失败: {e}")


async def main():
    """主函数"""
    await test_redis_connection()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO")

    # 运行测试
    asyncio.run(main())
