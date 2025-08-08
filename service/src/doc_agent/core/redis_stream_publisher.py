"""
Redis Streams 事件发布器

用于向 Redis Streams 发布任务事件，支持异步操作和错误处理。
"""

import json
import asyncio
from typing import Optional, Union

from doc_agent.core.logger import logger


class RedisStreamPublisher:
    """
    Redis Streams 事件发布器
    
    用于向 Redis Streams 发布任务相关的事件，支持异步操作。
    """

    job_idx = {}

    def __init__(self, redis_client):
        """
        初始化 Redis Streams 发布器
        
        Args:
            redis_client: Redis 客户端实例
        """
        self.redis_client = redis_client
        self._connection_lock = asyncio.Lock()
        logger.info("Redis Streams 发布器初始化完成")

    async def _ensure_connection(self):
        """
        确保Redis连接可用，如果连接关闭则重新连接
        """
        try:
            # 检查连接状态
            if hasattr(self.redis_client,
                       'connection') and self.redis_client.connection:
                if hasattr(self.redis_client.connection, 'is_connected'):
                    if not self.redis_client.connection.is_connected:
                        logger.warning("Redis连接已关闭，尝试重新连接...")
                        await self._reconnect()
                        return

            # 测试连接
            await self.redis_client.ping()

        except Exception as e:
            logger.warning(f"Redis连接检查失败，尝试重新连接: {e}")
            await self._reconnect()

    async def _reconnect(self):
        """
        重新连接Redis
        """
        try:
            from doc_agent.core.config import settings
            import redis.asyncio as redis

            # 关闭旧连接
            if self.redis_client:
                try:
                    await self.redis_client.close()
                except:
                    pass

            # 创建新连接
            self.redis_client = redis.from_url(settings.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True,
                                               socket_connect_timeout=10,
                                               socket_timeout=10,
                                               retry_on_timeout=True,
                                               health_check_interval=30)

            # 测试新连接
            await self.redis_client.ping()
            logger.info("Redis重新连接成功")

        except Exception as e:
            logger.error(f"Redis重新连接失败: {e}")
            raise

    async def publish_event(self, job_id: Union[str, int],
                            event_data: dict) -> Optional[str]:
        """
        发布事件到 Redis Stream
        
        Args:
            job_id: 任务ID
            event_data: 事件数据
            
        Returns:
            str: 事件ID，失败时返回 None
        """
        async with self._connection_lock:
            try:
                # 确保连接可用
                await self._ensure_connection()

                stream_name = f"job:{job_id}"
                i = self.job_idx.get(job_id, 0) + 1
                self.job_idx[job_id] = i

                event_id = await self.redis_client.xadd(
                    stream_name,
                    {"data": json.dumps(event_data, ensure_ascii=False)},
                    id="*")  # 让Redis自动生成ID

                # 设置 Stream 的过期时间为 24 小时
                try:
                    await self.redis_client.expire(stream_name, 24 * 60 * 60
                                                   )  # 24小时 = 86400秒
                    logger.debug(f"已设置 Stream {stream_name} 的过期时间为 24 小时")
                except Exception as e:
                    logger.warning(f"设置 Stream 过期时间失败: {e}")

                logger.info(
                    f"事件发布成功: job_id={job_id}, event_id={event_id}, event_type={event_data.get('event_type', 'unknown')}, i={i}"
                )

                return event_id

            except Exception as e:
                logger.error(f"事件发布失败: job_id={job_id}, error={e}")
                # 不抛出异常，只记录错误，避免影响主流程
                return None

    async def publish_task_started(self, job_id: Union[str, int],
                                   task_type: str, **kwargs) -> Optional[str]:
        """
        发布任务开始事件
        
        Args:
            job_id: 任务ID
            task_type: 任务类型 (如 "outline_generation", "document_generation")
            **kwargs: 额外的任务参数
            
        Returns:
            str: 事件ID
        """
        event_data = {
            "eventType": "task_started",
            "taskType": task_type,
            "status": "started",
            "timestamp": self._get_current_timestamp(),
            **kwargs
        }

        return await self.publish_event(job_id, event_data)

    async def publish_task_progress(self, job_id: Union[str,
                                                        int], task_type: str,
                                    progress: str, **kwargs) -> Optional[str]:
        """
        发布任务进度事件
        
        Args:
            job_id: 任务ID
            task_type: 任务类型
            progress: 进度描述
            **kwargs: 额外的进度信息
            
        Returns:
            str: 事件ID
        """
        event_data = {
            "eventType": "task_progress",
            "taskType": task_type,
            "progress": progress,
            "status": "running",
            "timestamp": self._get_current_timestamp(),
            **kwargs
        }

        return await self.publish_event(job_id, event_data)

    async def publish_task_completed(self,
                                     job_id: Union[str, int],
                                     task_type: str,
                                     result: dict = None,
                                     **kwargs) -> Optional[str]:
        """
        发布任务完成事件
        
        Args:
            job_id: 任务ID
            task_type: 任务类型
            result: 任务结果
            **kwargs: 额外的完成信息
            
        Returns:
            str: 事件ID
        """
        # 处理不可序列化的对象
        serializable_result = self._make_serializable(result) if result else {}
        serializable_kwargs = self._make_serializable(kwargs)

        event_data = {
            "eventType": "task_completed",
            "taskType": task_type,
            "status": "completed",
            "result": serializable_result,
            "timestamp": self._get_current_timestamp(),
            **serializable_kwargs
        }

        return await self.publish_event(job_id, event_data)

    async def publish_task_failed(self, job_id: Union[str,
                                                      int], task_type: str,
                                  error: str, **kwargs) -> Optional[str]:
        """
        发布任务失败事件
        
        Args:
            job_id: 任务ID
            task_type: 任务类型
            error: 错误信息
            **kwargs: 额外的错误信息
            
        Returns:
            str: 事件ID
        """
        event_data = {
            "eventType": "task_failed",
            "taskType": task_type,
            "status": "failed",
            "error": error,
            "timestamp": self._get_current_timestamp(),
            **kwargs
        }

        return await self.publish_event(job_id, event_data)

    async def publish_outline_generated(self, job_id: Union[str, int],
                                        outline: dict) -> Optional[str]:
        """
        发布大纲生成完成事件
        
        Args:
            job_id: 任务ID
            outline: 生成的大纲数据
            
        Returns:
            str: 事件ID
        """
        event_data = {
            "eventType": "outline_generated",
            "taskType": "outline_generation",
            "status": "completed",
            "outline": outline,
            "timestamp": self._get_current_timestamp()
        }

        return await self.publish_event(job_id, event_data)

    async def publish_document_generated(self, job_id: Union[str, int],
                                         document: dict) -> Optional[str]:
        """
        发布文档生成完成事件
        
        Args:
            job_id: 任务ID
            document: 生成的文档数据
            
        Returns:
            str: 事件ID
        """
        # 处理不可序列化的对象
        serializable_document = self._make_serializable(document)

        event_data = {
            "eventType": "document_generated",
            "taskType": "document_generation",
            "status": "completed",
            "document": serializable_document,
            "timestamp": self._get_current_timestamp()
        }

        return await self.publish_event(job_id, event_data)

    def _make_serializable(self, obj):
        """
        将对象转换为可序列化的格式
        
        Args:
            obj: 要转换的对象
            
        Returns:
            可序列化的对象
        """
        if isinstance(obj, dict):
            return {
                key: self._make_serializable(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, 'model_dump'):
            # 如果是Pydantic模型，使用model_dump()
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            # 如果是普通对象，转换为字典
            return obj.__dict__
        elif hasattr(obj, 'isoformat'):
            # 如果是datetime对象
            return obj.isoformat()
        else:
            # 如果是其他类型，尝试转换为字符串
            try:
                return str(obj)
            except:
                return f"<{type(obj).__name__} object>"

    def _get_current_timestamp(self) -> str:
        """
        获取当前时间戳
        
        Returns:
            str: ISO 格式的时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()

    async def get_stream_info(self, job_id: Union[str, int]) -> Optional[dict]:
        """
        获取 Stream 信息
        
        Args:
            job_id: 任务ID
            
        Returns:
            dict: Stream 信息，如果不存在则返回 None
        """
        try:
            stream_name = str(job_id)  # 直接使用job_id作为流名称
            info = await self.redis_client.xinfo_stream(stream_name)
            return info
        except Exception as e:
            logger.warning(f"获取 Stream 信息失败: job_id={job_id}, error={e}")
            return None

    async def get_stream_length(self, job_id: Union[str, int]) -> int:
        """
        获取 Stream 长度
        
        Args:
            job_id: 任务ID
            
        Returns:
            int: Stream 中的事件数量
        """
        try:
            stream_name = str(job_id)  # 直接使用job_id作为流名称
            length = await self.redis_client.xlen(stream_name)
            return length
        except Exception as e:
            logger.warning(f"获取 Stream 长度失败: job_id={job_id}, error={e}")
            return 0
