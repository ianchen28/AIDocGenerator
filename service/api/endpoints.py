import asyncio
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

# 导入数据模型
from src.doc_agent.schemas import (
    ContextStatusResponse,
    CreateContextRequest,
    CreateJobRequest,
    EditActionRequest,
    EditActionResponse,
    JobResponse,
    Outline,
    OutlineResponse,
    UpdateOutlineRequest,
    UpdateOutlineResponse,
)

# 导入Redis客户端和worker任务
from workers.tasks import generate_outline_task, get_redis_client, run_main_workflow

# 导入AI编辑工具
from src.doc_agent.tools.ai_editing_tool import AIEditingTool

# 创建API路由器实例
router = APIRouter()


async def placeholder_index_context(context_id: str, files: list):
    """占位符索引任务 - 模拟文件索引过程"""
    logger.info(f"开始索引上下文: {context_id}, 文件数量: {len(files)}")

    try:
        redis = await get_redis_client()

        # 更新状态为索引中
        await redis.hset(f"context:{context_id}",
                         mapping={
                             "status": "INDEXING",
                             "files_count": len(files),
                             "started_at": datetime.now().isoformat()
                         })

        # 模拟索引工作
        import asyncio
        await asyncio.sleep(3)  # 模拟索引耗时

        # 更新状态为完成
        await redis.hset(f"context:{context_id}",
                         mapping={
                             "status": "READY",
                             "completed_at": datetime.now().isoformat()
                         })

        logger.info(f"上下文索引完成: {context_id}")

    except Exception as e:
        logger.error(f"上下文索引失败: {context_id}, 错误: {e}")
        try:
            redis = await get_redis_client()
            await redis.hset(f"context:{context_id}",
                             mapping={
                                 "status": "FAILED",
                                 "error": str(e),
                                 "failed_at": datetime.now().isoformat()
                             })
        except Exception as redis_error:
            logger.error(f"无法更新Redis中的失败状态: {redis_error}")


@router.post("/contexts",
             response_model=ContextStatusResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def create_context(request: CreateContextRequest,
                         background_tasks: BackgroundTasks):
    """
    创建文件上下文
    启动后台索引任务，立即返回上下文ID和状态
    """
    # 生成唯一的上下文ID
    context_id = f"ctx-{uuid.uuid4().hex[:10]}"

    logger.info(f"创建新上下文: {context_id}, 文件数量: {len(request.files)}")

    try:
        # 存储上下文信息到Redis
        redis = await get_redis_client()
        context_data = {
            "context_id": context_id,
            "status": "PENDING",
            "files_count": len(request.files),
            "created_at": datetime.now().isoformat()
        }

        # 存储文件信息
        for i, file in enumerate(request.files):
            context_data[f"file_{i}_id"] = file.file_id
            context_data[f"file_{i}_name"] = file.file_name
            context_data[f"file_{i}_url"] = file.storage_url

        await redis.hset(f"context:{context_id}", mapping=context_data)

        # 启动后台索引任务
        background_tasks.add_task(placeholder_index_context, context_id,
                                  request.files)

        logger.info(f"上下文创建成功: {context_id}")

        return ContextStatusResponse(context_id=context_id, status="PENDING")

    except Exception as e:
        logger.error(f"创建上下文失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"创建上下文失败: {str(e)}") from e


@router.post("/jobs",
             response_model=JobResponse,
             status_code=status.HTTP_201_CREATED)
async def create_job(request: CreateJobRequest):
    """
    创建新的文档生成作业
    立即返回作业ID和状态
    """
    # 生成唯一的作业ID
    job_id = f"job-{uuid.uuid4().hex[:10]}"

    logger.info(f"创建新作业: {job_id}, 任务提示: {request.task_prompt[:50]}...")

    try:
        # 存储作业信息到Redis
        redis = await get_redis_client()
        job_data = {
            "job_id": job_id,
            "task_prompt": request.task_prompt,
            "genre": request.genre,
            "status": "CREATED",
            "created_at": datetime.now().isoformat()
        }

        # 如果提供了上下文ID，也存储
        if request.context_id:
            job_data["context_id"] = request.context_id
            logger.info(f"作业 {job_id} 关联上下文: {request.context_id}")

        logger.info(f"作业 {job_id} 使用 genre: {request.genre}")

        await redis.hset(f"job:{job_id}", mapping=job_data)

        logger.info(f"作业创建成功: {job_id}")

        return JobResponse(job_id=job_id,
                           status="CREATED",
                           created_at=datetime.now().isoformat())

    except Exception as e:
        logger.error(f"创建作业失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"创建作业失败: {str(e)}") from e


@router.post("/jobs/{job_id}/outline", status_code=status.HTTP_202_ACCEPTED)
async def generate_outline(job_id: str, background_tasks: BackgroundTasks):
    """
    触发指定作业的大纲生成任务
    """
    logger.info(f"触发大纲生成: {job_id}")

    try:
        # 验证作业是否存在
        redis = await get_redis_client()
        job_data = await redis.hgetall(f"job:{job_id}")

        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"作业 {job_id} 不存在")

        # 检查是否已经在生成大纲
        outline_data = await redis.hgetall(f"job:{job_id}:outline")
        if outline_data.get("outline_status") == "GENERATING":
            logger.warning(f"作业 {job_id} 的大纲正在生成中")
            return {
                "job_id": job_id,
                "outline_status": "GENERATING",
                "message": "大纲生成任务已在进行中"
            }

        # 启动后台大纲生成任务
        background_tasks.add_task(generate_outline_task, job_id)

        logger.info(f"大纲生成任务已启动: {job_id}")

        return {"job_id": job_id, "outline_status": "GENERATING"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动大纲生成失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"启动大纲生成失败: {str(e)}") from e


@router.get("/jobs/{job_id}/outline", response_model=OutlineResponse)
async def get_outline(job_id: str):
    """
    获取指定作业的大纲
    """
    logger.info(f"获取大纲: {job_id}")

    try:
        # 验证作业是否存在
        redis = await get_redis_client()
        job_data = await redis.hgetall(f"job:{job_id}")

        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"作业 {job_id} 不存在")

        # 获取大纲数据
        outline_data = await redis.hgetall(f"job:{job_id}:outline")

        if not outline_data:
            # 大纲尚未开始生成，返回FAILED状态
            return OutlineResponse(job_id=job_id,
                                   outline_status="FAILED",
                                   outline=None)

        outline_status = outline_data.get("outline_status", "PENDING")

        if outline_status == "READY":
            # 大纲已完成，解析大纲数据
            outline_json = outline_data.get("outline_data")
            if outline_json:
                try:
                    outline_dict = json.loads(outline_json)
                    outline = Outline(**outline_dict)

                    logger.info(f"成功获取大纲: {job_id}")
                    return OutlineResponse(job_id=job_id,
                                           outline_status="READY",
                                           outline=outline)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"大纲数据解析失败: {e}")
                    return OutlineResponse(job_id=job_id,
                                           outline_status="FAILED",
                                           outline=None)

        # 返回当前状态
        return OutlineResponse(job_id=job_id,
                               outline_status=outline_status,
                               outline=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取大纲失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"获取大纲失败: {str(e)}") from e


@router.put("/jobs/{job_id}/outline",
            status_code=status.HTTP_200_OK,
            response_model=UpdateOutlineResponse)
async def update_outline(job_id: str, request: UpdateOutlineRequest,
                         background_tasks: BackgroundTasks):
    """
    更新/确认大纲，并触发最终文档生成
    """
    logger.info(f"更新大纲并开始最终生成: {job_id}")

    try:
        # 验证作业是否存在
        redis = await get_redis_client()
        job_data = await redis.hgetall(f"job:{job_id}")

        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"作业 {job_id} 不存在")

        # 存储更新后的大纲
        updated_outline_json = request.outline.model_dump_json()

        await redis.hset(f"job:{job_id}:outline",
                         mapping={
                             "outline_status": "READY",
                             "outline_data": updated_outline_json,
                             "updated_at": datetime.now().isoformat()
                         })

        # 获取任务提示和genre，准备启动最终文档生成
        task_prompt = job_data.get("task_prompt", "")
        genre = job_data.get("genre", "default")

        # 启动最终文档生成工作流 - 使用Celery任务
        run_main_workflow.delay(job_id, task_prompt, genre)

        logger.info(f"大纲已更新，最终文档生成已启动: {job_id}")

        return {"job_id": job_id, "message": "大纲更新成功，最终文档生成已开始"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新大纲失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"更新大纲失败: {str(e)}") from e


@router.get("/jobs/{job_id}/events")
async def stream_events(job_id: str):
    """
    流式获取作业事件
    """
    logger.info(f"开始流式获取作业事件: {job_id}")

    try:
        redis = await get_redis_client()

        # 验证作业是否存在
        job_data = await redis.hgetall(f"job:{job_id}")
        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"作业 {job_id} 不存在")

        # 创建 SSE 响应
        async def event_generator():
            pubsub = redis.pubsub()
            await pubsub.subscribe(f"job:{job_id}:events")

            try:
                while True:
                    message = await pubsub.get_message(timeout=1.0)
                    if message and message["type"] == "message":
                        data = message["data"]
                        yield f"data: {data}\n\n"
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"事件流错误: {e}")
            finally:
                await pubsub.unsubscribe(f"job:{job_id}:events")
                await pubsub.close()

        return StreamingResponse(event_generator(),
                                 media_type="text/event-stream",
                                 headers={
                                     "Cache-Control":
                                     "no-cache",
                                     "Connection":
                                     "keep-alive",
                                     "Access-Control-Allow-Origin":
                                     "*",
                                     "Access-Control-Allow-Headers":
                                     "Cache-Control"
                                 })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取事件流失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"获取事件流失败: {str(e)}") from e


@router.get("/jobs/{job_id}/document/stream")
async def stream_document(job_id: str):
    """
    流式获取文档内容
    """
    logger.info(f"开始流式获取文档内容: {job_id}")

    try:
        redis = await get_redis_client()

        # 验证作业是否存在
        job_data = await redis.hgetall(f"job:{job_id}")
        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"作业 {job_id} 不存在")

        # 创建 SSE 响应
        async def document_generator():
            pubsub = redis.pubsub()
            await pubsub.subscribe(f"job:{job_id}:document")

            try:
                while True:
                    message = await pubsub.get_message(timeout=1.0)
                    if message and message["type"] == "message":
                        data = message["data"]
                        yield f"data: {data}\n\n"
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"文档流错误: {e}")
            finally:
                await pubsub.unsubscribe(f"job:{job_id}:document")
                await pubsub.close()

        return StreamingResponse(document_generator(),
                                 media_type="text/event-stream",
                                 headers={
                                     "Cache-Control":
                                     "no-cache",
                                     "Connection":
                                     "keep-alive",
                                     "Access-Control-Allow-Origin":
                                     "*",
                                     "Access-Control-Allow-Headers":
                                     "Cache-Control"
                                 })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档流失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"获取文档流失败: {str(e)}") from e


@router.get("/jobs/{job_id}/document")
async def get_document(job_id: str):
    """
    获取最终生成的文档
    """
    logger.info(f"获取最终文档: {job_id}")

    try:
        redis = await get_redis_client()

        # 验证作业是否存在
        job_data = await redis.hgetall(f"job:{job_id}")
        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"作业 {job_id} 不存在")

        # 获取文档内容
        final_document = job_data.get("final_document")
        if not final_document:
            # 检查作业状态
            job_status = job_data.get("status", "UNKNOWN")
            if job_status == "COMPLETED":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail="文档生成已完成但内容丢失")
            elif job_status in ["PENDING", "RUNNING", "processing"]:
                raise HTTPException(status_code=status.HTTP_202_ACCEPTED,
                                    detail="文档仍在生成中，请稍后再试")
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail="文档尚未生成")

        # 计算文档统计信息
        word_count = len(final_document.split())
        char_count = len(final_document)
        line_count = len(final_document.splitlines())

        return {
            "job_id": job_id,
            "status": job_data.get("status"),
            "document": {
                "content": final_document,
                "statistics": {
                    "word_count": word_count,
                    "char_count": char_count,
                    "line_count": line_count
                }
            },
            "created_at": job_data.get("created_at"),
            "completed_at": job_data.get("completed_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"获取文档失败: {str(e)}") from e


@router.get("/health")
async def health_check():
    """健康检查端点"""
    logger.info("健康检查端点被调用")
    return {"status": "healthy", "message": "API服务运行正常"}


# AI 编辑工具依赖注入函数
def get_ai_editing_tool():
    """
    获取 AI 编辑工具实例
    从依赖注入容器中获取 AIEditingTool 实例
    """
    # 从容器中获取 AIEditingTool 实例
    from core.container import Container

    # 获取容器实例（这里假设是单例模式）
    container = Container()
    return container.ai_editing_tool


@router.post("/actions/edit",
             response_model=EditActionResponse,
             status_code=status.HTTP_200_OK)
def edit_text(request: EditActionRequest,
              tool: AIEditingTool = Depends(get_ai_editing_tool)):
    """
    AI 文本编辑端点
    
    支持以下编辑操作：
    - polish: 润色文本，提升清晰度和风格
    - expand: 扩写文本，增加更多细节和深度
    - summarize: 缩写文本，提取关键要点
    """
    logger.info(f"收到文本编辑请求，操作类型: {request.action}")

    try:
        # 调用 AI 编辑工具
        edited_text = tool.run(action=request.action,
                               text=request.text,
                               command=request.command)

        logger.info(f"文本编辑完成，操作: {request.action}")

        # 返回编辑结果
        return EditActionResponse(original_text=request.text,
                                  edited_text=edited_text,
                                  action=request.action)

    except ValueError as e:
        logger.error(f"文本编辑参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    except Exception as e:
        logger.error(f"文本编辑失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"文本编辑失败: {str(e)}")
