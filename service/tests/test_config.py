#!/usr/bin/env python3
"""
测试配置系统
基于统一测试基础架构
"""

from test_base import BaseTestCase, skip_if_no_llm, skip_if_no_es, skip_if_no_web_search
from core.config import settings
import unittest


class ConfigTest(BaseTestCase):
    """配置系统测试类"""

    def test_basic_config_loading(self):
        """测试基本配置加载"""
        print("=== 基本配置测试 ===")

        # 测试基本配置
        print(f"Redis URL: {settings.redis_url}")
        print(f"OpenAI API Key: {'已设置' if settings.openai.api_key else '未设置'}")

        # 测试模型配置
        print(f"\n支持的模型数量: {len(settings.supported_models)}")
        for model_key, model_config in list(
                settings.supported_models.items())[:3]:
            print(
                f"  - {model_key}: {model_config.name} ({model_config.type})")

        # 验证基本配置不为空
        self.assertIsNotNone(settings.redis_url, "Redis URL 应该已设置")
        print("✅ 基本配置加载成功")

    def test_elasticsearch_config(self):
        """测试 Elasticsearch 配置"""
        print("=== Elasticsearch 配置测试 ===")

        es_config = settings.elasticsearch_config
        print(f"Hosts: {es_config.hosts}")
        print(f"Username: {es_config.username}")
        print(f"Index Prefix: {es_config.index_prefix}")

        # 验证 ES 配置
        self.assertIsNotNone(es_config.hosts, "ES hosts 应该已设置")
        self.assertIsNotNone(es_config.username, "ES username 应该已设置")
        print("✅ Elasticsearch 配置验证成功")

    def test_tavily_config(self):
        """测试 Tavily 配置"""
        print("=== Tavily 配置测试 ===")

        tavily_config = settings.tavily_config
        print(f"API Key: {'已设置' if tavily_config.api_key else '未设置'}")
        print(f"Search Depth: {tavily_config.search_depth}")
        print(f"Max Results: {tavily_config.max_results}")

        # 验证 Tavily 配置
        self.assertIsNotNone(tavily_config.search_depth, "Search depth 应该已设置")
        self.assertIsNotNone(tavily_config.max_results, "Max results 应该已设置")
        print("✅ Tavily 配置验证成功")

    def test_agent_config(self):
        """测试 Agent 配置"""
        print("=== Agent 配置测试 ===")

        agent_config = settings.agent_config
        print(f"Task Planner: {agent_config.task_planner.name}")
        print(f"Composer: {agent_config.composer.name}")
        print(f"Validator: {agent_config.validator.name}")

        # 验证 Agent 配置
        self.assertIsNotNone(agent_config.task_planner, "Task planner 应该已设置")
        self.assertIsNotNone(agent_config.composer, "Composer 应该已设置")
        self.assertIsNotNone(agent_config.validator, "Validator 应该已设置")
        print("✅ Agent 配置验证成功")

    def test_model_config_retrieval(self):
        """测试模型配置获取"""
        print("=== 模型配置获取测试 ===")

        # 测试获取特定模型配置
        test_models = ["moonshot_k2_0711_preview", "qwen_2_5_235b_a22b"]

        for model_key in test_models:
            model_config = settings.get_model_config(model_key)
            if model_config:
                print(f"✅ {model_key} 配置获取成功:")
                print(f"  - Name: {model_config.name}")
                print(f"  - URL: {model_config.url}")
                print(f"  - Type: {model_config.type}")
            else:
                print(f"⚠️  {model_key} 配置未找到")

        # 验证至少有一个模型配置可用
        self.assertGreater(len(settings.supported_models), 0, "至少应该有一个支持的模型")
        print("✅ 模型配置获取测试完成")

    def test_agent_component_config(self):
        """测试 Agent 组件配置获取"""
        print("=== Agent 组件配置测试 ===")

        # 测试获取 Agent 组件配置
        components = ["composer", "validator", "task_planner"]

        for component in components:
            component_config = settings.get_agent_component_config(component)
            if component_config:
                print(f"✅ {component} 组件配置获取成功:")
                print(f"  - Temperature: {component_config.temperature}")
                print(f"  - Max Tokens: {component_config.max_tokens}")
                print(f"  - Timeout: {component_config.timeout}")
            else:
                print(f"⚠️  {component} 组件配置未找到")

        print("✅ Agent 组件配置测试完成")

    @skip_if_no_llm
    def test_llm_model_configs(self):
        """测试 LLM 模型配置（仅在 LLM 可用时运行）"""
        print("=== LLM 模型配置测试 ===")

        # 测试 Moonshot 模型配置
        moonshot_config = settings.get_model_config("moonshot_k2_0711_preview")
        if moonshot_config:
            print(f"✅ Moonshot 模型配置:")
            print(f"  - Name: {moonshot_config.name}")
            print(f"  - URL: {moonshot_config.url}")
            print(f"  - Model ID: {moonshot_config.model_id}")
            print(f"  - Description: {moonshot_config.description}")
        else:
            print("⚠️  Moonshot 模型配置未找到")

        # 测试内部模型配置
        qwen_config = settings.get_model_config("qwen_2_5_235b_a22b")
        if qwen_config:
            print(f"✅ Qwen 模型配置:")
            print(f"  - Name: {qwen_config.name}")
            print(f"  - URL: {qwen_config.url}")
            print(f"  - Model ID: {qwen_config.model_id}")
        else:
            print("⚠️  Qwen 模型配置未找到")

        print("✅ LLM 模型配置测试完成")

    @skip_if_no_es
    def test_es_detailed_config(self):
        """测试 ES 详细配置（仅在 ES 可用时运行）"""
        print("=== ES 详细配置测试 ===")

        es_config = settings.elasticsearch_config
        print(f"ES 详细配置:")
        print(f"  - Hosts: {es_config.hosts}")
        print(f"  - Username: {es_config.username}")
        print(f"  - Password: {'已设置' if es_config.password else '未设置'}")
        print(f"  - Index Prefix: {es_config.index_prefix}")
        print(f"  - Timeout: {es_config.timeout}")

        # 验证 ES 配置完整性
        self.assertIsNotNone(es_config.hosts, "ES hosts 应该已设置")
        self.assertIsNotNone(es_config.username, "ES username 应该已设置")
        self.assertIsNotNone(es_config.password, "ES password 应该已设置")
        print("✅ ES 详细配置验证成功")

    @skip_if_no_web_search
    def test_web_search_config(self):
        """测试 WebSearch 配置（仅在 WebSearch 可用时运行）"""
        print("=== WebSearch 配置测试 ===")

        tavily_config = settings.tavily_config
        print(f"Tavily 详细配置:")
        print(f"  - API Key: {'已设置' if tavily_config.api_key else '未设置'}")
        print(f"  - Search Depth: {tavily_config.search_depth}")
        print(f"  - Max Results: {tavily_config.max_results}")
        # print(f"  - Include Answer: {tavily_config.include_answer}")  # 字段不存在，注释掉
        # print(f"  - Include Raw Content: {tavily_config.include_raw_content}")  # 字段不存在，注释掉

        # 验证 Tavily 配置完整性
        self.assertIsNotNone(tavily_config.search_depth, "Search depth 应该已设置")
        self.assertIsNotNone(tavily_config.max_results, "Max results 应该已设置")
        print("✅ WebSearch 配置验证成功")

    def test_config_validation(self):
        """测试配置验证"""
        print("=== 配置验证测试 ===")

        # 验证必要的配置项
        required_configs = [
            ("Redis URL", settings.redis_url),
            ("Supported Models", settings.supported_models),
            ("ES Config", settings.elasticsearch_config),
            ("Tavily Config", settings.tavily_config),
            ("Agent Config", settings.agent_config),
        ]

        for name, config in required_configs:
            if config is not None:
                print(f"✅ {name}: 已配置")
            else:
                print(f"❌ {name}: 未配置")

        # 验证至少有一些基本配置
        self.assertIsNotNone(settings.supported_models, "支持的模型应该已配置")
        self.assertGreater(len(settings.supported_models), 0, "至少应该有一个支持的模型")
        print("✅ 配置验证完成")


if __name__ == "__main__":
    unittest.main()
