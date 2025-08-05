"""
生成节点模块

负责大纲生成、章节拆分、参考文献生成等功能
"""

import json
from loguru import logger

from doc_agent.core.config import settings
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.schemas import Source
from doc_agent.graph.common import format_sources_to_text


def outline_generation_node(state: ResearchState,
                            llm_client: LLMClient,
                            prompt_selector: PromptSelector = None,
                            genre: str = "default") -> dict:
    """
    大纲生成节点 - 统一版本
    根据初始研究数据生成文档大纲
    支持基于配置的行为调整
    
    Args:
        state: 研究状态
        llm_client: LLM客户端
        prompt_selector: 提示词选择器
        genre: 文档类型
        
    Returns:
        dict: 包含 document_outline 的字典
    """
    topic = state.get("topic", "")
    initial_sources = state.get("initial_sources", [])

    if not topic:
        raise ValueError("主题不能为空")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"📋 开始生成大纲 (模式: {complexity_config['level']}): {topic}")

    # 格式化数据
    if initial_sources:
        initial_gathered_data = format_sources_to_text(initial_sources)
    else:
        initial_gathered_data = state.get("initial_gathered_data", "")

    if not initial_gathered_data:
        logger.warning("没有初始研究数据，使用默认大纲")
        return _generate_default_outline(topic, complexity_config)

    # 获取提示词模板
    prompt_template = _get_outline_prompt_template(complexity_config,
                                                   prompt_selector, genre)

    # 构建提示词
    prompt = prompt_template.format(
        topic=topic,
        initial_gathered_data=initial_gathered_data[:5000]  # 限制长度
    )

    try:
        # 根据复杂度调整参数
        temperature = 0.7
        max_tokens = 2000

        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens)

        # 解析响应
        outline = _parse_outline_response(response, complexity_config)

        logger.info(f"✅ 大纲生成完成，包含 {len(outline.get('chapters', []))} 个章节")

        return {"document_outline": outline}

    except Exception as e:
        logger.error(f"大纲生成失败: {str(e)}")
        return _generate_default_outline(topic, complexity_config)


def split_chapters_node(state: ResearchState) -> dict:
    """
    章节拆分节点 - 统一版本
    将文档大纲拆分为独立的章节任务列表
    根据配置限制章节数量
    """
    document_outline = state.get("document_outline", {})

    if not document_outline or "chapters" not in document_outline:
        raise ValueError("文档大纲不存在或格式无效")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    max_chapters = complexity_config.get('max_chapters', -1)

    logger.info(f"📂 开始拆分章节任务 (模式: {complexity_config['level']})")

    # 从大纲中提取章节信息
    chapters = document_outline.get("chapters", [])

    # 根据配置限制章节数量
    if max_chapters > 0:
        chapters = chapters[:max_chapters]
        logger.info(f"🔧 限制章节数量为 {len(chapters)} 个")

    # 创建章节任务列表
    chapters_to_process = []
    for chapter in chapters:
        # 根据复杂度调整预估章节数
        estimated_sections = 2 if complexity_config[
            'level'] == 'fast' else chapter.get("estimated_sections", 3)

        chapter_task = {
            "chapter_number":
            chapter.get("chapter_number",
                        len(chapters_to_process) + 1),
            "chapter_title":
            chapter.get("chapter_title", f"第{len(chapters_to_process) + 1}章"),
            "description":
            chapter.get("description", ""),
            "key_points":
            chapter.get("key_points", []),
            "estimated_sections":
            estimated_sections,
            "research_data":
            ""
        }
        chapters_to_process.append(chapter_task)

    logger.info(f"✅ 成功创建 {len(chapters_to_process)} 个章节任务")

    # 打印章节列表
    for chapter in chapters_to_process:
        logger.info(
            f"  📄 第{chapter['chapter_number']}章: {chapter['chapter_title']}")

    return {
        "chapters_to_process": chapters_to_process,
        "current_chapter_index": 0,
        "completed_chapters": []
    }


def bibliography_node(state: ResearchState) -> dict:
    """
    参考文献生成节点
    根据全局引用源生成参考文献列表
    """
    cited_sources = state.get("cited_sources", {})

    logger.info(f"📚 开始生成参考文献，共 {len(cited_sources)} 个引用源")

    if not cited_sources:
        logger.warning("没有引用源，生成空的参考文献")
        bibliography = "\n## 参考文献\n\n暂无参考文献。\n"
    else:
        # 生成参考文献
        bibliography_lines = ["\n## 参考文献\n"]

        # 按ID排序
        sorted_sources = sorted(cited_sources.items(), key=lambda x: x[0])

        for source_id, source in sorted_sources:
            citation = _format_citation(source_id, source)
            bibliography_lines.append(citation)

        bibliography = "\n".join(bibliography_lines)

        logger.info(f"✅ 参考文献生成完成，包含 {len(sorted_sources)} 条引用")

    # 获取现有的 final_document
    final_document = state.get("final_document", "")

    # 将参考文献添加到最终文档中
    updated_final_document = final_document + bibliography

    logger.info(f"📚 已将参考文献添加到最终文档中，总长度: {len(updated_final_document)} 字符")

    # 返回更新后的 final_document
    return {"final_document": updated_final_document}


def _get_outline_prompt_template(complexity_config, prompt_selector, genre):
    """获取大纲生成的提示词模板"""
    try:
        if complexity_config['use_simplified_prompts']:
            # 快速模式使用简化提示词
            from doc_agent.fast_prompts import FAST_OUTLINE_GENERATION_PROMPT
            return FAST_OUTLINE_GENERATION_PROMPT

        # 标准模式使用完整提示词
        if prompt_selector:
            return prompt_selector.get_prompt("main_orchestrator", "outline",
                                              genre)

    except Exception as e:
        logger.error(f"获取提示词模板失败: {e}")

    # 备用模板
    return """
基于以下研究数据，为主题"{topic}"生成详细的文档大纲。

研究数据：
{initial_gathered_data}

请生成JSON格式的大纲，包含：
- title: 文档标题
- summary: 文档摘要
- chapters: 章节列表，每个章节包含 chapter_number, chapter_title, description, key_points

输出JSON格式的大纲。
"""


def _parse_outline_response(response: str, complexity_config) -> dict:
    """解析大纲生成响应"""
    # 清除收尾的 ```json 和 ```
    response = response.replace('```json', '').replace('```', '').strip()
    #
    try:
        # 尝试解析JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            outline = json.loads(json_match.group(0))

            # 根据复杂度限制章节数量
            max_chapters = complexity_config.get('max_chapters', -1)
            if max_chapters > 0 and 'chapters' in outline:
                outline['chapters'] = outline['chapters'][:max_chapters]

            return outline
    except Exception as e:
        logger.error(f"解析大纲响应失败: {e}")

    # 返回默认大纲
    return _generate_default_outline("未知主题", complexity_config)


def _generate_default_outline(topic: str, complexity_config) -> dict:
    """生成默认大纲"""
    max_chapters = complexity_config.get('max_chapters', 3)
    if max_chapters <= 0:
        max_chapters = 3

    # 根据主题生成更合适的大纲
    if "水电站" in topic or "水电" in topic:
        chapters = [{
            "chapter_number": 1,
            "chapter_title": "水电站建造概述",
            "description": "介绍水电站建造的基本概念、重要性和技术特点",
            "key_points": ["水电站类型", "建造流程", "技术标准"]
        }, {
            "chapter_number": 2,
            "chapter_title": "建造过程中的主要问题",
            "description": "详细分析水电站建造过程中可能遇到的技术和管理问题",
            "key_points": ["地质问题", "技术难题", "管理挑战"]
        }, {
            "chapter_number": 3,
            "chapter_title": "解决方案与最佳实践",
            "description": "提供针对各类问题的解决方案和行业最佳实践",
            "key_points": ["技术方案", "管理措施", "预防策略"]
        }]
    else:
        # 通用大纲
        chapters = []
        for i in range(min(max_chapters, 3)):
            chapters.append({
                "chapter_number": i + 1,
                "chapter_title": f"{topic} - 第{i + 1}部分",
                "description": f"关于{topic}的第{i + 1}部分内容",
                "key_points": [f"{topic}相关要点"]
            })

    return {
        "title": f"{topic} 研究报告",
        "summary": f"本文档深入探讨了{topic}的相关内容，包括问题分析和解决方案。",
        "chapters": chapters[:max_chapters]  # 确保不超过最大章节数
    }


def _format_citation(source_id: int, source: Source) -> str:
    """格式化单个引用"""
    citation = f"[{source_id}] {source.title}"

    if source.url:
        citation += f" - {source.url}"

    citation += f" ({source.source_type})"

    return citation
