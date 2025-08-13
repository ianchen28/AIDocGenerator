# service/src/doc_agent/core/outline_generator.py

from typing import Any

from doc_agent.core.container import container
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.schemas import Source
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

        # 解析用户上传的context_files为sources
        initial_sources = []
        user_data_reference_files: list[Source] = []  # 用户上传的数据参考文件
        user_style_guide_content: list[Source] = []  # 用户上传的样式指南
        user_requirements_content: list[Source] = []  # 用户上传的需求文档
        user_outline_file: str = ""

        # 先解析context_files来获取user_outline_file
        if context_files:
            logger.info(
                f"Task {task_id}: 开始解析 {len(context_files)} 个context_files")
            for file in context_files:
                try:
                    file_token = file.get("attachmentFileToken")
                    ocr_file_token = file.get("attachmentOCRResultToken")
                    # 用户上传大纲文件，单独处理
                    if file.get("attachmentType") == 0:
                        user_outline_file = file_token
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
                    if file.get("attachmentType") == 1:
                        user_data_reference_files.extend(sources)
                    elif file.get("attachmentType") == 2:
                        user_style_guide_content.extend(sources)
                    elif file.get("attachmentType") == 3:
                        user_requirements_content.extend(sources)
                except Exception as e:
                    logger.error(f"Task {task_id}: 解析文件失败: {e}")

            logger.info(
                f"Task {task_id}: 总共解析出 {len(initial_sources)} 个sources")

        # 根据是否有用户上传的大纲文件来决定使用哪个图
        if user_outline_file:
            logger.info(f"Task {task_id}: 检测到用户上传的大纲文件，使用大纲加载器图")
            outline_graph = container_instance.get_outline_loader_graph_runnable_for_job(
                task_id)
        else:
            logger.info(f"Task {task_id}: 未检测到用户上传的大纲文件，使用标准大纲生成图")
            outline_graph = container_instance.get_outline_graph_runnable_for_job(
                task_id)

        # 准备图的输入
        graph_input = {
            "job_id": task_id,
            "task_prompt": task_prompt,  # 将task_prompt映射到topic
            "is_online": is_online,
            "initial_sources": initial_sources,  # 添加解析后的sources
            "style_guide_content": style_guide_content,
            "requirements": requirements,
            "user_outline_file": user_outline_file,
            "user_data_reference_files": user_data_reference_files,
            "user_style_guide_content": user_style_guide_content,
            "user_requirements_content": user_requirements_content,
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
