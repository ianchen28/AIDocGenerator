# service/api/endpoints.py
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from doc_agent.core.logger import logger

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

# 导入请求/响应模型 (Schemas)
from doc_agent.schemas import (
    OutlineGenerationRequest,
    DocumentGenerationRequest,
    TaskCreationResponse,
)
# 导入我们新的核心逻辑函数
from doc_agent.core.outline_generator import generate_outline_async
from doc_agent.core.document_generator import generate_document_sync
# 导入任务ID生成器
from doc_agent.core.task_id_generator import generate_task_id

# 创建API路由器实例
# router = APIRouter()
router = APIRouter(tags=["Generation Jobs & Tasks"])


def get_ai_editing_tool():
    from doc_agent.core.container import Container
    return Container().ai_editing_tool


# =================================================================
#  核心接口改造 (使用 FastAPI BackgroundTasks, 不再依赖 Celery)
# =================================================================


@router.post("/jobs/outline",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED,
             summary="以背景任务形式生成大纲 (非Celery)")
async def generate_outline_endpoint(request: OutlineGenerationRequest,
                                    background_tasks: BackgroundTasks):
    """
    接收大纲生成请求，将其作为后台任务运行，并立即返回任务ID。
    该接口不使用Celery，任务在FastAPI应用进程的后台执行。
    """
    logger.info(f"收到大纲生成请求，正在添加到后台任务。SessionId: {request.session_id}")
    job_id = generate_task_id()

    background_tasks.add_task(
        generate_outline_async,
        job_id=str(job_id),
        session_id=request.session_id,
        task_prompt=request.task_prompt,
        is_online=request.is_online,
        context_files=request.context_files,
        style_guide_content=request.style_guide_content,
        requirements=request.requirements,
    )

    logger.success(f"大纲生成任务 {job_id} 已提交到后台。")
    return TaskCreationResponse(
        redis_stream_key=str(job_id),
        session_id=request.session_id,
    )


@router.post("/jobs/document-from-outline",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED,
             summary="从大纲生成文档的背景任务 (非Celery)")
async def generate_document_endpoint(request: DocumentGenerationRequest,
                                     background_tasks: BackgroundTasks):
    """
    接收文档生成请求，将其作为后台任务运行，并立即返回任务ID。
    该接口不使用Celery，任务在FastAPI应用进程的后台执行。
    """
    logger.info(f"收到文档生成请求，正在添加到后台任务。JobId: {request.session_id}")
    task_id = generate_task_id()
    session_id = request.session_id
    task_prompt = request.task_prompt
    outline_json_file = request.outline
    context_files = request.context_files
    is_online = request.is_online

    background_tasks.add_task(generate_document_sync,
                              task_id=str(task_id),
                              task_prompt=task_prompt,
                              session_id=session_id,
                              outline_json_file=outline_json_file,
                              context_files=context_files,
                              is_online=is_online)

    logger.success(f"文档生成任务 {task_id} 已提交到后台。")
    return TaskCreationResponse(
        redis_stream_key=str(task_id),
        session_id=session_id,
    )


# @router.post(
#     "/jobs/outline",
#     response_model=TaskCreationResponse,  # 使用统一模型
#     response_model_by_alias=True,  # 强制按别名输出
#     status_code=status.HTTP_202_ACCEPTED)
# async def generate_outline_from_query(request: OutlineGenerationRequest):
#     logger.info(f"收到大纲生成请求，sessionId: {request.session_id}")
#     task_id = generate_task_id()
#     try:
#         tasks.generate_outline_from_query_task.delay(
#             job_id=task_id,
#             task_prompt=request.task_prompt,
#             is_online=request.is_online,
#             context_files=request.context_files,
#             redis_stream_key=task_id,  # 传递给 worker
#         )
#         logger.success(f"大纲生成任务已提交，Task ID: {task_id}")
#         return TaskCreationResponse(
#             redis_stream_key=task_id,
#             session_id=request.session_id,
#         )
#     except Exception as e:
#         logger.error(f"提交大纲生成任务失败: {e}")
#         raise HTTPException(status_code=500, detail="任务提交失败")

# @router.post("/jobs/document-from-outline",
#              response_model=TaskCreationResponse,
#              response_model_by_alias=True,
#              status_code=status.HTTP_202_ACCEPTED)
# async def generate_document_from_outline_json(
#     request: DocumentGenerationFromOutlineRequest, ):
#     logger.info(f"📥 收到从outline JSON生成文档请求，jobId: {request.job_id}")
#     logger.info(
#         f"📋 请求详情: sessionId={request.session_id}, outline长度={len(request.outline_json)}"
#     )

#     task_id = generate_task_id()
#     logger.info(f"🆔 生成任务ID: {task_id}")

#     try:
#         # 这一步保持不变，因为请求体中 outline_json 本身就是字符串
#         logger.info("🚀 提交Celery任务...")
#         result = tasks.generate_document_from_outline_task.delay(
#             job_id=task_id,
#             # 直接传递请求中的 JSON 字符串
#             outline_json=request.outline_json,
#             session_id=request.session_id,
#         )

#         logger.info(f"🔍 Celery任务发送结果: {result.id}")
#         logger.success(f"✅ 文档生成任务已提交，Task ID: {task_id}")

#         response_object = TaskCreationResponse(
#             redis_stream_key=task_id,
#             session_id=request.session_id,
#         )
#         logger.info(f"📤 返回响应: {response_object}")
#         return response_object

#     except Exception as e:
#         logger.error(f"❌ 提交文档生成任务失败: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="任务提交失败")


@router.post(
    "/jobs/document-from-outline-mock",
    response_model=TaskCreationResponse,  # 使用统一模型
    response_model_by_alias=True,  # 强制按别名输出
    status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline_json_mock(
    request: DocumentGenerationRequest, ):
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


# =================================================================
# 模拟服务端点 - 用于测试
# =================================================================


async def simulate_mock_generation_process(task_id: str, session_id: str):
    """一个完整的模拟后台任务，包括 Redis 流发布"""
    logger.info(
        f"[MOCK] Task {task_id} for session {session_id} has started in the background."
    )

    try:
        # 获取 Redis 客户端
        import redis.asyncio as redis
        from doc_agent.core.config import settings

        redis_client = redis.from_url(settings.redis_url,
                                      encoding="utf-8",
                                      decode_responses=True)
        await redis_client.ping()
        logger.info("模拟服务Redis客户端连接成功")

        # 发布任务开始事件
        await publish_mock_event(
            redis_client, task_id, {
                "eventType": "task_started",
                "taskType": "document_generation",
                "status": "started",
                "outline_title": "人工智能技术发展趋势"
            })

        # 发布分析进度
        await publish_mock_event(
            redis_client, task_id, {
                "eventType": "task_progress",
                "taskType": "document_generation",
                "progress": "正在分析大纲结构",
                "status": "running",
                "step": "analysis"
            })

        await asyncio.sleep(2)  # 模拟处理时间

        # 模拟章节处理
        chapters = [{
            "title": "人工智能概述",
            "index": 0
        }, {
            "title": "核心技术发展",
            "index": 1
        }, {
            "title": "应用领域拓展",
            "index": 2
        }]

        all_answer_origins = []
        all_web_sources = []

        for chapter in chapters:
            chapter_title = chapter["title"]
            chapter_index = chapter["index"]

            # 发布章节开始事件
            await publish_mock_event(
                redis_client, task_id, {
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
                    redis_client, task_id, {
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

            # 流式输出章节内容
            await publish_mock_event(
                redis_client, task_id, {
                    "eventType": "writer_started",
                    "taskType": "document_generation",
                    "progress": f"开始编写章节 {chapter_index + 1}",
                    "status": "running"
                })

            await stream_mock_document_content(redis_client, task_id,
                                               chapter_content)

            await asyncio.sleep(1)  # 章节间隔

        # 发布参考文献事件
        citations_data = {
            "answerOrigins": all_answer_origins,
            "webs": all_web_sources
        }

        await publish_mock_event(
            redis_client, task_id, {
                "eventType": "citations_completed",
                "taskType": "document_generation",
                "citations": citations_data,
                "totalAnswerOrigins": len(all_answer_origins),
                "totalWebSources": len(all_web_sources),
                "status": "completed"
            })

        # 发布任务完成事件
        await publish_mock_event(
            redis_client, task_id, {
                "eventType": "task_completed",
                "taskType": "document_generation",
                "status": "completed",
                "totalChapters": len(chapters),
                "citations": citations_data
            })

        logger.info(
            f"[MOCK] Task {task_id} for session {session_id} has finished.")

    except Exception as e:
        logger.error(
            f"[MOCK] Task {task_id} for session {session_id} failed: {e}")
        try:
            await publish_mock_event(
                redis_client, task_id, {
                    "eventType": "task_failed",
                    "taskType": "document_generation",
                    "status": "failed",
                    "error": str(e)
                })
        except:
            pass


async def publish_mock_event(redis_client, task_id: str, event_data: dict):
    """发布模拟事件到Redis Stream"""
    try:
        from datetime import datetime

        # 构造 Stream 名称 - 使用session_id作为流名称，与mock_document_service.py保持一致
        stream_name = task_id

        # 发布事件到 Redis Stream - 使用自动生成的ID
        counter_key = f"stream_counter:{stream_name}"
        i = await redis_client.incr(counter_key)
        # 让 Redis 自动生成 ID，但在事件数据中包含 sessionId-idx 格式
        session_id_idx = f"{task_id}-{i}"  # 事件数据中的格式: sessionId-idx

        # 准备事件数据
        event_data["redisId"] = session_id_idx
        event_data["timestamp"] = datetime.now().isoformat()

        await redis_client.xadd(
            stream_name, {"data": json.dumps(event_data, ensure_ascii=False)},
            id=session_id_idx)
        logger.info(f"模拟事件发布成功: {event_data.get('eventType', 'unknown')}")
    except Exception as e:
        logger.error(f"模拟事件发布失败: {e}")


async def stream_mock_document_content(redis_client,
                                       task_id: str,
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
                redis_client, task_id, {
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
            redis_client, task_id, {
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
