# service/src/doc_agent/graph/state.py
from typing import List, TypedDict, Annotated
from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    """图的状态，代表了整个任务的记忆"""
    topic: str
    research_plan: str
    search_queries: List[str]
    gathered_data: str
    final_document: str

    # 使用Annotated和add_messages来让LangGraph自动管理消息历史
    # 这对于需要对话式修正的Agent特别有用
    messages: Annotated[list, add_messages]
