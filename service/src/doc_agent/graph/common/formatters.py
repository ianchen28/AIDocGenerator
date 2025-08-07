"""
格式化器模块

提供各种数据格式化功能，包括：
- 源信息的文本格式化
- 引用标记的处理
"""

import re
from typing import Optional

from doc_agent.core.logger import logger

from doc_agent.schemas import Source


def format_sources_to_text(sources: list[Source], start_idx: int = 1) -> str:
    """
    将 Source 对象列表格式化为文本格式，用于向后兼容
    
    Args:
        sources: Source 对象列表
        
    Returns:
        str: 格式化的文本
    """
    if not sources:
        return "没有收集到相关数据"

    formatted_text = "收集到的信息源:\n\n"

    for i, source in enumerate(sources, start_idx):
        formatted_text += f"=== 信息源 {i} ===\n"
        formatted_text += f"标题: {source.title}\n"
        if source.url:
            formatted_text += f"URL: {source.url}\n"
        formatted_text += f"类型: {source.source_type}\n"
        formatted_text += f"内容: {source.content}\n\n"

    return formatted_text


def process_citations(
    raw_text: str,
    available_sources: list[Source],
    global_cited_sources: Optional[dict[int, Source]] = None
) -> tuple[str, list[Source]]:
    """
    处理LLM输出中的引用标记，提取引用的源并格式化文本
    
    Args:
        raw_text: LLM的原始输出文本
        available_sources: 可用的信息源列表
        global_cited_sources: 全局已引用的源字典，用于连续编号
        
    Returns:
        tuple[str, list[Source]]: (处理后的文本, 引用的源列表)
    """
    processed_text = raw_text
    cited_sources = []

    if global_cited_sources is None:
        global_cited_sources = {}

    try:
        # 创建源ID到源对象的映射
        source_map = {source.id: source for source in available_sources}

        # 查找所有 <sources>[...]</sources> 标签
        sources_pattern = r'<sources>\[([^\]]*)\]</sources>'
        matches = re.findall(sources_pattern, processed_text)

        logger.debug(f"🔍 找到 {len(matches)} 个引用标记")

        for match in matches:
            if not match.strip():  # 空标签 <sources>[]</sources>
                # 替换为空字符串（综合分析，不需要引用）
                processed_text = processed_text.replace(
                    f'<sources>[{match}]</sources>', '', 1)
                logger.debug("  📝 处理空引用标记（综合分析）")
                continue

            # 解析源ID列表
            try:
                source_ids = [
                    int(id.strip()) for id in match.split(',')
                    if id.strip().isdigit()
                ]
                logger.debug(f"  📚 解析到源ID: {source_ids}")

                # 收集引用的源并分配全局编号
                citation_markers = []
                for source_id in source_ids:
                    if source_id in source_map:
                        source = source_map[source_id]
                        cited_sources.append(source)

                        # 分配全局编号
                        if source_id not in global_cited_sources:
                            global_cited_sources[source_id] = source

                        # 使用全局编号
                        global_number = list(
                            global_cited_sources.keys()).index(source_id) + 1
                        citation_markers.append(f"[{global_number}]")

                        logger.debug(
                            f"    ✅ 添加引用源: [{global_number}] {source.title}")
                    else:
                        logger.warning(f"    ⚠️  未找到源ID: {source_id}")

                # 替换为格式化的引用标记
                formatted_citation = "".join(citation_markers)
                processed_text = processed_text.replace(
                    f'<sources>[{match}]</sources>', formatted_citation, 1)

            except ValueError as e:
                logger.error(f"❌ 解析源ID失败: {e}")
                # 移除无效的标签
                processed_text = processed_text.replace(
                    f'<sources>[{match}]</sources>', '', 1)

        logger.info(f"✅ 引用处理完成，引用了 {len(cited_sources)} 个信息源")

    except Exception as e:
        logger.error(f"❌ 处理引用时发生错误: {e}")
        # 如果处理失败，返回原始文本和空列表
        return raw_text, []

    return processed_text, cited_sources


def format_chapter_summary(chapter_title: str,
                           content: str,
                           max_length: int = 200) -> str:
    """
    生成章节摘要文本
    
    Args:
        chapter_title: 章节标题
        content: 章节内容
        max_length: 摘要最大长度
        
    Returns:
        str: 格式化的摘要文本
    """
    # 提取内容的前几句话作为摘要
    sentences = re.split(r'[。！？.!?]', content)
    summary = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            if len(summary) + len(sentence) < max_length:
                summary += sentence + "。"
            else:
                break

    if not summary:
        summary = content[:max_length] + "..."

    return f"章节《{chapter_title}》摘要：{summary}"
