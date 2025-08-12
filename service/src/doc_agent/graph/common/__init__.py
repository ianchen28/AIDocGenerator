"""
共享工具模块

包含在不同节点之间共享的工具函数、源管理和解析器
"""

from .formatters import (
    format_requirements_to_text,
    format_sources_to_text,
    process_citations,
    format_chapter_summary,
)
from .parsers import (
    parse_es_search_results,
    parse_planner_response,
    parse_reflection_response,
    parse_web_search_results,
    parse_llm_json_response,
)
from .source_manager import (
    calculate_text_similarity,
    get_or_create_source_id,
    merge_sources_with_deduplication,
)

__all__ = [
    # 源管理
    'calculate_text_similarity',
    'get_or_create_source_id',
    'merge_sources_with_deduplication',
    # 解析器
    'parse_web_search_results',
    'parse_es_search_results',
    'parse_planner_response',
    'parse_reflection_response',
    'parse_llm_json_response',
    # 格式化器
    'format_requirements_to_text',
    'format_sources_to_text',
    'process_citations',
    'format_chapter_summary',
]
