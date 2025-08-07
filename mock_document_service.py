#!/usr/bin/env python3
"""
模拟文档生成服务 - 简化版本

只实现根据outline生成Document的核心响应逻辑
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

# 配置日志
logger.add("logs/mock_service.log", rotation="1 day", retention="7 days")

app = FastAPI(title="Mock Document Generation Service", version="1.0.0")

# Redis 配置 - 使用配置文件
import sys
import os

# 添加项目路径到 sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'service', 'src'))

# 导入配置
from doc_agent.core.config import settings

# 使用配置文件中的 Redis URL
REDIS_URL = settings.redis_url


class DocumentGenerationFromOutlineRequest(BaseModel):
    """从outline JSON字符串生成文档的请求模型"""
    task_prompt: str = Field(..., description="任务提示")
    outlineJson: str = Field(..., description="outline的JSON序列化字符串")
    sessionId: str = Field(..., description="会话ID，用于追踪")


class TaskCreationResponse(BaseModel):
    """任务创建后的API响应"""
    job_id: str = Field(..., description="唯一任务ID")


async def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例"""
    try:
        redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        logger.info("Redis客户端连接成功")
        return redis_client
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        raise


async def publish_event(redis_client: redis.Redis, session_id: str, event_data: dict):
    """发布事件到Redis Stream"""
    try:
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
        logger.info(f"事件发布成功: {event_data.get('eventType', 'unknown')}")
    except Exception as e:
        logger.error(f"事件发布失败: {e}")


async def stream_document_content(redis_client: redis.Redis, session_id: str, content: str, chunk_size: int = 10):
    """流式输出文档内容到Redis Stream"""
    try:
        # 将内容按字符分割成token
        tokens = list(content)
        
        for i in range(0, len(tokens), chunk_size):
            chunk = tokens[i:i + chunk_size]
            chunk_text = ''.join(chunk)
            
            # 发布内容流事件
            await publish_event(redis_client, session_id, {
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
        await publish_event(redis_client, session_id, {
            "eventType": "document_content_completed",
            "taskType": "document_generation",
            "totalTokens": len(tokens),
            "status": "completed"
        })
        
        logger.info(f"文档内容流式输出完成，共 {len(tokens)} 个token")
        
    except Exception as e:
        logger.error(f"流式输出文档内容失败: {e}")


def generate_mock_chapter_content(chapter_title: str, chapter_index: int) -> str:
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
    sources = []
    
    # 生成文档类型的引用源
    sources.append({
        "id": f"{chapter_index * 3 + 1}",
        "detailId": f"{chapter_index * 3 + 1}",
        "originInfo": f"关于{chapter_title}的重要研究成果和最新发现。本文主要参考了相关领域的研究文献，包括理论基础、实证研究和应用案例。",
        "title": f"{chapter_title}研究综述.pdf",
        "fileToken": f"token_{chapter_index * 3 + 1}_{int(time.time())}",
        "domainId": "document",
        "isFeishuSource": None,
        "valid": "true",
        "metadata": json.dumps({
            "file_name": f"{chapter_title}研究综述.pdf",
            "locations": [{"pagenum": chapter_index + 1}],
            "source": "data_platform"
        }, ensure_ascii=False)
    })
    
    # 生成标准类型的引用源
    sources.append({
        "id": f"{chapter_index * 3 + 2}",
        "detailId": f"{chapter_index * 3 + 2}",
        "originInfo": f"详细的技术分析报告，包含{chapter_title}的核心技术要点和标准规范。",
        "title": f"GB/T {chapter_index + 1000}-2023 {chapter_title}技术标准.pdf",
        "fileToken": f"token_{chapter_index * 3 + 2}_{int(time.time())}",
        "domainId": "standard",
        "isFeishuSource": None,
        "valid": "true",
        "metadata": json.dumps({
            "file_name": f"GB/T {chapter_index + 1000}-2023 {chapter_title}技术标准.pdf",
            "locations": [{"pagenum": chapter_index + 5}],
            "code": f"GB/T {chapter_index + 1000}-2023",
            "gfid": f"GB/T {chapter_index + 1000}-2023",
            "source": "data_platform"
        }, ensure_ascii=False)
    })
    
    # 生成书籍类型的引用源
    sources.append({
        "id": f"{chapter_index * 3 + 3}",
        "detailId": f"{chapter_index * 3 + 3}",
        "originInfo": f"最新的学术研究成果，为{chapter_title}提供了理论支撑和实践指导。",
        "title": f"{chapter_title}技术手册.pdf",
        "fileToken": f"token_{chapter_index * 3 + 3}_{int(time.time())}",
        "domainId": "book",
        "isFeishuSource": None,
        "valid": "true",
        "metadata": json.dumps({
            "file_name": f"{chapter_title}技术手册.pdf",
            "locations": [{"pagenum": chapter_index + 10}],
            "source": "data_platform"
        }, ensure_ascii=False)
    })
    
    return sources


def generate_mock_web_sources(chapter_title: str, chapter_index: int) -> list:
    """生成模拟的网页引用源列表"""
    web_sources = []
    
    web_sources.append({
        "id": f"web_{chapter_index * 2 + 1}",
        "detailId": f"web_{chapter_index * 2 + 1}",
        "materialContent": f"关于{chapter_title}的在线资料和最新动态。包含相关技术发展、行业趋势和实际应用案例。",
        "materialTitle": f"{chapter_title}技术发展动态-技术资讯",
        "url": f"https://example.com/tech/{chapter_title.lower().replace(' ', '-')}",
        "siteName": "技术资讯网",
        "datePublished": "2023年12月15日",
        "materialId": f"web_{chapter_index * 2 + 1}_{int(time.time())}"
    })
    
    web_sources.append({
        "id": f"web_{chapter_index * 2 + 2}",
        "detailId": f"web_{chapter_index * 2 + 2}",
        "materialContent": f"{chapter_title}相关的研究报告和行业分析。",
        "materialTitle": f"{chapter_title}行业分析报告-研究报告",
        "url": f"https://research.example.com/report/{chapter_index + 1}",
        "siteName": "研究报告网",
        "datePublished": "2023年11月20日",
        "materialId": f"web_{chapter_index * 2 + 2}_{int(time.time())}"
    })
    
    return web_sources


async def simulate_document_generation(session_id: str, outline_data: dict):
    """模拟文档生成过程"""
    try:
        redis_client = await get_redis_client()

        # 1. 发布任务开始事件
        await publish_event(redis_client, session_id, {
            "eventType": "task_started",
            "taskType": "document_generation",
            "status": "started",
            "outline_title": outline_data.get("title", "未知标题")
        })

        # 2. 发布分析进度
        await publish_event(redis_client, session_id, {
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
            await publish_event(redis_client, session_id, {
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
                await publish_event(redis_client, session_id, {
                    "eventType": "chapter_progress",
                    "taskType": "document_generation",
                    "chapterTitle": chapter_title,
                    "step": step,
                    "progress": f"正在执行{step}步骤",
                    "status": "running"
                })
                await asyncio.sleep(1)  # 模拟步骤处理时间

            # 生成章节内容
            chapter_content = generate_mock_chapter_content(chapter_title, chapter_index)
            
            # 生成章节的引用源
            chapter_sources = generate_mock_sources(chapter_title, chapter_index)
            chapter_web_sources = generate_mock_web_sources(chapter_title, chapter_index)
            
            all_answer_origins.extend(chapter_sources)
            all_web_sources.extend(chapter_web_sources)
            
            # 发布章节完成事件
            await publish_event(redis_client, session_id, {
                "eventType": "chapter_completed",
                "taskType": "document_generation",
                "chapterTitle": chapter_title,
                "chapterContent": chapter_content,
                "chapterIndex": chapter_index,
                "status": "completed"
            })

            # 4. 每个章节完成后立即流式输出该章节内容
            await publish_event(redis_client, session_id, {
                "eventType": "writer_started",
                "taskType": "document_generation",
                "progress": f"开始编写章节 {chapter_index + 1}",
                "status": "running"
            })
            
            await stream_document_content(redis_client, session_id, chapter_content)
            
            await asyncio.sleep(1)  # 章节间隔

        # 5. 发布参考文献事件
        citations_data = {
            "answerOrigins": all_answer_origins,
            "webs": all_web_sources
        }
        
        await publish_event(redis_client, session_id, {
            "eventType": "citations_completed",
            "taskType": "document_generation",
            "citations": citations_data,
            "totalAnswerOrigins": len(all_answer_origins),
            "totalWebSources": len(all_web_sources),
            "status": "completed"
        })

        # 6. 发布任务完成事件
        await publish_event(redis_client, session_id, {
            "eventType": "task_completed",
            "taskType": "document_generation",
            "status": "completed",
            "totalChapters": len(chapters),
            "citations": citations_data
        })

        logger.info(f"Session {session_id}: 文档生成完成")

    except Exception as e:
        logger.error(f"Session {session_id}: 文档生成失败: {e}")
        await publish_event(redis_client, session_id, {
            "eventType": "task_failed",
            "taskType": "document_generation",
            "status": "failed",
            "error": str(e)
        })


@app.post("/jobs/document-from-outline",
          response_model=TaskCreationResponse,
          status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline_json(request: DocumentGenerationFromOutlineRequest):
    """从outline JSON字符串生成文档接口（模拟版本）"""
    logger.info(f"收到文档生成请求，sessionId: {request.sessionId}")

    try:
        # 解析outline JSON
        outline_data = json.loads(request.outlineJson)

        # 验证数据
        if not outline_data.get('title', '').strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="大纲标题不能为空")

        if not outline_data.get('nodes'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="大纲节点不能为空")

        # 启动异步任务
        asyncio.create_task(simulate_document_generation(request.sessionId, outline_data))

        return TaskCreationResponse(job_id=request.sessionId)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                          detail=f"outline JSON格式无效: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档生成请求处理失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"文档生成请求处理失败: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "mock_document_generation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 