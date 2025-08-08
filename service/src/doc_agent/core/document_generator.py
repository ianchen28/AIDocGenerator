# service/src/doc_agent/core/document_generator.py

import json
from typing import Optional

from doc_agent.core.container import container
from doc_agent.core.logger import logger
from doc_agent.graph.state import ResearchState
from doc_agent.schemas import Source
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
                                               context_files, is_online)

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

        logger.success(f"Job {task_id}: 后台文档生成任务成功完成。")

    except Exception as e:
        logger.error(f"Job {task_id}: 后台文档生成任务失败。错误: {e}", exc_info=True)


def generate_initial_state(task_prompt: str,
                           outline_json_file: str,
                           context_files: Optional[list[dict]] = None,
                           is_online: bool = False) -> ResearchState:
    """
    生成初始状态
    
    outline_json_file: 大纲文件路径
    内容为：
    ```json
    [
        {
            "type": "outline-title",
            "content": {
            "title": "生命中的美好与沉思",
            "wordcount": 5000,
            "wordcountType": "diy"
            }
        },
        {
            "type": "outline",
            "content": [
            {
                "id": 1,
                "image_infos": [],
                "title": "自然之美",
                "content": "本章探讨了自然界的美如何影响人类的情感和思考，以及人与自然之间的深刻联系。",
                "children": [
                {
                    "id": 1.1,
                    "image_infos": [],
                    "title": "自然的启示",
                    "content": "通过自然界的例子，如四季更替、日出日落，探讨自然界如何教会我们生命的道理。",
                    "children": []
                },
                {
                    "id": 1.2,
                    "image_infos": [],
                    "title": "心灵的慰藉",
                    "content": "分析自然景观如何成为人们心灵的避风港，提供安慰和力量。",
                    "children": []
                },
                {
                    "id": 1.3,
                    "image_infos": [],
                    "title": "人与自然的和谐",
                    "content": "讨论如何在现代社会中保持与自然的和谐关系，以及这种和谐对个人和社会的重要性。",
                    "children": []
                }
                ]
            },
            {
                "id": 2,
                "image_infos": [],
                "title": "情感之深",
                "content": "本章聚焦于人生中的情感体验，包括亲情、友情和爱情，探讨这些情感如何塑造我们的生活。",
                "children": [
                {
                    "id": 2.1,
                    "image_infos": [],
                    "title": "亲情的力量",
                    "content": "通过具体的故事和案例，展示亲情如何在困难时刻给予我们力量和支持。",
                    "children": []
                },
                {
                    "id": 2.2,
                    "image_infos": [],
                    "title": "友情的珍贵",
                    "content": "分析友情在人生中的重要性，以及如何维护和珍惜真正的友谊。",
                    "children": []
                },
                {
                    "id": 2.3,
                    "image_infos": [],
                    "title": "爱情的甜蜜与苦涩",
                    "content": "探讨爱情中的喜悦与挑战，以及爱情如何影响个人的成长。",
                    "children": []
                }
                ]
            }
            ]
        }
        ]
    ```

    其他字段参考：
    {
        "sessionId": 1,
        "taskPrompt": "分析“分治策略”在解决大型语言模型上下文长度限制问题中的应用、挑战与未来方向",
        "isOnline": false,
        "contextFiles": [
            {
            "id": 123,   //long
            "attachmentType": 0,    //附件类型(0-大纲模板/1-上传参考资料/2-知识选择参考资料)
            "attachmentName": "s3://...",   //文件名称
            "attachmentFileType": "content"，    //文件类型  docx、pdf、...
            "attachmentFileToken":"",   //文件token
            "attachmentOCRResultToken":"" //ocr结果文件token
            "isContentRefer": 0,   //是否内容参考(0-否/1-是)
            "isStyleImitative": 0,   //是否风格仿写(0-否/1-是)
            "isWritingRequirement": 0  //是否编写要求(0-否/1-是)
            },
            "outline":""   //大纲文件token，仅生成文档传
        }
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
