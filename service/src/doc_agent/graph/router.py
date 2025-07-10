# service/src/doc_agent/graph/router.py
from .state import ResearchState
from ..llm_clients.base import LLMClient


def supervisor_router(
    state: ResearchState, llm_client: LLMClient
) -> Literal["continue_to_writer", "rerun_researcher"]:
    """条件路由: 决策下一步走向"""
    # ... 调用一个LLM来判断资料是否充足
    # prompt = f"Given the topic '{state['topic']}' and gathered data '{state['gathered_data']}', is the research sufficient to write a comprehensive document? Answer 'yes' or 'no'."
    # decision = llm_client.invoke(prompt)
    decision = "yes"  # 伪代码
    if "yes" in decision.lower():
        return "continue_to_writer"
    else:
        return "rerun_researcher"
