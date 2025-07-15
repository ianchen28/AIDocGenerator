# service/src/doc_agent/llm_clients/__init__.py

from .base import LLMClient
from .providers import (InternalLLMClient, GeminiClient, DeepSeekClient,
                        MoonshotClient, RerankerClient, EmbeddingClient)

# 动态导入配置，避免相对导入问题
import sys
from pathlib import Path

# 添加service目录到路径
service_dir = Path(__file__).parent.parent.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.config import settings


def get_llm_client(model_key: str = "qwen_2_5_235b_a22b") -> LLMClient:
    """
    工厂函数，根据配置创建并返回一个LLM客户端实例
    
    Args:
        model_key: 模型键名，从config.yaml的supported_models中获取，
            默认为qwen_2_5_235b_a22b
        
    Returns:
        LLMClient: 相应的客户端实例
    """
    model_config = settings.get_model_config(model_key)
    if not model_config:
        raise ValueError(f"Model {model_key} not found in configuration")

    # 根据模型类型创建相应的客户端
    if model_config.type == "enterprise_generate":
        # 企业内网模型
        return InternalLLMClient(base_url=model_config.url,
                                 api_key=model_config.api_key,
                                 model_name=model_config.model_id,
                                 reasoning=model_config.reasoning)
    elif model_config.type == "external_generate":
        # 外部模型
        if "gemini" in model_config.model_id.lower():
            return GeminiClient(base_url=model_config.url,
                                api_key=model_config.api_key,
                                model_name=model_config.model_id,
                                reasoning=model_config.reasoning)
        elif "deepseek" in model_config.model_id.lower():
            return DeepSeekClient(base_url=model_config.url,
                                  api_key=model_config.api_key,
                                  model_name=model_config.model_id,
                                  reasoning=model_config.reasoning)
        elif ("moonshot" in model_config.model_id.lower()
              or "kimi" in model_config.name.lower()):
            return MoonshotClient(base_url=model_config.url,
                                  api_key=model_config.api_key,
                                  model_name=model_config.model_id,
                                  reasoning=model_config.reasoning)
        else:
            raise ValueError(f"Unknown model type: {model_config.type}")
    else:
        raise ValueError(f"Unknown model type: {model_config.type}")


def get_reranker_client() -> RerankerClient:
    """获取Reranker客户端"""
    reranker_config = settings.get_model_config("reranker")
    if reranker_config:
        return RerankerClient(base_url=reranker_config.url,
                              api_key=reranker_config.api_key)
    else:
        raise ValueError("Reranker model not found in configuration")


def get_embedding_client() -> EmbeddingClient:
    """获取Embedding客户端"""
    embedding_config = settings.get_model_config("gte_qwen")
    if embedding_config:
        return EmbeddingClient(base_url=embedding_config.url,
                               api_key=embedding_config.api_key)
    else:
        raise ValueError("Embedding model not found in configuration")
