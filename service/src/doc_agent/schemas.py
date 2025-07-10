# service/src/doc_agent/schemas.py
from pydantic import BaseModel, Field
from typing import Literal


class GenerationRequest(BaseModel):
    """API请求体"""
    topic: str = Field(..., description="文档生成的主题")
    style: str = Field("professional", description="文档风格")


class TaskCreationResponse(BaseModel):
    """任务创建后的API响应"""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """任务状态查询的API响应"""
    task_id: str
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    progress: str | None = None  # e.g., "Executing web search"


class TaskResultResponse(BaseModel):
    """任务结果查询的API响应"""
    task_id: str
    status: Literal["COMPLETED"]
    document_url: str  # 指向最终文档的链接或直接包含内容
    # document_content: str
