"""
写作节点模块

负责基于研究数据生成章节内容
"""

import re
from pprint import pformat as pprint
from typing import Any

from doc_agent.core.logging_config import get_logger
from doc_agent.graph.callbacks import publish_event

logger = get_logger(__name__)

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.config import settings
from doc_agent.graph.callbacks import TokenStreamCallbackHandler
from doc_agent.graph.common import (
    format_requirements_to_text as _format_requirements_to_text, )
from doc_agent.graph.common import format_sources_to_text as _format_sources_to_text
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
    支持引用工作流，自动处理引用标记和源追踪，支持 token 级别流式输出到 Redis
    
    Args:
        state: 研究状态，包含章节信息、研究数据和已完成章节
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
        prompt_version: prompt版本，默认为"v3_context_aware"
        
    Returns:
        dict: 包含当前章节内容和引用源的字典
    """
    logger.info("--- WRITER NODE ---")
    logger.info(f"writer state keys: {list(state.keys())}")
    job_id = state.get("job_id")
    if not job_id:
        logger.error("Writer node: job_id not found in state.")
        # 即使没有 job_id 也可以继续，但无法发布事件
        job_id = "unknown_job"

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
    chapter_word_count = current_chapter.get("chapter_word_count", 0)
    sub_sections = current_chapter.get("sub_sections", [])  # 获取子节信息

    publish_event(
        job_id, "章节写作", "document_generation", "RUNNING",
        {"description": f"开始写作章节{current_chapter_index + 1}：{chapter_title}"})

    if not chapter_title:
        raise ValueError("章节标题不能为空")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"🔧 使用复杂度级别: {complexity_config['level']}")
    logger.info(f"📊 当前章节子节数量: {len(sub_sections)}")

    # 从状态中获取研究数据
    gathered_sources = state.get("gathered_sources", [])
    user_requirement_sources = state.get("user_requirement_sources", [])
    user_style_guide_sources = state.get("user_style_guide_sources", [])
    logger.info(f"🔍 用户要求内容: {user_requirement_sources}")
    logger.info(f"🔍 样式指南内容: {user_style_guide_sources}")

    # 添加调试日志
    logger.info(f"📚 gathered_sources 数量: {len(gathered_sources)}")
    logger.info(
        f"🎨 user_style_guide_sources 数量: {len(user_style_guide_sources)}")
    logger.info(
        f"📋 user_requirement_sources 数量: {len(user_requirement_sources)}")

    # 构建上下文
    context_for_writing = _build_writing_context(completed_chapters)
    previous_chapters_context = _build_previous_chapters_context(
        completed_chapters_content)

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
                           gathered_sources, user_requirement_sources,
                           user_style_guide_sources, chapter_word_count,
                           context_for_writing,
                           style_guide_content, sub_sections,
                           state.get("current_citation_index", 1))

    logger.debug(f"Invoking LLM with writer prompt:\n{pprint(prompt)}")

    try:
        # 创建流式回调处理器
        streaming_handler = TokenStreamCallbackHandler(
            job_id=job_id,
            chapter_title=chapter_title,
            chapter_index=current_chapter_index)

        logger.info(f"开始为章节 '{chapter_title}' 流式调用 LLM...")

        # 使用同步流式调用 LLM
        response_list = []
        # 仅监听第一次流式输出
        enable_listen_logger = True
        for chunk in llm_client.stream(prompt,
                                       temperature=temperature,
                                       max_tokens=max_tokens,
                                       **extra_params):
            # 累加 token 内容
            response_list.append(chunk)
            # 使用 TokenStreamCallbackHandler 发送每个 token
            streaming_handler.on_llm_new_token(
                chunk, enable_listen_logger=enable_listen_logger)
            enable_listen_logger = False

        # 在一章生成结束时额外添加一个换行符
        streaming_handler.on_llm_new_token(
            "\n", enable_listen_logger=enable_listen_logger)
        logger.success(f"章节 '{chapter_title}' 内容流式生成完毕。")

        # 发送剩余缓冲
        try:
            streaming_handler.flush()
        except Exception:
            pass

        # 使用流式生成的完整响应
        response = "".join(response_list)

        logger.info(f"实际生成 {len(response)} 字，目标 {chapter_word_count} 字")
        # 获取章节编号信息
        current_chapter_index = state.get("current_chapter_index", 0)
        chapters_to_process = state.get("chapters_to_process", [])
        chapter_number = current_chapter_index + 1

        # 确保响应格式正确
        if not response.strip():
            response = f"## {chapter_number}. {chapter_title}\n\n无法生成章节内容。"
        elif not response.startswith("##"):
            # 如果没有二级标题，添加章节标题
            response = f"## {chapter_number}. {chapter_title}\n\n{response}"
        else:
            # 如果已经有二级标题，确保格式正确
            lines = response.split('\n')
            if lines and lines[0].startswith(
                    '## ') and not lines[0].startswith('### '):
                # 这是章节标题，确保包含编号
                if not lines[0].strip().startswith(f"## {chapter_number}."):
                    lines[0] = f"## {chapter_number}. {chapter_title}"
                    response = '\n'.join(lines)

        # 处理引用标记
        _update_cited_sources_inplace(response, gathered_sources)

        # 后处理
        final_document = _response_postprocess(response)

        # 根据引用标记，对相关文献进行标记，并更新状态
        cited_sources = [source for source in gathered_sources if source.cited]
        logger.info(f"✅ 章节生成完成，引用了 {len(cited_sources)} 个信息源")

        # 返回当前章节的内容和引用源
        return {
            "final_document": final_document,
            "cited_sources_in_chapter": cited_sources
        }

    except Exception as e:
        # 如果LLM调用失败，返回错误信息
        logger.error(f"Writer node error: {str(e)}")
        current_chapter_index = state.get("current_chapter_index", 0)
        chapter_number = current_chapter_index + 1

        error_content = f"""## {chapter_number}. {chapter_title}

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


def _get_prompt_template(prompt_selector, prompt_version, genre,
                         style_guide_content, complexity_config):
    """获取合适的提示词模板"""
    try:
        # 根据复杂度决定是否使用简化提示词
        if complexity_config['use_simplified_prompts']:
            # 使用快速提示词 - 现在从prompts模块获取
            from doc_agent.prompts.writer import V4_FAST
            return V4_FAST

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


def _build_prompt(prompt_template,
                  topic,
                  chapter_title,
                  chapter_description,
                  current_chapter_index,
                  chapters_to_process,
                  previous_chapters_context,
                  gathered_sources,
                  user_requirement_sources,
                  user_style_guide_sources,
                  chapter_word_count,
                  context_for_writing,
                  style_guide_content,
                  sub_sections,
                  source_begin_idx=1,
                  max_length=30000):
    """构建完整的提示词，智能控制长度"""

    # 初始化各部分内容
    available_sources_text = ""
    prompt_requirements = ""
    style_requirements = ""

    # 计算基础内容的长度（不包括可变部分）
    base_content = f"""
topic={topic}
chapter_title={chapter_title}
chapter_description={chapter_description}
chapter_number={current_chapter_index + 1}
total_chapters={len(chapters_to_process)}
previous_chapters_context={previous_chapters_context or "这是第一章，没有前置内容。"}
context_for_writing={context_for_writing}
"""

    # 格式化子节信息
    sub_sections_text = ""
    if sub_sections:
        sub_sections_text = "\n\n当前章节的子节结构：\n"
        for sub_section in sub_sections:
            section_number = sub_section.get("section_number", "?")
            section_title = sub_section.get("section_title", "未命名子节")
            section_description = sub_section.get("section_description", "")
            key_points = sub_section.get("key_points", [])

            sub_sections_text += f"\n{section_number} {section_title}\n"
            if section_description:
                sub_sections_text += f"描述: {section_description}\n"
            if key_points:
                sub_sections_text += f"要点: {', '.join(key_points)}\n"

    # 计算已用长度
    used_length = len(base_content) + len(sub_sections_text)
    remaining_length = max_length - used_length

    # 智能分配剩余长度
    # 优先级：可用信息源 > 用户要求 > 样式指南
    sources_ratio = 0.6  # 60% 给信息源
    requirements_ratio = 0.25  # 25% 给用户要求
    style_ratio = 0.15  # 15% 给样式指南

    sources_max_length = int(remaining_length * sources_ratio)
    requirements_max_length = int(remaining_length * requirements_ratio)
    style_max_length = int(remaining_length * style_ratio)

    # 1. 处理可用信息源
    if gathered_sources:
        available_sources_text = _format_sources_to_text(
            gathered_sources, source_begin_idx)

        # 如果信息源内容过长，进行智能截断
        if len(available_sources_text) > sources_max_length:
            available_sources_text = _truncate_sources_text(
                gathered_sources, sources_max_length)
            logger.info(f"📚 信息源内容已截断至 {len(available_sources_text)} 字符")

    # 2. 处理用户要求内容
    if user_requirement_sources:
        # 直接处理字符串列表，不依赖 _format_requirements_to_text
        prompt_requirements = _sample_format_source_list(
            user_requirement_sources, requirements_max_length)
        logger.info(f"📝 用户要求内容: {prompt_requirements}")

    # 3. 处理样式指南内容
    if user_style_guide_sources:
        # 直接处理字符串列表，不依赖 _format_requirements_to_text
        style_requirements = _sample_format_source_list(
            user_style_guide_sources, style_max_length)
        logger.info(f"📝 样式指南内容: {style_requirements}")

    # 4. 处理样式指南内容（如果有）
    formatted_style_guide = ""
    if style_guide_content and style_guide_content.strip():
        # 为样式指南预留一些空间
        style_guide_max_length = style_max_length - len(style_requirements)
        if len(style_guide_content) > style_guide_max_length:
            formatted_style_guide = _sample_format_source_list(
                [style_guide_content], style_guide_max_length)
        else:
            formatted_style_guide = f"\n{style_guide_content}\n"

        logger.info(f"📝 样式指南长度: {len(formatted_style_guide)} 字符")

    # 构建最终prompt
    final_prompt = prompt_template.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description,
        chapter_number=current_chapter_index + 1,
        total_chapters=len(chapters_to_process),
        previous_chapters_context=previous_chapters_context or "这是第一章，没有前置内容。",
        available_sources_text=available_sources_text,
        chapter_word_count=chapter_word_count,
        prompt_requirements=prompt_requirements,
        style_requirements=style_requirements,
        context_for_writing=context_for_writing,
        style_guide_content=formatted_style_guide,
        sub_sections_info=sub_sections_text)

    logger.info(f"📝 最终prompt长度: {len(final_prompt)} 字符 (限制: {max_length})")
    return final_prompt


def _update_cited_sources_inplace(raw_text: str,
                                  available_sources: list[Source]) -> None:
    """ 根据 raw_text 中的内容，识别多种引用标记格式，并更新 available_sources 中 id 为 n 的 cited 字段

    Args:
        raw_text: LLM的原始输出文本
        available_sources: 可用的信息源列表
    """
    # 创建源ID映射
    source_map = {source.id: source for source in available_sources}

    # 识别多种引用格式
    cited_source_ids = set()

    # 1. 识别 <[n]> 格式
    pattern1 = r'<\[(\d+)\]>'
    matches1 = re.findall(pattern1, raw_text)
    for source_id in matches1:
        cited_source_ids.add(int(source_id))

    # 2. 识别 **<信息源 n>** 格式
    pattern2 = r'\*\*<信息源\s*(\d+)>\*\*'
    matches2 = re.findall(pattern2, raw_text)
    for source_id in matches2:
        cited_source_ids.add(int(source_id))

    # 3. 识别 <[n], [m]> 格式
    pattern3 = r'<\[(\d+)\],\s*\[(\d+)\]>'
    matches3 = re.findall(pattern3, raw_text)
    for match in matches3:
        for source_id in match:
            cited_source_ids.add(int(source_id))

    # 4. 识别 [n] 格式（标准引用格式）
    pattern4 = r'\[(\d+)\]'
    matches4 = re.findall(pattern4, raw_text)
    for source_id in matches4:
        cited_source_ids.add(int(source_id))

    # 5. 识别 <信息源 n> 格式
    pattern5 = r'<信息源\s*(\d+)>'
    matches5 = re.findall(pattern5, raw_text)
    for source_id in matches5:
        cited_source_ids.add(int(source_id))

    # 更新引用状态
    for source_id in cited_source_ids:
        if source_id in source_map:
            source_map[source_id].cited = True
            logger.debug(f"✅ 标记源 [{source_id}] 为已引用")
        else:
            logger.warning(f"⚠️  未找到源ID: {source_id}")

    logger.info(f"📚 识别到 {len(cited_source_ids)} 个引用源")


def _response_postprocess(response: str) -> str:
    """ 对 LLM 的原始输出进行后处理，包括：
    1. 删除前后的 ``` 标记
    2. 标准化引用格式
    3. 其他后处理
    """
    # 删除前后的 ``` 标记
    response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)

    # 标准化引用格式
    response = _standardize_citation_formats(response)

    return response


def _standardize_citation_formats(text: str) -> str:
    """标准化引用格式，将各种引用格式统一转换为标准格式"""

    # 1. 将 **<信息源 n>** 转换为 [n]
    text = re.sub(r'\*\*<信息源\s*(\d+)>\*\*', r'[\1]', text)

    # 2. 将 <信息源 n> 转换为 [n]
    text = re.sub(r'<信息源\s*(\d+)>', r'[\1]', text)

    # 3. 将 <[n], [m]> 转换为 [n][m]
    text = re.sub(r'<\[(\d+)\],\s*\[(\d+)\]>', r'[\1][\2]', text)

    # 4. 将 <[n]> 转换为 [n]
    text = re.sub(r'<\[(\d+)\]>', r'[\1]', text)

    # 5. 处理连续的引用，如 [1][2][3] 保持原样
    # 这个正则表达式已经能正确处理

    logger.debug(f"📝 引用格式标准化完成")
    return text


def _truncate_sources_text(sources: list[Source], max_length: int) -> str:
    """智能截断信息源文本，优先保留重要信息源"""
    if not sources:
        return ""

    # 按重要性排序：已引用的 > 有URL的 > 有作者的 > 其他
    def source_priority(source):
        priority = 0
        if source.cited:
            priority += 1000
        if source.url:
            priority += 100
        if source.author:
            priority += 10
        return priority

    sorted_sources = sorted(sources, key=source_priority, reverse=True)

    truncated_text = "可用信息源列表:\n\n"
    current_length = len(truncated_text)

    for source in sorted_sources:
        source_text = f"[Source {source.id}] {source.title}\n"
        source_text += f"  类型: {source.source_type}\n"
        if source.url:
            source_text += f"  URL: {source.url}\n"
        if source.author:
            source_text += f"  作者: {source.author}\n"
        if source.date:
            source_text += f"  日期: {source.date}\n"
        if source.page_number is not None:
            source_text += f"  页码: {source.page_number}\n"
        if source.file_token:
            source_text += f"  文件Token: {source.file_token}\n"

        # 智能截断内容
        content_preview = source.content[:150] + "..." if len(
            source.content) > 150 else source.content
        source_text += f"  内容: {content_preview}\n\n"

        if current_length + len(source_text) > max_length:
            truncated_text += f"... (还有 {len(sorted_sources) - len(truncated_text.split('[Source')) + 1} 个信息源未显示)\n"
            break

        truncated_text += source_text
        current_length += len(source_text)

    return truncated_text


def _summarize_requirements(requirements_content: list,
                            max_length: int) -> str:
    """提炼用户要求的要点"""
    if not requirements_content:
        return ""

    # 简单的关键词提取和总结
    summary = "用户要求要点:\n"

    for i, requirement in enumerate(requirements_content, 1):
        if isinstance(requirement, str):
            # 提取前50个字符作为要点
            key_point = requirement[:50] + "..." if len(
                requirement) > 50 else requirement
            summary += f"{i}. {key_point}\n"
        elif isinstance(requirement, dict):
            # 如果是字典，提取关键字段
            title = requirement.get('title', '未命名要求')
            content = requirement.get('content', '')
            key_point = content[:30] + "..." if len(content) > 30 else content
            summary += f"{i}. {title}: {key_point}\n"

    # 如果还是太长，进一步截断
    if len(summary) > max_length:
        summary = summary[:max_length - 20] + "...\n"

    return summary


def _sample_format_source_list(requirements_content: list[Source],
                               max_length: int) -> str:
    """格式化要求列表为文本"""
    if not requirements_content:
        return ""

    whole_content = "".join(
        [source.content for source in requirements_content])
    if len(whole_content) <= max_length:
        return whole_content

    sample_rate = max_length / len(whole_content)
    sample_count = max(1, int(sample_rate * len(requirements_content)))

    # 随机抽取但保持顺序
    if sample_rate < 1:
        import random
        # 生成所有索引，然后随机选择 sample_count 个，保持顺序
        all_indices = list(range(len(requirements_content)))
        selected_indices = sorted(random.sample(all_indices, sample_count))
        sampled_sources = [requirements_content[i] for i in selected_indices]
        sampled_content = "... ".join(
            [source.content for source in sampled_sources])
    else:
        sampled_content = whole_content

    return sampled_content
