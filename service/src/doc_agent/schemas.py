# service/src/doc_agent/schemas.py
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- Context Models ---
class ContextFile(BaseModel):
    """上下文文件模型"""
    file_id: str
    file_name: str
    storage_url: str
    file_type: Literal["content", "style", "requirements"]  # 新增字段，区分文件类型


class CreateContextRequest(BaseModel):
    """创建上下文请求"""
    files: list[ContextFile]


class ContextStatusResponse(BaseModel):
    """上下文状态响应"""
    context_id: str
    status: Literal["PENDING", "INDEXING", "READY", "FAILED"]


# --- Job Models ---
class CreateJobRequest(BaseModel):
    """创建作业请求"""
    context_id: Optional[str] = None
    task_prompt: str = Field(..., description="用户的核心任务指令")
    genre: str = Field("default", description="文档类型，用于选择相应的prompt策略")


class JobResponse(BaseModel):
    """作业响应"""
    job_id: str
    status: str
    created_at: str


# --- Outline Models ---
class OutlineNode(BaseModel):
    """大纲节点模型（递归结构）"""
    id: str
    title: str
    content_summary: Optional[str] = None
    children: list['OutlineNode'] = []


# 支持递归模型引用
OutlineNode.model_rebuild()


class Outline(BaseModel):
    """大纲模型"""
    title: str
    nodes: list[OutlineNode]


class OutlineResponse(BaseModel):
    """大纲响应模型"""
    job_id: str
    outline_status: Literal["GENERATING", "READY", "FAILED"]
    outline: Optional[Outline] = None


class UpdateOutlineRequest(BaseModel):
    """更新大纲请求模型"""
    outline: Outline


class UpdateOutlineResponse(BaseModel):
    """更新大纲响应模型"""
    job_id: str
    message: str


# --- Legacy Models (保持向后兼容) ---
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
