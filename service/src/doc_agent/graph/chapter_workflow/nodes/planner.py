"""
规划节点模块

负责为章节生成研究计划和搜索查询
"""

from pprint import pformat as pprint
from typing import Any

from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.config import settings
from doc_agent.graph.callbacks import publish_event
from doc_agent.graph.common import parse_planner_response
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient


def planner_node(state: ResearchState,
                 llm_client: LLMClient,
                 prompt_selector: PromptSelector,
                 genre: str = "default") -> dict[str, Any]:
    """
    节点1: 规划研究步骤
    从状态中获取 topic 和当前章节信息，创建 prompt 调用 LLM 生成研究计划和搜索查询
    
    Args:
        state: 研究状态，包含 topic 和当前章节信息
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
        
    Returns:
        dict: 包含 research_plan 和 search_queries 的字典
    """
    topic = state.get("topic", "")
    job_id = state.get("job_id", "")
    chapters_to_process = state.get("chapters_to_process", [])
    current_chapter_index = state.get("current_chapter_index", 0)

    if not topic:
        raise ValueError("Topic is required in state")

    # 获取当前章节信息
    current_chapter = None
    if current_chapter_index < len(chapters_to_process):
        current_chapter = chapters_to_process[current_chapter_index]

    chapter_title = current_chapter.get("chapter_title",
                                        "") if current_chapter else ""
    chapter_description = current_chapter.get("description",
                                              "") if current_chapter else ""
    chapter_word_count = current_chapter.get("chapter_word_count")

    # 获取子节信息
    sub_sections = current_chapter.get("sub_sections",
                                       []) if current_chapter else []

    logger.info(f"📋 规划章节研究: {chapter_title}")
    logger.info(f"📝 章节描述: {chapter_description}")
    logger.info(f"📊 子节数量: {len(sub_sections)}")

    # 格式化子节信息
    sub_sections_text = ""
    if sub_sections:
        sub_sections_text = "\n\n当前章节的子节结构：\n"
        for sub_section in sub_sections:
            section_number = sub_section.get("section_number", "?")
            section_title = sub_section.get("section_title", "未命名子节")
            section_description = sub_section.get("section_description", "")

            sub_sections_text += f"\n{section_number} {section_title}\n"
            if section_description:
                sub_sections_text += f"描述: {section_description}\n"

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"🔧 使用复杂度级别: {complexity_config['level']}")

    # 根据复杂度选择prompt
    if complexity_config['use_simplified_prompts']:
        # 使用快速提示词 - 现在从prompts模块获取
        from doc_agent.prompts.planner import V3_FAST
        prompt_template = V3_FAST
    else:
        # 使用标准提示词
        from doc_agent.prompts.planner import V1_DEFAULT
        prompt_template = V1_DEFAULT

    # 获取任务规划器配置
    task_planner_config = settings.get_agent_component_config("task_planner")
    if not task_planner_config:
        raise ValueError("Task planner configuration not found")

    # 创建研究计划生成的 prompt，要求 JSON 格式响应
    prompt = prompt_template.format(topic=topic,
                                    chapter_title=chapter_title,
                                    chapter_description=chapter_description,
                                    sub_sections_text=sub_sections_text)

    logger.debug(f"Invoking LLM with prompt:\n{pprint(prompt)}")

    try:
        # 调用 LLM 生成研究计划
        # 根据复杂度配置调整超时时间
        timeout = complexity_config.get('llm_timeout',
                                        task_planner_config.timeout)
        max_retries = complexity_config.get('max_retries', 5)

        response = llm_client.invoke(
            prompt,
            temperature=task_planner_config.temperature,
            max_tokens=task_planner_config.max_tokens,
            **task_planner_config.extra_params)

        logger.debug(f"🔍 LLM原始响应: {repr(response)}")
        logger.debug(f"📝 响应长度: {len(response)} 字符")
        logger.info(f"🔍 LLM响应内容:\n{response}")

        # 解析 JSON 响应
        research_plan, search_queries = parse_planner_response(response)

        publish_event(
            job_id, "章节规划", "document_generation", "SUCCESS", {
                "research_plan": research_plan,
                "search_queries": search_queries,
                "description": f"收集 {chapter_title} 相关信息"
            })

        # 应用基于复杂度的查询数量限制
        max_queries = complexity_config.get(
            'chapter_search_queries', complexity_config.get('max_queries', 5))
        logger.info(f"📊 planner_node 当前查询数量配置: {max_queries}")

        if len(search_queries) > max_queries:
            logger.info(f"📊 限制搜索查询数量: {len(search_queries)} -> {max_queries}")
            search_queries = search_queries[:max_queries]

        logger.info(f"✅ 生成研究计划: {len(search_queries)} 个搜索查询")
        for i, query in enumerate(search_queries, 1):
            logger.debug(f"  {i}. {query}")

        # 返回完整的状态更新
        result = {
            "research_plan": research_plan,
            "search_queries": search_queries
        }
        logger.debug(f"📤 Planner节点返回结果: {pprint(result)}")
        return result

    except Exception as e:
        # 如果 LLM 调用失败，返回默认计划
        logger.error(f"Planner node error: {str(e)}")

        # 根据复杂度生成默认查询
        if complexity_config['level'] == 'fast':
            default_queries = [
                f"{topic} {chapter_title} 概述", f"{topic} {chapter_title} 主要内容"
            ]
        else:
            default_queries = [
                f"{topic} {chapter_title} 概述", f"{topic} {chapter_title} 主要内容",
                f"{topic} {chapter_title} 关键要点",
                f"{topic} {chapter_title} 最新发展", f"{topic} {chapter_title} 重要性"
            ]

        logger.warning(f"⚠️  使用默认搜索查询: {len(default_queries)} 个")
        for i, query in enumerate(default_queries, 1):
            logger.debug(f"  {i}. {query}")

        result = {
            "research_plan": f"研究计划：对章节 {chapter_title} 进行深入研究，收集相关信息并整理成文档。",
            "search_queries": default_queries
        }
        logger.debug(f"📤 Planner节点返回默认结果: {pprint(result)}")
        return result


def _get_fallback_prompt_template() -> str:
    """获取备用的提示词模板"""
    return """
你是一个专业的研究规划专家。请为以下章节制定详细的研究计划和搜索策略。

**文档主题:** {topic}

**当前章节信息:**
- 章节标题: {chapter_title}
- 章节描述: {chapter_description}

**任务要求:**
1. 分析章节主题，确定研究重点和方向
2. 制定详细的研究计划，包括研究步骤和方法
3. 生成5-8个高质量的搜索查询，用于收集相关信息
4. 确保搜索查询具有针对性和全面性

**输出格式:**
请以JSON格式返回结果，包含以下字段：
- research_plan: 详细的研究计划
- search_queries: 搜索查询列表（数组）

请立即开始制定研究计划。
"""
