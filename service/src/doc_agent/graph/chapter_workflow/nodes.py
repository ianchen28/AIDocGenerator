"""
章节工作流节点模块

这个文件现在作为向后兼容的接口，实际功能已迁移到 nodes/ 子模块中。
"""

# 导入新的模块化节点
from .nodes.planner import planner_node
from .nodes.researcher import researcher_node, async_researcher_node
from .nodes.writer import writer_node
from .nodes.reflection import reflection_node

# 导入共享工具函数（保持向后兼容）
from ..common import (
    calculate_text_similarity,
    get_or_create_source_id,
    merge_sources_with_deduplication,
    parse_web_search_results,
    parse_es_search_results,
    parse_planner_response,
    parse_reflection_response,
    format_sources_to_text,
    process_citations,
)

# 为了向后兼容，保留原有的函数名
_parse_web_search_results = parse_web_search_results
_parse_es_search_results = parse_es_search_results
_parse_reflection_response = parse_reflection_response
_process_citations = process_citations
_format_sources_to_text = format_sources_to_text

__all__ = [
    # 节点函数
    'planner_node',
    'researcher_node',
    'async_researcher_node',
    'writer_node',
    'reflection_node',

    # 工具函数（向后兼容）
    'calculate_text_similarity',
    'get_or_create_source_id',
    'merge_sources_with_deduplication',
    'parse_web_search_results',
    'parse_es_search_results',
    'parse_planner_response',
    'parse_reflection_response',
    'format_sources_to_text',
    'process_citations',

    # 旧函数名（向后兼容）
    '_parse_web_search_results',
    '_parse_es_search_results',
    '_parse_reflection_response',
    '_process_citations',
    '_format_sources_to_text',
]
