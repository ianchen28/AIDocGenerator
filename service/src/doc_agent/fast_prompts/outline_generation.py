# service/src/doc_agent/fast_prompts/outline_generation.py
"""
快速大纲生成提示词模板 - 简化版本
目标：生成2-3个章节，快速完成
"""

FAST_OUTLINE_GENERATION_PROMPT = """
你是一位专业的文档结构设计专家。基于提供的初始研究数据，为主题生成一个简化的文档大纲。

**主题**: {topic}

**初始研究数据**:
{initial_gathered_data}

**任务要求**:
1. 分析研究数据，识别2-3个主要主题
2. 创建一个简洁的文档结构
3. 每个章节应该有明确的焦点
4. 确保覆盖主题的核心要点

**输出格式要求**:
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
    "title": "文档标题",
    "summary": "文档的简短摘要（50-100字）",
    "chapters": [
        {{
            "chapter_number": 1,
            "chapter_title": "第一章标题",
            "description": "本章的简要描述",
            "key_points": ["要点1", "要点2"],
            "estimated_sections": 2
        }},
        {{
            "chapter_number": 2,
            "chapter_title": "第二章标题",
            "description": "本章的简要描述",
            "key_points": ["要点1", "要点2"],
            "estimated_sections": 2
        }}
    ],
    "total_chapters": 2,
    "estimated_total_words": 5000
}}

**重要提示**:
- 只生成2-3个章节
- 章节标题应该简洁明了
- 描述应该简短但清晰
- 必须输出有效的JSON格式
- 目标总字数控制在5000字左右
"""
