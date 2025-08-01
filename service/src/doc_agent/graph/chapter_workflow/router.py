# service/src/doc_agent/graph/router.py
import pprint
from typing import Literal

from loguru import logger

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

    if not topic:
        # 如果没有主题，默认需要重新研究
        logger.warning("❌ 没有主题，返回 rerun_researcher")
        return "rerun_researcher"

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

    # 使用 PromptSelector 获取 prompt 模板
    try:
        prompt_template = prompt_selector.get_prompt("prompts", "supervisor",
                                                     genre)
        logger.debug(f"✅ 成功获取 supervisor prompt 模板，genre: {genre}")
    except Exception as e:
        logger.error(f"❌ 获取 supervisor prompt 模板失败: {e}")
        # 使用默认的 prompt 模板作为备用
        prompt_template = """**角色：** 你是一个高效的决策机器人。
**任务：** 根据下方的数据摘要，判断是否可以开始为「{topic}」撰写一个章节。

**决策标准：**
- 如果来源数量 >= 3 且总字符数 >= 200，返回 "FINISH"
- 如果来源数量 >= 2 且总字符数 >= 500，返回 "FINISH"
- 其他情况返回 "CONTINUE"

**数据摘要：**
- 来源数量: {num_sources}
- 总字符数: {total_length}

**你的决策：**
你的回答只能是一个单词："FINISH" 或 "CONTINUE"。
"""

    # 3. 构建简化的评估提示词
    prompt = prompt_template.format(topic=topic,
                                    num_sources=num_sources,
                                    total_length=total_length)

    logger.debug(
        f"Invoking LLM with supervisor prompt:\n{pprint.pformat(prompt)}")

    try:
        # 4. 调用 LLM 客户端
        # 使用小的 max_tokens，因为期望的输出很短
        max_tokens = 10

        logger.info("🤖 调用 LLM 进行决策判断...")
        logger.debug(f"📝 Prompt 长度: {len(prompt)} 字符")
        logger.debug(f"🔧 参数: max_tokens={max_tokens}, temperature=0")

        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = llm_client.invoke(prompt,
                                             temperature=0,
                                             max_tokens=max_tokens)
                break  # 成功则跳出重试循环
            except Exception as e:
                if "400" in str(e) and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️  第 {attempt + 1} 次尝试失败 (400错误)，正在重试...")
                    import time
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    raise e  # 最后一次尝试失败或其他错误，抛出异常

                # 4. 解析响应 - 简化处理逻辑
        # 直接检查响应中是否包含 "FINISH" 或 "CONTINUE"
        decision = response.strip().upper()
        clean_response = response  # 初始化 clean_response

        # 如果响应被截断或包含推理过程，尝试提取决策关键词
        if "FINISH" not in decision and "CONTINUE" not in decision:
            # 尝试从响应中提取任何可能的决策词
            import re
            # 移除可能的推理标签
            clean_response = re.sub(r'<think>.*',
                                    '',
                                    response,
                                    flags=re.IGNORECASE)
            clean_response = re.sub(r'<THINK>.*',
                                    '',
                                    clean_response,
                                    flags=re.IGNORECASE)
            decision = clean_response.strip().upper()

        # 添加详细的调试信息
        logger.debug(f"🔍 LLM原始响应: '{response}'")
        logger.debug(f"🔍 响应长度: {len(response)} 字符")
        logger.debug(f"🔍 清理后响应: '{clean_response}'")
        logger.debug(f"🔍 处理后决策: '{decision}'")
        logger.debug(f"🔍 是否包含FINISH: {'FINISH' in decision}")
        logger.debug(f"🔍 是否包含CONTINUE: {'CONTINUE' in decision}")

        # 5. 根据响应决定路由
        if "FINISH" in decision:
            logger.info("✅ 决策: FINISH -> continue_to_writer")
            return "continue_to_writer"
        else:
            # 如果包含 "CONTINUE" 或其他任何内容，都需要重新研究
            logger.info("✅ 决策: CONTINUE/其他 -> rerun_researcher")
            return "rerun_researcher"

    except Exception as e:
        # 如果 LLM 调用失败，默认继续研究以确保安全
        logger.error(f"❌ Supervisor router error: {str(e)}")
        logger.error(f"❌ 错误类型: {type(e).__name__}")
        return "rerun_researcher"
