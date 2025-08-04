# service/src/doc_agent/retrievers/web_retriever.py

from doc_agent.tools.web_search import WebSearchTool
from doc_agent.core.config import settings
from doc_agent.retriever.base import BaseRetriever
from doc_agent.schemas import Source


class WebRetriever(BaseRetriever):

    def __init__(self):
        self.tool = WebSearchTool()

    def retrieve(self, query: str, **kwargs) -> list[Source]:
        """
        执行网络搜索并返回结构化 Source 列表
        """
        top_k = kwargs.get("top_k", 10)
        search_results = self.tool.search(query, top_k=top_k)
        sources = []
        if search_results.get('results'):
            for result in search_results['results']:
                sources.append(
                    Source(title=result.get('title', 'No title'),
                           url=result.get('url', 'No url'),
                           content=result.get('content', 'No content'),
                           raw_content=str(result),
                           type='web',
                           summary=result.get('summary', 'No summary')))
        return sources
