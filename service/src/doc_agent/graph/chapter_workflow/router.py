# service/src/doc_agent/graph/router.py
import pprint
from typing import Literal

from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient


def supervisor_router(
    state: ResearchState,
    llm_client: LLMClient,
    prompt_selector: PromptSelector,
    genre: str = "default"
) -> Literal["continue_to_writer", "rerun_researcher"]:
    """
    条件路由: 决策下一步走向
    评估收集的研究数据是否足够撰写高质量文档
    Args:
        state: 研究状态，包含 topic 和 gathered_data
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
    Returns:
        str: "continue_to_writer" 如果数据充足，"rerun_researcher" 如果需要更多研究
    """
    logger.info("🚀 ====== 进入 supervisor_router 路由节点 ======")

    # 1. 从状态中提取 topic 和研究数据
    topic = state.get("topic", "")
    gathered_sources = state.get("gathered_sources", [])
    gathered_data = state.get("gathered_data", "")  # 保持向后兼容

    # 🔧 新增：检查重试次数，避免无限循环
    retry_count = state.get("researcher_retry_count", 0)
    max_retries = 3  # 最大重试次数

    logger.info(f"📊 当前重试次数: {retry_count}/{max_retries}")

    if not topic:
        # 如果没有主题，默认需要重新研究
        logger.warning("❌ 没有主题，返回 rerun_researcher")
        return "rerun_researcher"

    # 🔧 新增：如果超过最大重试次数，强制继续到writer
    if retry_count >= max_retries:
        logger.warning(f"⚠️ 已达到最大重试次数 {max_retries}，强制继续到writer")
        return "continue_to_writer"

    # 检查是否有研究数据（优先检查 gathered_sources）
    if not gathered_sources and not gathered_data:
        # 如果没有收集到数据，需要重新研究
        logger.warning("❌ 没有收集到数据，返回 rerun_researcher")
        return "rerun_researcher"

    # 2. 预分析步骤：计算元数据
    if gathered_sources:
        # 使用新的 Source 对象格式
        num_sources = len(gathered_sources)
        total_length = sum(len(source.content) for source in gathered_sources)
        logger.info(f"📊 使用 gathered_sources 格式，来源数量: {num_sources}")
    else:
        # 使用旧的字符串格式（向后兼容）
        num_sources = gathered_data.count("===")
        total_length = len(gathered_data)
        logger.info(f"📊 使用 gathered_data 格式，来源数量: {num_sources}")

    logger.info(f"📋 Topic: {topic}")
    logger.info(f"📊 Gathered data 长度: {total_length} 字符")
    logger.info(f"🔍 来源数量: {num_sources}")

    # 🔧 新增：简化决策逻辑，避免LLM调用失败
    # 如果数据量足够，直接继续到writer
    if num_sources >= 2 or total_length >= 500:
        logger.info("✅ 数据量充足，直接继续到writer")
        return "continue_to_writer"

    # 如果数据量不足但还有重试机会，继续研究
    if retry_count < max_retries:
        logger.info("📝 数据量不足，继续研究")
        return "rerun_researcher"

    # 如果数据量不足且已达到最大重试次数，强制继续
    logger.warning("⚠️ 数据量不足但已达到最大重试次数，强制继续到writer")
    return "continue_to_writer"
