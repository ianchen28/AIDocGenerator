# service/src/doc_agent/schemas.py
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


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
    session_id: Union[str, int] = Field(...,
                                        alias="sessionId",
                                        description="会话ID，类似job_id，支持字符串或长整型")
    task_prompt: str = Field(..., alias="taskPrompt", description="用户的核心指令")
    is_online: bool = Field(False, alias="isOnline", description="是否调用web搜索")
    context_files: Optional[list[dict]] = Field(None,
                                                alias="contextFiles",
                                                description="相关上传文件列表")

    # 文件相关字段（用于后续处理）
    attachment_type: Optional[int] = Field(
        None,
        alias="attachmentType",
        description="附件类型(0-大纲模板/1-上传参考资料/2-知识选择参考资料)")
    attachment_file_token: Optional[str] = Field(None,
                                                 alias="attachmentFileToken",
                                                 description="文件唯一token")
    is_content_refer: Optional[int] = Field(None,
                                            alias="isContentRefer",
                                            description="是否内容参考(0-否/1-是)")
    is_style_imitative: Optional[int] = Field(None,
                                              alias="isStyleImitative",
                                              description="是否风格仿写(0-否/1-是)")
    is_writing_requirement: Optional[int] = Field(
        None, alias="isWritingRequirement", description="是否编写要求(0-否/1-是)")

    class Config:
        populate_by_name = True


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


class OutlineGenerationResponse(BaseModel):
    """大纲生成响应模型"""
    session_id: Union[str, int] = Field(...,
                                        alias="sessionId",
                                        description="会话ID，支持字符串或长整型")
    redis_stream_key: str = Field(...,
                                  alias="redisStreamKey",
                                  description="Redis流响应的key，用于前端监听")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")

    class Config:
        populate_by_name = True


class TaskStatusResponse(BaseModel):
    """任务状态查询的API响应"""
    task_id: str
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    progress: Optional[str] = None  # e.g., "Executing web search"


class TaskResultResponse(BaseModel):
    """任务结果查询的API响应"""
    task_id: str
    status: Literal["COMPLETED"]
    document_url: str  # 指向最终文档的链接或直接包含内容
    # document_content: str


# --- AI Editing Models ---
class EditActionRequest(BaseModel):
    """AI 编辑请求模型"""
    action: Literal["expand", "summarize", "continue_writing", "polish",
                    "custom"] = Field(...,
                                      description="编辑操作类型：扩写、总结、续写、润色或自定义命令")
    text: str = Field(..., description="要编辑的文本内容")
    command: Optional[str] = Field(None,
                                   description="当 action 为 'custom' 时，此字段为必填项")
    context: Optional[str] = Field(
        None, description="当 action 为 'continue_writing' 时，此字段为可选的上下文信息")
    polish_style: Optional[Literal[
        "professional", "conversational", "readable", "subtle", "academic",
        "literary"]] = Field(None, description="当 action 为 'polish' 时，此字段为必填项")

    @model_validator(mode='after')
    def validate_action_requirements(self):
        """验证不同 action 的必填字段"""
        if self.action == "polish" and not self.polish_style:
            raise ValueError("当 action 为 'polish' 时，polish_style 字段为必填项")

        if self.action == "custom" and not self.command:
            raise ValueError("当 action 为 'custom' 时，command 字段为必填项")

        # 续写功能不再要求 context 字段为必填项
        # if self.action == "continue_writing" and not self.context:
        #     raise ValueError("当 action 为 'continue_writing' 时，context 字段为必填项")

        return self


class EditActionResponse(BaseModel):
    """AI 编辑响应模型"""
    original_text: str = Field(..., description="原始文本")
    edited_text: str = Field(..., description="编辑后的文本")
    action: str = Field(..., description="执行的编辑操作")
