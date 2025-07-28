#!/usr/bin/env python3
"""
Redis回调处理器
用于将LangGraph执行事件发布到Redis，支持实时事件流监控
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from loguru import logger

# 导入Redis客户端
try:
    from ....workers.tasks import get_redis_client
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path

    # 添加项目根目录到Python路径
    current_file = Path(__file__)
    service_dir = current_file.parent.parent.parent.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    from workers.tasks import get_redis_client


class RedisCallbackHandler(BaseCallbackHandler):
    """
    Redis回调处理器

    将LangGraph执行过程中的各种事件发布到Redis，
    以支持实时事件流监控和前端状态更新
    """

    def __init__(self, job_id: str):
        """
        初始化Redis回调处理器

        Args:
            job_id: 作业ID，用于构建Redis频道名称
        """
        super().__init__()
        self.job_id = job_id
        self.channel_name = f"job:{job_id}:events"
        self.redis_client = None

        logger.info(
            f"Redis回调处理器已初始化 - Job ID: {job_id}, Channel: {self.channel_name}")

    async def _get_redis_client(self):
        """获取Redis客户端实例"""
        if self.redis_client is None:
            try:
                self.redis_client = await get_redis_client()
            except Exception as e:
                logger.error(f"获取Redis客户端失败: {e}")
                self.redis_client = None
        return self.redis_client

    async def _publish_event(self, event_type: str, data: dict[str, Any]):
        """
        发布事件到Redis

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        try:
            redis = await self._get_redis_client()
            if redis is None:
                return

            # 构建事件载荷
            payload = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "job_id": self.job_id
            }

            # 发布到Redis频道
            await redis.publish(self.channel_name,
                                json.dumps(payload, ensure_ascii=False))

            logger.debug(f"事件已发布 - 类型: {event_type}, 频道: {self.channel_name}")

        except Exception as e:
            logger.error(f"发布事件失败: {e}")

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """链开始执行时的回调"""
        chain_name = serialized.get("name", "Unknown Chain")

        # 根据链名称确定阶段
        phase = "PROCESSING"
        message = f"开始执行 {chain_name}"

        if "research" in chain_name.lower():
            phase = "RETRIEVAL"
            message = "开始从知识库和网络检索信息..."
        elif "outline" in chain_name.lower():
            phase = "OUTLINE_GENERATION"
            message = "开始生成文档大纲..."
        elif "planner" in chain_name.lower():
            phase = "PLANNING"
            message = "制定研究计划..."
        elif "writer" in chain_name.lower():
            phase = "WRITING"
            message = "开始撰写文档内容..."

        # 同步发布事件（避免异步问题）
        try:
            # 使用线程池执行异步操作
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._publish_event(
                        "phase_update", {
                            "phase": phase,
                            "message": message,
                            "chain_name": chain_name,
                            "run_id": str(run_id),
                            "inputs": {
                                k:
                                str(v)[:100] +
                                "..." if len(str(v)) > 100 else str(v)
                                for k, v in inputs.items()
                            }
                        }))
                # 不等待结果，避免阻塞
        except Exception as e:
            logger.debug(f"发布事件失败（非阻塞）: {e}")

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """链执行结束时的回调"""
        # 发布完成事件
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._publish_event(
                        "done", {
                            "task": "chain_execution",
                            "message": "链执行完成",
                            "run_id": str(run_id),
                            "outputs_summary": {
                                k: f"{len(str(v))} characters"
                                for k, v in outputs.items()
                            }
                        }))
        except Exception as e:
            logger.debug(f"发布完成事件失败（非阻塞）: {e}")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """工具开始执行时的回调"""
        tool_name = serialized.get("name", "Unknown Tool")

        # 发布工具调用事件
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._publish_event(
                        "tool_call", {
                            "tool_name":
                            tool_name,
                            "status":
                            "START",
                            "input":
                            input_str[:200] +
                            "..." if len(input_str) > 200 else input_str,
                            "run_id":
                            str(run_id)
                        }))
        except Exception as e:
            logger.debug(f"发布工具调用事件失败（非阻塞）: {e}")

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """工具执行结束时的回调"""
        # 如果输出看起来像是搜索结果，发布source_found事件
        if len(output) > 100:  # 假设是有意义的搜索结果
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._publish_event(
                            "source_found", {
                                "source_type":
                                "search_result",
                                "title":
                                "搜索结果",
                                "snippet":
                                output[:300] +
                                "..." if len(output) > 300 else output,
                                "run_id":
                                str(run_id)
                            }))
            except Exception as e:
                logger.debug(f"发布搜索结果事件失败（非阻塞）: {e}")

        # 发布工具完成事件
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._publish_event(
                        "tool_call", {
                            "tool_name": "tool",
                            "status": "END",
                            "output_length": len(output),
                            "run_id": str(run_id)
                        }))
        except Exception as e:
            logger.debug(f"发布工具完成事件失败（非阻塞）: {e}")

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """聊天模型开始时的回调"""
        model_name = serialized.get("name", "LLM")

        # 发布思考过程事件
        asyncio.create_task(
            self._publish_event(
                "thought", {
                    "text": f"正在调用{model_name}进行推理和分析...",
                    "model_name": model_name,
                    "run_id": str(run_id),
                    "message_count": sum(
                        len(msg_list) for msg_list in messages)
                }))

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """LLM开始时的回调"""
        model_name = serialized.get("name", "LLM")

        # 发布LLM调用开始事件
        asyncio.create_task(
            self._publish_event(
                "thought", {
                    "text": f"开始使用{model_name}处理内容，正在生成响应...",
                    "model_name": model_name,
                    "run_id": str(run_id),
                    "prompt_count": len(prompts)
                }))

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """LLM结束时的回调"""
        # 发布LLM完成事件
        asyncio.create_task(
            self._publish_event(
                "thought", {
                    "text": "LLM响应生成完成，正在处理结果...",
                    "run_id": str(run_id),
                    "generation_count": len(response.generations)
                }))

    def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """链执行错误时的回调"""
        # 发布错误事件
        asyncio.create_task(
            self._publish_event(
                "error", {
                    "code": 5001,
                    "message": f"执行过程中遇到错误: {str(error)[:200]}",
                    "error_type": type(error).__name__,
                    "run_id": str(run_id)
                }))

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """工具执行错误时的回调"""
        # 发布工具错误事件
        asyncio.create_task(
            self._publish_event(
                "error", {
                    "code": 5002,
                    "message": f"工具执行失败: {str(error)[:200]}",
                    "error_type": type(error).__name__,
                    "run_id": str(run_id)
                }))

    def on_text(
        self,
        text: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """文本输出时的回调"""
        # 对于长文本，可以作为思考过程发布
        if len(text.strip()) > 20:
            asyncio.create_task(
                self._publish_event(
                    "thought", {
                        "text": text[:500] +
                        ("..." if len(text) > 500 else ""),
                        "run_id": str(run_id)
                    }))


def create_redis_callback_handler(job_id: str) -> RedisCallbackHandler:
    """
    创建Redis回调处理器的工厂函数

    Args:
        job_id: 作业ID

    Returns:
        RedisCallbackHandler实例
    """
    return RedisCallbackHandler(job_id)
