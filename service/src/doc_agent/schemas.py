# service/src/doc_agent/schemas.py
from typing import Any, Literal, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


# --- Unified Source Model ---
class Source(BaseModel):
    """
    统一的信息源模型，支持所有前端格式（answer_origins 和 webs）
    使用 alias 实现下划线命名到驼峰命名的自动转换
    """
    model_config = ConfigDict(
        populate_by_name=True,  # 允许通过别名进行填充
        extra="allow"  # 允许额外字段，提高兼容性
    )

    # === 基础字段 ===
    id: int = Field(..., description="唯一顺序标识符，用于引用（如 1, 2, 3...）")
    doc_id: str = Field(..., description="文档ID", alias="docId")
    doc_from: str = Field(..., description="文档来源", alias="docFrom")
    domain_id: str = Field(..., description="文档域ID", alias="domainId")
    index: str = Field(..., description="文档索引", alias="index")
    source_type: str = Field(
        ...,
        alias="sourceType",
        description="信息源类型（如 'webpage', 'document', 'es_result'）")
    title: str = Field(..., description="信息源标题")
    content: str = Field(..., description="信息源的实际文本内容片段")

    # === 通用可选字段 ===
    url: Optional[str] = Field(None, description="信息源URL，如果可用")
    date: Optional[str] = Field(None, description="信息源日期，如果可用")
    author: Optional[str] = Field(None, description="信息源作者，如果可用")
    page_number: Optional[int] = Field(None, description="信息源页码，如果可用")
    cited: bool = Field(False, description="是否被引用")

    # === 文件相关字段 ===
    file_token: Optional[str] = Field(None,
                                      alias="fileToken",
                                      description="文件token，可选")
    ocr_file_token: Optional[str] = Field(None,
                                          alias="ocrFileToken",
                                          description="ocr文件token，可选")
    ocr_result_token: Optional[str] = Field(None,
                                            description="ocr结果文件token，可选")

    # === 前端格式字段（通过 alias 转换为驼峰命名）===
    # answer_origins 格式字段
    domain_id: str = Field("document",
                           alias="domainId",
                           description="域ID（前端格式）")
    is_feishu_source: bool = Field(False,
                                   alias="isFeishuSource",
                                   description="是否飞书源（前端格式）")
    is_valid: bool = Field(True, alias="valid", description="是否有效（前端格式）")
    origin_info: str = Field("", alias="originInfo", description="来源信息（前端格式）")

    # webs 格式字段
    date_published: str = Field("",
                                alias="datePublished",
                                description="发布日期（前端格式）")
    material_content: str = Field("",
                                  alias="materialContent",
                                  description="材料内容（前端格式）")
    material_id: str = Field("", alias="materialId", description="材料ID（前端格式）")
    material_title: str = Field("",
                                alias="materialTitle",
                                description="材料标题（前端格式）")
    site_name: str = Field("", alias="siteName", description="站点名称（前端格式）")

    # === 元数据字段 ===
    metadata: dict = Field(default_factory=dict, description="元数据信息")

    # === 额外字段（用于扩展）===
    detail_id: Optional[str] = Field(None,
                                     alias="detailId",
                                     description="详情ID")
    code: Optional[str] = Field(None, description="代码标识")
    gfid: Optional[str] = Field(None, description="GFID标识")

    @model_validator(mode='after')
    def populate_frontend_fields(self):
        """自动填充前端格式字段"""
        # 填充 answer_origins 格式字段
        if not self.origin_info:
            self.origin_info = (self.content or "")[:1000]  # 限制长度

        if not self.domain_id:
            self.domain_id = "document"

        # 填充 webs 格式字段
        if not self.date_published and self.date:
            self.date_published = self.date

        if not self.material_content:
            self.material_content = (self.content or "")[:1000]

        if not self.material_id:
            self.material_id = f"web_{self.id}" if self.source_type == "webpage" else f"doc_{self.id}"

        if not self.material_title:
            self.material_title = self.title or ""

        if not self.site_name and self.url:
            try:
                self.site_name = urlparse(self.url).netloc
            except Exception:
                self.site_name = ""

        # 填充元数据
        if not self.metadata:
            self.metadata = {
                "file_name":
                self.title or "",
                "locations": ([{
                    "pagenum": self.page_number
                }] if self.page_number is not None else []),
                "source":
                "data_platform"
            }

        return self

    def to_dict(self, **kwargs) -> dict[str, Any]:
        """转换为字典，支持 Pydantic 的所有参数"""
        return self.model_dump(**kwargs)

    def to_json(self, **kwargs) -> str:
        """转换为 JSON 字符串"""
        return self.model_dump_json(**kwargs)

    @classmethod
    def batch_to_redis_fe(
        cls,
        sources: list['Source'],
        content_max_length: int = 1000
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        批量转换 Source 列表为前端需要的格式
        使用 model_dump() 自动处理 alias 转换
        """
        answer_origins = []
        webs = []

        for source in sources:
            try:
                # 使用 model_dump() 自动处理 alias 转换
                source_dict = source.model_dump(by_alias=True)

                if source.source_type == "webpage":
                    # 网页类型 -> webs 格式
                    web_dict = {
                        "id":
                        source_dict.get("id"),
                        "datePublished":
                        source_dict.get("datePublished", ""),
                        "materialContent":
                        source_dict.get("materialContent",
                                        "")[:content_max_length],
                        "materialId":
                        source_dict.get("materialId", ""),
                        "materialTitle":
                        source_dict.get("materialTitle", ""),
                        "siteName":
                        source_dict.get("siteName", ""),
                        "url":
                        source_dict.get("url", "")
                    }
                    webs.append(web_dict)
                else:
                    # 其他类型 -> answer_origins 格式
                    origin_dict = {
                        "id":
                        source_dict.get("id"),
                        "docId":
                        source_dict.get("docId", ""),
                        "docFrom":
                        source_dict.get("docFrom", ""),
                        "domainId":
                        source_dict.get("domainId", ""),
                        "index":
                        source_dict.get("index", ""),
                        "title":
                        source_dict.get("title", ""),
                        "fileToken":
                        source_dict.get("fileToken", ""),
                        "isFeishuSource":
                        source_dict.get("isFeishuSource", False),
                        "valid":
                        source_dict.get("valid", True),
                        "originInfo":
                        source_dict.get("originInfo", "")[:content_max_length],
                        "metadata":
                        source_dict.get("metadata", {})
                    }
                    answer_origins.append(origin_dict)

            except Exception as e:
                from doc_agent.core.logger import logger
                logger.warning(f"Source {source.id} 转换失败: {e}")

        return answer_origins, webs

    @classmethod
    def create_es_result(cls,
                         id: int,
                         title: str,
                         content: str,
                         file_token: str = None,
                         page_number: int = None,
                         **kwargs) -> 'Source':
        """创建 ES 搜索结果源"""
        return cls(id=id,
                   source_type="es_result",
                   title=title,
                   content=content,
                   file_token=file_token,
                   page_number=page_number,
                   **kwargs)

    @classmethod
    def create_webpage(cls,
                       id: int,
                       title: str,
                       content: str,
                       url: str,
                       date: str = None,
                       **kwargs) -> 'Source':
        """创建网页源"""
        return cls(id=id,
                   source_type="webpage",
                   title=title,
                   content=content,
                   url=url,
                   date=date,
                   **kwargs)

    @classmethod
    def create_document(cls,
                        id: int,
                        title: str,
                        content: str,
                        file_token: str = None,
                        **kwargs) -> 'Source':
        """创建文档源"""
        return cls(id=id,
                   source_type="document",
                   title=title,
                   content=content,
                   file_token=file_token,
                   **kwargs)


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
