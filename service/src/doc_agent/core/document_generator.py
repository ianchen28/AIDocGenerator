"""service/src/doc_agent/core/document_generator.py"""

from typing import Optional

from doc_agent.core.container import container
from doc_agent.core.file_parser import parse_context_files
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.graph.state import ResearchState
from doc_agent.tools.file_module import file_processor


def generate_initial_state(task_prompt: str,
                           outline_file_token: str,
                           task_id: str,
                           context_files: Optional[list[dict]] = None,
                           is_online: bool = False) -> ResearchState:
    """
    生成初始状态

    Args:
        task_prompt: 任务提示
        outline_file_token: 大纲文件的storage token
        task_id: 任务ID
        context_files: 上下文文件列表
        is_online: 是否在线模式

    Returns:
        ResearchState: 初始状态对象
    """
    # 解析大纲文件
    document_outline = file_processor.filetoken_to_outline(outline_file_token)
    if not document_outline:
        logger.error("解析大纲失败，file_token 无法转换为有效的 outline。token: {}",
                     outline_file_token)
        raise ValueError("无效的大纲文件：解析失败或格式不正确")

    word_count = document_outline["word_count"]
    title = document_outline["title"]
    logger.info(f"word_count: {word_count}")
    logger.info(f"document_outline: {document_outline}")

    # 解析用户上传文件
    user_data_reference_files, user_style_guide_content, user_requirements_content, _ = parse_context_files(
        context_files or [], task_id, "document")

    # 创建 ResearchState 前记录数据
    logger.info(
        f"Job {task_id}: 创建 ResearchState，user_data_reference_files 数量: {len(user_data_reference_files)}"
    )

    return ResearchState(
        job_id=task_id,
        task_prompt=task_prompt,
        topic=title,
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
        # 获取容器实例
        container_instance = container()
        document_graph = container_instance.get_document_graph_runnable_for_job(
            task_id)

        # 准备图的初始状态
        initial_state = generate_initial_state(task_prompt, outline_file_token,
                                               task_id, context_files,
                                               is_online)

        # 发布开始事件
        publish_event(task_id,
                      "文档生成",
                      "document_generation",
                      "START", {},
                      task_finished=False)

        logger.info(f"Job {task_id}: 开始执行文档生成图...")

        # 以流式方式执行图并获取最终结果
        final_state = None
        async for event in document_graph.astream(initial_state,
                                                  config={
                                                      "configurable": {
                                                          "thread_id":
                                                          session_id,
                                                          "job_id": task_id
                                                      }
                                                  }):
            for key, value in event.items():
                logger.info(f"Job {task_id} - 文档生成步骤: '{key}' 已完成。")
                final_state = value  # 保存最终状态

        # 检查是否成功生成了文档
        if final_state and hasattr(final_state, 'get'):
            final_document = final_state.get("final_document", "")
            if final_document:
                logger.info(
                    f"Job {task_id}: 文档生成成功，文档长度: {len(final_document)} 字符")
            else:
                logger.warning(f"Job {task_id}: 文档生成完成，但未找到最终文档内容")
        else:
            logger.warning(f"Job {task_id}: 文档生成完成，但未获取到最终状态")

        # 发布完成事件
        publish_event(task_id,
                      "文档生成",
                      "document_generation",
                      "SUCCESS", {"description": "文档生成已完成"},
                      task_finished=True)

        logger.success(f"Job {task_id}: 后台文档生成任务成功完成。")

    except Exception as e:
        logger.error("Job {}: 后台文档生成任务失败。错误: {}", task_id, e, exc_info=True)
