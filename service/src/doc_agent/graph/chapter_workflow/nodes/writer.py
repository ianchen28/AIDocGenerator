"""
写作节点模块

负责基于研究数据生成章节内容
"""

import re
from pprint import pformat as pprint
from typing import Any

from loguru import logger

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.config import settings
from doc_agent.graph.common import (
    format_sources_to_text as _format_sources_to_text, )
from doc_agent.graph.common import (
    get_or_create_source_id, )
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.schemas import Source


def writer_node(state: ResearchState,
                llm_client: LLMClient,
                prompt_selector: PromptSelector,
                genre: str = "default",
                prompt_version: str = "v3_context_aware") -> dict[str, Any]:
    """
    章节写作节点
    基于当前章节的研究数据和已完成章节的上下文，生成当前章节的内容
    支持引用工作流，自动处理引用标记和源追踪
    
    Args:
        state: 研究状态，包含章节信息、研究数据和已完成章节
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
        prompt_version: prompt版本，默认为"v3_context_aware"
        
    Returns:
        dict: 包含当前章节内容和引用源的字典
    """
    # 获取基本信息
    topic = state.get("topic", "")
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])
    completed_chapters_content = state.get("completed_chapters_content", [])
    completed_chapters = state.get("completed_chapters", [])

    # 验证当前章节索引
    if current_chapter_index >= len(chapters_to_process):
        raise ValueError(f"章节索引 {current_chapter_index} 超出范围")

    # 获取当前章节信息
    current_chapter = chapters_to_process[current_chapter_index]
    chapter_title = current_chapter.get("chapter_title", "")
    chapter_description = current_chapter.get("description", "")

    if not chapter_title:
        raise ValueError("章节标题不能为空")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"🔧 使用复杂度级别: {complexity_config['level']}")

    # 从状态中获取研究数据
    gathered_sources = state.get("gathered_sources", [])

    # 构建上下文
    context_for_writing = _build_writing_context(completed_chapters)
    previous_chapters_context = _build_previous_chapters_context(
        completed_chapters_content)

    available_sources_text = _format_sources_to_text(gathered_sources)

    # 获取文档生成器配置
    document_writer_config = settings.get_agent_component_config(
        "document_writer")
    if document_writer_config:
        temperature = document_writer_config.temperature
        max_tokens = document_writer_config.max_tokens
        extra_params = document_writer_config.extra_params
    else:
        temperature = 0.7
        max_tokens = 4000
        extra_params = {}

    # 根据复杂度调整参数
    timeout = complexity_config.get('llm_timeout', 180)

    # 获取样式指南内容
    style_guide_content = state.get("style_guide_content", "")

    # 获取合适的提示词模板
    prompt_template = _get_prompt_template(prompt_selector, prompt_version,
                                           genre, style_guide_content,
                                           complexity_config)

    # 构建提示词
    prompt = _build_prompt(prompt_template, topic, chapter_title,
                           chapter_description, current_chapter_index,
                           chapters_to_process, previous_chapters_context,
                           available_sources_text, context_for_writing,
                           style_guide_content)

    # 限制 prompt 长度
    prompt = _truncate_prompt_if_needed(prompt, previous_chapters_context,
                                        completed_chapters_content,
                                        available_sources_text, topic,
                                        chapter_title, chapter_description,
                                        current_chapter_index,
                                        chapters_to_process, prompt_selector)

    logger.debug(f"Invoking LLM with writer prompt:\n{pprint(prompt)}")

    try:
        # 调用LLM生成章节内容
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        # 确保响应格式正确
        if not response.strip():
            response = f"## {chapter_title}\n\n无法生成章节内容。"
        elif not response.startswith("##"):
            # 如果没有二级标题，添加章节标题
            response = f"## {chapter_title}\n\n{response}"

        # 处理引用标记
        processed_response, cited_sources = _process_citations_inline(
            response, gathered_sources, state)

        logger.info(f"✅ 章节生成完成，引用了 {len(cited_sources)} 个信息源")
        for source in cited_sources:
            logger.debug(f"  📚 引用源: [{source.id}] {source.title}")

        # 返回当前章节的内容和引用源
        return {
            "final_document": processed_response,
            "cited_sources_in_chapter": cited_sources
        }

    except Exception as e:
        # 如果LLM调用失败，返回错误信息
        logger.error(f"Writer node error: {str(e)}")
        error_content = f"""## {chapter_title}

### 章节生成错误

由于技术原因，无法生成本章节的内容。

**错误信息:** {str(e)}

**章节描述:** {chapter_description}

请检查系统配置或稍后重试。
"""
        return {
            "final_document": error_content,
            "cited_sources_in_chapter": []
        }


def _build_writing_context(completed_chapters: list) -> str:
    """构建滑动窗口 + 全局摘要上下文"""
    context_for_writing = ""

    if completed_chapters:
        # 获取最后一章的完整内容（滑动窗口）
        last_chapter = completed_chapters[-1]
        if isinstance(last_chapter, dict) and "content" in last_chapter:
            context_for_writing += f"**Context from the previous chapter (Full Text):**\n{last_chapter['content']}\n\n"
            logger.info(
                f"📖 添加前一章完整内容到上下文，长度: {len(last_chapter['content'])} 字符")

        # 如果有更多章节，获取早期章节的摘要（全局摘要）
        if len(completed_chapters) > 1:
            earlier_summaries = []
            for chapter in completed_chapters[:-1]:  # 除了最后一章的所有章节
                if isinstance(chapter, dict) and "summary" in chapter:
                    earlier_summaries.append(chapter["summary"])
                elif isinstance(chapter, dict) and "content" in chapter:
                    # 如果没有摘要，使用内容的前200字符作为摘要
                    content = chapter["content"]
                    summary = content[:200] + "..." if len(
                        content) > 200 else content
                    earlier_summaries.append(summary)

            if earlier_summaries:
                context_for_writing += "**Context from earlier chapters (Summaries):**\n" + "\n\n".join(
                    earlier_summaries)
                logger.info(f"📚 添加 {len(earlier_summaries)} 个早期章节摘要到上下文")

    if not context_for_writing:
        context_for_writing = "这是第一章，没有前置内容。"
        logger.info("📝 这是第一章，使用默认上下文")

    return context_for_writing


def _build_previous_chapters_context(completed_chapters_content: list) -> str:
    """构建已完成章节的上下文摘要"""
    if not completed_chapters_content:
        return ""

    return "\n\n".join([
        f"第{i+1}章摘要:\n{content[:500]}..."
        if len(content) > 500 else f"第{i+1}章:\n{content}"
        for i, content in enumerate(completed_chapters_content)
    ])


def _format_available_sources(gathered_sources: list[Source]) -> str:
    """格式化可用信息源列表"""
    if not gathered_sources:
        return ""

    available_sources_text = "可用信息源列表:\n\n"
    for source in gathered_sources:
        available_sources_text += f"[Source {source.id}] {source.title}\n"
        available_sources_text += f"  类型: {source.source_type}\n"
        if source.url:
            available_sources_text += f"  URL: {source.url}\n"
        available_sources_text += f"  内容: {source.content[:200]}...\n\n"

    return available_sources_text


def _get_prompt_template(prompt_selector, prompt_version, genre,
                         style_guide_content, complexity_config):
    """获取合适的提示词模板"""
    try:
        # 根据复杂度决定是否使用简化提示词
        if complexity_config['use_simplified_prompts']:
            # 使用快速提示词
            from doc_agent.fast_prompts import FAST_WRITER_PROMPT
            return FAST_WRITER_PROMPT

        # 根据指定的 prompt_version 获取模板
        from doc_agent.prompts.writer import PROMPTS

        # 如果有样式指南，优先使用 v4_with_style_guide 版本
        if style_guide_content and style_guide_content.strip():
            if "v4_with_style_guide" in PROMPTS:
                logger.info("✅ 使用 v4_with_style_guide 版本，检测到样式指南")
                return PROMPTS["v4_with_style_guide"]

        # 使用指定版本
        if prompt_version in PROMPTS:
            logger.debug(f"✅ 成功获取 writer {prompt_version} prompt 模板")
            return PROMPTS[prompt_version]

        # 回退版本
        if "v3_context_aware" in PROMPTS:
            logger.debug("✅ 回退到 writer v3_context_aware prompt 模板")
            return PROMPTS["v3_context_aware"]

        if "v2_with_citations" in PROMPTS:
            logger.debug("✅ 回退到 writer v2_with_citations prompt 模板")
            return PROMPTS["v2_with_citations"]

    except Exception as e:
        logger.warning(f"⚠️  获取 prompt 失败: {e}")

    # 最后的备用方案
    return _get_fallback_prompt_template()


def _get_fallback_prompt_template() -> str:
    """获取备用的提示词模板"""
    return """
你是一个专业的文档写作专家。请基于提供的研究数据，为指定章节撰写内容。

**文档主题:** {topic}
**章节标题:** {chapter_title}
**章节描述:** {chapter_description}
**章节编号:** {chapter_number}/{total_chapters}

**可用信息源:**
{available_sources}

**写作要求:**
1. 基于研究数据撰写内容，确保信息准确性和完整性
2. 保持章节结构清晰，逻辑连贯
3. 使用专业但易懂的语言
4. 在写作时，如果使用了某个信息源的内容，请使用特殊标记：<sources>[源ID]</sources>
5. 例如：<sources>[1]</sources> 这里使用了源1的信息
6. 如果是自己的综合总结，使用：<sources>[]</sources>

请立即开始撰写章节内容。
"""


def _build_prompt(prompt_template, topic, chapter_title, chapter_description,
                  current_chapter_index, chapters_to_process,
                  previous_chapters_context, available_sources_text,
                  context_for_writing, style_guide_content):
    """构建完整的提示词"""
    if style_guide_content and style_guide_content.strip():
        # 格式化样式指南内容
        formatted_style_guide = f"\n{style_guide_content}\n"
        logger.info(f"📝 包含样式指南的写作，样式指南长度: {len(style_guide_content)} 字符")

        return prompt_template.format(
            topic=topic,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            chapter_number=current_chapter_index + 1,
            total_chapters=len(chapters_to_process),
            previous_chapters_context=previous_chapters_context
            or "这是第一章，没有前置内容。",
            available_sources_text=available_sources_text,
            context_for_writing=context_for_writing,
            style_guide_content=formatted_style_guide)
    else:
        logger.info("📝 标准写作，未包含样式指南")
        return prompt_template.format(
            topic=topic,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            chapter_number=current_chapter_index + 1,
            total_chapters=len(chapters_to_process),
            previous_chapters_context=previous_chapters_context
            or "这是第一章，没有前置内容。",
            available_sources_text=available_sources_text,
            context_for_writing=context_for_writing)


def _truncate_prompt_if_needed(prompt, previous_chapters_context,
                               completed_chapters_content,
                               available_sources_text, topic, chapter_title,
                               chapter_description, current_chapter_index,
                               chapters_to_process, prompt_selector):
    """如果提示词过长，进行截断处理"""
    max_prompt_length = 30000

    if len(prompt) <= max_prompt_length:
        return prompt

    logger.warning(
        f"⚠️  Writer prompt 长度 {len(prompt)} 超过限制 {max_prompt_length}，进行截断")

    # 优先保留当前章节的研究数据，适当缩减已完成章节的上下文
    if len(previous_chapters_context) > 5000:
        # 只保留每章的简短摘要
        previous_chapters_context = "\n\n".join([
            f"第{i+1}章摘要:\n{content[:200]}..."
            for i, content in enumerate(completed_chapters_content)
        ])

    # 如果研究数据也太长，进行截断
    if len(available_sources_text) > 15000:
        available_sources_text = available_sources_text[:15000] + "\n\n... (研究数据已截断)"

    # 使用简化的模板重新构建prompt
    simple_prompt_template = _get_fallback_prompt_template()

    # 即使截断，也要保留基本的源信息
    available_sources_text = "可用信息源列表:\n\n"
    if len(available_sources_text) > 1000:  # 如果数据很长，只显示前几个源
        available_sources_text += "由于数据量较大，仅显示部分信息源。请基于研究数据撰写内容，并正确引用。\n\n"

    prompt = simple_prompt_template.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description,
        chapter_number=current_chapter_index + 1,
        total_chapters=len(chapters_to_process),
        available_sources_text=available_sources_text)

    logger.info(f"📝 截断后 writer prompt 长度: {len(prompt)} 字符")
    return prompt


def _process_citations_inline(
        raw_text: str, available_sources: list[Source],
        state: ResearchState) -> tuple[str, list[Source]]:
    """
    处理LLM输出中的引用标记，提取引用的源并格式化文本
    使用新的信源管理逻辑避免重复引用
    
    Args:
        raw_text: LLM的原始输出文本
        available_sources: 可用的信息源列表
        state: 研究状态
        
    Returns:
        tuple[str, list[Source]]: (处理后的文本, 引用的源列表)
    """
    processed_text = raw_text
    cited_sources = []

    # 获取全局已引用的信源列表（从状态中获取）
    global_cited_sources = state.get("cited_sources", {})
    all_existing_sources = list(
        global_cited_sources.values()) if global_cited_sources else []

    # 创建源ID到源对象的映射
    source_map = {source.id: source for source in available_sources}

    def _replace_sources_tag(match):
        """替换引用标记的辅助函数，使用新的信源管理逻辑"""
        try:
            # 提取源ID列表，例如从 [1, 3] 中提取 [1, 3]
            content = match.group(1).strip()

            if not content:  # 空标签 <sources>[]</sources>
                logger.debug("  📝 处理空引用标记（综合分析）")
                return ""  # 移除空标签

            # 解析源ID列表
            source_ids = []
            for id_str in content.split(','):
                id_str = id_str.strip()
                if id_str.isdigit():
                    source_ids.append(int(id_str))

            logger.debug(f"  📚 解析到源ID: {source_ids}")

            # 收集引用的源并生成引用标记
            citation_markers = []
            for source_id in source_ids:
                if source_id in source_map:
                    source = source_map[source_id]

                    # 使用新的信源管理逻辑获取正确的ID
                    correct_source_id = get_or_create_source_id(
                        source, all_existing_sources)

                    # 如果ID不同，说明找到了重复信源
                    if correct_source_id != source_id:
                        logger.info(
                            f"    🔄 发现重复信源: [{source_id}] -> [{correct_source_id}] {source.title}"
                        )

                    # 添加到引用列表（避免重复添加）
                    if source not in cited_sources:
                        cited_sources.append(source)

                    citation_markers.append(f"[{correct_source_id}]")
                    logger.debug(
                        f"    ✅ 添加引用源: [{correct_source_id}] {source.title}")
                else:
                    logger.warning(f"    ⚠️  未找到源ID: {source_id}")

            # 返回格式化的引用标记
            return "".join(citation_markers)

        except Exception as e:
            logger.error(f"❌ 处理引用标记失败: {e}")
            return ""  # 移除无效标签

    # 使用正则表达式替换所有引用标记
    sources_pattern = r'<sources>\[([^\]]*)\]</sources>'
    processed_text = re.sub(sources_pattern, _replace_sources_tag,
                            processed_text)

    # 额外处理：移除任何剩余的引用占位符
    processed_text = re.sub(r'\[引用需补充，暂为空\]', '', processed_text)
    processed_text = re.sub(r'<sources>\[\]</sources>', '', processed_text)

    logger.info(f"✅ 引用处理完成，引用了 {len(cited_sources)} 个信息源")

    return processed_text, cited_sources
