"""
Redis Streams 事件发布器

用于向 Redis Streams 发布任务事件，支持异步操作和错误处理。
"""

import json
import asyncio
from typing import Optional, Union
from redis import Redis  # 确保导入的是同步的 Redis

from doc_agent.core.logger import logger
from doc_agent.core.redis_health_check import get_redis_client


class RedisStreamPublisher:
    """
    使用 aioredis 和 Redis INCR 命令的健壮事件发布器。
    """

    def __init__(self, redis_client: Redis, stream_name: str):
        if not hasattr(redis_client, 'xadd'):
            raise TypeError("redis_client 必须是一个同步的 Redis 客户端实例")
        self.redis_client = redis_client
        self.stream_name = stream_name
        logger.info(
            f"同步 RedisStreamPublisher 已初始化，将发布到 Stream: '{self.stream_name}'")

    def publish_event(self, job_id: Union[str, int], event_data: dict):

        job_id_str = str(job_id)

        try:
            # 2. 使用 Redis INCR 生成原子性的序列号
            counter_key = f"job_counter:{job_id_str}"
            i = self.redis_client.incr(counter_key)
            custom_id = f"{job_id_str}-{i}"

            stream_name = f"job:{job_id_str}"
            # aioredis 的 xadd 期望一个字典，其值为 str, bytes, int 或 float
            # 我们将 event_data 序列化为 JSON 字符串
            fields = {"data": json.dumps(event_data, ensure_ascii=False)}

            # 4. 使用 xadd 命令，让Redis自动生成ID
            event_id = self.redis_client.xadd(stream_name,
                                              fields,
                                              id=custom_id)

            # 5. 设置过期时间
            self.redis_client.expire(stream_name, 24 * 60 * 60)

            logger.info(
                f"事件发布成功: job_id={job_id_str}, event_id={event_id}, event_type={event_data.get('eventType', 'unknown')}, i={i}"
            )

        except Exception as e:
            logger.error(
                f"事件发布失败: job_id={job_id_str}, custom_id={custom_id}, error_type={type(e).__name__}, error_msg={e}"
            )

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

        self.publish_event(job_id, event_data)

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

        self.publish_event(job_id, event_data)

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

        self.publish_event(job_id, event_data)

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

        self.publish_event(job_id, event_data)

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

        self.publish_event(job_id, event_data)

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

        self.publish_event(job_id, event_data)

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
