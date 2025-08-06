# service/src/doc_agent/graph/state.py
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages

from doc_agent.schemas import Source


class ResearchState(TypedDict):
    """
    增强的状态，用于两级工作流：
    1. 上层研究与大纲生成
    2. 章节级详细研究与写作
    """
    # 日志追踪 ID
    run_id: Optional[str]  # 用于日志追踪的唯一标识符

    # 研究主题
    topic: str

    # 文档样式和需求指南
    style_guide_content: Optional[str]  # 样式指南内容
    requirements_content: Optional[str]  # 需求文档内容

    # 第一层: 上层研究的初始研究结果
    initial_sources: list[Source]  # 初始研究结果

    # 文档结构
    document_outline: dict  # 结构化的大纲，包含章节和部分

    # 章节处理
    chapters_to_process: list[
        dict]  # 章节列表: [{"chapter_title": "...", "description": "..."}]
    current_chapter_index: int  # 当前处理的章节索引

    # 上下文积累 - 保持连贯性
    completed_chapters: list[dict[
        str,
        Any]]  # e.g., [{"title": "...", "content": "...", "summary": "..."}]

    # 最终输出
    final_document: str  # 完整的、拼接的文档

    # 章节级研究状态
    research_plan: str  # 当前章节的研究计划
    search_queries: list[str]  # 当前章节的搜索查询列表
    gathered_sources: list[Source]  # 当前章节收集的数据

    # 源追踪
    sources: list[Source]  # 当前章节收集的所有信息源，章节生成后并入 all_sources
    all_sources: list[Source]  # 所有章节收集的所有信息源
    current_citation_index: int = 1  # 当前章节引用源的索引编号

    # 全局引用源追踪 - 用于最终参考文献
    cited_sources: list[Source]  # 🔧 修复：改为列表以保持一致性
    cited_sources_in_chapter: list[Source]  # 当前章节引用源

    # 对话历史
    messages: Annotated[list, add_messages]
