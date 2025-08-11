#!/usr/bin/env python3
"""
简单测试 f-string 问题
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger


def test_f_string():
    """测试 f-string 问题"""
    logger.info("=== 开始测试 f-string ===")

    try:
        # 测试第一个 f-string
        task_prompt = "请写一篇关于人工智能的文章，要求1000字"

        prompt = f"""
你是一个专业的任务分析引擎。你的唯一目标是解析用户提供的文本，并从中提取关键的任务要求。

你必须严格遵循以下指令：
1.  分析文本，识别出任务的【主题】、【字数要求】和【其他要求】。
2.  你的输出必须是一个单一、有效的 JSON 对象，不能包含任何 JSON 格式之外的额外文本、解释或注释。
3.  严格按照下面的 schema 和字段规则生成 JSON：

```json
{
    "topic": "任务的核心主题或标题。",
    "word_count": "从文本中提取明确的字数要求，只保留数字部分作为字符串。如果没有提到任何字数要求，则该字段的值必须是 '-1'。",
    "other_requirements": "除了主题和字数外的所有其他具体要求，例如格式、风格、需要包含的要点、受众等。如果没有，则该字段为空字符串 ''。"
}
```

示例学习:

示例 1:
用户输入: "帮我写一篇关于人工智能对未来社会影响的文章，要求 800 字左右，需要包含正反两方面的观点。"
JSON 输出:

```JSON
{
    "topic": "人工智能对未来社会影响",
    "word_count": "800",
    "other_requirements": "需要包含正反两方面的观点"
}
```

示例 2:
用户输入: "写一份关于下季度市场营销活动的策划方案，要包括目标受众分析和预算分配。"
JSON 输出:

```JSON
{
    "topic": "下季度市场营销活动的策划方案",
    "word_count": "-1",
    "other_requirements": "要包括目标受众分析和预算分配"
}
```
示例 3:
用户输入: "给我讲讲全球变暖的原因"
JSON 输出:

```JSON
{
    "topic": "全球变暖的原因",
    "word_count": "-1",
    "other_requirements": ""
}
```
示例 4:
用户输入: "请为我们公司的季度总结报告写一个开场白，大约 200 字，风格要正式、鼓舞人心，并且要提到我们团队第二季度的主要成就：'项目A成功上线'和'客户满意度提升15%'"
JSON 输出:

```JSON
{
    "topic": "公司季度总结报告的开场白",
    "word_count": "200",
    "other_requirements": "风格要求正式、鼓舞人心；需要提到第二季度的主要成就：'项目A成功上线'和'客户满意度提升15%'"
}
```

任务开始

用户输入:
{task_prompt}
    """

        logger.info("✅ 第一个 f-string 测试成功")

        # 测试第二个 f-string
        topic = "测试主题"
        other_requirements = "测试要求"

        prompt2 = f"""
你是一个专业的研究策略师和信息检索专家。

你的任务是根据用户提供的【主题】和【具体要求】，生成一组用于在多个信息源（如 Google 搜索、Elasticsearch 数据库）进行检索的高质量、多样化的搜索查询(Search Queries)。

**核心指令:**

1.  **深入理解**: 分析【主题】和【具体要求】，理解用户的核心意图。
2.  **拆解与扩展**: 将复杂的任务拆解成多个更小、更具体的子问题。从不同角度进行思考，例如：
    * **核心定义**: 关于主题本身是什么。
    * **关键方面**: 任务要求中提到的每个要点。
    * **案例/数据**: 寻找相关的实例、统计数据或证据。
    * **方法/过程**: 如果是"如何做"的问题，寻找具体步骤和方法。
    * **对比/评价**: 寻找正反观点、优缺点对比。
3.  **生成查询**: 基于上述分析，生成一组简洁、有效的搜索查询。查询应该像真人专家会输入到搜索引擎中的那样。
4.  **格式化输出**: 你的输出必须是一个单一、有效的 JSON 对象，格式为 `{{"search_queries": ["查询1", "查询2", ...]}}`。除此之外，不要包含任何解释性文字。

---
**示例学习:**

**示例 1:**
输入:
{{
    "topic": "人工智能对未来社会影响",
    "other_requirements": "需要包含正反两方面的观点"
}}
JSON 输出:
```json
{{
    "search_queries": [
        "人工智能对社会的影响",
        "AI 技术的积极应用案例",
        "人工智能带来的好处和机遇",
        "人工智能的潜在风险与挑战",
        "AI 伦理问题与社会隐患",
        "未来AI技术发展趋势"
    ]
}}
```

任务开始

请根据下面的输入生成搜索查询：

输入:

JSON

{{
    "topic": "{topic}",
    "other_requirements": "{other_requirements or ''}"
}}
    """

        logger.info("✅ 第二个 f-string 测试成功")
        return True

    except Exception as e:
        logger.error(f"❌ f-string 测试失败: {e}")
        import traceback
        logger.error(f"完整错误信息: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_f_string()
    if success:
        logger.success("🎉 f-string 测试通过！")
    else:
        logger.error("❌ f-string 测试失败")
