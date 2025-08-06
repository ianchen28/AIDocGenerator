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

    大纲范例：

    {
        "title": "水电站建造过程中的问题与解决方案",
        "summary": "本报告旨在探讨水电站建造过程中常见的问题及其解决措施，从施工技术、环境条件和项目管理等多个角度进行分析，以期为未来的水电站建设提供参考。",
        "chapters": [
            {
                "chapter_number": 1,
                "chapter_title": "施工技术问题",
                "description": "本章详细分析了水电站建造过程中的具体施工技术问题及其解决方案，包括基坑开挖、混凝土浇筑和模板缺陷等方面。",
                "sub_sections": [
                    {
                        "section_number": 1.1,
                        "section_title": "基坑土石方开挖问题",
                        "section_description": "讨论基坑开挖过程中常见的问题，如边坡坡比不符、超欠挖等，并提出相应的解决措施。",
                        "key_points": [
                            "基坑边坡坡比与设计图纸不符",
                            "存在大量超欠挖，导致二次开挖",
                            "解决方案：精确控制开挖参数，避免超欠挖"
                        ]
                    },
                    {
                        "section_number": 1.2,
                        "section_title": "地下水丰富情况下的混凝土浇筑问题",
                        "section_description": "分析在地下水丰富的条件下进行混凝土浇筑时可能出现的问题，如水泥浆被冲走、混凝土被水浸泡等，并提供解决方案。",
                        "key_points": [
                            "岩石裂隙水无法有效外排",
                            "混凝土浇筑过程中水泥浆被冲走",
                            "解决方案：采用有效的排水系统，确保混凝土质量"
                        ]
                    },
                    {
                        "section_number": 1.3,
                        "section_title": "混凝土模板缺陷问题",
                        "section_description": "探讨混凝土浇筑过程中模板可能出现的缺陷，如跑模、炸模、漏浆等，并提出预防措施。",
                        "key_points": [
                            "模板固定不牢导致跑模、炸模",
                            "模板密封不良导致漏浆",
                            "解决方案：加强模板设计和施工质量控制"
                        ]
                    }
                ]
            },
            {
                "chapter_number": 2,
                "chapter_title": "施工环境与条件问题",
                "description": "本章分析了水电站建造过程中面临的复杂施工环境和条件，包括地形、气候等因素，并提供相应的应对策略。",
                "sub_sections": [
                    {
                        "section_number": 2.1,
                        "section_title": "地形条件问题",
                        "section_description": "讨论水电站建设地点的地形条件对施工的影响，如工作场地狭小、地形陡峭等，并提出解决方案。",
                        "key_points": [
                            "工作场地狭小，施工空间有限",
                            "地形陡峭，施工难度大",
                            "解决方案：提前做好工程布局，合理利用空间资源"
                        ]
                    },
                    {
                        "section_number": 2.2,
                        "section_title": "气候条件问题",
                        "section_description": "分析恶劣气候条件对水电站施工的影响，如雨季施工、高温或低温施工等，并提供应对措施。",
                        "key_points": [
                            "雨季施工导致排水困难",
                            "高温或低温影响施工进度和质量",
                            "解决方案：根据气候条件合理安排施工进度"
                        ]
                    },
                    {
                        "section_number": 2.3,
                        "section_title": "资源与材料供应问题",
                        "section_description": "探讨水电站建设过程中资源与材料供应的挑战，尤其是在偏远地区，并提出解决办法。",
                        "key_points": [
                            "偏远地区材料供应不足",
                            "运输成本高，供应链不稳定",
                            "解决方案：提前储备材料，建立稳定的供应链"
                        ]
                    }
                ]
            }
        ],
        "total_chapters": 3,
        "estimated_total_words": 5000
    }
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
        # 获取子节信息
        sub_sections = chapter.get("sub_sections", [])

        # 根据复杂度调整预估章节数
        estimated_sections = len(sub_sections) if sub_sections else (
            2 if complexity_config['level'] == 'fast' else 3)

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
            "sub_sections":
            sub_sections,  # 添加子节信息
            "research_data":
            ""
        }
        chapters_to_process.append(chapter_task)

    logger.info(f"✅ 成功创建 {len(chapters_to_process)} 个章节任务")

    # 打印章节列表和子节信息
    for chapter in chapters_to_process:
        sub_sections = chapter.get("sub_sections", [])
        logger.info(
            f"  📄 第{chapter['chapter_number']}章: {chapter['chapter_title']} ({len(sub_sections)} 子节)"
        )

        for sub_section in sub_sections:
            sub_title = sub_section.get("section_title", "未命名子节")
            key_points = sub_section.get("key_points", [])
            logger.info(
                f"    📝 {sub_section.get('section_number', '?')}: {sub_title} ({len(key_points)} 要点)"
            )

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
    cited_sources = state.get("cited_sources", [])  # 🔧 修复：改为列表而不是字典

    logger.info(f"📚 开始生成参考文献，共 {len(cited_sources)} 个引用源")

    if not cited_sources:
        logger.warning("没有引用源，生成空的参考文献")
        bibliography = "\n## 参考文献\n\n暂无参考文献。\n"
    else:
        # 生成参考文献
        bibliography_lines = ["\n## 参考文献\n"]

        # 🔧 修复：使用 source.id 作为引用编号，保持与文档内容一致
        for source in cited_sources:
            citation = _format_citation(source.id, source)
            bibliography_lines.append(citation)

        bibliography = "\n".join(bibliography_lines)

        logger.info(f"✅ 参考文献生成完成，包含 {len(cited_sources)} 条引用")

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

    try:
        # 尝试解析JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            outline = json.loads(json_match.group(0))

            # 验证和修复大纲结构
            outline = _validate_and_fix_outline_structure(
                outline, complexity_config)

            # 根据复杂度限制章节数量
            max_chapters = complexity_config.get('max_chapters', -1)
            if max_chapters > 0 and 'chapters' in outline:
                outline['chapters'] = outline['chapters'][:max_chapters]

            return outline
    except Exception as e:
        logger.error(f"解析大纲响应失败: {e}")

    # 返回默认大纲
    return _generate_default_outline("未知主题", complexity_config)


def _validate_and_fix_outline_structure(outline: dict,
                                        complexity_config: dict) -> dict:
    """验证和修复大纲结构，确保三级结构完整"""

    if 'chapters' not in outline:
        logger.warning("大纲缺少chapters字段，使用默认大纲")
        return _generate_default_outline("未知主题", complexity_config)

    chapters = outline['chapters']
    fixed_chapters = []

    for i, chapter in enumerate(chapters):
        # 确保章节有基本字段
        if 'chapter_title' not in chapter:
            chapter['chapter_title'] = f"第{i+1}章"
        if 'description' not in chapter:
            chapter['description'] = f"第{i+1}章的内容描述"
        if 'chapter_number' not in chapter:
            chapter['chapter_number'] = i + 1

        # 检查是否有sub_sections，如果没有则添加默认的
        if 'sub_sections' not in chapter or not chapter['sub_sections']:
            logger.info(f"章节 {chapter['chapter_title']} 缺少子节，添加默认子节")
            chapter['sub_sections'] = [{
                "section_number": float(f"{i+1}.1"),
                "section_title": f"{chapter['chapter_title']}概述",
                "section_description": f"{chapter['chapter_title']}的基本概述",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "section_number": float(f"{i+1}.2"),
                "section_title": f"{chapter['chapter_title']}分析",
                "section_description": f"{chapter['chapter_title']}的深入分析",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "section_number": float(f"{i+1}.3"),
                "section_title": f"{chapter['chapter_title']}总结",
                "section_description": f"{chapter['chapter_title']}的总结和展望",
                "key_points": ["要点1", "要点2", "要点3"]
            }]
        else:
            # 验证子节结构
            for j, sub_section in enumerate(chapter['sub_sections']):
                if 'section_title' not in sub_section:
                    sub_section['section_title'] = f"第{i+1}.{j+1}节"
                if 'section_description' not in sub_section:
                    sub_section['section_description'] = f"第{i+1}.{j+1}节的描述"
                if 'section_number' not in sub_section:
                    sub_section['section_number'] = float(f"{i+1}.{j+1}")
                if 'key_points' not in sub_section or not sub_section[
                        'key_points']:
                    sub_section['key_points'] = ["要点1", "要点2", "要点3"]

        fixed_chapters.append(chapter)

    # 确保至少有3个章节
    while len(fixed_chapters) < 3:
        chapter_num = len(fixed_chapters) + 1
        fixed_chapters.append({
            "chapter_number":
            chapter_num,
            "chapter_title":
            f"第{chapter_num}章",
            "description":
            f"第{chapter_num}章的内容描述",
            "sub_sections": [{
                "section_number": float(f"{chapter_num}.1"),
                "section_title": f"第{chapter_num}章概述",
                "section_description": f"第{chapter_num}章的基本概述",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "section_number": float(f"{chapter_num}.2"),
                "section_title": f"第{chapter_num}章分析",
                "section_description": f"第{chapter_num}章的深入分析",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "section_number": float(f"{chapter_num}.3"),
                "section_title": f"第{chapter_num}章总结",
                "section_description": f"第{chapter_num}章的总结和展望",
                "key_points": ["要点1", "要点2", "要点3"]
            }]
        })

    outline['chapters'] = fixed_chapters
    logger.info(f"✅ 大纲结构验证完成，包含 {len(fixed_chapters)} 个章节，每个章节包含子节")

    return outline


def _generate_default_outline(topic: str, complexity_config) -> dict:
    """生成默认大纲"""
    max_chapters = complexity_config.get('max_chapters', 3)
    if max_chapters <= 0:
        max_chapters = 3

        # 根据主题生成更合
        # 通用大纲
        chapters = []
        for i in range(min(max_chapters, 3)):
            chapters.append({
                "chapter_number":
                i + 1,
                "chapter_title":
                f"{topic} - 第{i + 1}部分",
                "description":
                f"关于{topic}的第{i + 1}部分内容",
                "sub_sections": [{
                    "section_number":
                    float(f"{i+1}.1"),
                    "section_title":
                    f"第{i+1}部分概述",
                    "section_description":
                    f"第{i+1}部分的基本概述",
                    "key_points":
                    [f"{topic}概述要点1", f"{topic}概述要点2", f"{topic}概述要点3"]
                }, {
                    "section_number":
                    float(f"{i+1}.2"),
                    "section_title":
                    f"第{i+1}部分分析",
                    "section_description":
                    f"第{i+1}部分的深入分析",
                    "key_points":
                    [f"{topic}分析要点1", f"{topic}分析要点2", f"{topic}分析要点3"]
                }, {
                    "section_number":
                    float(f"{i+1}.3"),
                    "section_title":
                    f"第{i+1}部分总结",
                    "section_description":
                    f"第{i+1}部分的总结和展望",
                    "key_points":
                    [f"{topic}总结要点1", f"{topic}总结要点2", f"{topic}总结要点3"]
                }]
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
