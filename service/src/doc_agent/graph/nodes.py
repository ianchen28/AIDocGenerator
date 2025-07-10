# service/src/doc_agent/graph/nodes.py
from .state import ResearchState
from ..llm_clients.base import LLMClient
from ..tools.web_search import WebSearchTool


def planner_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """节点1: 规划研究步骤"""
    # ... 调用LLM生成plan和queries
    return {"research_plan": "...", "search_queries": ["q1", "q2"]}


def researcher_node(state: ResearchState, search_tool: WebSearchTool) -> dict:
    """节点2: 执行搜索"""
    # ... 使用search_tool执行搜索
    return {"gathered_data": "..."}


def writer_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """节点3: 撰写文档"""
    # ... 调用LLM生成最终文档
    return {"final_document": "..."}
