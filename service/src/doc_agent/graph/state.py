# service/src/doc_agent/graph/state.py
from typing import Any, Optional, TypedDict

from doc_agent.schemas import Source


class ResearchState(TypedDict):
    """
    增强的状态，用于两级工作流：
    1. 上层研究与大纲生成
    2. 章节级详细研究与写作
    """
    # 日志追踪 ID
    run_id: Optional[str]  # 用于日志追踪的唯一标识符

    # 原始 prompt
    task_prompt: str
    # 研究主题
    topic: str

    # 文档样式和需求指南
    style_guide_content: Optional[str]  # 样式指南内容
    requirements_content: Optional[str]  # 需求文档内容

    # 以上为输入信息
    # -- 篇章级研究状态 --
    # 大纲结构
    document_outline: dict

    # 搜索信息源
    # id -> Source
    sources: dict[str, Source]

    # 章节处理
    chapters_to_process: list[
        dict]  # 章节列表: [{"chapter_title": "...", "description": "..."}]
    current_chapter_index: int  # 当前处理的章节索引

    # 上下文积累 - 保持连贯性
    completed_chapters: list[dict[
        str,
        Any]]  # e.g., [{"title": "...", "content": "...", "summary": "..."}]

    # -- 章节级研究状态 --
    # 研究计划
    research_plan: str
    # 搜索查询列表
    search_queries: list[str]
    # 每章节信息源列表
    chapter_research_list: list[dict[str, Any]]

    final_document: str
