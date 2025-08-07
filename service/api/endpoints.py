# service/api/endpoints.py
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

# 导入我们新的、统一的数据模型
from doc_agent.schemas import (
    DocumentGenerationRequest,
    DocumentGenerationFromOutlineRequest,
    EditActionRequest,
    OutlineGenerationRequest,
    TaskCreationResponse,  # 导入统一的响应模型
)

# 导入AI编辑工具和任务ID生成器
from doc_agent.tools.ai_editing_tool import AIEditingTool
from doc_agent.core.task_id_generator import generate_task_id
# 导入Celery任务
from workers import tasks

# 创建API路由器实例
router = APIRouter()


def get_ai_editing_tool():
    from doc_agent.core.container import Container
    return Container().ai_editing_tool


@router.post(
    "/jobs/outline",
    response_model=TaskCreationResponse,  # 使用统一模型
    response_model_by_alias=True,  # 强制按别名输出
    status_code=status.HTTP_202_ACCEPTED)
async def generate_outline_from_query(request: OutlineGenerationRequest):
    logger.info(f"收到大纲生成请求，sessionId: {request.session_id}")
    task_id = generate_task_id()
    try:
        tasks.generate_outline_from_query_task.delay(
            job_id=task_id,
            task_prompt=request.task_prompt,
            is_online=request.is_online,
            context_files=request.context_files,
            redis_stream_key=task_id,  # 传递给 worker
        )
        logger.success(f"大纲生成任务已提交，Task ID: {task_id}")
        return TaskCreationResponse(
            redis_stream_key=task_id,
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"提交大纲生成任务失败: {e}")
        raise HTTPException(status_code=500, detail="任务提交失败")


@router.post(
    "/jobs/document-from-outline",
    response_model=TaskCreationResponse,  # 使用统一模型
    response_model_by_alias=True,  # 强制按别名输出
    status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline_json(
    request: DocumentGenerationFromOutlineRequest, ):
    logger.info(f"收到从outline JSON生成文档请求，jobId: {request.job_id}")
    task_id = generate_task_id()
    try:
        outline_data = json.loads(request.outline_json)
        tasks.generate_document_from_outline_task.delay(
            job_id=task_id,
            outline=outline_data,
            session_id=request.session_id,
        )
        logger.success(f"文档生成任务已提交，Task ID: {task_id}")
        return TaskCreationResponse(
            redis_stream_key=task_id,
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"提交文档生成任务失败: {e}")
        raise HTTPException(status_code=500, detail="任务提交失败")


# =================================================================
# 模拟服务端点 - 用于测试
# =================================================================


async def simulate_mock_generation_process(task_id: str, session_id: str):
    """一个模拟后台任务的简单函数"""
    logger.info(
        f"[MOCK] Task {task_id} for session {session_id} has started in the background."
    )
    await asyncio.sleep(5)  # 模拟耗时工作
    logger.info(
        f"[MOCK] Task {task_id} for session {session_id} has finished.")


@router.post(
    "/jobs/document-from-outline-mock",
    response_model=TaskCreationResponse,  # 使用统一模型
    response_model_by_alias=True,  # 强制按别名输出
    status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline_json_mock(
    request: DocumentGenerationFromOutlineRequest, ):
    logger.info(f"收到模拟文档生成请求，sessionId: {request.session_id}")
    task_id = generate_task_id()
    try:
        # 启动一个不会阻塞主线程的后台模拟任务
        asyncio.create_task(
            simulate_mock_generation_process(task_id, request.session_id))
        logger.success(f"模拟后台任务已启动，Task ID: {task_id}")
        # 立即返回响应
        return TaskCreationResponse(redis_stream_key=task_id,
                                    session_id=request.session_id)
    except Exception as e:
        logger.error(f"模拟文档生成请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"模拟请求处理失败: {str(e)}")


# --- 其他端点保持不变 ---


@router.get("/health")
async def health_check():
    logger.info("健康检查端点被调用")
    return {"status": "healthy", "message": "API服务运行正常"}


@router.post("/actions/edit", status_code=status.HTTP_200_OK)
async def edit_text(request: EditActionRequest,
                    tool: AIEditingTool = Depends(get_ai_editing_tool)):
    """
    AI 文本编辑端点（流式响应）

    支持以下编辑操作：
    - polish: 润色文本，支持多种风格（professional, conversational, readable, subtle, academic, literary）
    - expand: 扩写文本，增加更多细节和深度
    - summarize: 缩写文本，提取关键要点
    - continue_writing: 续写文本，基于上下文继续创作
    - custom: 自定义编辑，根据用户指令进行编辑

    返回 Server-Sent Events (SSE) 流式响应
    """
    logger.info(f"收到文本编辑请求，操作类型: {request.action}")

    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'event': 'start', 'action': request.action}, ensure_ascii=False)}\n\n"

            # 调用 AI 编辑工具的流式方法
            async for token in tool.arun(action=request.action,
                                         text=request.text,
                                         command=request.command,
                                         context=request.context,
                                         polish_style=request.polish_style):
                # 将每个 token 包装成 SSE 格式
                yield f"data: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"

            # 发送结束事件
            yield f"data: {json.dumps({'event': 'end', 'action': request.action}, ensure_ascii=False)}\n\n"

            logger.info(f"文本编辑流式响应完成，操作: {request.action}")

        except ValueError as e:
            # 发送错误事件
            error_data = {'event': 'error', 'error': '参数错误', 'detail': str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            logger.error(f"文本编辑参数错误: {e}")

        except Exception as e:
            # 发送错误事件
            error_data = {'event': 'error', 'error': '编辑失败', 'detail': str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            logger.error(f"文本编辑失败: {e}")

    # 返回流式响应
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        })
