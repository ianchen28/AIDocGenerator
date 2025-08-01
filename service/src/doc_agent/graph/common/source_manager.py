"""
源管理模块

提供源（Source）对象的管理功能，包括：
- 文本相似度计算
- 源ID的获取或创建
- 源列表的合并与去重
"""

from loguru import logger

from doc_agent.schemas import Source


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（基于前100个字符）
    
    Args:
        text1: 第一段文本
        text2: 第二段文本
        
    Returns:
        float: 相似度百分比 (0-100)
    """
    if not text1 or not text2:
        return 0.0

    # 取前100个字符进行比较
    text1_preview = text1[:100].strip()
    text2_preview = text2[:100].strip()

    if not text1_preview or not text2_preview:
        return 0.0

    # 计算公共字符数（考虑字符位置）
    min_len = min(len(text1_preview), len(text2_preview))
    if min_len == 0:
        return 0.0

    # 计算字符级相似度
    common_chars = 0
    for i in range(min_len):
        if text1_preview[i] == text2_preview[i]:
            common_chars += 1

    # 计算相似度百分比
    similarity = (common_chars / min_len) * 100

    # 如果相似度很高，进一步检查关键词匹配
    if similarity > 80.0:
        # 检查关键词匹配
        keywords1 = set(text1_preview.split())
        keywords2 = set(text2_preview.split())

        if keywords1 and keywords2:
            common_keywords = keywords1.intersection(keywords2)
            keyword_similarity = len(common_keywords) / max(
                len(keywords1), len(keywords2)) * 100

            # 综合字符相似度和关键词相似度
            final_similarity = (similarity + keyword_similarity) / 2
            return final_similarity

    return similarity


def get_or_create_source_id(new_source: Source,
                            existing_sources: list[Source]) -> int:
    """
    获取或创建信源ID，避免重复引用
    
    Args:
        new_source: 新的信源对象
        existing_sources: 已知的信源列表
        
    Returns:
        int: 信源的ID（如果找到重复的返回现有ID，否则返回新ID）
    """
    if not existing_sources:
        # 如果没有现有信源，直接返回新信源的ID
        return new_source.id

    # 检查URL匹配
    if new_source.url:
        for existing_source in existing_sources:
            if existing_source.url and existing_source.url == new_source.url:
                logger.debug(
                    f"🔗 通过URL匹配找到重复信源: [{existing_source.id}] {existing_source.title}"
                )
                return existing_source.id

    # 检查内容相似度
    for existing_source in existing_sources:
        similarity = calculate_text_similarity(new_source.content,
                                               existing_source.content)
        if similarity > 95.0:  # 相似度阈值95%
            logger.debug(
                f"📄 通过内容相似度匹配找到重复信源: [{existing_source.id}] {existing_source.title} (相似度: {similarity:.1f}%)"
            )
            return existing_source.id

    # 如果没有找到重复，返回新信源的ID
    logger.debug(f"🆕 未找到重复信源，使用新ID: [{new_source.id}] {new_source.title}")
    return new_source.id


def merge_sources_with_deduplication(
        new_sources: list[Source],
        existing_sources: list[Source]) -> list[Source]:
    """
    合并信源列表，去除重复项
    
    Args:
        new_sources: 新的信源列表
        existing_sources: 现有的信源列表
        
    Returns:
        list[Source]: 去重后的信源列表
    """
    if not new_sources:
        return existing_sources

    if not existing_sources:
        return new_sources

    # 创建现有信源的映射，用于快速查找
    existing_source_map = {source.id: source for source in existing_sources}
    merged_sources = existing_sources.copy()

    for new_source in new_sources:
        # 检查是否已存在相同ID的信源
        if new_source.id in existing_source_map:
            logger.debug(f"🔄 跳过重复ID的信源: [{new_source.id}] {new_source.title}")
            continue

        # 检查URL和内容重复
        is_duplicate = False
        for existing_source in existing_sources:
            # URL匹配检查
            if new_source.url and existing_source.url and new_source.url == existing_source.url:
                logger.debug(
                    f"🔗 跳过URL重复的信源: [{new_source.id}] {new_source.title}")
                is_duplicate = True
                break

            # 内容相似度检查
            similarity = calculate_text_similarity(new_source.content,
                                                   existing_source.content)
            if similarity > 95.0:
                logger.debug(
                    f"📄 跳过内容重复的信源: [{new_source.id}] {new_source.title} (相似度: {similarity:.1f}%)"
                )
                is_duplicate = True
                break

        if not is_duplicate:
            merged_sources.append(new_source)
            logger.debug(f"✅ 添加新信源: [{new_source.id}] {new_source.title}")

    logger.info(
        f"🔄 信源合并完成: 原有 {len(existing_sources)} 个，新增 {len(new_sources)} 个，合并后 {len(merged_sources)} 个"
    )
    return merged_sources
