import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

# 导入数据模型
from doc_agent.schemas import (
    DocumentGenerationRequest,
    DocumentGenerationFromOutlineRequest,
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

        # 触发 Celery 任务 - 使用大纲生成任务
        from workers.tasks import generate_outline_from_query_task
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
                lambda: generate_outline_from_query_task.apply_async(
                    kwargs={
                        'job_id': request.session_id,  # 使用session_id作为job_id
                        'task_prompt': request.task_prompt,
                        'is_online': request.is_online,
                        'context_files': request.context_files,
                        'style_guide_content': style_guide_content,
                        'requirements': requirements,
                        'redis_stream_key': redis_stream_key
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


@router.post("/jobs/document-from-outline",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline_json(
        request: DocumentGenerationFromOutlineRequest):
    """
    从outline JSON字符串生成文档接口

    接收outline的JSON序列化字符串，解析后触发异步文档生成任务。
    立即返回任务ID，实际的文档生成在后台进行。
    """
    logger.info(f"收到从outline JSON生成文档请求，job_id: {request.job_id}")

    try:
        # 解析outline JSON字符串
        import json
        outline_data = json.loads(request.outline_json)

        logger.info("outline JSON解析成功:")
        logger.info(f"  job_id: {request.job_id}")
        logger.info(f"  session_id: {request.session_id}")
        logger.info(f"  outline_title: {outline_data.get('title', '未知标题')}")
        logger.info(
            f"  outline_nodes: {len(outline_data.get('nodes', []))} 个节点")

        # 验证解析后的数据
        if not outline_data.get('title', '').strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="大纲标题不能为空")

        if not outline_data.get('nodes'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="大纲节点不能为空")

        # 触发 Celery 任务
        from workers.tasks import generate_document_from_outline_task
        generate_document_from_outline_task.delay(
            job_id=request.job_id,
            outline=outline_data,
            session_id=request.session_id)

        logger.info(f"从outline JSON生成文档任务已接收，job_id: {request.job_id}")

        return TaskCreationResponse(job_id=request.job_id)

    except json.JSONDecodeError as e:
        logger.error(f"outline JSON解析失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"outline JSON格式无效: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从outline JSON生成文档请求处理失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"从outline JSON生成文档请求处理失败: {str(e)}") from e


# =================================================================
# 模拟服务端点 - 用于测试，不影响线上服务
# =================================================================


async def get_mock_redis_client():
    """获取模拟服务的Redis客户端实例"""
    import redis.asyncio as redis
    from doc_agent.core.config import settings

    try:
        redis_client = redis.from_url(settings.redis_url,
                                      encoding="utf-8",
                                      decode_responses=True)
        await redis_client.ping()
        logger.info("模拟服务Redis客户端连接成功")
        return redis_client
    except Exception as e:
        logger.error(f"模拟服务Redis连接失败: {e}")
        raise


async def publish_mock_event(redis_client, session_id: str, event_data: dict):
    """发布模拟事件到Redis Stream"""
    try:
        from datetime import datetime

        # 构造 Stream 名称 - 直接使用session_id作为流名称
        stream_name = str(session_id)

        # 发布事件到 Redis Stream - 使用自动生成的ID
        counter_key = f"stream_counter:{stream_name}"
        i = await redis_client.incr(counter_key)
        # 让 Redis 自动生成 ID，但在事件数据中包含 sessionId-idx 格式
        session_id_idx = f"{session_id}-{i}"  # 事件数据中的格式: sessionId-idx

        # 准备事件数据
        event_data["redis_id"] = session_id_idx
        event_data["timestamp"] = datetime.now().isoformat()

        await redis_client.xadd(
            stream_name,
            {"data": json.dumps(event_data, ensure_ascii=False)},
            id="*"  # 让 Redis 自动生成 ID
        )
        logger.info(f"模拟事件发布成功: {event_data.get('eventType', 'unknown')}")
    except Exception as e:
        logger.error(f"模拟事件发布失败: {e}")


async def stream_mock_document_content(redis_client,
                                       session_id: str,
                                       content: str,
                                       chunk_size: int = 10):
    """流式输出模拟文档内容到Redis Stream"""
    try:
        # 将内容按字符分割成token
        tokens = list(content)

        for i in range(0, len(tokens), chunk_size):
            chunk = tokens[i:i + chunk_size]
            chunk_text = ''.join(chunk)

            # 发布内容流事件
            await publish_mock_event(
                redis_client, session_id, {
                    "eventType": "document_content_stream",
                    "taskType": "document_generation",
                    "content": chunk_text,
                    "tokenIndex": i,
                    "totalTokens": len(tokens),
                    "progress": f"{i + len(chunk)}/{len(tokens)}",
                    "status": "streaming"
                })

            # 模拟token生成的时间间隔
            await asyncio.sleep(0.1)

        # 发布流式输出完成事件
        await publish_mock_event(
            redis_client, session_id, {
                "eventType": "document_content_completed",
                "taskType": "document_generation",
                "totalTokens": len(tokens),
                "status": "completed"
            })

        logger.info(f"模拟文档内容流式输出完成，共 {len(tokens)} 个token")

    except Exception as e:
        logger.error(f"模拟流式输出文档内容失败: {e}")


def generate_mock_chapter_content(chapter_title: str,
                                  chapter_index: int) -> str:
    """生成模拟的章节内容"""
    return f"""## {chapter_title}

这是第 {chapter_index + 1} 章的模拟内容。

### 章节概述
本章主要介绍了 {chapter_title} 的相关内容。

### 主要内容
1. **背景介绍**
   - 历史发展脉络
   - 当前现状分析

2. **核心要点**
   - 关键技术要素
   - 重要影响因素

3. **总结**
通过对 {chapter_title} 的全面分析，我们发现这一领域具有重要的研究价值。

### 参考文献
1. 张三, 李四. 《{chapter_title}研究综述》. 学术期刊, 2023.
2. 王五, 赵六. 《{chapter_title}发展趋势分析》. 研究报告, 2023.
"""


def generate_mock_sources(chapter_title: str, chapter_index: int) -> list:
    """生成模拟的引用源列表"""
    import time

    sources = []

    # 生成文档类型的引用源
    sources.append({
        "id":
        f"{chapter_index * 3 + 1}",
        "detailId":
        f"{chapter_index * 3 + 1}",
        "originInfo":
        f"关于{chapter_title}的重要研究成果和最新发现。本文主要参考了相关领域的研究文献，包括理论基础、实证研究和应用案例。",
        "title":
        f"{chapter_title}研究综述.pdf",
        "fileToken":
        f"token_{chapter_index * 3 + 1}_{int(time.time())}",
        "domainId":
        "document",
        "isFeishuSource":
        None,
        "valid":
        "true",
        "metadata":
        json.dumps(
            {
                "file_name": f"{chapter_title}研究综述.pdf",
                "locations": [{
                    "pagenum": chapter_index + 1
                }],
                "source": "data_platform"
            },
            ensure_ascii=False)
    })

    # 生成标准类型的引用源
    sources.append({
        "id":
        f"{chapter_index * 3 + 2}",
        "detailId":
        f"{chapter_index * 3 + 2}",
        "originInfo":
        f"详细的技术分析报告，包含{chapter_title}的核心技术要点和标准规范。",
        "title":
        f"GB/T {chapter_index + 1000}-2023 {chapter_title}技术标准.pdf",
        "fileToken":
        f"token_{chapter_index * 3 + 2}_{int(time.time())}",
        "domainId":
        "standard",
        "isFeishuSource":
        None,
        "valid":
        "true",
        "metadata":
        json.dumps(
            {
                "file_name":
                f"GB/T {chapter_index + 1000}-2023 {chapter_title}技术标准.pdf",
                "locations": [{
                    "pagenum": chapter_index + 5
                }],
                "code": f"GB/T {chapter_index + 1000}-2023",
                "gfid": f"GB/T {chapter_index + 1000}-2023",
                "source": "data_platform"
            },
            ensure_ascii=False)
    })

    # 生成书籍类型的引用源
    sources.append({
        "id":
        f"{chapter_index * 3 + 3}",
        "detailId":
        f"{chapter_index * 3 + 3}",
        "originInfo":
        f"最新的学术研究成果，为{chapter_title}提供了理论支撑和实践指导。",
        "title":
        f"{chapter_title}技术手册.pdf",
        "fileToken":
        f"token_{chapter_index * 3 + 3}_{int(time.time())}",
        "domainId":
        "book",
        "isFeishuSource":
        None,
        "valid":
        "true",
        "metadata":
        json.dumps(
            {
                "file_name": f"{chapter_title}技术手册.pdf",
                "locations": [{
                    "pagenum": chapter_index + 10
                }],
                "source": "data_platform"
            },
            ensure_ascii=False)
    })

    return sources


def generate_mock_web_sources(chapter_title: str, chapter_index: int) -> list:
    """生成模拟的网页引用源列表"""
    import time

    web_sources = []

    web_sources.append({
        "id":
        f"web_{chapter_index * 2 + 1}",
        "detailId":
        f"web_{chapter_index * 2 + 1}",
        "materialContent":
        f"关于{chapter_title}的在线资料和最新动态。包含相关技术发展、行业趋势和实际应用案例。",
        "materialTitle":
        f"{chapter_title}技术发展动态-技术资讯",
        "url":
        f"https://example.com/tech/{chapter_title.lower().replace(' ', '-')}",
        "siteName":
        "技术资讯网",
        "datePublished":
        "2023年12月15日",
        "materialId":
        f"web_{chapter_index * 2 + 1}_{int(time.time())}"
    })

    web_sources.append({
        "id":
        f"web_{chapter_index * 2 + 2}",
        "detailId":
        f"web_{chapter_index * 2 + 2}",
        "materialContent":
        f"{chapter_title}相关的研究报告和行业分析。",
        "materialTitle":
        f"{chapter_title}行业分析报告-研究报告",
        "url":
        f"https://research.example.com/report/{chapter_index + 1}",
        "siteName":
        "研究报告网",
        "datePublished":
        "2023年11月20日",
        "materialId":
        f"web_{chapter_index * 2 + 2}_{int(time.time())}"
    })

    return web_sources


async def simulate_mock_document_generation(session_id: str,
                                            outline_data: dict):
    """模拟文档生成过程"""
    try:
        redis_client = await get_mock_redis_client()

        # 1. 发布任务开始事件
        await publish_mock_event(
            redis_client, session_id, {
                "eventType": "task_started",
                "taskType": "document_generation",
                "status": "started",
                "outline_title": outline_data.get("title", "未知标题")
            })

        # 2. 发布分析进度
        await publish_mock_event(
            redis_client, session_id, {
                "eventType": "task_progress",
                "taskType": "document_generation",
                "progress": "正在分析大纲结构",
                "status": "running",
                "step": "analysis"
            })

        await asyncio.sleep(2)  # 模拟处理时间

        # 3. 处理每个章节
        chapters = outline_data.get("nodes", [])
        all_answer_origins = []
        all_web_sources = []

        for chapter_index, node in enumerate(chapters):
            chapter_title = node.get("title", f"章节 {chapter_index + 1}")

            # 发布章节开始事件
            await publish_mock_event(
                redis_client, session_id, {
                    "eventType": "chapter_started",
                    "taskType": "document_generation",
                    "chapterTitle": chapter_title,
                    "chapterIndex": chapter_index,
                    "totalChapters": len(chapters),
                    "status": "running"
                })

            # 模拟章节处理步骤
            steps = ["planner", "researcher", "supervisor", "writer"]
            for step in steps:
                await publish_mock_event(
                    redis_client, session_id, {
                        "eventType": "chapter_progress",
                        "taskType": "document_generation",
                        "chapterTitle": chapter_title,
                        "step": step,
                        "progress": f"正在执行{step}步骤",
                        "status": "running"
                    })
                await asyncio.sleep(1)  # 模拟步骤处理时间

            # 生成章节内容
            chapter_content = generate_mock_chapter_content(
                chapter_title, chapter_index)

            # 生成章节的引用源
            chapter_sources = generate_mock_sources(chapter_title,
                                                    chapter_index)
            chapter_web_sources = generate_mock_web_sources(
                chapter_title, chapter_index)

            all_answer_origins.extend(chapter_sources)
            all_web_sources.extend(chapter_web_sources)

            # 发布章节完成事件
            await publish_mock_event(
                redis_client, session_id, {
                    "eventType": "chapter_completed",
                    "taskType": "document_generation",
                    "chapterTitle": chapter_title,
                    "chapterContent": chapter_content,
                    "chapterIndex": chapter_index,
                    "status": "completed"
                })

            # 4. 每个章节完成后立即流式输出该章节内容
            await publish_mock_event(
                redis_client, session_id, {
                    "eventType": "writer_started",
                    "taskType": "document_generation",
                    "progress": f"开始编写章节 {chapter_index + 1}",
                    "status": "running"
                })

            await stream_mock_document_content(redis_client, session_id,
                                               chapter_content)

            await asyncio.sleep(1)  # 章节间隔

        # 5. 发布参考文献事件
        citations_data = {
            "answerOrigins": all_answer_origins,
            "webs": all_web_sources
        }

        await publish_mock_event(
            redis_client, session_id, {
                "eventType": "citations_completed",
                "taskType": "document_generation",
                "citations": citations_data,
                "totalAnswerOrigins": len(all_answer_origins),
                "totalWebSources": len(all_web_sources),
                "status": "completed"
            })

        # 6. 发布任务完成事件
        await publish_mock_event(
            redis_client, session_id, {
                "eventType": "task_completed",
                "taskType": "document_generation",
                "status": "completed",
                "totalChapters": len(chapters),
                "citations": citations_data
            })

        logger.info(f"模拟服务 Session {session_id}: 文档生成完成")

    except Exception as e:
        logger.error(f"模拟服务 Session {session_id}: 文档生成失败: {e}")
        try:
            await publish_mock_event(
                redis_client, session_id, {
                    "eventType": "task_failed",
                    "taskType": "document_generation",
                    "status": "failed",
                    "error": str(e)
                })
        except:
            pass


@router.post("/jobs/document-from-outline/mock",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline_json_mock(
        request: DocumentGenerationFromOutlineRequest):
    """
    从outline JSON字符串生成文档接口（模拟版本）

    接收outline的JSON序列化字符串，解析后触发模拟文档生成任务。
    立即返回任务ID，实际的文档生成在后台进行并通过Redis流推送进度。
    此端点为测试用途，不影响线上服务体系。
    """
    logger.info(f"收到模拟文档生成请求，sessionId: {request.session_id}")

    try:
        # 解析outline JSON
        outline_data = json.loads(request.outline_json)

        # 验证数据
        if not outline_data.get('title', '').strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="大纲标题不能为空")

        if not outline_data.get('nodes'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="大纲节点不能为空")

        # 启动异步任务
        import asyncio
        asyncio.create_task(
            simulate_mock_document_generation(request.session_id,
                                              outline_data))

        return TaskCreationResponse(job_id=request.session_id)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"outline JSON格式无效: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模拟文档生成请求处理失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"模拟文档生成请求处理失败: {str(e)}")
