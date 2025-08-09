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
    date: Optional[str] = Field(None, description="信息源日期，如果可用")
    author: Optional[str] = Field(None, description="信息源作者，如果可用")
    page_number: Optional[int] = Field(None, description="信息源页码，如果可用")
    cited: bool = Field(False, description="是否被引用")
    file_token: Optional[str] = Field(None, description="文件token，可选")
    ocr_result_token: Optional[str] = Field(None,
                                            description="ocr结果文件token，可选")


class AnswerOrigin(BaseModel):
    """
    内部参考文献来源模型，用于追踪和引用信息来源
    """
    domain_id: str = Field(..., description="域ID", alias="domainId")
    file_token: str = Field(..., description="文件token", alias="fileToken")
    is_feishu_source: bool = Field(...,
                                   description="是否是飞书源",
                                   alias="isFeishuSource")
    metadata: dict = Field(..., description="元数据", alias="metadata")
    origininfo: str = Field(..., description="来源信息", alias="origininfo")
    title: str = Field(..., description="标题", alias="title")
    valid: bool = Field(..., description="是否有效", alias="valid")


class WebSource(BaseModel):
    """
    网页源模型，用于追踪和引用信息来源
    """
    date_published: str = Field(...,
                                description="数据发布时间",
                                alias="datePublished")
    material_content: str = Field(...,
                                  description="材料内容",
                                  alias="materialContent")
    material_id: str = Field(..., description="材料ID", alias="materialId")
    material_title: str = Field(..., description="材料标题", alias="materialTitle")
    site_name: str = Field(..., description="站点名称", alias="siteName")
    url: str = Field(..., description="URL", alias="url")


# --- Outline Models ---
class OutlineNode(BaseModel):
    """大纲节点模型（递归结构）"""
    id: str = Field(..., description="节点ID,支持多级格式如 1.1.2")
    title: str = Field(..., description="节点标题")
    content_summary: Optional[str] = Field(None,
                                           alias="contentSummary",
                                           description="节点内容概要")
    children: list['OutlineNode'] = Field(default_factory=list,
                                          description="子节点列表")
    image_infos: list[dict] = Field(default_factory=list,
                                    alias="imageInfos",
                                    description="节点相关图片信息")
    level: Optional[int] = Field(None, description="节点层级,从1开始计数")
    parent_id: Optional[str] = Field(None,
                                     alias="parentId",
                                     description="父节点ID")

    @model_validator(mode='after')
    def calculate_level(self):
        """计算节点层级"""
        if self.id:
            self.level = len(self.id.split('.'))
        return self

    @model_validator(mode='after')
    def set_parent_id(self):
        """设置父节点ID"""
        if self.id and '.' in self.id:
            self.parent_id = '.'.join(self.id.split('.')[:-1])
        return self


# 支持递归模型引用
OutlineNode.model_rebuild()


class Outline(BaseModel):
    """大纲模型"""
    title: str = Field(..., description="文档标题")
    word_count: int = Field(5000, alias="wordCount", description="全文字数")
    nodes: list[OutlineNode] = Field(..., description="大纲节点列表")
    max_depth: Optional[int] = Field(None, description="大纲最大深度")

    @model_validator(mode='after')
    def calculate_max_depth(self):
        """计算大纲最大深度"""
        if self.nodes:

            def get_depth(node: OutlineNode) -> int:
                if not node.children:
                    return 1
                return 1 + max(get_depth(child) for child in node.children)

            self.max_depth = max(get_depth(node) for node in self.nodes)
        return self


# --- Request Models ---
class OutlineGenerationRequest(BaseModel):
    """大纲生成请求模型"""
    model_config = ConfigDict(populate_by_name=True)

    session_id: Union[str, int] = Field(...,
                                        alias="sessionId",
                                        description="会话ID")
    task_prompt: str = Field(..., alias="taskPrompt", description="用户的核心指令")
    is_online: bool = Field(False, alias="isOnline", description="是否调用web搜索")
    context_files: Optional[list[dict]] = Field(None,
                                                alias="contextFiles",
                                                description="相关上传文件列表")
    style_guide_content: Optional[str] = Field(None,
                                               alias="styleGuideContent",
                                               description="样式指南内容")
    requirements: Optional[str] = Field(None, description="需求说明")

    @model_validator(mode='before')
    @classmethod
    def validate_session_id(cls, data):
        if isinstance(data, dict) and 'sessionId' in data:
            if isinstance(data['sessionId'], (int, float)):
                data['sessionId'] = str(data['sessionId'])
        return data


# 后续和大纲生成 request 合并
class DocumentGenerationRequest(BaseModel):
    """文档生成请求模型"""
    task_prompt: str = Field(..., alias="taskPrompt", description="用户的核心指令")
    session_id: str = Field(..., alias="sessionId", description="由后端生成的唯一任务ID")
    outline: str = Field(..., description="结构化的大纲对象文件")
    context_files: Optional[list[dict]] = Field(None,
                                                alias="contextFiles",
                                                description="相关上传文件列表")
    is_online: bool = Field(False, alias="isOnline", description="是否调用web搜索")


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
