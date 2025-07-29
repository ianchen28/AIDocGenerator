# service/src/doc_agent/prompts/outline_generation.py
"""
大纲生成提示词模板
"""

V1_DEFAULT = """
你是一位专业的文档结构设计专家。基于提供的初始研究数据，为主题生成一个详细的文档大纲。

**主题**: {topic}

**初始研究数据**:
{initial_gathered_data}

**任务要求**:
1. 分析研究数据，识别主要主题和子主题
2. 创建一个逻辑清晰、层次分明的文档结构
3. 每个章节应该有明确的焦点和目标
4. 章节之间应该有良好的逻辑流程
5. 确保覆盖主题的所有重要方面

**输出格式要求**:
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
    "title": "文档标题",
    "summary": "文档的简短摘要（100-200字）",
    "chapters": [
        {{
            "chapter_number": 1,
            "chapter_title": "第一章标题",
            "description": "本章的详细描述，包括主要内容和目标",
            "key_points": ["要点1", "要点2", "要点3"],
            "estimated_sections": 3
        }},
        {{
            "chapter_number": 2,
            "chapter_title": "第二章标题",
            "description": "本章的详细描述",
            "key_points": ["要点1", "要点2"],
            "estimated_sections": 4
        }}
    ],
    "total_chapters": 5,
    "estimated_total_words": 15000
}}

**重要提示**:
- 建议生成4-8个章节
- 每个章节应该有独特的焦点，避免内容重复
- 章节标题应该清晰、具体
- 描述应该详细说明该章节将涵盖的内容
- 必须输出有效的JSON格式
"""

# 支持版本选择的PROMPTS字典
PROMPTS = {"v1_default": V1_DEFAULT}
