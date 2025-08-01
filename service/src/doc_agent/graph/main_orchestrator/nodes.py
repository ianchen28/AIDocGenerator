"""
主编排器节点模块

这个文件现在作为向后兼容的接口，实际功能已迁移到 nodes/ 子模块中。
"""

# 导入新的模块化节点
from .nodes.research import initial_research_node
from .nodes.generation import (outline_generation_node, split_chapters_node,
                               bibliography_node)
from .nodes.editor import fusion_editor_node

# 导入共享工具函数（保持向后兼容）
from ..common import (
    parse_web_search_results,
    parse_es_search_results,
    format_sources_to_text,
)

# 为了向后兼容，保留原有的函数名（带下划线的版本）
_parse_web_search_results = parse_web_search_results
_parse_es_search_results = parse_es_search_results
_format_sources_to_text = format_sources_to_text

__all__ = [
    # 节点函数
    'initial_research_node',
    'outline_generation_node',
    'split_chapters_node',
    'bibliography_node',
    'fusion_editor_node',

    # 工具函数（向后兼容）
    'parse_web_search_results',
    'parse_es_search_results',
    'format_sources_to_text',

    # 旧函数名（向后兼容）
    '_parse_web_search_results',
    '_parse_es_search_results',
    '_format_sources_to_text',
]
