# service/src/doc_agent/core/outline_generator.py

import asyncio
from doc_agent.core.logger import logger
from typing import List, Dict, Any

from doc_agent.core.container import container
from doc_agent.graph.callbacks import publish_event


async def generate_outline_async(
    job_id: str,
    session_id: str,
    task_prompt: str,
    is_online: bool = False,
    context_files: list[dict[str, Any]] = None,
    style_guide_content: str = None,
    requirements: str = None,
):
    """
    (后台任务) 通过直接调用图（Graph）来生成大纲。
    """
    logger.info(f"Job {job_id}: 开始在后台生成大纲，主题: '{task_prompt[:100]}...'")
    logger.info(f"  is_online: {is_online}, session_id: {session_id}")

    try:
        # 获取编译好的图（Graph）
        # 为每个作业创建专门的图执行器
        container_instance = container()
        outline_graph = container_instance.get_outline_graph_runnable_for_job(
            job_id)

        # 准备图的输入
        graph_input = {
            "job_id": job_id,
            "topic": task_prompt,  # 将task_prompt映射到topic
            "is_online": is_online,
            "context_files": context_files or [],
            "style_guide_content": style_guide_content,
            "requirements": requirements,
        }

        publish_event(job_id,
                      "大纲生成",
                      "outline_generation",
                      "START", {},
                      task_finished=False)

        # 以流式方式调用图并获取结果，这样可以处理过程中的事件
        # config 用于设置会话ID，以便使用对话记忆
        async for event in outline_graph.astream(graph_input,
                                                 config={
                                                     "configurable": {
                                                         "thread_id":
                                                         session_id,
                                                         "job_id": job_id
                                                     }
                                                 }):
            # 在后台任务中，我们主要关心日志，所以可以打印出每个步骤的完成情况
            for key, _value in event.items():
                logger.info(f"Job {job_id} - 大纲生成步骤: '{key}' 已完成。")

        logger.success(f"Job {job_id}: 后台大纲生成任务成功完成。")

    except Exception as e:
        logger.error(f"Job {job_id}: 后台大纲生成任务失败。错误: {e}", exc_info=True)
