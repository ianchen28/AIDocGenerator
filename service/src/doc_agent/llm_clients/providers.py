# service/src/doc_agent/llm_clients/providers.py
from typing import Optional, Dict, Any
from openai import OpenAI
from .base import LLMClient


class OpenAIClient(LLMClient):

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称，默认为gpt-4o
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        调用OpenAI chat completions API
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            str: 模型响应的内容
        """
        try:
            # 构建消息
            messages = [{"role": "user", "content": prompt}]

            # 获取可选参数
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)

            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["temperature", "max_tokens"]
                })

            # 返回第一个选择的内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise ValueError(
                    "No response content received from OpenAI API")

        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")


class InternalClient(LLMClient):

    def __init__(self, api_url: str, api_key: str):
        # ... 初始化 internal client
        pass

    def invoke(self, prompt: str, **kwargs) -> str:
        # ... 实现调用逻辑
        return "Response from Internal"


class RerankerClient(LLMClient):

    def __init__(self, api_url: str, api_key: str):
        # ... 初始化 reranker client
        pass

    def invoke(self, prompt: str, **kwargs) -> str:
        # ... 实现调用逻辑
        return "Response from Reranker"


class EmbeddingClient(LLMClient):

    def __init__(self, api_url: str, api_key: str):
        # ... 初始化 embedding client
        pass

    def invoke(self, prompt: str, **kwargs) -> str:
        # ... 实现调用逻辑
        return "Response from Embedding"
