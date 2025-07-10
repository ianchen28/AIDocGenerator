# service/src/doc_agent/llm_clients/__init__.py

from .base import LLMClient
from .providers import OpenAIClient, InternalClient
from ....core.config import settings  # <--- 导入配置实例


def get_llm_client(provider: str = "openai") -> LLMClient:
    """工厂函数，根据配置创建并返回一个LLM客户端实例"""
    if provider == "openai":
        # 从 settings 对象中安全地获取配置
        return OpenAIClient(api_key=settings.openai.api_key,
                            model=settings.openai.model)
    elif provider == "internal":
        return InternalClient(api_url=settings.internal_llm.api_url,
                              api_key=settings.internal_llm.api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
