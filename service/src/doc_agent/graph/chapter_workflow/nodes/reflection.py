"""
反思节点模块

负责分析现有数据并生成更精确的搜索查询
"""

from pprint import pformat as pprint
from typing import Any

from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.config import settings
from doc_agent.graph.common import (
    format_sources_to_text as _format_sources_to_text, )
from doc_agent.graph.common import (
    parse_reflection_response as _parse_reflection_response, )
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient


async def reflection_node(state: ResearchState,
                          llm_client: LLMClient,
                          prompt_selector: PromptSelector,
                          genre: str = "default") -> dict[str, Any]:
    """
    智能查询扩展节点
    分析现有的搜索查询和已收集的数据，生成更精确、更相关的搜索查询

    Args:
        state: 研究状态，包含 topic、search_queries 和 gathered_data
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"

    Returns:
        dict: 包含更新后的 search_queries 的字典
    """
    # 从状态中获取必要信息
    topic = state.get("topic", "")
    original_search_queries = state.get("search_queries", [])
    gathered_data = state.get("gathered_data", "")
    gathered_sources = state.get("gathered_sources", [])
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])

    # 获取当前章节信息
    current_chapter = None
    if current_chapter_index < len(chapters_to_process):
        current_chapter = chapters_to_process[current_chapter_index]

    chapter_title = current_chapter.get("chapter_title",
                                        "") if current_chapter else ""
    chapter_description = current_chapter.get("description",
                                              "") if current_chapter else ""

    # 优先使用 gathered_sources 的数据，如果没有则使用 gathered_data
    if gathered_sources and not gathered_data:
        gathered_data = _format_sources_to_text(gathered_sources)
        logger.info(
            f"📊 从 gathered_sources 转换为 gathered_data，长度: {len(gathered_data)} 字符"
        )

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"🔧 使用复杂度级别: {complexity_config['level']}")

    logger.info("🤔 开始智能查询扩展分析")
    logger.info(f"📋 章节: {chapter_title}")
    logger.info(f"🔍 原始查询数量: {len(original_search_queries)}")
    logger.info(f"📊 已收集数据长度: {len(gathered_data)} 字符")
    logger.info(f"📚 已收集源数量: {len(gathered_sources)}")

    # 验证输入数据
    if not topic:
        logger.warning("❌ 缺少主题信息，无法进行查询扩展")
        return {"search_queries": original_search_queries}

    if not original_search_queries:
        logger.warning("❌ 没有原始查询，无法进行扩展")
        return {"search_queries": []}

    # 检查是否有足够的数据进行分析
    has_sufficient_data = ((gathered_data and len(gathered_data.strip()) >= 50)
                           or (gathered_sources and len(gathered_sources) > 0))

    if not has_sufficient_data:
        logger.warning("❌ 收集的数据不足，无法进行有效分析")
        return {"search_queries": original_search_queries}

    # 获取查询扩展器配置
    query_expander_config = settings.get_agent_component_config(
        "query_expander")
    if not query_expander_config:
        temperature = 0.7
        max_tokens = 2000
        extra_params = {}
    else:
        temperature = query_expander_config.temperature
        max_tokens = query_expander_config.max_tokens
        extra_params = query_expander_config.extra_params

    # 根据复杂度调整参数
    timeout = complexity_config.get('llm_timeout', 180)

    # 获取提示词模板
    prompt_template = _get_prompt_template(prompt_selector, genre,
                                           complexity_config)

    # 准备数据摘要（避免prompt过长）
    gathered_data_summary = gathered_data
    if len(gathered_data) > 3000:
        gathered_data_summary = gathered_data[:
                                              1500] + "\n\n... (数据已截断) ...\n\n" + gathered_data[
                                                  -1500:]

    # 格式化原始查询
    original_queries_text = "\n".join(
        [f"{i+1}. {query}" for i, query in enumerate(original_search_queries)])

    # 构建 prompt
    prompt = prompt_template.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description,
        original_queries=original_queries_text,
        gathered_data_summary=gathered_data_summary)

    logger.debug(f"Invoking LLM with reflection prompt:\n{pprint(prompt)}")

    try:
        # 调用 LLM 生成新的查询
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        logger.debug(f"🔍 LLM原始响应: {repr(response)}")
        logger.debug(f"📝 响应长度: {len(response)} 字符")

        # 解析响应，提取新的查询
        new_queries = _parse_reflection_response(response)

        if new_queries:
            logger.info(f"✅ 成功生成 {len(new_queries)} 个新查询")
            for i, query in enumerate(new_queries, 1):
                logger.debug(f"  {i}. {query}")

            # 根据复杂度限制查询数量
            max_queries = complexity_config.get('chapter_search_queries', 3)
            if len(new_queries) > max_queries:
                new_queries = new_queries[:max_queries]
                logger.info(f"📊 限制查询数量到 {max_queries} 个")

            # 返回更新后的查询列表
            return {"search_queries": new_queries}
        else:
            logger.warning("⚠️ 无法解析新查询，保持原始查询")
            return {"search_queries": original_search_queries}

    except Exception as e:
        logger.error(f"Reflection node error: {str(e)}")
        logger.warning("⚠️ 查询扩展失败，保持原始查询")
        return {"search_queries": original_search_queries}


def _get_prompt_template(prompt_selector, genre, complexity_config):
    """获取合适的提示词模板"""
    try:
        # 根据复杂度决定是否使用简化提示词
        if complexity_config['use_simplified_prompts']:
            # 快速模式使用简化的提示词
            return _get_simplified_prompt_template()

        # 标准模式使用完整提示词
        prompt_template = prompt_selector.get_prompt("chapter_workflow",
                                                     "reflection", genre)
        logger.debug(f"✅ 成功获取 reflection prompt 模板，genre: {genre}")
        return prompt_template

    except Exception as e:
        logger.error(f"❌ 获取 reflection prompt 模板失败: {e}")
        # 使用 prompts/reflection.py 中的备用模板
        try:
            from doc_agent.prompts.reflection import PROMPTS
            prompt_template = PROMPTS.get("v1_fallback", PROMPTS["v1_default"])
            logger.debug("✅ 成功获取 reflection 备用模板")
            return prompt_template
        except Exception as e2:
            logger.error(f"❌ 获取 reflection 备用模板也失败: {e2}")
            # 最后的备用方案
            return _get_fallback_prompt_template()


def _get_simplified_prompt_template() -> str:
    """获取简化的提示词模板（快速模式）"""
    return """
你是研究专家。基于已收集的数据，生成2个更精确的搜索查询。

**主题:** {topic}
**章节:** {chapter_title}

**原始查询:**
{original_queries}

**已收集数据摘要:**
{gathered_data_summary}

**输出JSON格式:**
{{
  "new_queries": ["查询1", "查询2"],
  "reasoning": "简要说明"
}}
"""


def _get_fallback_prompt_template() -> str:
    """获取备用的提示词模板"""
    return """
你是一个专业的研究专家和查询优化师。请分析现有的搜索查询和已收集的数据，生成更精确、更相关的搜索查询。

**文档主题:** {topic}

**当前章节信息:**
- 章节标题: {chapter_title}
- 章节描述: {chapter_description}

**原始搜索查询:**
{original_queries}

**已收集的数据摘要:**
{gathered_data_summary}

**任务要求:**
1. 仔细分析已收集的数据，识别信息缺口、模糊之处或新的有趣方向
2. 考虑原始查询的覆盖范围和深度
3. 生成2-3个新的、高度相关的、更具体的或探索性的搜索查询
4. 新查询应该：
   - 填补信息缺口
   - 深入特定方面
   - 探索新的角度或视角
   - 使用更精确的关键词

**输出格式:**
请以JSON格式返回结果，包含以下字段：
- new_queries: 新的搜索查询列表（数组，2-3个查询）
- reasoning: 简要说明为什么需要这些新查询

请立即开始分析并生成新的查询。
"""
