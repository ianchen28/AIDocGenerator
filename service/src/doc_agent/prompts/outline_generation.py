# service/src/doc_agent/prompts/outline_generation.py
"""
大纲生成提示词模板
"""

V1_DEFAULT = """
**角色:** 你是一位专业的文档结构专家，负责为文档生成详细的大纲结构。

**文档主题:** {topic}

**研究数据摘要:**
{initial_gathered_data}

**任务要求:**
基于研究数据和主题，生成一个详细的文档大纲，包括：
1. 文档标题
2. 章节结构（3-5个章节）
3. 每个章节的标题和描述
4. 章节之间的逻辑关系

**输出格式:**
请以JSON格式输出，包含以下字段：
- title: 文档标题
- chapters: 章节列表，每个章节包含：
  - chapter_title: 章节标题
  - description: 章节描述
  - key_points: 关键要点列表

**示例输出:**
```json
{{
  "title": "文档标题",
  "chapters": [
    {{
      "chapter_title": "第一章标题",
      "description": "章节描述",
      "key_points": ["要点1", "要点2"]
    }}
  ]
}}
```

请立即开始生成文档大纲。
"""

# 简化版本的大纲生成prompt
V1_SIMPLE = """
**角色:** 你是一位文档结构专家，为简化任务生成大纲。

**文档主题:** {topic}

**研究数据摘要:**
{initial_gathered_data}

**任务要求:**
生成一个简化的文档大纲，包括：
1. 文档标题
2. 2 个章节
3. 每个章节的标题和简短描述

**输出格式:**
```json
{{
  "title": "文档标题",
  "chapters": [
    {{
      "chapter_title": "章节标题",
      "description": "简短描述"
    }}
  ]
}}
```

请立即开始生成文档大纲。
"""

# 支持版本选择的PROMPTS字典
PROMPTS = {"v1_default": V1_DEFAULT, "v1_simple": V1_SIMPLE}
