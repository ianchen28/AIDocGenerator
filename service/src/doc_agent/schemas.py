# service/src/doc_agent/schemas.py
from typing import Literal, Optional, Union, Any, List

from pydantic import BaseModel, Field, model_validator, ConfigDict


# --- Unified Task Creation Response ---
# 这是我们新的、唯一的异步任务创建响应模型
class TaskCreationResponse(BaseModel):
    """
    统一的、标准的异步任务创建成功后的响应体。
    """
    # 使用 ConfigDict 来设置 Pydantic v2 的配置
    model_config = ConfigDict(populate_by_name=True  # 允许通过别名进行填充
                              )

    # 内部字段名使用 snake_case，对外通过 alias 暴露 camelCase
    redis_stream_key: str = Field(...,
                                  alias="redisStreamKey",
                                  description="Redis流的Key，用于前端监听，通常就是任务ID")
    session_id: str = Field(..., alias="sessionId", description="会话ID，用于追踪")


# --- Source Models ---
class Source(BaseModel):
    """信息源模型，用于追踪和引用信息来源"""
    id: int = Field(..., description="唯一顺序标识符，用于引用（如 1, 2, 3...）")
    source_type: str = Field(
        ...,
        alias="sourceType",
        description="信息源类型（如 'webpage', 'document', 'es_result'）")
    title: str = Field(..., description="信息源标题")
    url: Optional[str] = Field(None, description="信息源URL，如果可用")
    content: str = Field(..., description="信息源的实际文本内容片段")
    cited: bool = Field(False, description="是否被引用")


# --- Outline Models ---
class OutlineNode(BaseModel):
    """大纲节点模型（递归结构）"""
    id: str
    title: str
    content_summary: Optional[str] = Field(None, alias="contentSummary")
    children: List['OutlineNode'] = []


# 支持递归模型引用
OutlineNode.model_rebuild()


class Outline(BaseModel):
    """大纲模型"""
    title: str
    nodes: List[OutlineNode]


# --- Request Models ---
class OutlineGenerationRequest(BaseModel):
    """大纲生成请求模型"""
    model_config = ConfigDict(populate_by_name=True)

    session_id: Union[str, int] = Field(...,
                                        alias="sessionId",
                                        description="会话ID")
    task_prompt: str = Field(..., alias="taskPrompt", description="用户的核心指令")
    is_online: bool = Field(False, alias="isOnline", description="是否调用web搜索")
    context_files: Optional[List[dict]] = Field(None,
                                                alias="contextFiles",
                                                description="相关上传文件列表")

    @model_validator(mode='before')
    @classmethod
    def validate_session_id(cls, data):
        if isinstance(data, dict) and 'sessionId' in data:
            if isinstance(data['sessionId'], (int, float)):
                data['sessionId'] = str(data['sessionId'])
        return data


class DocumentGenerationRequest(BaseModel):
    """文档生成请求模型"""
    job_id: str = Field(..., alias="jobId", description="由后端生成的唯一任务ID")
    outline: Outline = Field(..., description="结构化的大纲对象")


class DocumentGenerationFromOutlineRequest(BaseModel):
    """从outline JSON字符串生成文档的请求模型"""
    model_config = ConfigDict(populate_by_name=True)

    job_id: str = Field(..., alias="jobId", description="由后端生成的唯一任务ID")
    outline_json: str = Field(...,
                              alias="outlineJson",
                              description="outline的JSON序列化字符串")
    session_id: Optional[str] = Field(None,
                                      alias="sessionId",
                                      description="会话ID，用于追踪")


class EditActionRequest(BaseModel):
    """AI 编辑请求模型"""
    model_config = ConfigDict(populate_by_name=True)

    action: Literal["expand", "summarize", "continue_writing", "polish",
                    "custom"] = Field(..., description="编辑操作类型")
    text: str = Field(..., description="要编辑的文本内容")
    command: Optional[str] = Field(None, description="自定义命令")
    context: Optional[str] = Field(None, description="上下文信息")
    polish_style: Optional[Literal["professional", "conversational",
                                   "readable", "subtle", "academic",
                                   "literary"]] = Field(None,
                                                        alias="polishStyle",
                                                        description="润色风格")
