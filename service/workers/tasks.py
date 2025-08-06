import asyncio
import json
from typing import Union

import redis.asyncio as redis
from loguru import logger

# 导入 Celery 应用程序
from .celery_app import celery_app


def _get_detailed_progress_message(node_name: str) -> str:
    """
    根据节点名称生成详细的进度消息
    
    Args:
        node_name: 节点名称
        
    Returns:
        str: 详细的进度消息
    """
    progress_messages = {
        "initial_research": "已完成初始研究阶段，正在整理收集到的信息源，为大纲生成做准备...",
        "outline_generation": "已完成大纲生成阶段，正在优化文档结构和章节安排...",
        "planner": "已完成计划制定阶段，正在确定研究方向和重点内容...",
        "researcher": "已完成深入研究阶段，正在分析收集到的详细信息...",
        "writer": "已完成内容撰写阶段，正在完善文档内容...",
        "reflection": "已完成反思优化阶段，正在检查和完善文档质量...",
        "supervisor": "已完成监督决策阶段，正在评估当前进度并确定下一步行动...",
        "editor": "已完成编辑优化阶段，正在完善文档格式和内容...",
        "generation": "已完成内容生成阶段，正在创建最终的文档内容...",
        "research": "已完成研究阶段，正在整理和分析相关信息..."
    }

    return progress_messages.get(node_name, f"已完成步骤: {node_name}")


# 延迟导入container以避免循环导入
def get_container():
    """延迟导入container以避免循环导入"""
    from doc_agent.core.container import container
    return container


# Redis连接现在每次都创建新的，避免连接超时问题


async def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例"""
    try:
        # 每次都创建新的连接，避免连接超时问题
        from doc_agent.core.config import settings
        redis_client = redis.from_url(settings.redis_url,
                                      encoding="utf-8",
                                      decode_responses=True)
        # 测试连接
        await redis_client.ping()
        logger.info("Redis客户端连接成功")
        return redis_client
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        raise


@celery_app.task
def generate_outline_from_query_task(job_id: Union[str, int],
                                     task_prompt: str,
                                     is_online: bool = False,
                                     context_files: dict = None,
                                     style_guide_content: str = None,
                                     requirements: str = None,
                                     redis_stream_key: str = None) -> str:
    """
    从查询生成大纲的异步任务

    Args:
        job_id: 作业ID
        task_prompt: 用户的核心指令
        is_online: 是否调用web搜索
        context_files: 上下文文件列表（可选）
        style_guide_content: 风格指南内容（可选）
        requirements: 编写要求（可选）
        redis_stream_key: Redis流key（可选）

    Returns:
        任务状态
    """
    logger.info(f"大纲生成任务开始 - Job ID: {job_id}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(
            _generate_outline_from_query_task_async(job_id, task_prompt,
                                                    is_online, context_files,
                                                    style_guide_content,
                                                    requirements,
                                                    redis_stream_key))
    except Exception as e:
        logger.error(f"大纲生成任务失败: {e}")
        return "FAILED"


async def _generate_outline_from_query_task_async(
        job_id: Union[str, int],
        task_prompt: str,
        is_online: bool = False,
        context_files: dict = None,
        style_guide_content: str = None,
        requirements: str = None,
        redis_stream_key: str = None) -> str:
    """异步大纲生成任务的内部实现"""
    try:
        # 获取Redis客户端和发布器
        redis = await get_redis_client()
        from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher(redis)

        # 发布任务开始事件
        await publisher.publish_task_started(job_id=job_id,
                                             task_type="outline_generation",
                                             task_prompt=task_prompt)

        logger.info(f"Job {job_id}: 开始生成大纲，主题: '{task_prompt[:50]}...'")
        logger.info(f"  is_online: {is_online}")
        logger.info(
            f"  context_files: {len(context_files) if context_files else 0} 个文件"
        )
        logger.info(f"  style_guide_content: {bool(style_guide_content)}")
        logger.info(f"  requirements: {bool(requirements)}")
        logger.info(f"  redis_stream_key: {redis_stream_key}")

        # 使用真正的工作流生成大纲
        from doc_agent.core.container import container
        from doc_agent.graph.state import ResearchState
        import uuid

        # 创建初始状态
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        initial_state = ResearchState(
            topic=task_prompt,
            style_guide_content=style_guide_content or "",
            requirements_content=requirements or "",
            initial_sources=[],
            document_outline={},
            chapters_to_process=[],
            current_chapter_index=0,
            current_citation_index=1,
            completed_chapters=[],
            final_document="",
            sources=[],
            all_sources=[],
            cited_sources=[],
            cited_sources_in_chapter=[],
            messages=[],
            run_id=run_id,
        )

        # 发布进度事件
        await publisher.publish_task_progress(
            job_id=job_id,
            task_type="outline_generation",
            progress="正在分析您的需求，准备开始大纲生成流程...",
            step="analysis")

        # 执行真正的工作流
        outline_result = None
        try:
            logger.info(
                f"🔍 [API Task] 开始执行工作流，初始状态: {initial_state.get('topic', 'unknown')}"
            )

            async for step_output in container.outline_graph.astream(
                    initial_state):
                node_name = list(step_output.keys())[0]
                logger.info(f"✅ [API Task] Finished step: [ {node_name} ]")
                step_result = list(step_output.values())[0]

                # 发布进度事件
                progress_message = _get_detailed_progress_message(node_name)
                await publisher.publish_task_progress(
                    job_id=job_id,
                    task_type="outline_generation",
                    progress=progress_message,
                    step=node_name)

                logger.info(
                    f"🔍 [API Task] Step result keys: {list(step_result.keys()) if step_result else 'None'}"
                )

                if step_result and "document_outline" in step_result:
                    outline_result = step_result.get("document_outline")
                    logger.info(
                        f"✅ [API Task] 找到 document_outline，结构: {list(outline_result.keys()) if outline_result else 'None'}"
                    )
                    break
                else:
                    logger.info(f"📋 [API Task] Step {node_name} 完成，等待下一个步骤...")

        except Exception as e:
            logger.error(f"❌ [API Task] Error during outline generation: {e}")
            logger.error(
                f"❌ [API Task] Exception details: {type(e).__name__}: {str(e)}"
            )
            import traceback
            logger.error(f"❌ [API Task] Traceback: {traceback.format_exc()}")
            raise e

        if not outline_result:
            # 如果工作流失败，使用备用方案
            logger.warning("⚠️  工作流失败，使用备用大纲生成方案")
            outline_result = {
                "title":
                f"基于'{task_prompt}'的技术文档",
                "nodes": [{
                    "id": "node_1",
                    "title": "引言",
                    "content_summary": f"介绍{task_prompt}的基本概念和背景"
                }, {
                    "id": "node_2",
                    "title": "技术原理",
                    "content_summary": f"详细解释{task_prompt}的核心原理"
                }, {
                    "id": "node_3",
                    "title": "应用场景",
                    "content_summary": f"展示{task_prompt}的实际应用案例"
                }]
            }

        # 发布大纲生成完成事件
        await publisher.publish_outline_generated(job_id, outline_result)

        # 保存大纲结果到Redis
        outline_json = json.dumps(outline_result, ensure_ascii=False)
        await redis.set(f"job_result:{job_id}", outline_json, ex=3600)  # 1小时过期

        # 发布任务完成事件
        await publisher.publish_task_completed(
            job_id=job_id,
            task_type="outline_generation",
            result={"outline": outline_result},
            duration="7s")

        logger.info(f"Job {job_id}: 大纲生成完成")

        return "COMPLETED"

    except Exception as e:
        logger.error(f"Job {job_id}: 大纲生成失败: {e}")

        # 发布任务失败事件
        try:
            await publisher.publish_task_failed(job_id=job_id,
                                                task_type="outline_generation",
                                                error=str(e))
        except Exception as publish_error:
            logger.error(f"发布失败事件时出错: {publish_error}")

        return "FAILED"


@celery_app.task
def generate_document_from_outline_task(job_id: Union[str, int],
                                        outline: dict,
                                        session_id: str = None) -> str:
    """
    从大纲生成文档的异步任务

    Args:
        job_id: 作业ID
        outline: 结构化的大纲对象
        session_id: 会话ID，用于追踪

    Returns:
        任务状态
    """
    logger.info(f"文档生成任务开始 - Job ID: {job_id}, Session ID: {session_id}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(
            _generate_document_from_outline_task_async(job_id, outline,
                                                       session_id))
    except Exception as e:
        logger.error(f"文档生成任务失败: {e}")
        return "FAILED"


async def _generate_document_from_outline_task_async(job_id: Union[str, int],
                                                     outline: dict,
                                                     session_id: str = None
                                                     ) -> str:
    """异步文档生成任务的内部实现"""
    try:
        # 获取Redis客户端和发布器
        redis = await get_redis_client()
        from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher(redis)

        # 发布任务开始事件
        await publisher.publish_task_started(job_id=job_id,
                                             task_type="document_generation",
                                             outline_title=outline.get(
                                                 "title", "未知标题"))

        logger.info(
            f"Job {job_id}: 开始生成文档，大纲标题: '{outline.get('title', '未知标题')}'")

        # 初始化状态，将outline集成到二阶段工作流程
        from doc_agent.graph.state import ResearchState

        # 构建初始状态
        initial_state = ResearchState(run_id=str(job_id),
                                      topic=outline.get("title", "技术文档"),
                                      style_guide_content=None,
                                      requirements_content=None,
                                      initial_sources=[],
                                      document_outline=outline,
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
                                      messages=[])

        # 从outline中提取章节信息
        chapters = []
        for i, node in enumerate(outline.get("nodes", [])):
            chapter_info = {
                "chapter_title": node.get("title", f"章节 {i+1}"),
                "description": node.get("content_summary", ""),
                "node_id": node.get("id", f"node_{i+1}"),
                "children": node.get("children", [])
            }
            chapters.append(chapter_info)

        initial_state["chapters_to_process"] = chapters
        logger.info(f"Job {job_id}: 提取到 {len(chapters)} 个章节")

        # 发布进度事件
        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="document_generation",
                                              progress="正在分析大纲结构",
                                              step="analysis")

        # 获取容器和章节工作流图
        container = get_container()
        chapter_workflow = container.chapter_graph

        if not chapter_workflow:
            logger.error(f"Job {job_id}: 章节工作流图未找到")
            raise Exception("章节工作流图未初始化")

        # 开始处理每个章节
        completed_chapters = []
        all_sources = []
        cited_sources = []

        for chapter_index, chapter in enumerate(chapters):
            logger.info(
                f"Job {job_id}: 开始处理章节 {chapter_index + 1}/{len(chapters)}: {chapter['chapter_title']}"
            )

            # 更新当前章节索引
            current_state = initial_state.copy()
            current_state["current_chapter_index"] = chapter_index
            current_state["chapters_to_process"] = chapters
            current_state["completed_chapters"] = completed_chapters
            current_state["all_sources"] = all_sources
            current_state["cited_sources"] = cited_sources

            # 发布章节处理进度
            await publisher.publish_task_progress(
                job_id=job_id,
                task_type="document_generation",
                progress=f"正在处理章节: {chapter['chapter_title']}",
                step=f"chapter_{chapter_index + 1}")

            try:
                # 执行章节工作流
                result = await chapter_workflow.ainvoke(current_state)

                # 提取章节结果
                if "final_document" in result:
                    chapter_content = result["final_document"]
                else:
                    chapter_content = f"章节 {chapter['chapter_title']} 的内容..."

                # 收集引用源
                chapter_sources = result.get("cited_sources_in_chapter", [])
                all_sources.extend(chapter_sources)
                cited_sources.extend(chapter_sources)

                # 保存章节结果
                completed_chapter = {
                    "title": chapter["chapter_title"],
                    "content": chapter_content,
                    "sources": chapter_sources,
                    "chapter_index": chapter_index
                }
                completed_chapters.append(completed_chapter)

                logger.info(
                    f"Job {job_id}: 章节 {chapter['chapter_title']} 处理完成")

            except Exception as chapter_error:
                logger.error(
                    f"Job {job_id}: 章节 {chapter['chapter_title']} 处理失败: {chapter_error}"
                )
                # 继续处理下一个章节
                continue

        # 合并所有章节内容
        final_document_parts = []
        final_document_parts.append(f"# {outline.get('title', '技术文档')}\n\n")

        for chapter in completed_chapters:
            final_document_parts.append(f"## {chapter['title']}\n\n")
            final_document_parts.append(f"{chapter['content']}\n\n")

        final_document = "".join(final_document_parts)

        # 生成最终文档结果
        document_result = {
            "title": outline.get("title", "技术文档"),
            "content": final_document,
            "word_count": len(final_document.split()),
            "char_count": len(final_document),
            "sections": len(completed_chapters),
            "generated_at": str(asyncio.get_event_loop().time()),
            "chapters": completed_chapters,
            "sources": all_sources
        }

        # 发布文档生成完成事件
        await publisher.publish_document_generated(job_id, document_result)

        # 保存文档结果到Redis
        document_json = json.dumps(document_result, ensure_ascii=False)
        await redis.set(f"job_result:{job_id}", document_json,
                        ex=3600)  # 1小时过期

        # 发布任务完成事件
        await publisher.publish_task_completed(
            job_id=job_id,
            task_type="document_generation",
            result={"document": document_result},
            duration="completed")

        logger.info(f"Job {job_id}: 文档生成完成，共处理 {len(completed_chapters)} 个章节")

        return "COMPLETED"

    except Exception as e:
        logger.error(f"Job {job_id}: 文档生成失败: {e}")

        # 发布任务失败事件
        try:
            await publisher.publish_task_failed(
                job_id=job_id, task_type="document_generation", error=str(e))
        except Exception as publish_error:
            logger.error(f"发布失败事件时出错: {publish_error}")

        return "FAILED"


@celery_app.task
def get_job_status(job_id: Union[str, int]) -> dict:
    """
    获取任务状态

    Args:
        job_id: 任务ID

    Returns:
        任务状态字典
    """
    try:
        # 使用同步方式运行异步函数
        return asyncio.run(_get_job_status_async(job_id))
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return {"status": "error", "error": str(e)}


async def _get_job_status_async(job_id: Union[str, int]) -> dict:
    """异步获取任务状态的内部实现"""
    try:
        redis = await get_redis_client()
        job_data = await redis.hgetall(f"job:{job_id}")

        if not job_data:
            return {"status": "not_found"}

        return job_data

    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return {"status": "error", "error": str(e)}


# Celery 任务导入
from .celery_app import celery_app


@celery_app.task
def run_main_workflow(job_id: str, topic: str, genre: str = "default") -> str:
    """
    主要的异步工作流函数
    使用真实的图执行器和Redis回调处理器

    Args:
        job_id: 任务ID
        topic: 文档主题
        genre: 文档类型，用于选择相应的prompt策略

    Returns:
        任务状态
    """
    logger.info(f"主工作流开始 - Job ID: {job_id}, Topic: {topic}, Genre: {genre}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(_run_main_workflow_async(job_id, topic, genre))
    except Exception as e:
        logger.error(f"主工作流任务失败: {e}")
        return "FAILED"


async def _run_main_workflow_async(job_id: str,
                                   topic: str,
                                   genre: str = "default") -> str:
    """异步主工作流任务的内部实现"""
    try:
        # 获取Redis客户端
        redis = await get_redis_client()

        # 更新任务状态为进行中
        await redis.hset(f"job:{job_id}",
                         mapping={
                             "status": "processing",
                             "topic": topic,
                             "genre": genre,
                             "started_at": str(asyncio.get_event_loop().time())
                         })

        # 获取带有Redis回调处理器的图执行器
        logger.info(f"Job {job_id}: 获取图执行器...")
        container = get_container()
        runnable = container.get_graph_runnable_for_job(job_id, genre)

        # 创建初始状态
        from doc_agent.graph.state import ResearchState
        import uuid

        run_id = f"run-{uuid.uuid4().hex[:8]}"
        initial_state = ResearchState(
            topic=topic,
            style_guide_content="",
            requirements_content="",
            initial_sources=[],
            document_outline={},
            chapters_to_process=[],
            current_chapter_index=0,
            current_citation_index=1,
            completed_chapters=[],
            final_document="",
            sources=[],
            all_sources=[],
            cited_sources=[],
            cited_sources_in_chapter=[],
            messages=[],
            run_id=run_id,
        )

        logger.info(f"Job {job_id}: 开始执行工作流...")

        # 执行工作流
        async for step_output in runnable.astream(initial_state):
            node_name = list(step_output.keys())[0]
            logger.info(f"Job {job_id}: 完成步骤 [{node_name}]")

        # 更新任务状态为完成
        await redis.hset(f"job:{job_id}",
                         mapping={
                             "status": "completed",
                             "completed_at":
                             str(asyncio.get_event_loop().time())
                         })

        logger.info(f"Job {job_id}: 工作流执行完成")
        return "COMPLETED"

    except Exception as e:
        logger.error(f"Job {job_id}: 工作流执行失败: {e}")

        # 更新任务状态为失败
        try:
            await redis.hset(f"job:{job_id}",
                             mapping={
                                 "status": "failed",
                                 "error": str(e),
                                 "failed_at":
                                 str(asyncio.get_event_loop().time())
                             })
        except Exception as update_error:
            logger.error(f"更新任务状态失败: {update_error}")

        return "FAILED"


@celery_app.task
def test_celery_task(message: str) -> str:
    """
    测试 Celery 任务
    
    Args:
        message: 测试消息
        
    Returns:
        str: 返回的消息
    """
    logger.info(f"执行 Celery 测试任务: {message}")
    return f"Celery 任务执行成功: {message}"


@celery_app.task
def generate_document_celery(job_id: Union[str, int], topic: str) -> dict:
    """
    使用 Celery 执行文档生成任务
    
    Args:
        job_id: 作业ID
        topic: 文档主题
        
    Returns:
        dict: 执行结果
    """
    logger.info(f"开始 Celery 文档生成任务: {job_id}, 主题: {topic}")

    try:
        # 这里可以调用现有的文档生成逻辑
        # 暂时返回模拟结果
        result = {
            "job_id": job_id,
            "status": "completed",
            "topic": topic,
            "document_length": 5000,
            "chapters": 5
        }

        logger.info(f"Celery 文档生成任务完成: {job_id}")
        return result

    except Exception as e:
        logger.error(f"Celery 文档生成任务失败: {job_id}, 错误: {e}")
        return {"job_id": job_id, "status": "failed", "error": str(e)}


@celery_app.task
def process_files_task(context_id: str, files: list[dict]) -> str:
    """
    处理上传文件的异步任务
    
    Args:
        context_id: 上下文ID
        files: 文件列表，每个文件包含 file_id, file_name, storage_url, file_type
        
    Returns:
        任务状态
    """
    logger.info(f"文件处理任务开始 - Context ID: {context_id}, 文件数量: {len(files)}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(_process_files_task_async(context_id, files))
    except Exception as e:
        logger.error(f"文件处理任务失败: {e}")
        return "FAILED"


async def _process_files_task_async(context_id: str, files: list[dict]) -> str:
    """异步文件处理任务的内部实现"""
    try:
        # 获取Redis客户端
        redis_client = await get_redis_client()

        # 初始化内容列表
        style_contents = []
        requirements_contents = []

        # 遍历所有文件
        for file_info in files:
            file_id = file_info.get("file_id")
            file_name = file_info.get("file_name")
            storage_url = file_info.get("storage_url")
            file_type = file_info.get("file_type", "content")  # 默认为content

            logger.info(f"处理文件: {file_name} (类型: {file_type})")

            if file_type == "content":
                # 保持现有的向量索引逻辑
                logger.info(f"处理内容文件: {file_name}")
                # TODO: 实现向量索引逻辑
                # 这里应该调用现有的向量索引处理函数

            elif file_type == "style":
                # 读取样式指南内容
                logger.info(f"处理样式指南文件: {file_name}")
                try:
                    content = read_file_content(storage_url)
                    style_contents.append(content)
                    logger.info(f"样式指南文件处理完成: {file_name}")
                except Exception as e:
                    logger.error(f"处理样式指南文件失败: {file_name}, 错误: {e}")

            elif file_type == "requirements":
                # 读取需求文档内容
                logger.info(f"处理需求文档文件: {file_name}")
                try:
                    content = read_file_content(storage_url)
                    requirements_contents.append(content)
                    logger.info(f"需求文档文件处理完成: {file_name}")
                except Exception as e:
                    logger.error(f"处理需求文档文件失败: {file_name}, 错误: {e}")

            else:
                logger.warning(f"未知文件类型: {file_type}, 文件: {file_name}")

        # 存储样式指南内容到Redis
        if style_contents:
            style_guide_content = "\n\n".join(style_contents)
            await redis_client.hset(f"context:{context_id}",
                                    "style_guide_content", style_guide_content)
            logger.info(f"样式指南内容已存储到Redis, 长度: {len(style_guide_content)} 字符")

        # 存储需求文档内容到Redis
        if requirements_contents:
            requirements_content = "\n\n".join(requirements_contents)
            await redis_client.hset(f"context:{context_id}",
                                    "requirements_content",
                                    requirements_content)
            logger.info(f"需求文档内容已存储到Redis, 长度: {len(requirements_content)} 字符")

        # 更新上下文状态为就绪
        await redis_client.hset(f"context:{context_id}", "status", "READY")

        logger.info(f"文件处理任务完成 - Context ID: {context_id}")
        return "SUCCESS"

    except Exception as e:
        logger.error(f"文件处理任务失败 - Context ID: {context_id}, 错误: {e}")
        return "FAILED"


def read_file_content(storage_url: str) -> str:
    """
    读取文件内容的工具函数
    
    Args:
        storage_url: 文件存储URL
        
    Returns:
        文件内容字符串
    """
    # TODO: 实现实际的文件读取逻辑
    # 这里应该根据storage_url读取文件内容
    # 暂时返回模拟内容
    logger.info(f"读取文件内容: {storage_url}")
    return f"模拟文件内容 - {storage_url}"
