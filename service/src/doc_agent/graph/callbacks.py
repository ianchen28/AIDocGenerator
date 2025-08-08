#!/usr/bin/env python3
"""
Redis回调处理器
用于将LangGraph执行事件发布到Redis，支持实时事件流监控
"""

import asyncio
from concurrent.futures import Future

from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from doc_agent.core.logger import logger

# 导入Redis Streams发布器
from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
from doc_agent.core.redis_health_check import get_main_event_loop


class RedisCallbackHandler(BaseCallbackHandler):
    """
    一个线程安全的回调处理器，用于从同步代码中向 Redis 发布异步事件。
    """

    def __init__(self, job_id: str):
        from doc_agent.core.container import get_container
        container = get_container()
        # publisher 现在是一个完全同步的对象
        self.publisher = container.redis_publisher
        self.job_id = job_id
        super().__init__()

    def _publish_event(self, event_type: str, data: Optional[dict] = None):
        try:
            event_data = {"eventType": event_type}
            if data:
                event_data.update(data)

            # 直接调用，不再需要任何 asyncio 的处理
            self.publisher.publish_event(self.job_id, event_data)

        except Exception as e:
            # 记录下任何可能的异常，但不要让它中断主流程
            logger.warning(
                f"事件发布失败 - 类型: {event_type}, Job ID: {self.job_id}, 错误: {e}")

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
        # 安全处理 serialized 可能为 None 的情况
        if serialized is None:
            serialized = {}
        chain_name = serialized.get("name", "Unknown Chain")

        # 根据链名称确定阶段
        phase = "PROCESSING"
        message = f"开始执行 {chain_name}"

        if "research" in chain_name.lower():
            phase = "RETRIEVAL"
            message = "正在从知识库和网络检索相关信息，收集主题相关的资料和最新信息..."
        elif "outline" in chain_name.lower():
            phase = "OUTLINE_GENERATION"
            message = "正在基于收集到的信息生成详细的文档大纲，包括章节结构和内容安排..."
        elif "planner" in chain_name.lower():
            phase = "PLANNING"
            message = "正在制定详细的研究计划，确定文档的重点内容和研究方向..."
        elif "writer" in chain_name.lower():
            phase = "WRITING"
            message = "正在根据大纲撰写详细的文档内容，确保内容的准确性和完整性..."

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
        # 安全处理 serialized 可能为 None 的情况
        if serialized is None:
            serialized = {}
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
        # 安全处理 serialized 可能为 None 的情况
        if serialized is None:
            serialized = {}
        model_name = serialized.get("name", "LLM")

        # 发布思考过程事件
        asyncio.create_task(
            self._publish_event(
                "thought", {
                    "text": f"正在调用{model_name}进行深度分析和内容生成，请稍候...",
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
        # 安全处理 serialized 可能为 None 的情况
        if serialized is None:
            serialized = {}
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


class TokenStreamCallbackHandler(BaseCallbackHandler):
    """
    一个专门用于将 LLM 生成的 token 流式传输到 Redis 的回调处理器。
    """

    def __init__(self, job_id: str, chapter_title: str):
        """
        初始化处理器。
        Args:
            job_id (str): 当前的作业 ID。
            chapter_title (str): 正在生成内容的章节标题，用于提供上下文。
        """
        from doc_agent.core.container import get_container
        container = get_container()
        self.publisher = container.redis_publisher
        self.job_id = job_id
        self.chapter_title = chapter_title
        super().__init__()

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """
        当 LLM 生成一个新 token 时被调用。
        """
        if not token:  # 忽略空 token
            return

        try:
            # 定义一个清晰的事件结构
            event_data = {
                "eventType": "on_llm_token",
                "data": {
                    "token": token,
                    "chapter_title": self.chapter_title,
                }
            }
            # 使用我们已经验证过的同步发布器来发送事件
            self.publisher.publish_event(self.job_id, event_data)
        except Exception as e:
            # 只记录警告，避免因为流式传输失败而中断整个文档生成过程
            logger.warning(
                f"Token streaming to Redis failed for job {self.job_id}: {e}")


def create_redis_callback_handler(job_id: str) -> RedisCallbackHandler:
    """
    创建Redis回调处理器的工厂函数

    Args:
        job_id: 作业ID

    Returns:
        RedisCallbackHandler实例
    """
    return RedisCallbackHandler(job_id)
