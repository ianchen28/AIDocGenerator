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

# 支持三级大纲结构的完整版本
V3_WITH_SUBSECTIONS = """
**角色:** 你是一位专业的文档结构设计专家。基于提供的初始研究数据，为主题生成一个详细的文档大纲。

**文档主题:** {topic}

**研究数据摘要:**
{initial_gathered_data}

**任务要求:**
1. 分析研究数据，识别主要主题
2. 创建一个完整的文档结构
3. 每个章节应该有明确的焦点
4. 确保覆盖主题的核心要点
5. **必须生成三级大纲结构**：章节 -> 子节 -> 要点

**输出格式要求:**
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
    "title": "文档标题",
    "summary": "文档的简短摘要（50-100字）",
    "chapters": [
        {{
            "number": 1,
            "title": "第一章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 1.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 1.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 1.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "number": 2,
            "title": "第二章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 2.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 2.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 2.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "number": 3,
            "title": "第三章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 3.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 3.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 3.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }}
    ],
    "total_chapters": 3,
    "estimated_total_words": 5000
}}

**重要提示:**
- **必须生成恰好3个章节**
- **每个章节必须包含3个子节**
- **每个子节必须包含3个要点**
- 要生成完整的三级大纲结构
- 章节标题应该简洁明了
- 描述应该简短但清晰
- 必须输出有效的JSON格式
- 目标总字数控制在5000字左右
"""

# 快速版本的大纲生成prompt（来自fast_prompts）
V4_FAST = """
你是一位专业的文档结构设计专家。基于提供的初始研究数据，为主题生成一个简化的文档大纲。

**主题**: {topic}

**初始研究数据**:
{initial_gathered_data}

**任务要求**:
1. 分析研究数据，识别2-3个主要主题
2. 创建一个简洁的文档结构
3. 每个章节应该有明确的焦点
4. 确保覆盖主题的核心要点
5. **必须生成三级大纲结构**：章节 -> 子节 -> 要点

**输出格式要求**:
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
    "title": "文档标题",
    "summary": "文档的简短摘要（50-100字）",
    "chapters": [
        {{
            "number": 1,
            "title": "第一章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 1.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 1.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 1.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "number": 2,
            "title": "第二章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 2.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 2.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 2.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "number": 3,
            "title": "第三章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 3.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 3.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 3.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }}
    ],
    "total_chapters": 3,
    "estimated_total_words": 5000
}}

**重要提示**:
- **必须生成恰好3个章节**
- **每个章节必须包含3个子节**
- **每个子节必须包含3个要点**
- 要生成完整的三级大纲结构
- 章节标题应该简洁明了
- 描述应该简短但清晰
- 必须输出有效的JSON格式
- 目标总字数控制在5000字左右
"""

# 支持版本选择的PROMPTS字典
PROMPTS = {
    "v1_default": V1_DEFAULT,
    "v1_simple": V1_SIMPLE,
    "v2_with_requirements": V2_WITH_REQUIREMENTS,
    "v3_with_subsections": V3_WITH_SUBSECTIONS,
    "v4_fast": V4_FAST
}
