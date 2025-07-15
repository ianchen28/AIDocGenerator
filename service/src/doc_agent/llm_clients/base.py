# service/src/doc_agent/llm_clients/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMClient(ABC):
    """
    LLM客户端的抽象基类
    定义了所有LLM客户端必须实现的方法
    """

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        同步调用模型
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            str: 模型响应的内容
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        pass


class BaseOutputParser(ABC):
    """
    输出解析器的抽象基类
    定义了所有输出解析器必须实现的方法
    """

    @abstractmethod
    def parse(self, response: str) -> str:
        """
        解析模型响应
        """
