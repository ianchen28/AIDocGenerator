# service/src/doc_agent/retrievers/web_retriever.py

from doc_agent.tools.web_search import WebSearchTool
from doc_agent.core.config import settings
from doc_agent.retriever.base import BaseRetriever
from doc_agent.schemas import Source
from typing import Union
from loguru import logger


class WebRetriever(BaseRetriever):

    def __init__(self):
        self.tool = WebSearchTool()

    def retrieve(self, query: str, **kwargs) -> list[Source]:
        """
        同步执行网络搜索并返回结构化 Source 列表
        """
        logger.info(f"开始网络搜索，查询: {query[:50]}...")
        
        try:
            top_k = kwargs.get("top_k", 10)
            search_results = self.tool.search(query, top_k=top_k)
            sources = []
            
            if search_results.get('results'):
                for result in search_results['results']:
                    sources.append(
                        Source(
                            title=result.get('title', 'No title'),
                            url=result.get('url', 'No url'),
                            content=result.get('content', 'No content'),
                            raw_content=str(result),
                            type='web',
                            summary=result.get('summary', 'No summary')
                        )
                    )
            
            logger.info(f"网络搜索完成，返回 {len(sources)} 个Source对象")
            return sources
            
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            return []

    async def retrieve_async(self, query: str, **kwargs) -> list[Source]:
        """
        异步执行网络搜索并返回结构化 Source 列表（推荐使用）
        """
        logger.info(f"开始异步网络搜索，查询: {query[:50]}...")
        
        try:
            top_k = kwargs.get("top_k", 10)
            
            # 使用异步搜索方法（如果可用）
            if hasattr(self.tool, 'search_async'):
                search_results = await self.tool.search_async(query, top_k=top_k)
            else:
                # 回退到同步方法
                search_results = self.tool.search(query, top_k=top_k)
            
            sources = []
            if search_results.get('results'):
                for result in search_results['results']:
                    sources.append(
                        Source(
                            title=result.get('title', 'No title'),
                            url=result.get('url', 'No url'),
                            content=result.get('content', 'No content'),
                            raw_content=str(result),
                            type='web',
                            summary=result.get('summary', 'No summary')
                        )
                    )
            
            logger.info(f"异步网络搜索完成，返回 {len(sources)} 个Source对象")
            return sources
            
        except Exception as e:
            logger.error(f"异步网络搜索失败: {str(e)}")
            return []
