# service/core/config.py

import os
import yaml
from typing import Dict, List, Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ModelConfig(BaseSettings):
    """单个模型配置"""
    name: str
    type: str  # "enterprise" or "external"
    model_id: str
    url: str
    api_key: str
    description: str
    reasoning: bool = False


class ElasticsearchConfig(BaseSettings):
    """Elasticsearch配置"""
    hosts: List[str]
    port: int = 9200
    scheme: str = "https"
    username: str
    password: str
    verify_certs: bool = False
    index_prefix: str = "doc_gen"
    timeout: int = 30
    max_retries: int = 3
    retry_on_timeout: bool = True


class TavilyConfig(BaseSettings):
    """Tavily搜索配置"""
    api_key: str
    search_depth: str = "advanced"
    max_results: int = 6


class AgentComponentConfig(BaseSettings):
    """Agent组件配置"""
    name: str
    description: str
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 180
    retry_count: int = 5
    enable_logging: bool = True
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseSettings):
    """Agent整体配置"""
    task_planner: AgentComponentConfig
    retriever: AgentComponentConfig
    executor: AgentComponentConfig
    composer: AgentComponentConfig
    validator: AgentComponentConfig
    knowledge_retriever: AgentComponentConfig
    hybrid_retriever: AgentComponentConfig
    content_composer: AgentComponentConfig
    content_checker: AgentComponentConfig


# 保持原有接口的配置类
class OpenAISettings(BaseSettings):
    api_key: str = Field("", alias="OPENAI_API_KEY")
    model: str = Field("gpt-4o", alias="OPENAI_MODEL")


class InternalLLMSettings(BaseSettings):
    base_url: str = Field("", alias="INTERNAL_LLM_BASE_URL")
    api_key: str = Field("", alias="INTERNAL_LLM_API_KEY")


class RerankerSettings(BaseSettings):
    base_url: str = Field("", alias="RERANKER_BASE_URL")
    api_key: str = Field("", alias="RERANKER_API_KEY")


class EmbeddingSettings(BaseSettings):
    base_url: str = Field("", alias="EMBEDDING_BASE_URL")
    api_key: str = Field("", alias="EMBEDDING_API_KEY")


class TavilySettings(BaseSettings):
    api_key: str = Field("", alias="TAVILY_API_KEY")


class AgentSettings(BaseSettings):
    temperature: float = Field(0.7, alias="AGENT_TEMPERATURE")
    max_tokens: int = Field(4096, alias="AGENT_MAX_TOKENS")


class AppSettings(BaseSettings):
    """应用的主配置类"""
    model_config = SettingsConfigDict(env_file="../.env",
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    openai: OpenAISettings = OpenAISettings()
    internal_llm: InternalLLMSettings = InternalLLMSettings()
    tavily: TavilySettings = TavilySettings()
    agent: AgentSettings = AgentSettings()
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # YAML配置缓存
    _yaml_config: Optional[Dict[str, Any]] = None
    _supported_models: Optional[Dict[str, ModelConfig]] = None
    _elasticsearch_config: Optional[ElasticsearchConfig] = None
    _tavily_config: Optional[TavilyConfig] = None
    _agent_config: Optional[AgentConfig] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()

    def _load_yaml_config(self):
        """加载YAML配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self._yaml_config = yaml.safe_load(f)
        else:
            self._yaml_config = {}

    def _resolve_env_vars(self, value: str) -> str:
        """解析环境变量占位符"""
        if isinstance(value,
                      str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, value)
        return value

    def _process_model_config(self, model_key: str,
                              model_data: Dict[str, Any]) -> ModelConfig:
        """处理单个模型配置"""
        processed_data = {}
        for key, value in model_data.items():
            if isinstance(value, str):
                processed_data[key] = self._resolve_env_vars(value)
            else:
                processed_data[key] = value
        return ModelConfig(**processed_data)

    @property
    def supported_models(self) -> Dict[str, ModelConfig]:
        """获取支持的模型配置"""
        if self._supported_models is None:
            self._supported_models = {}
            if self._yaml_config and 'supported_models' in self._yaml_config:
                for model_key, model_data in self._yaml_config[
                        'supported_models'].items():
                    self._supported_models[
                        model_key] = self._process_model_config(
                            model_key, model_data)
        return self._supported_models

    @property
    def elasticsearch_config(self) -> ElasticsearchConfig:
        """获取Elasticsearch配置"""
        if self._elasticsearch_config is None:
            if self._yaml_config and 'elasticsearch' in self._yaml_config:
                self._elasticsearch_config = ElasticsearchConfig(
                    **self._yaml_config['elasticsearch'])
            else:
                self._elasticsearch_config = ElasticsearchConfig(
                    hosts=["localhost:9200"], username="", password="")
        return self._elasticsearch_config

    @property
    def tavily_config(self) -> TavilyConfig:
        """获取Tavily配置"""
        if self._tavily_config is None:
            if self._yaml_config and 'tavily' in self._yaml_config:
                tavily_data = self._yaml_config['tavily'].copy()
                tavily_data['api_key'] = self._resolve_env_vars(
                    tavily_data['api_key'])
                self._tavily_config = TavilyConfig(**tavily_data)
            else:
                self._tavily_config = TavilyConfig(api_key=self.tavily.api_key)
        return self._tavily_config

    @property
    def agent_config(self) -> AgentConfig:
        """获取Agent配置"""
        if self._agent_config is None:
            if self._yaml_config and 'agent_config' in self._yaml_config:
                agent_data = self._yaml_config['agent_config']
                processed_agent_data = {}
                for component_name, component_data in agent_data.items():
                    processed_agent_data[
                        component_name] = AgentComponentConfig(
                            **component_data)
                self._agent_config = AgentConfig(**processed_agent_data)
            else:
                # 默认配置
                default_component = AgentComponentConfig(
                    name="default",
                    description="Default component",
                    provider="qwen_2_5_235b_a22b",
                    model="qwen_2_5_235b_a22b")
                self._agent_config = AgentConfig(
                    task_planner=default_component,
                    retriever=default_component,
                    executor=default_component,
                    composer=default_component,
                    validator=default_component,
                    knowledge_retriever=default_component,
                    hybrid_retriever=default_component,
                    content_composer=default_component,
                    content_checker=default_component)
        return self._agent_config

    def get_model_config(self, model_key: str) -> Optional[ModelConfig]:
        """获取指定模型的配置"""
        return self.supported_models.get(model_key)

    def get_agent_component_config(
            self, component_name: str) -> Optional[AgentComponentConfig]:
        """获取指定Agent组件的配置"""
        return getattr(self.agent_config, component_name, None)


# 创建全局settings实例
settings = AppSettings()
