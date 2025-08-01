import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

# 导入数据模型
from doc_agent.schemas import (
    DocumentGenerationRequest,
    EditActionRequest,
    OutlineGenerationRequest,
    TaskCreationResponse,
)

# 导入AI编辑工具
from doc_agent.tools.ai_editing_tool import AIEditingTool

# 导入Celery任务（稍后创建）
# from workers.tasks import generate_outline_from_query_task, generate_document_from_outline_task

# 创建API路由器实例
router = APIRouter()


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
    from doc_agent.core.container import Container
    container = Container()
    return container.ai_editing_tool


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
    return StreamingResponse(event_generator(),
                             media_type="text/event-stream",
                             headers={
                                 "Cache-Control": "no-cache",
                                 "Connection": "keep-alive",
                                 "Access-Control-Allow-Origin": "*",
                                 "Access-Control-Allow-Headers":
                                 "Cache-Control"
                             })


@router.post("/jobs/outline",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_outline_from_query(request: OutlineGenerationRequest):
    """
    大纲生成接口

    接收用户查询和可选的上下文文件，触发异步大纲生成任务。
    立即返回任务ID，实际的大纲生成在后台进行。
    """
    logger.info(f"收到大纲生成请求，job_id: {request.job_id}")

    try:
        # 验证请求数据
        if not request.task_prompt.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="任务提示不能为空")

        # 记录请求信息
        logger.info("大纲生成请求详情:")
        logger.info(f"  job_id: {request.job_id}")
        logger.info(f"  task_prompt: {request.task_prompt[:100]}...")
        logger.info(
            f"  context_files: {len(request.context_files) if request.context_files else 0} 个文件"
        )

        # 触发 Celery 任务
        from workers.tasks import generate_outline_from_query_task
        generate_outline_from_query_task.delay(
            job_id=request.job_id,
            task_prompt=request.task_prompt,
            context_files=request.context_files.model_dump()
            if request.context_files else None)

        # 临时占位：记录任务已接收
        logger.info(f"大纲生成任务已接收，job_id: {request.job_id}")

        return TaskCreationResponse(job_id=request.job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"大纲生成请求处理失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"大纲生成请求处理失败: {str(e)}") from e


@router.post("/jobs/document",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline(request: DocumentGenerationRequest):
    """
    文档生成接口

    接收结构化的大纲对象，触发异步文档生成任务。
    立即返回任务ID，实际的文档生成在后台进行。
    """
    logger.info(f"收到文档生成请求，job_id: {request.job_id}")

    try:
        # 验证请求数据
        if not request.outline.title.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="大纲标题不能为空")

        if not request.outline.nodes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="大纲节点不能为空")

        # 记录请求信息
        logger.info("文档生成请求详情:")
        logger.info(f"  job_id: {request.job_id}")
        logger.info(f"  outline_title: {request.outline.title}")
        logger.info(f"  outline_nodes: {len(request.outline.nodes)} 个节点")

        # 触发 Celery 任务
        from workers.tasks import generate_document_from_outline_task
        generate_document_from_outline_task.delay(
            job_id=request.job_id, outline=request.outline.model_dump())

        # 临时占位：记录任务已接收
        logger.info(f"文档生成任务已接收，job_id: {request.job_id}")

        return TaskCreationResponse(job_id=request.job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档生成请求处理失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"文档生成请求处理失败: {str(e)}") from e
