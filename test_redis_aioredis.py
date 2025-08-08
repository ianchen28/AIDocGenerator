#!/usr/bin/env python3
"""
使用aioredis的Redis连接测试
"""
import asyncio
import aioredis
from doc_agent.core.config import settings
from doc_agent.core.logging_config import logger


async def main():
    """
    使用aioredis的Redis连接测试
    """
    logger.info(f"开始测试 Redis 连接，目标地址: {settings.redis_url}")

    try:
        logger.info("正在创建 Redis 客户端...")
        redis_client = aioredis.from_url(settings.redis_url)

        logger.info("客户端创建成功，正在尝试 PING...")
        response = await redis_client.ping()

        if response:
            logger.success("✅ ✅ ✅ Redis 连接成功！收到了 PONG 响应。")
        else:
            logger.error("❌ ❌ ❌ 连接看似成功，但 PING 没有返回预期的响应。")

        logger.info("正在尝试 INCR 命令...")
        counter = await redis_client.incr("test_counter")
        logger.success(f"✅ ✅ ✅ INCR 命令成功！计数器值: {counter}")

        # 关闭连接
        await redis_client.close()

    except aioredis.AuthenticationError as e:
        logger.error("❌ ❌ ❌ 认证失败！请检查 Redis URL 中的密码是否正确。")
        logger.error(f"错误信息: {e}")
    except aioredis.ConnectionError as e:
        logger.error("❌ ❌ ❌ Redis 连接错误！")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {e}")
    except Exception as e:
        logger.error(f"❌ ❌ ❌ Redis 连接或命令执行失败！")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {e}")
        import traceback
        logger.error(f"完整堆栈: {traceback.format_exc()}")
    finally:
        logger.info("测试结束。")


if __name__ == "__main__":
    asyncio.run(main())
