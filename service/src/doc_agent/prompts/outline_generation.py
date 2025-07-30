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
2. 章节结构（**严格要求：必须恰好{target_chapter_count}个章节，不能多也不能少**）
3. 每个章节的标题和描述
4. 章节之间的逻辑关系

**重要说明:**
- **章节数量限制：必须严格按照{target_chapter_count}个章节生成，这是硬性要求**

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

# 支持需求文档的大纲生成prompt
V2_WITH_REQUIREMENTS = """
**角色:** 你是一位专业的文档结构专家，负责为文档生成详细的大纲结构。

**文档主题:** {topic}

**研究数据摘要:**
{initial_gathered_data}

{requirements_content}

**任务要求:**
基于研究数据和主题，生成一个详细的文档大纲，包括：
1. 文档标题
2. 章节结构（**严格要求：必须恰好{target_chapter_count}个章节，不能多也不能少**）
3. 每个章节的标题和描述
4. 章节之间的逻辑关系

**重要说明:**
- **章节数量限制：必须严格按照{target_chapter_count}个章节生成，这是硬性要求**
- 如果提供了用户需求文档，生成的大纲**必须**涵盖需求文档中提到的所有要点
- 大纲应该确保所有需求都得到适当的章节覆盖，但不能超过{target_chapter_count}个章节
- 如果需求内容很多，请将相关内容合并到{target_chapter_count}个章节中
- 如果未提供需求文档，则按正常流程生成大纲

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

# 支持版本选择的PROMPTS字典
PROMPTS = {
    "v1_default": V1_DEFAULT,
    "v1_simple": V1_SIMPLE,
    "v2_with_requirements": V2_WITH_REQUIREMENTS
}
