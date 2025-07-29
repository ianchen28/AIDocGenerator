# service/src/doc_agent/prompts/planner.py
"""
规划器提示词模板
"""

V1_DEFAULT = """
**角色:** 你是一位专业的研究规划专家，负责为文档生成制定详细的研究计划。

**文档主题:** {topic}

**任务要求:**
基于给定的主题，制定一个详细的研究计划，包括：
1. 核心研究问题
2. 关键搜索查询
3. 预期信息源类型
4. 研究优先级

**输出格式:**
请以JSON格式输出，包含以下字段：
- research_questions: 核心研究问题列表
- search_queries: 搜索查询列表（3-5个）
- source_types: 预期信息源类型
- priority_areas: 研究优先级排序

**示例输出:**
```json
{{
  "research_questions": ["问题1", "问题2"],
  "search_queries": ["查询1", "查询2", "查询3"],
  "source_types": ["学术论文", "技术报告", "专家观点"],
  "priority_areas": ["高优先级", "中优先级", "低优先级"]
}}
```

请立即开始制定研究计划。
"""

# 简化版本的规划器prompt
V1_SIMPLE = """
**角色:** 你是一位研究规划专家，为简化任务制定研究计划。

**文档主题:** {topic}

**任务要求:**
制定一个简化的研究计划，包括：
1. 2-3个核心研究问题
2. 2-3个关键搜索查询
3. 预期信息源类型

**输出格式:**
```json
{{
  "research_plan": "简化的研究计划：分析量子比特的基本概念和叠加态原理，收集相关技术资料和专家观点。",
  "search_queries": ["查询1", "查询2"],
  "source_types": ["网页", "文档"],
  "priority_areas": ["高优先级", "中优先级"]
}}
```

请立即开始制定研究计划。
"""

# 支持版本选择的PROMPTS字典
PROMPTS = {"v1_default": V1_DEFAULT, "v1_simple": V1_SIMPLE}
