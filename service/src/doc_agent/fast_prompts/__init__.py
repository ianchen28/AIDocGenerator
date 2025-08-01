# service/src/doc_agent/fast_prompts/__init__.py
"""
Fast Prompts 模块

包含用于快速演示模式的简化提示词模板
目标：3-5分钟内完成文档生成
"""

from .content_processor import (
    FAST_CONTENT_COMPRESSION_PROMPT,
    FAST_KEY_POINTS_EXTRACTION_PROMPT,
    FAST_RESEARCH_DATA_SUMMARY_PROMPT,
)
from .outline_generation import FAST_OUTLINE_GENERATION_PROMPT
from .planner import FAST_PLANNER_PROMPT
from .supervisor import FAST_SUPERVISOR_PROMPT
from .writer import FAST_WRITER_PROMPT

__all__ = [
    'FAST_OUTLINE_GENERATION_PROMPT', 'FAST_PLANNER_PROMPT',
    'FAST_WRITER_PROMPT', 'FAST_SUPERVISOR_PROMPT',
    'FAST_RESEARCH_DATA_SUMMARY_PROMPT', 'FAST_KEY_POINTS_EXTRACTION_PROMPT',
    'FAST_CONTENT_COMPRESSION_PROMPT'
]
