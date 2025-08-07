# service/src/doc_agent/utils/content_processor.py
import json
from typing import Any

from doc_agent.core.logger import logger
from ..llm_clients.base import LLMClient


def summarize_content(content: str,
                      llm_client: LLMClient,
                      max_length: int = 2000) -> str:
    """
    缩写内容，提取关键信息
    Args:
        content: 原始内容
        llm_client: LLM客户端
        max_length: 目标长度
    Returns:
        str: 缩写后的内容
    """
    logger.info(f"开始缩写内容，目标长度: {max_length} 字符")
    logger.debug(f"原始内容长度: {len(content)} 字符")

    if len(content) <= max_length:
        logger.info("内容长度已在目标范围内，无需缩写")
        return content

    # 导入提示词模板
    from ..prompts import CONTENT_COMPRESSION_PROMPT

    prompt = CONTENT_COMPRESSION_PROMPT.format(
        research_data=content[:8000],  # 限制输入长度
        target_length=max_length)

    try:
        logger.debug("调用LLM客户端进行内容缩写")
        response = llm_client.invoke(prompt,
                                     temperature=0.3,
                                     max_tokens=min(max_length * 2, 4000))
        result = response.strip()
        logger.info(f"内容缩写完成，结果长度: {len(result)} 字符")
        return result
    except Exception as e:
        logger.error(f"内容缩写失败: {str(e)}")
        # 简单的截断作为后备方案
        fallback_result = content[:max_length] + "..."
        logger.warning(f"使用后备方案，截断内容到 {len(fallback_result)} 字符")
        return fallback_result


def extract_key_points(content: str,
                       llm_client: LLMClient,
                       num_points: int = 5) -> list[str]:
    """
    从内容中提取关键要点
    Args:
        content: 原始内容
        llm_client: LLM客户端
        num_points: 要点数量
    Returns:
        List[str]: 关键要点列表
    """
    logger.info(f"开始提取关键要点，目标数量: {num_points}")
    logger.debug(f"原始内容长度: {len(content)} 字符")

    # 导入提示词模板
    from ..prompts import KEY_POINTS_EXTRACTION_PROMPT

    prompt = KEY_POINTS_EXTRACTION_PROMPT.format(
        research_data=content[:6000],  # 限制输入长度
        key_points_count=num_points)

    try:
        logger.debug("调用LLM客户端提取关键要点")
        response = llm_client.invoke(prompt, temperature=0.3, max_tokens=1000)

        # 解析JSON响应
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        try:
            data = json.loads(cleaned_response.strip())
            key_points = data.get("key_points", [])
            logger.info(f"成功提取 {len(key_points)} 个关键要点")
            return key_points
        except Exception as json_err:
            logger.error(f"关键要点提取失败: JSON解析错误: {json_err}")
            logger.debug(f"LLM原始响应: {repr(response)}")
            # 简单的后备方案
            fallback_points = [f"要点{i+1}" for i in range(num_points)]
            logger.warning(f"使用后备方案，生成 {len(fallback_points)} 个默认要点")
            return fallback_points

    except Exception as e:
        logger.error(f"关键要点提取失败: {str(e)}")
        # 简单的后备方案
        fallback_points = [f"要点{i+1}" for i in range(num_points)]
        logger.warning(f"使用后备方案，生成 {len(fallback_points)} 个默认要点")
        return fallback_points


def expand_content(content: str,
                   llm_client: LLMClient,
                   target_length: int = 3000) -> str:
    """
    扩写内容，增加详细程度
    Args:
        content: 原始内容
        llm_client: LLM客户端
        target_length: 目标长度
    Returns:
        str: 扩写后的内容
    """
    logger.info(f"开始扩写内容，目标长度: {target_length} 字符")
    logger.debug(f"原始内容长度: {len(content)} 字符")

    if len(content) >= target_length:
        logger.info("内容长度已达到目标，无需扩写")
        return content

    prompt = f"""
请将以下内容扩写到 {target_length} 字符左右，增加详细程度和深度：

{content}

要求：
1. 保持原有核心观点不变
2. 增加具体的例子和说明
3. 添加相关的背景信息
4. 使用更丰富的表达方式
5. 确保扩写后的内容有价值

请直接返回扩写后的内容，不要添加任何额外说明。
"""

    try:
        logger.debug("调用LLM客户端进行内容扩写")
        response = llm_client.invoke(prompt,
                                     temperature=0.7,
                                     max_tokens=min(target_length * 2, 6000))
        result = response.strip()
        logger.info(f"内容扩写完成，结果长度: {len(result)} 字符")
        return result
    except Exception as e:
        logger.error(f"内容扩写失败: {str(e)}")
        logger.warning("扩写失败，返回原始内容")
        return content


def process_research_data(research_data: str,
                          llm_client: LLMClient,
                          summary_length: int = 3000,
                          key_points_count: int = 8) -> dict[str, Any]:
    """
    处理研究数据，生成摘要和关键要点
    Args:
        research_data: 原始研究数据
        llm_client: LLM客户端
        summary_length: 摘要长度
        key_points_count: 关键要点数量
    Returns:
        Dict[str, Any]: 包含摘要和关键要点的字典
    """
    logger.info(f"开始处理研究数据: {len(research_data)} 字符")
    logger.debug(f"处理参数 - 摘要长度: {summary_length}, 要点数量: {key_points_count}")

    # 生成摘要
    summary = summarize_content(research_data, llm_client, summary_length)

    # 提取关键要点
    key_points = extract_key_points(research_data, llm_client,
                                    key_points_count)

    result = {
        "summary": summary,
        "key_points": key_points,
        "original_length": len(research_data),
        "processed_length": len(summary)
    }

    logger.info(f"数据处理完成: 摘要 {len(summary)} 字符, {len(key_points)} 个要点")
    logger.debug(f"处理结果: {result}")

    return result
