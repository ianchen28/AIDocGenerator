# service/src/doc_agent/schemas.py
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- Source Models ---
class Source(BaseModel):
    """信息源模型，用于追踪和引用信息来源"""
    id: int = Field(..., description="唯一顺序标识符，用于引用（如 1, 2, 3...）")
    source_type: str = Field(
        ..., description="信息源类型（如 'webpage', 'document', 'es_result'）")
    title: str = Field(..., description="信息源标题")
    url: Optional[str] = Field(None, description="信息源URL，如果可用")
    content: str = Field(..., description="信息源的实际文本内容片段")


# --- Context Models ---
class ContextFile(BaseModel):
    """上下文文件模型"""
    file_id: str
    file_name: str
    storage_url: str
    file_type: Literal["content", "style",
                       "requirements"] = "content"  # 新增字段，区分文件类型，默认为content


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


# --- Outline Generation Models ---
class OutlineGenerationRequest(BaseModel):
    """大纲生成请求模型"""
    job_id: str = Field(..., description="由后端生成的唯一任务ID")
    task_prompt: str = Field(..., description="用户的核心指令")
    context_files: Optional[list[ContextFile]] = Field(None,
                                                       description="上下文文件列表")


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


# --- Document Generation Models ---
class DocumentGenerationRequest(BaseModel):
    """文档生成请求模型"""
    job_id: str = Field(..., description="由后端生成的唯一任务ID")
    outline: Outline = Field(..., description="结构化的大纲对象")


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
    job_id: str = Field(..., description="唯一任务ID")


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


# --- AI Editing Models ---
class EditActionRequest(BaseModel):
    """AI 编辑请求模型"""
    action: Literal["expand", "summarize", "continue_writing",
                    "polish_professional", "polish_conversational",
                    "custom"] = Field(
                        ..., description="编辑操作类型：扩写、总结、续写、专业润色、口语化润色或自定义命令")
    text: str = Field(..., description="要编辑的文本内容")
    command: Optional[str] = Field(None,
                                   description="当 action 为 'custom' 时，此字段为必填项")
    context: Optional[str] = Field(
        None, description="当 action 为 'continue_writing' 时，此字段为上下文信息")


class EditActionResponse(BaseModel):
    """AI 编辑响应模型"""
    original_text: str = Field(..., description="原始文本")
    edited_text: str = Field(..., description="编辑后的文本")
    action: str = Field(..., description="执行的编辑操作")
