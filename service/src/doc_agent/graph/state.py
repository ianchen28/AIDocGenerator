# service/src/doc_agent/graph/state.py
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages

from ..schemas import Source


class ResearchState(TypedDict):
    """
    增强的状态，用于两级工作流：
    1. 上层研究与大纲生成
    2. 章节级详细研究与写作
    """
    # 研究主题
    topic: str

    # 第一层: 上层研究的初始研究结果
    initial_sources: list[Source]  # 初始研究结果

    # 文档结构
    document_outline: dict  # 结构化的大纲，包含章节和部分

    # 章节处理
    chapters_to_process: list[
        dict]  # 章节列表: [{"chapter_title": "...", "description": "..."}]
    current_chapter_index: int  # 当前处理的章节索引

    # 上下文积累 - 保持连贯性
    completed_chapters_content: list[str]  # 已写章节的上下文内容

    # 最终输出
    final_document: str  # 完整的、拼接的文档

    # 章节级研究状态
    research_plan: str  # 当前章节的研究计划
    search_queries: list[str]  # 当前章节的搜索查询列表
    gathered_sources: list[Source]  # 当前章节收集的数据

    # 源追踪 - 用于引用和溯源
    sources: list[Source]  # 当前章节收集的所有信息源

    # 全局引用源追踪 - 用于最终参考文献
    cited_sources: dict  # 存储所有唯一源，按ID索引

    # 当前章节的引用源 - 用于章节级引用追踪
    cited_sources_in_chapter: list[Source]  # 当前章节引用的源列表

    # 对话历史
    messages: Annotated[list, add_messages]
