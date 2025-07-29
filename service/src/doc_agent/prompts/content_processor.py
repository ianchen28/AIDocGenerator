# service/src/doc_agent/prompts/content_processor.py
"""
内容处理器提示词模板
"""

V1_DEFAULT_RESEARCH_DATA_SUMMARY = """
你是一位专业的研究数据分析师。请对以下研究数据进行总结和分析。

**研究数据:**
{research_data}

**任务要求:**
1. 分析数据的主要内容和关键信息
2. 识别重要的观点、事实和数据
3. 总结核心发现和结论
4. 保持客观、准确的表述

**输出格式:**
请提供一份结构化的总结，包括：
- 主要发现
- 关键数据点
- 重要观点
- 结论和建议

请确保总结简洁明了，突出重点信息。
"""

V1_DEFAULT_KEY_POINTS_EXTRACTION = """
你是一位专业的信息提取专家。请从以下研究数据中提取关键要点。

**研究数据:**
{research_data}

**任务要求:**
1. 识别最重要的观点和结论
2. 提取关键的数据和事实
3. 总结核心概念和理论
4. 列出主要发现和见解

**输出格式:**
请提供一份关键要点列表，每个要点应该：
- 简洁明了（1-2句话）
- 具体明确
- 具有实际价值
- 便于理解和记忆

请提取{key_points_count}个最重要的要点。
"""

V1_DEFAULT_CONTENT_COMPRESSION = """
你是一位专业的内容压缩专家。请对以下研究数据进行智能压缩，保留最重要的信息。

**原始研究数据:**
{research_data}

**压缩要求:**
1. 保留核心信息和关键观点
2. 删除冗余和重复内容
3. 简化复杂表述，保持清晰
4. 确保压缩后的内容仍然完整和有意义
5. 目标长度：{target_length}字符

**输出格式:**
请提供压缩后的内容，确保：
- 信息完整性和准确性
- 逻辑结构清晰
- 重点突出
- 易于理解

请直接输出压缩后的内容，不要添加额外的说明。
"""

# 支持版本选择的PROMPTS字典
DATA_SUMMARY_PROMPTS = {
    "v1_default": V1_DEFAULT_RESEARCH_DATA_SUMMARY,
}

KEY_POINTS_EXTRACTION_PROMPTS = {
    "v1_default": V1_DEFAULT_KEY_POINTS_EXTRACTION,
}

CONTENT_COMPRESSION_PROMPTS = {
    "v1_default": V1_DEFAULT_CONTENT_COMPRESSION,
}

# 统一的PROMPTS字典，用于PromptSelector
# 包含所有三个prompt的内容，以支持完整的content_processor功能
PROMPTS = {
    "v1_default":
    V1_DEFAULT_RESEARCH_DATA_SUMMARY + "\n\n" +
    V1_DEFAULT_KEY_POINTS_EXTRACTION + "\n\n" + V1_DEFAULT_CONTENT_COMPRESSION,
}
