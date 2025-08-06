import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

# 导入数据模型
from doc_agent.schemas import (
    DocumentGenerationRequest,
    EditActionRequest,
    OutlineGenerationRequest,
    OutlineGenerationResponse,
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
             response_model=OutlineGenerationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_outline_from_query(request: OutlineGenerationRequest):
    """
    大纲生成接口

    接收用户查询和可选的上下文文件，触发异步大纲生成任务。
    立即返回Redis流key，实际的大纲生成在后台进行并通过Redis流推送进度。
    """
    logger.info(f"收到大纲生成请求，session_id: {request.session_id}")

    try:
        # 验证请求数据
        if not request.task_prompt.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="任务提示不能为空")

        # 生成Redis流key - 直接使用session_id作为流名称
        redis_stream_key = str(request.session_id)

        # 记录请求信息
        logger.info("大纲生成请求详情:")
        logger.info(f"  session_id: {request.session_id}")
        logger.info(f"  task_prompt: {request.task_prompt[:100]}...")
        logger.info(f"  is_online: {request.is_online}")
        logger.info(
            f"  context_files: {len(request.context_files) if request.context_files else 0} 个文件"
        )
        logger.info(f"  redis_stream_key: {redis_stream_key}")

        # 处理文件相关逻辑
        style_guide_content = None
        requirements = None
        if request.context_files:
            logger.info("开始处理上传文件...")
            from doc_agent.tools.file_processor import process_context_files
            style_guide_content, requirements = process_context_files(
                request.context_files)
            logger.info(
                f"文件处理完成 - style_guide: {bool(style_guide_content)}, requirements: {bool(requirements)}"
            )

        # 触发 Celery 任务 - 使用最新的 run_main_workflow
        from workers.tasks import run_main_workflow
        from workers.celery_app import celery_app
        logger.info("准备提交 Celery 任务...")

        # 构建带密码的 broker_url 进行连接测试
        from doc_agent.core.config import settings

        # 从 config.yaml 中读取 Redis 配置
        if hasattr(settings, '_yaml_config') and settings._yaml_config:
            redis_config = settings._yaml_config.get('redis', {})
            redis_host = redis_config.get('host', 'localhost')
            redis_port = redis_config.get('port', 6379)
            redis_db = redis_config.get('db', 0)
            redis_password = redis_config.get('password', None)

            # 按照要求的逻辑构建 URL
            if redis_password:
                broker_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
            else:
                broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        else:
            # 如果无法从 YAML 读取，使用环境变量中的 URL
            import os
            broker_url = os.environ.get('REDIS_URL',
                                        'redis://localhost:6379/0')

        # 测试 Celery 连接
        try:
            logger.info(f"测试 broker URL: {broker_url}")
            # 创建临时的 Celery 实例进行连接测试
            from celery import Celery
            test_celery = Celery('test', broker=broker_url, backend=broker_url)
            inspect_result = test_celery.control.inspect().active()
            logger.info(f"Celery 连接测试成功: {inspect_result}")
        except Exception as e:
            logger.error(f"Celery 连接测试失败: {e}")
            raise

        try:
            # 使用同步方式提交任务
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: run_main_workflow.apply_async(
                    kwargs={
                        'job_id': request.session_id,  # 使用session_id作为job_id
                        'topic': request.task_prompt,
                        'genre': 'default'  # 使用默认genre，后续可扩展
                    },
                    countdown=0,
                    expires=300  # 5分钟过期
                ))
            logger.info(f"Celery 任务已提交，任务 ID: {result.id}")
        except Exception as e:
            logger.error(f"提交 Celery 任务失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise

        # 记录任务已接收
        logger.info(f"大纲生成任务已接收，session_id: {request.session_id}")

        return OutlineGenerationResponse(session_id=request.session_id,
                                         redis_stream_key=redis_stream_key,
                                         status="ACCEPTED",
                                         message="大纲生成任务已提交，请通过Redis流监听进度")

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
