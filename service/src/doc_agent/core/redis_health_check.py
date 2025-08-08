"""
Redis连接健康检查模块

用于监控Redis连接状态，提供连接健康检查和自动重连功能。
"""

import asyncio
import time
from typing import Optional, Callable
from doc_agent.core.logger import logger


class RedisHealthChecker:
    """
    Redis连接健康检查器
    
    定期检查Redis连接状态，在连接断开时自动重连。
    """

    def __init__(self, redis_client, check_interval: int = 30):
        """
        初始化健康检查器
        
        Args:
            redis_client: Redis客户端实例
            check_interval: 检查间隔（秒）
        """
        self.redis_client = redis_client
        self.check_interval = check_interval
        self.is_running = False
        self.last_check_time = 0
        self.connection_healthy = True
        self._check_task = None

    async def start_monitoring(self):
        """开始监控Redis连接"""
        if self.is_running:
            logger.warning("Redis健康检查器已在运行")
            return

        self.is_running = True
        logger.info(f"开始Redis连接健康监控，检查间隔: {self.check_interval}秒")

        self._check_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """停止监控Redis连接"""
        self.is_running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("Redis连接健康监控已停止")

    async def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                await self._check_connection()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Redis健康检查出错: {e}")
                await asyncio.sleep(5)  # 出错后短暂等待

    async def _check_connection(self):
        """检查Redis连接状态"""
        try:
            start_time = time.time()
            await self.redis_client.ping()
            check_time = time.time() - start_time

            if not self.connection_healthy:
                logger.info(f"Redis连接已恢复，响应时间: {check_time:.3f}秒")
                self.connection_healthy = True
            else:
                logger.debug(f"Redis连接正常，响应时间: {check_time:.3f}秒")

            self.last_check_time = time.time()

        except Exception as e:
            if self.connection_healthy:
                logger.warning(f"Redis连接异常: {e}")
                self.connection_healthy = False
            else:
                logger.error(f"Redis连接持续异常: {e}")

    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        return self.connection_healthy

    async def force_reconnect(self):
        """强制重新连接"""
        try:
            logger.info("强制重新连接Redis...")

            # 关闭旧连接
            if self.redis_client:
                try:
                    await self.redis_client.close()
                except:
                    pass

            # 重新创建连接
            from doc_agent.core.config import settings
            import redis.asyncio as redis

            self.redis_client = redis.from_url(settings.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True,
                                               socket_connect_timeout=10,
                                               socket_timeout=10,
                                               retry_on_timeout=True,
                                               health_check_interval=30)

            # 测试新连接
            await self.redis_client.ping()
            self.connection_healthy = True
            logger.info("Redis重新连接成功")

        except Exception as e:
            logger.error(f"Redis重新连接失败: {e}")
            self.connection_healthy = False
            raise


class RedisConnectionManager:
    """
    Redis连接管理器
    
    管理Redis连接的创建、监控和重连。
    """

    def __init__(self):
        self.redis_client = None
        self.health_checker = None
        self._lock = asyncio.Lock()

    async def get_client(self):
        """获取Redis客户端，如果不存在则创建"""
        async with self._lock:
            if self.redis_client is None:
                await self._create_client()
            return self.redis_client

    async def _create_client(self):
        """创建Redis客户端"""
        try:
            from doc_agent.core.config import settings
            import redis.asyncio as redis

            self.redis_client = redis.from_url(settings.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True,
                                               socket_connect_timeout=10,
                                               socket_timeout=10,
                                               retry_on_timeout=True,
                                               health_check_interval=30)

            # 测试连接
            await self.redis_client.ping()

            # 创建健康检查器
            self.health_checker = RedisHealthChecker(self.redis_client)
            await self.health_checker.start_monitoring()

            logger.info("Redis连接管理器初始化成功")

        except Exception as e:
            logger.error(f"创建Redis客户端失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.health_checker:
            await self.health_checker.stop_monitoring()

        if self.redis_client:
            try:
                await self.redis_client.close()
            except:
                pass

        logger.info("Redis连接管理器已关闭")

    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        if self.health_checker:
            return self.health_checker.is_healthy()
        return False


# 全局连接管理器实例
_connection_manager = None


async def get_redis_connection_manager() -> RedisConnectionManager:
    """获取全局Redis连接管理器"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = RedisConnectionManager()
    return _connection_manager


async def get_redis_client():
    """获取Redis客户端"""
    manager = await get_redis_connection_manager()
    return await manager.get_client()


async def close_redis_connections():
    """关闭所有Redis连接"""
    global _connection_manager
    if _connection_manager:
        await _connection_manager.close()
        _connection_manager = None
