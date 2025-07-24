# service/src/doc_agent/fast_prompts/planner.py
"""
快速规划器提示词模板 - 简化版本
目标：减少搜索查询数量，快速完成研究
"""

FAST_PLANNER_PROMPT = """
你是一个专业的研究规划专家。请为以下章节制定简化的研究计划和搜索策略。

**文档主题:** {topic}
**当前章节:** {chapter_title}
**章节描述:** {chapter_description}

请严格按照以下 JSON 格式输出，不要包含任何其他内容：

{{
    "research_plan": "简要的研究计划，包括：1. 需要了解的核心概念 2. 需要收集的关键信息",
    "search_queries": ["搜索查询1", "搜索查询2"]
}}

要求：
1. research_plan 应该是一个简化的步骤计划
2. search_queries 应该包含2个具体的搜索查询，覆盖章节的主要方面
3. 必须严格按照 JSON 格式输出，确保 JSON 格式正确
4. 搜索查询应该使用通用关键词，确保能在知识库中找到相关内容
5. 搜索查询应该针对当前章节的核心内容
"""
