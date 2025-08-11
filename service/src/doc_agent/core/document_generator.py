"""service/src/doc_agent/core/document_generator.py"""

from typing import Optional

from doc_agent.core.container import container
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.graph.state import ResearchState
from doc_agent.tools.file_module import file_processor
from doc_agent.schemas import Source


async def generate_document_sync(task_id: str,
                                 task_prompt: str,
                                 session_id: str,
                                 outline_file_token: str,
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
        initial_state = generate_initial_state(task_prompt, outline_file_token,
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
                           outline_file_token: str,
                           task_id: str,
                           context_files: Optional[list[dict]] = None,
                           is_online: bool = False) -> ResearchState:
    """
    生成初始状态
    
    outline_file_token: 大纲文件的storage token
    """
    document_outline = file_processor.filetoken_to_outline(outline_file_token)
    word_count = document_outline["word_count"]
    logger.info(f"word_count: {word_count}")
    logger.info(f"document_outline: {document_outline}")
    # 解析用户上传文件
    user_data_reference_files = []
    user_style_guide_content = []
    user_requirements_content = []
    initial_sources = []  # 用于搜索知识的sources

    if context_files:
        logger.info(f"Job {task_id}: 开始解析 {len(context_files)} 个context_files")
        user_data_reference_files: list[Source] = []  # 用户上传的数据参考文件
        user_style_guide_content: list[Source] = []  # 用户上传的样式指南
        user_requirements_content: list[Source] = []  # 用户上传的需求文档
        for file in context_files:
            try:
                file_token = file.get("attachmentFileToken")
                ocr_file_token = file.get("attachmentOCRResultToken")
                if file_token:
                    # 文件装载为 Source 对象
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
                logger.error(f"Job {task_id}: 解析文件失败: {e}")

        logger.info(
            f"Job {task_id}: 总共解析出 {len(initial_sources)} 个sources用于搜索")
    else:
        logger.info(f"Job {task_id}: 没有context_files需要解析")

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
        initial_sources=initial_sources,  # 使用解析的sources
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
