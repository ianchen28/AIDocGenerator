# service/src/doc_agent/graph/router.py
from typing import Literal
from .state import ResearchState
from ..llm_clients.base import LLMClient


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
    # 1. 从状态中提取 topic 和 gathered_data
    topic = state.get("topic", "")
    gathered_data = state.get("gathered_data", "")

    if not topic:
        # 如果没有主题，默认需要重新研究
        return "rerun_researcher"

    if not gathered_data:
        # 如果没有收集到数据，需要重新研究
        return "rerun_researcher"

    # 2. 构建高度特定和约束的提示（中文）
    prompt = f"""
**角色：** 你是一位研究主管，需要判断下方资料是否足够撰写完整文档。

**主题：**「{topic}」

**已收集的研究资料：**
{gathered_data}

**评判标准（宽松版）：**
- 如果资料包含3条或以上详细检索结果，每条都有具体内容，且总字数超过500字，则视为"充足"
- 如果只有1-2条检索，或内容过于简单（只有定义），则视为"不充足"

**重要提示：**
- 只要资料内容丰富、有多个方面、有具体信息，就应该返回FINISH
- 不要过于苛刻，资料不需要完美无缺
- 重点看是否有足够的内容来写文档

**你的决策：**
请根据上述标准判断，当前资料能否用于撰写文档？只能回答一个单词：
- "FINISH" = 资料充足，可以写文档
- "CONTINUE" = 资料不足，需要更多研究

请直接输出：FINISH 或 CONTINUE
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
        response = llm_client.invoke(prompt,
                                     temperature=0,
                                     max_tokens=max_tokens)

        # 4. 解析响应 - 使用 strip() 和 upper() 处理空白和大小写
        decision = response.strip().upper()

        # 添加调试信息
        print(f"🔍 LLM原始响应: '{response}'")
        print(f"🔍 处理后决策: '{decision}'")

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
        print(f"Supervisor router error: {str(e)}")
        return "rerun_researcher"
