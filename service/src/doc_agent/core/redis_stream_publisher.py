"""
Redis Streams 事件发布器

用于向 Redis Streams 发布任务事件，支持异步操作和错误处理。
"""

import json
from typing import Optional

from loguru import logger


class RedisStreamPublisher:
    """
    Redis Streams 事件发布器
    
    用于向 Redis Streams 发布任务相关的事件，支持异步操作。
    """

    def __init__(self, redis_client):
        """
        初始化 Redis Streams 发布器
        
        Args:
            redis_client: Redis 客户端实例
        """
        self.redis_client = redis_client
        logger.info("Redis Streams 发布器初始化完成")

    async def publish_event(self, job_id: str,
                            event_data: dict) -> Optional[str]:
        """
        发布事件到 Redis Stream
        
        Args:
            job_id: 任务ID
            event_data: 事件数据字典
            
        Returns:
            str: 事件ID，如果发布失败则返回 None
            
        Raises:
            Exception: 当发布失败时抛出异常
        """
        try:
            # 构造 Stream 名称
            stream_name = f"job_events:{job_id}"

            # 准备事件数据
            event_payload = {
                "data": json.dumps(event_data, ensure_ascii=False),
                "timestamp": event_data.get("timestamp", ""),
                "eventType": event_data.get("eventType", "unknown")
            }

            # 发布事件到 Redis Stream
            event_id = await self.redis_client.xadd(stream_name, event_payload)

            logger.info(
                f"事件发布成功: job_id={job_id}, event_id={event_id}, event_type={event_data.get('event_type', 'unknown')}"
            )

            return event_id

        except Exception as e:
            logger.error(f"事件发布失败: job_id={job_id}, error={e}")
            raise Exception(f"发布事件失败: {str(e)}") from e

    async def publish_task_started(self, job_id: str, task_type: str,
                                   **kwargs) -> Optional[str]:
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

    async def publish_task_progress(self, job_id: str, task_type: str,
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
                                     job_id: str,
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
        event_data = {
            "eventType": "task_completed",
            "taskType": task_type,
            "status": "completed",
            "result": result or {},
            "timestamp": self._get_current_timestamp(),
            **kwargs
        }

        return await self.publish_event(job_id, event_data)

    async def publish_task_failed(self, job_id: str, task_type: str,
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

    async def publish_outline_generated(self, job_id: str,
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

    async def publish_document_generated(self, job_id: str,
                                         document: dict) -> Optional[str]:
        """
        发布文档生成完成事件
        
        Args:
            job_id: 任务ID
            document: 生成的文档数据
            
        Returns:
            str: 事件ID
        """
        event_data = {
            "eventType": "document_generated",
            "taskType": "document_generation",
            "status": "completed",
            "document": document,
            "timestamp": self._get_current_timestamp()
        }

        return await self.publish_event(job_id, event_data)

    def _get_current_timestamp(self) -> str:
        """
        获取当前时间戳
        
        Returns:
            str: ISO 格式的时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()

    async def get_stream_info(self, job_id: str) -> Optional[dict]:
        """
        获取 Stream 信息
        
        Args:
            job_id: 任务ID
            
        Returns:
            dict: Stream 信息，如果不存在则返回 None
        """
        try:
            stream_name = f"job_events:{job_id}"
            info = await self.redis_client.xinfo_stream(stream_name)
            return info
        except Exception as e:
            logger.warning(f"获取 Stream 信息失败: job_id={job_id}, error={e}")
            return None

    async def get_stream_length(self, job_id: str) -> int:
        """
        获取 Stream 长度
        
        Args:
            job_id: 任务ID
            
        Returns:
            int: Stream 中的事件数量
        """
        try:
            stream_name = f"job_events:{job_id}"
            length = await self.redis_client.xlen(stream_name)
            return length
        except Exception as e:
            logger.warning(f"获取 Stream 长度失败: job_id={job_id}, error={e}")
            return 0
