# service/src/doc_agent/retrievers/base.py
from abc import ABC, abstractmethod
from doc_agent.schemas import Source


class BaseRetriever(ABC):
    """
    所有数据检索器的抽象基类。
    它强制所有子类必须实现一个 retrieve 方法，
    并确保返回统一的、结构化的 List[Source] 对象。
    """

    @abstractmethod
    def retrieve(self, query: str, **kwargs) -> list[Source]:
        """
        根据查询字符串，从数据源检索信息。
        :param query: 搜索的查询语句。
        :param kwargs: 其他可能的参数，如 top_k 等。
        :return: 一个包含 Source 对象的列表。
        """
        pass
