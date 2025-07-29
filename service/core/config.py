#!/usr/bin/env python3
"""
配置管理模块
"""

import os
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    hosts: list[str]
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
    extra_params: dict[str, Any] = Field(default_factory=dict)


class ESSearchConfig(BaseSettings):
    """ES检索配置"""
    vector_recall_size: int = 20
    hybrid_recall_size: int = 15
    rerank_size: int = 8
    min_score: float = 0.3


class DocumentLengthConfig(BaseSettings):
    """文档长度配置"""
    total_target_words: int = 8000
    chapter_target_words: int = 1600
    chapter_count: int = 5
    min_chapter_words: int = 800
    max_chapter_words: int = 2500


class FastTestModeConfig(BaseSettings):
    """快速测试模式配置"""
    enabled: bool = False
    total_target_words: int = 3000
    chapter_target_words: int = 600
    vector_recall_size: int = 10
    hybrid_recall_size: int = 8
    rerank_size: int = 5


class DocumentGenerationConfig(BaseSettings):
    """文档生成配置"""
    es_search: ESSearchConfig
    document_length: DocumentLengthConfig
    fast_test_mode: FastTestModeConfig


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


class LoggingSettings(BaseSettings):
    """日志配置"""
    model_config = SettingsConfigDict(extra='ignore')

    level: str = Field("INFO", alias="LOGGING_LEVEL")
    file_path: str = Field("logs/app.log", alias="LOGGING_FILE_PATH")
    rotation: str = Field("10 MB", alias="LOGGING_ROTATION")
    retention: str = Field("7 days", alias="LOGGING_RETENTION")


class SearchConfig(BaseSettings):
    """搜索配置"""
    max_queries: int = 5
    max_results_per_query: int = 5
    max_search_rounds: int = 5


class AppSettings(BaseSettings):
    """应用的主配置类"""
    model_config = SettingsConfigDict(env_file=".env",
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    openai: OpenAISettings = OpenAISettings()
    internal_llm: InternalLLMSettings = InternalLLMSettings()
    tavily: TavilySettings = TavilySettings()
    agent: AgentSettings = AgentSettings()
    logging: LoggingSettings = LoggingSettings()
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # YAML配置缓存
    _yaml_config: Optional[dict[str, Any]] = None
    _supported_models: Optional[dict[str, ModelConfig]] = None
    _elasticsearch_config: Optional[ElasticsearchConfig] = None
    _tavily_config: Optional[TavilyConfig] = None
    _agent_config: Optional[AgentConfig] = None
    _document_generation_config: Optional[DocumentGenerationConfig] = None
    _logging_config: Optional[LoggingSettings] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()
        self._search_config = None  # 初始化搜索配置缓存

    def _load_yaml_config(self):
        """加载YAML配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, encoding='utf-8') as f:
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
                              model_data: dict[str, Any]) -> ModelConfig:
        """处理单个模型配置"""
        processed_data = {}
        for key, value in model_data.items():
            if isinstance(value, str):
                processed_data[key] = self._resolve_env_vars(value)
            else:
                processed_data[key] = value
        return ModelConfig(**processed_data)

    @property
    def supported_models(self) -> dict[str, ModelConfig]:
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
    def search_config(self) -> SearchConfig:
        """获取搜索配置"""
        if self._search_config is None:
            if self._yaml_config and 'search_config' in self._yaml_config:
                self._search_config = SearchConfig(
                    **self._yaml_config['search_config'])
            else:
                self._search_config = SearchConfig()  # 使用默认配置
        return self._search_config

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
                    # 跳过非组件配置字段（如 default_llm）
                    if isinstance(component_data, dict):
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

    @property
    def document_generation_config(self) -> DocumentGenerationConfig:
        """获取文档生成配置"""
        if self._document_generation_config is None:
            if self._yaml_config and 'document_generation' in self._yaml_config:
                self._document_generation_config = DocumentGenerationConfig(
                    **self._yaml_config['document_generation'])
            else:
                # 使用默认配置
                self._document_generation_config = DocumentGenerationConfig(
                    es_search=ESSearchConfig(),
                    document_length=DocumentLengthConfig(),
                    fast_test_mode=FastTestModeConfig())
        return self._document_generation_config

    @property
    def logging_config(self) -> LoggingSettings:
        """获取日志配置"""
        if self._logging_config is None:
            if self._yaml_config and 'logging' in self._yaml_config:
                # 从YAML加载配置，但允许环境变量覆盖
                yaml_logging = self._yaml_config['logging']
                self._logging_config = LoggingSettings(
                    level=yaml_logging.get('level', 'INFO'),
                    file_path=yaml_logging.get('file_path', 'logs/app.log'),
                    rotation=yaml_logging.get('rotation', '10 MB'),
                    retention=yaml_logging.get('retention', '7 days'))
            else:
                # 使用默认配置
                self._logging_config = LoggingSettings()
        return self._logging_config

    def get_raw_logging_config(self) -> dict[str, Any]:
        """获取原始YAML日志配置（不经过环境变量覆盖）"""
        if self._yaml_config and 'logging' in self._yaml_config:
            return self._yaml_config['logging'].copy()
        return {}

    def get_document_config(self, fast_mode: bool = False) -> dict[str, Any]:
        """获取文档配置，支持快速模式"""
        config = self.document_generation_config

        if fast_mode and config.fast_test_mode.enabled:
            # 使用快速测试模式配置
            return {
                'total_target_words': config.fast_test_mode.total_target_words,
                'chapter_target_words':
                config.fast_test_mode.chapter_target_words,
                'vector_recall_size': config.fast_test_mode.vector_recall_size,
                'hybrid_recall_size': config.fast_test_mode.hybrid_recall_size,
                'rerank_size': config.fast_test_mode.rerank_size,
                'min_score': config.es_search.min_score
            }
        else:
            # 使用正常模式配置
            return {
                'total_target_words':
                config.document_length.total_target_words,
                'chapter_target_words':
                config.document_length.chapter_target_words,
                'vector_recall_size': config.es_search.vector_recall_size,
                'hybrid_recall_size': config.es_search.hybrid_recall_size,
                'rerank_size': config.es_search.rerank_size,
                'min_score': config.es_search.min_score
            }


# 创建全局settings实例
settings = AppSettings()
