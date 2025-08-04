# service/src/doc_agent/retrievers/base.py
from abc import ABC, abstractmethod
from typing import Union
from doc_agent.schemas import Source


class BaseRetriever(ABC):
    """
    所有数据检索器的抽象基类。
    它强制所有子类必须实现一个 retrieve 方法，
    并确保返回统一的、结构化的 List[Source] 对象。
    
    支持同步和异步两种实现方式：
    - 同步实现：直接返回 list[Source]
    - 异步实现：返回 awaitable，需要 await
    """

    @abstractmethod
    def retrieve(self, query: str, **kwargs) -> Union[list[Source], "BaseRetriever"]:
        """
        根据查询字符串，从数据源检索信息。
        
        Args:
            query: 搜索的查询语句。
            kwargs: 其他可能的参数，如 top_k 等。
            
        Returns:
            同步实现：直接返回 list[Source]
            异步实现：返回 self，需要 await self.retrieve_async()
        """
        pass

    async def retrieve_async(self, query: str, **kwargs) -> list[Source]:
        """
        异步检索方法（可选实现）
        
        Args:
            query: 搜索的查询语句。
            kwargs: 其他可能的参数，如 top_k 等。
            
        Returns:
            list[Source]: Source对象列表
        """
        # 默认实现：调用同步方法
        return self.retrieve(query, **kwargs)
