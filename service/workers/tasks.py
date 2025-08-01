import asyncio
import json

import redis.asyncio as redis
from loguru import logger

# 导入 Celery 应用程序
from .celery_app import celery_app


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
        redis_client = redis.from_url("redis://localhost:6379",
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
def generate_outline_from_query_task(job_id: str,
                                     task_prompt: str,
                                     context_files: dict = None) -> str:
    """
    从查询生成大纲的异步任务

    Args:
        job_id: 作业ID
        task_prompt: 用户的核心指令
        context_files: 上下文文件列表（可选）

    Returns:
        任务状态
    """
    logger.info(f"大纲生成任务开始 - Job ID: {job_id}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(
            _generate_outline_from_query_task_async(job_id, task_prompt,
                                                    context_files))
    except Exception as e:
        logger.error(f"大纲生成任务失败: {e}")
        return "FAILED"


async def _generate_outline_from_query_task_async(job_id: str,
                                                  task_prompt: str,
                                                  context_files: dict = None
                                                  ) -> str:
    """异步大纲生成任务的内部实现"""
    try:
        # 获取Redis客户端和发布器
        redis = await get_redis_client()
        from core.redis_stream_publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher(redis)

        # 发布任务开始事件
        await publisher.publish_task_started(job_id=job_id,
                                             task_type="outline_generation",
                                             task_prompt=task_prompt)

        logger.info(f"Job {job_id}: 开始生成大纲，主题: '{task_prompt[:50]}...'")

        # TODO: 调用新的"从 Query 到大纲"的 LangGraph 图
        # 这里将替换为实际的图执行逻辑
        # outline_graph = get_outline_generation_graph()
        # result = await outline_graph.ainvoke({
        #     "task_prompt": task_prompt,
        #     "context_files": context_files
        # })

        # 模拟大纲生成过程
        await asyncio.sleep(3)  # 模拟处理时间

        # 发布进度事件
        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="outline_generation",
                                              progress="正在分析用户需求",
                                              step="analysis")

        await asyncio.sleep(2)

        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="outline_generation",
                                              progress="正在搜索相关信息",
                                              step="search")

        await asyncio.sleep(2)

        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="outline_generation",
                                              progress="正在生成大纲结构",
                                              step="structure")

        # 生成示例大纲
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
def generate_document_from_outline_task(job_id: str, outline: dict) -> str:
    """
    从大纲生成文档的异步任务

    Args:
        job_id: 作业ID
        outline: 结构化的大纲对象

    Returns:
        任务状态
    """
    logger.info(f"文档生成任务开始 - Job ID: {job_id}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(
            _generate_document_from_outline_task_async(job_id, outline))
    except Exception as e:
        logger.error(f"文档生成任务失败: {e}")
        return "FAILED"


async def _generate_document_from_outline_task_async(job_id: str,
                                                     outline: dict) -> str:
    """异步文档生成任务的内部实现"""
    try:
        # 获取Redis客户端和发布器
        redis = await get_redis_client()
        from core.redis_stream_publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher(redis)

        # 发布任务开始事件
        await publisher.publish_task_started(job_id=job_id,
                                             task_type="document_generation",
                                             outline_title=outline.get(
                                                 "title", "未知标题"))

        logger.info(
            f"Job {job_id}: 开始生成文档，大纲标题: '{outline.get('title', '未知标题')}'")

        # TODO: 调用新的"从大纲到文档"的 LangGraph 图
        # 这里将替换为实际的图执行逻辑
        # document_graph = get_document_generation_graph()
        # result = await document_graph.ainvoke({
        #     "outline": outline
        # })

        # 模拟文档生成过程
        await asyncio.sleep(3)  # 模拟处理时间

        # 发布进度事件
        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="document_generation",
                                              progress="正在分析大纲结构",
                                              step="analysis")

        await asyncio.sleep(2)

        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="document_generation",
                                              progress="正在生成章节内容",
                                              step="content_generation")

        await asyncio.sleep(2)

        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="document_generation",
                                              progress="正在添加引用和链接",
                                              step="citations")

        await asyncio.sleep(2)

        await publisher.publish_task_progress(job_id=job_id,
                                              task_type="document_generation",
                                              progress="正在格式化和优化",
                                              step="formatting")

        # 生成示例文档
        document_result = {
            "title": outline.get("title", "技术文档"),
            "content": f"这是基于大纲 '{outline.get('title')}' 生成的完整文档内容...",
            "word_count": 2500,
            "char_count": 15000,
            "sections": len(outline.get("nodes", [])),
            "generated_at": str(asyncio.get_event_loop().time())
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
            duration="9s")

        logger.info(f"Job {job_id}: 文档生成完成")

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
def get_job_status(job_id: str) -> dict:
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


async def _get_job_status_async(job_id: str) -> dict:
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
def generate_document_celery(job_id: str, topic: str) -> dict:
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
