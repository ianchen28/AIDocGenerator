# service/src/doc_agent/graph/router.py
from typing import Literal
from ..state import ResearchState
from ...llm_clients.base import LLMClient


def supervisor_router(
    state: ResearchState, llm_client: LLMClient
) -> Literal["continue_to_writer", "rerun_researcher"]:
    """
    条件路由: 决策下一步走向
    
    评估收集的研究数据是否足够撰写高质量文档
    
    Args:
        state: 研究状态，包含 topic 和 gathered_data
        llm_client: LLM客户端实例
        
    Returns:
        str: "continue_to_writer" 如果数据充足，"rerun_researcher" 如果需要更多研究
    """
    print("🚀 ====== 进入 supervisor_router 路由节点 ======")

    # 1. 从状态中提取 topic 和 gathered_data
    topic = state.get("topic", "")
    gathered_data = state.get("gathered_data", "")

    # 计算数据质量指标
    total_length = len(gathered_data)
    data_preview = gathered_data[:200] if gathered_data else ""

    # 简单的数据质量评估
    has_content = bool(gathered_data and gathered_data.strip())
    has_minimum_length = total_length > 100  # 至少100字符
    has_keywords = any(keyword in gathered_data.lower()
                       for keyword in ['人工智能', '电力', '技术', '应用', '政策', '发展'])

    print(f"📋 Topic: {topic}")
    print(f"📊 Gathered data 长度: {total_length} 字符")
    print(f"📝 Gathered data 预览: {data_preview}...")
    print(
        f"🔍 数据质量评估: 有内容={has_content}, 长度足够={has_minimum_length}, 包含关键词={has_keywords}"
    )

    if not topic:
        # 如果没有主题，默认需要重新研究
        print("❌ 没有主题，返回 rerun_researcher")
        return "rerun_researcher"

    if not gathered_data:
        # 如果没有收集到数据，需要重新研究
        print("❌ 没有收集到数据，返回 rerun_researcher")
        return "rerun_researcher"

    # 快速判断：如果数据明显不足，直接返回 CONTINUE
    if not has_content or not has_minimum_length or not has_keywords:
        print("⚠️  数据质量明显不足，直接返回 rerun_researcher")
        print(f"   - 有内容: {has_content}")
        print(f"   - 长度足够: {has_minimum_length}")
        print(f"   - 包含关键词: {has_keywords}")
        return "rerun_researcher"

    # 2. 构建智能评估提示词
    prompt = f"""
**任务：** 评估收集的研究数据是否足够撰写关于「{topic}」的高质量文档。

**数据质量指标：**
- 数据长度: {total_length} 字符
- 有实际内容: {'是' if has_content else '否'}
- 长度足够(>100字符): {'是' if has_minimum_length else '否'}
- 包含相关关键词: {'是' if has_keywords else '否'}

**数据预览：**
{gathered_data[:1000] if gathered_data else '无数据'}

**评估标准：**
1. 数据必须包含实际内容（不是空字符串或错误信息）
2. 数据长度应该超过100字符
3. 数据应该包含与主题相关的关键词
4. 数据内容应该与主题「{topic}」相关

**决策规则：**
- 如果数据质量良好（有内容、长度足够、包含关键词），返回 "FINISH"
- 如果数据质量不足（无内容、长度不够、不包含关键词），返回 "CONTINUE"

请根据上述标准严格判断，只能回答一个单词：FINISH 或 CONTINUE
"""

    try:
        # 3. 调用 LLM 客户端
        # 根据模型类型设置合适的max_tokens
        max_tokens = 10
        if hasattr(llm_client, 'reasoning') and llm_client.reasoning:
            # 如果支持推理模式，使用更大的token限制
            max_tokens = 1000
        if hasattr(llm_client,
                   'model_name') and 'gemini' in llm_client.model_name.lower():
            max_tokens = 5000

        # 限制 prompt 长度，避免超过模型输入限制
        max_prompt_length = 30000  # 30K 字符限制
        if len(prompt) > max_prompt_length:
            print(f"⚠️  Prompt 长度 {len(prompt)} 超过限制 {max_prompt_length}，进行截断")
            # 保留开头和结尾的重要信息，截断中间的研究资料
            header = prompt[:prompt.find("**已收集的研究资料：**") +
                            len("**已收集的研究资料：**")]
            footer = prompt[prompt.find("**评判标准（宽松版）：**"):]
            # 从 gathered_data 中取前 10000 字符
            gathered_data_preview = gathered_data[:10000] + "\n\n... (内容已截断，保留前10000字符)"
            prompt = header + "\n\n" + gathered_data_preview + "\n\n" + footer
            print(f"📝 截断后 prompt 长度: {len(prompt)} 字符")

        print(f"🤖 调用 LLM 进行决策判断...")
        print(f"📝 Prompt 长度: {len(prompt)} 字符")
        print(f"🔧 参数: max_tokens={max_tokens}, temperature=0")

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
                    print(f"⚠️  第 {attempt + 1} 次尝试失败 (400错误)，正在重试...")
                    import time
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    raise e  # 最后一次尝试失败或其他错误，抛出异常

        # 4. 解析响应 - 使用 strip() 和 upper() 处理空白和大小写
        decision = response.strip().upper()

        # 添加详细的调试信息
        print(f"🔍 LLM原始响应: '{response}'")
        print(f"🔍 响应长度: {len(response)} 字符")
        print(f"🔍 处理后决策: '{decision}'")
        print(f"🔍 是否包含FINISH: {'FINISH' in decision}")
        print(f"🔍 是否包含CONTINUE: {'CONTINUE' in decision}")

        # 5. 根据响应决定路由
        if "FINISH" in decision:
            print("✅ 决策: FINISH -> continue_to_writer")
            return "continue_to_writer"
        else:
            # 如果包含 "CONTINUE" 或其他任何内容，都需要重新研究
            print("✅ 决策: CONTINUE/其他 -> rerun_researcher")
            return "rerun_researcher"

    except Exception as e:
        # 如果 LLM 调用失败，默认继续研究以确保安全
        print(f"❌ Supervisor router error: {str(e)}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return "rerun_researcher"
