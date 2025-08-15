# service/src/doc_agent/core/outline_generator.py

from typing import Any

from doc_agent.core.container import container
from doc_agent.core.file_parser import parse_context_files
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event


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
        # 获取容器实例
        container_instance = container()

        # 解析用户上传的context_files
        user_data_reference_files, user_style_guide_content, user_requirements_content, user_outline_file = parse_context_files(
            context_files or [], task_id, "outline")

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
            "task_prompt": task_prompt,
            "is_online": is_online,
            "style_guide_content": style_guide_content,
            "requirements": requirements,
            "user_outline_file": user_outline_file,
            "user_data_reference_files": user_data_reference_files,
            "user_style_guide_content": user_style_guide_content,
            "user_requirements_content": user_requirements_content,
        }

        # 发布开始事件
        publish_event(task_id,
                      "大纲生成",
                      "outline_generation",
                      "START", {},
                      task_finished=False)

        # 以流式方式调用图并获取结果
        async for event in outline_graph.astream(graph_input,
                                                 config={
                                                     "configurable": {
                                                         "thread_id":
                                                         session_id,
                                                         "job_id": task_id
                                                     }
                                                 }):
            for key, _value in event.items():
                logger.info(f"Task {task_id} - 大纲生成步骤: '{key}' 已完成。")

        # 发布完成事件
        publish_event(task_id,
                      "大纲生成",
                      "outline_generation",
                      "SUCCESS", {"description": "大纲生成已完成"},
                      task_finished=True)

        logger.success(f"Task {task_id}: 后台大纲生成任务成功完成。")

    except Exception as e:
        logger.error(f"Task {task_id}: 后台大纲生成任务失败。错误: {e}", exc_info=True)
