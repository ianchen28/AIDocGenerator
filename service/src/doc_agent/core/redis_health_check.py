# service/src/doc_agent/core/redis_health_check.py

import aioredis
from doc_agent.core.config import settings
from doc_agent.core.logging_config import logger

# 1. 创建一个全局变量来存储主事件循环
main_event_loop = None
# 2. 将 redis_pool 初始化为 None
redis_pool = None


async def init_redis_pool():
    """
    在应用启动时初始化 Redis 连接池。
    """
    global redis_pool
    if redis_pool is None:
        logger.info("正在初始化 Redis 连接池...")
        redis_pool = aioredis.from_url(
            settings.redis_url,
            max_connections=50,
            # aioredis 会自动解码响应，这通常是我们想要的
            encoding="utf-8",
            decode_responses=True)
        logger.info("Redis 连接池初始化成功。")


async def close_redis_pool():
    """
    在应用关闭时关闭 Redis 连接池。
    """
    global redis_pool
    if redis_pool:
        logger.info("正在关闭 Redis 连接池...")
        await redis_pool.close()
        logger.info("Redis 连接池已关闭。")


def get_redis_client():
    """
    获取一个 Redis 客户端实例。
    在 aioredis 中，我们直接复用启动时创建的那个单例客户端。
    """
    if redis_pool is None:
        raise RuntimeError("Redis 连接池尚未初始化。请在应用启动时调用 init_redis_pool。")
    return redis_pool


async def get_redis_client_async():
    """
    异步获取一个 Redis 客户端实例。
    """
    if redis_pool is None:
        raise RuntimeError("Redis 连接池尚未初始化。请在应用启动时调用 init_redis_pool。")
    return redis_pool


# 2. 创建一个函数来获取保存的主循环
def get_main_event_loop():
    """
    返回在应用启动时捕获的主事件循环。
    """
    if main_event_loop is None:
        raise RuntimeError("主事件循环尚未被捕获。")
    return main_event_loop


async def check_redis_connection():
    """
    检查与 Redis 的连接。
    """
    try:
        # 使用 get_redis_client 来确保我们从池中获取连接
        client = get_redis_client()
        await client.ping()
        logger.info("Redis 连接测试成功。")
        return True
    except Exception as e:
        logger.error(f"Redis 连接测试失败: {e}")
        return False
