import asyncio
import redis.asyncio as redis
import json
from loguru import logger
from typing import Optional


# 延迟导入container以避免循环导入
def get_container():
    """延迟导入container以避免循环导入"""
    try:
        # 尝试相对导入
        from ..core.container import container
        return container
    except ImportError:
        # 如果相对导入失败，尝试绝对导入
        import sys
        from pathlib import Path

        # 添加项目根目录到Python路径
        current_file = Path(__file__)
        service_dir = current_file.parent.parent
        if str(service_dir) not in sys.path:
            sys.path.insert(0, str(service_dir))

        from core.container import container
        return container


# Redis客户端实例
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url("redis://localhost:6379",
                                          encoding="utf-8",
                                          decode_responses=True)
            # 测试连接
            await redis_client.ping()
            logger.info("Redis客户端连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    return redis_client


async def generate_outline_task(job_id: str) -> str:
    """
    生成大纲的异步任务
    
    Args:
        job_id: 作业ID
        
    Returns:
        任务状态
    """
    logger.info(f"大纲生成任务开始 - Job ID: {job_id}")

    try:
        # 获取Redis客户端
        redis = await get_redis_client()

        # 获取作业信息
        job_data = await redis.hgetall(f"job:{job_id}")
        if not job_data:
            logger.error(f"Job {job_id}: 作业不存在")
            return "FAILED"

        task_prompt = job_data.get("task_prompt", "")
        if not task_prompt:
            logger.error(f"Job {job_id}: 缺少任务提示")
            return "FAILED"

        # 更新大纲状态为生成中
        await redis.hset(f"job:{job_id}:outline",
                         mapping={
                             "outline_status": "GENERATING",
                             "started_at": str(asyncio.get_event_loop().time())
                         })

        logger.info(f"Job {job_id}: 开始生成大纲，主题: '{task_prompt[:50]}...'")

        # 模拟大纲生成过程 - 稍后将替换为实际的graph执行
        logger.debug(f"Job {job_id}: 正在生成大纲...")
        await asyncio.sleep(8)  # 模拟大纲生成耗时

        # 创建模拟大纲数据（基于任务提示）
        mock_outline = {
            "title":
            f"关于'{task_prompt[:30]}...'的文档",
            "nodes": [{
                "id": "node_1",
                "title": "概述与背景",
                "content_summary": f"介绍{task_prompt[:20]}的基本概念和重要性",
                "children": []
            }, {
                "id": "node_2",
                "title": "核心内容分析",
                "content_summary": f"深入分析{task_prompt[:20]}的关键要素",
                "children": []
            }, {
                "id": "node_3",
                "title": "应用与实践",
                "content_summary": f"探讨{task_prompt[:20]}的实际应用场景",
                "children": []
            }]
        }

        # 更新大纲状态为完成，并存储大纲数据
        await redis.hset(f"job:{job_id}:outline",
                         mapping={
                             "outline_status":
                             "READY",
                             "outline_data":
                             json.dumps(mock_outline, ensure_ascii=False),
                             "completed_at":
                             str(asyncio.get_event_loop().time())
                         })

        logger.info(f"Job {job_id}: 大纲生成完成")
        return "COMPLETED"

    except Exception as e:
        logger.error(f"Job {job_id}: 大纲生成失败 - {e}")

        # 更新大纲状态为失败
        try:
            redis = await get_redis_client()
            await redis.hset(f"job:{job_id}:outline",
                             mapping={
                                 "outline_status": "FAILED",
                                 "error": str(e),
                                 "failed_at":
                                 str(asyncio.get_event_loop().time())
                             })
        except Exception as redis_error:
            logger.error(f"无法更新Redis中的失败状态: {redis_error}")

        return "FAILED"


async def run_main_workflow(job_id: str, topic: str) -> str:
    """
    主要的异步工作流函数
    使用真实的图执行器和Redis回调处理器
    
    Args:
        job_id: 任务ID
        topic: 文档主题
        
    Returns:
        任务状态
    """
    logger.info(f"主工作流开始 - Job ID: {job_id}, Topic: {topic}")

    try:
        # 获取Redis客户端
        redis = await get_redis_client()

        # 更新任务状态为进行中
        await redis.hset(f"job:{job_id}",
                         mapping={
                             "status": "processing",
                             "topic": topic,
                             "started_at": str(asyncio.get_event_loop().time())
                         })

        # 1. 获取带有Redis回调处理器的图执行器
        logger.info(f"Job {job_id}: 获取图执行器...")
        container = get_container()
        runnable = container.get_graph_runnable_for_job(job_id)

        # 2. 从Redis获取初始状态数据
        logger.info(f"Job {job_id}: 获取初始状态数据...")

        # 获取作业基本信息
        job_data = await redis.hgetall(f"job:{job_id}")
        if not job_data:
            logger.error(f"Job {job_id}: 作业数据不存在")
            return "FAILED"

        # 获取大纲数据（如果存在）
        outline_data = await redis.hgetall(f"job:{job_id}:outline")
        document_outline = None

        if outline_data and outline_data.get("outline_data"):
            try:
                outline_json = outline_data.get("outline_data")
                document_outline = json.loads(outline_json)
                logger.info(
                    f"Job {job_id}: 找到现有大纲，包含 {len(document_outline.get('nodes', []))} 个节点"
                )
            except json.JSONDecodeError as e:
                logger.warning(f"Job {job_id}: 大纲数据解析失败，将重新生成: {e}")
                document_outline = None

        # 3. 构建初始状态
        initial_state = {
            "topic": topic,
            "messages": [],
            "initial_gathered_data": "",  # 将在图执行中填充
            "document_outline": document_outline or {},  # 使用现有大纲或空字典
            "chapters_to_process": [],  # 将在图执行中填充
            "current_chapter_index": 0,
            "completed_chapters_content": [],
            "final_document": "",
            "research_plan": "",
            "search_queries": [],
            "gathered_data": ""
        }

        logger.info(f"Job {job_id}: 初始状态构建完成")
        logger.debug(
            f"Job {job_id}: 初始状态 - Topic: {topic}, 有大纲: {bool(document_outline)}"
        )

        # 4. 执行图工作流
        logger.info(f"Job {job_id}: 开始执行主工作流图...")

        # 发布开始事件
        await redis.publish(
            f"job:{job_id}:events",
            json.dumps(
                {
                    "event": "phase_update",
                    "data": {
                        "phase": "WORKFLOW_START",
                        "message": "开始执行主文档生成工作流...",
                        "job_id": job_id
                    },
                    "timestamp": str(asyncio.get_event_loop().time())
                },
                ensure_ascii=False))

        # 执行图
        result = await runnable.ainvoke(initial_state)

        # 5. 处理执行结果
        logger.info(f"Job {job_id}: 图执行完成")

        # 提取最终文档
        final_document = result.get("final_document", "")
        if final_document:
            # 存储最终文档到Redis
            await redis.hset(f"job:{job_id}:document",
                             mapping={
                                 "content": final_document,
                                 "created_at":
                                 str(asyncio.get_event_loop().time()),
                                 "word_count": len(final_document.split()),
                                 "char_count": len(final_document)
                             })
            logger.info(f"Job {job_id}: 最终文档已保存，字符数: {len(final_document)}")

        # 发布完成事件
        await redis.publish(
            f"job:{job_id}:events",
            json.dumps(
                {
                    "event": "done",
                    "data": {
                        "task": "main_workflow",
                        "message": "主工作流执行完成",
                        "job_id": job_id,
                        "document_length": len(final_document)
                    },
                    "timestamp": str(asyncio.get_event_loop().time())
                },
                ensure_ascii=False))

        # 更新任务状态为完成
        await redis.hset(f"job:{job_id}",
                         mapping={
                             "status": "completed",
                             "final_document_length": len(final_document),
                             "completed_at":
                             str(asyncio.get_event_loop().time())
                         })

        logger.info(f"Job {job_id}: 主工作流完成，文档长度: {len(final_document)} 字符")
        return "COMPLETED"

    except Exception as e:
        logger.error(f"Job {job_id}: 主工作流执行失败 - {e}")
        logger.exception("详细错误信息:")

        # 发布错误事件
        try:
            redis = await get_redis_client()
            await redis.publish(
                f"job:{job_id}:events",
                json.dumps(
                    {
                        "event": "error",
                        "data": {
                            "code": 5003,
                            "message": f"主工作流执行失败: {str(e)[:200]}",
                            "error_type": type(e).__name__,
                            "job_id": job_id
                        },
                        "timestamp": str(asyncio.get_event_loop().time())
                    },
                    ensure_ascii=False))
        except Exception as event_error:
            logger.error(f"发布错误事件失败: {event_error}")

        # 更新任务状态为失败
        try:
            redis = await get_redis_client()
            await redis.hset(f"job:{job_id}",
                             mapping={
                                 "status": "failed",
                                 "error": str(e),
                                 "failed_at":
                                 str(asyncio.get_event_loop().time())
                             })
        except Exception as redis_error:
            logger.error(f"无法更新Redis中的失败状态: {redis_error}")

        return "FAILED"


async def get_job_status(job_id: str) -> dict:
    """
    获取任务状态
    
    Args:
        job_id: 任务ID
        
    Returns:
        任务状态字典
    """
    try:
        redis = await get_redis_client()
        job_data = await redis.hgetall(f"job:{job_id}")

        if not job_data:
            return {"status": "not_found"}

        return job_data

    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return {"status": "error", "error": str(e)}
