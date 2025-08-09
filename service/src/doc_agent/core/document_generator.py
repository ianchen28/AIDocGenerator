"""service/src/doc_agent/core/document_generator.py"""

from typing import Optional

from doc_agent.core.container import container
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.graph.state import ResearchState
from doc_agent.tools.file_processor import file_processor


async def generate_document_sync(task_id: str,
                                 task_prompt: str,
                                 session_id: str,
                                 outline_json_file: str,
                                 context_files: Optional[list[dict]] = None,
                                 is_online: bool = False):
    """
    (后台任务) 通过直接调用图（Graph）来从大纲生成完整文档。
    """
    logger.info(f"Job {task_id}: 开始在后台生成文档，SessionId: {session_id}")

    try:
        # 获取已构建的文档生成图
        container_instance = container()
        document_graph = container_instance.get_document_graph_runnable_for_job(
            task_id)

        # 准备图的初始状态
        initial_state = generate_initial_state(task_prompt, outline_json_file,
                                               task_id, context_files,
                                               is_online)

        logger.info(f"Job {task_id}: 开始执行文档生成图...")
        # 以流式方式执行图
        async for event in document_graph.astream(initial_state,
                                                  config={
                                                      "configurable": {
                                                          "thread_id":
                                                          session_id,
                                                          "job_id": task_id
                                                      }
                                                  }):
            for key, _value in event.items():
                logger.info(f"Job {task_id} - 文档生成步骤: '{key}' 已完成。")
        publish_event(task_id,
                      "文档生成",
                      "document_generation",
                      "SUCCESS", {"description": "文档生成已完成"},
                      task_finished=True)

        logger.success(f"Job {task_id}: 后台文档生成任务成功完成。")

    except Exception as e:
        # 使用逗号参数传入异常而不是在 f-string 中使用替换，避免格式化错误
        logger.error("Job {}: 后台文档生成任务失败。错误: {}", task_id, e, exc_info=True)


def generate_initial_state(task_prompt: str,
                           outline_json_file: str,
                           task_id: str,
                           context_files: Optional[list[dict]] = None,
                           is_online: bool = False) -> ResearchState:
    """
    生成初始状态
    
    outline_json_file: 大纲文件路径
    """
    document_outline = file_processor.filetoken_to_outline(outline_json_file)
    word_count = document_outline["word_count"]
    logger.info(f"word_count: {word_count}")
    logger.info(f"document_outline: {document_outline}")
    # 解析用户上传文件
    user_data_reference_files = []
    user_style_guide_content = []
    user_requirements_content = []
    for file in context_files:
        # 文件装载为 Source 对象
        sources = file_processor.filetoken_to_sources(
            file.get("attachmentFileToken"))
        for source in sources:
            if file.get("attachmentType") == 1:
                user_data_reference_files.append(source)
            elif file.get("attachmentType") == 2:
                user_style_guide_content.append(source)
            elif file.get("attachmentType") == 3:
                user_requirements_content.append(source)

    return ResearchState(
        job_id=task_id,
        task_prompt=task_prompt,
        topic=task_prompt,  # 使用 task_prompt 作为 topic
        document_outline=document_outline,
        user_data_reference_files=user_data_reference_files,
        user_style_guide_content=user_style_guide_content,
        user_requirements_content=user_requirements_content,
        is_online=is_online,
        word_count=word_count,
        # 添加其他必需字段的默认值
        run_id=None,
        style_guide_content=None,
        requirements_content=None,
        initial_sources=[],
        chapters_to_process=[],
        current_chapter_index=0,
        completed_chapters=[],
        final_document="",
        research_plan="",
        search_queries=[],
        gathered_sources=[],
        sources=[],
        all_sources=[],
        current_citation_index=1,
        cited_sources=[],
        cited_sources_in_chapter=[],
        messages=[],
    )
