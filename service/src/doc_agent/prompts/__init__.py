# service/src/doc_agent/prompts/__init__.py
"""
Prompts 模块

包含所有用于文档生成的提示词模板
"""

from .outline_generation import OUTLINE_GENERATION_PROMPT
from .planner import PLANNER_PROMPT
from .writer import WRITER_PROMPT
from .supervisor import SUPERVISOR_PROMPT
from .content_processor import (RESEARCH_DATA_SUMMARY_PROMPT,
                                KEY_POINTS_EXTRACTION_PROMPT,
                                CONTENT_COMPRESSION_PROMPT)
from .writer import WRITER_PROMPT_SIMPLE

__all__ = [
    'OUTLINE_GENERATION_PROMPT', 'PLANNER_PROMPT', 'WRITER_PROMPT',
    'WRITER_PROMPT_SIMPLE', 'SUPERVISOR_PROMPT',
    'RESEARCH_DATA_SUMMARY_PROMPT', 'KEY_POINTS_EXTRACTION_PROMPT',
    'CONTENT_COMPRESSION_PROMPT'
]
