# service/src/doc_agent/core/outline_generator.py

from typing import Any

from doc_agent.core.container import container
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.tools.file_module import file_processor


async def generate_outline_async(
    task_id: str,
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
    logger.info(f"Task {task_id}: 开始在后台生成大纲，主题: '{task_prompt[:100]}...'")
    logger.info(f"  is_online: {is_online}, session_id: {session_id}")

    try:
        # 获取编译好的图（Graph）
        # 为每个作业创建专门的图执行器
        container_instance = container()
        outline_graph = container_instance.get_outline_graph_runnable_for_job(
            task_id)

        # 解析用户上传的context_files为sources
        initial_sources = []
        if context_files:
            logger.info(
                f"Task {task_id}: 开始解析 {len(context_files)} 个context_files")
            for file in context_files:
                try:
                    file_token = file.get("attachmentFileToken")
                    ocr_file_token = file.get("attachmentOCRResultToken")
                    if file_token:
                        # 使用file_processor解析文件为sources
                        sources = file_processor.filetoken_to_sources(
                            file_token,
                            ocr_file_token,
                            title=
                            f"Context File: {file.get('fileName', 'Unknown')}",
                            chunk_size=2000,
                            overlap=200)
                        initial_sources.extend(sources)
                        logger.info(
                            f"Task {task_id}: 成功解析文件 {file_token}，生成 {len(sources)} 个sources"
                        )
                    else:
                        logger.warning(
                            f"Task {task_id}: 文件缺少attachmentFileToken: {file}")
                except Exception as e:
                    logger.error(f"Task {task_id}: 解析文件失败: {e}")

            logger.info(
                f"Task {task_id}: 总共解析出 {len(initial_sources)} 个sources")

        # 准备图的输入
        graph_input = {
            "job_id": task_id,
            "topic": task_prompt,  # 将task_prompt映射到topic
            "is_online": is_online,
            "initial_sources": initial_sources,  # 添加解析后的sources
            "style_guide_content": style_guide_content,
            "requirements": requirements,
        }

        publish_event(task_id,
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
                                                         "job_id": task_id
                                                     }
                                                 }):
            # 在后台任务中，我们主要关心日志，所以可以打印出每个步骤的完成情况
            for key, _value in event.items():
                logger.info(f"Task {task_id} - 大纲生成步骤: '{key}' 已完成。")

        logger.success(f"Task {task_id}: 后台大纲生成任务成功完成。")

    except Exception as e:
        logger.error(f"Task {task_id}: 后台大纲生成任务失败。错误: {e}", exc_info=True)
