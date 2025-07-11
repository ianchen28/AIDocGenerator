#!/usr/bin/env python3
"""
测试配置系统
"""

from test_base import TestBase, setup_paths

# 设置测试环境
setup_paths()

from core.config import settings


def test_config():
    """测试配置加载"""
    print("=== 配置系统测试 ===")

    # 测试基本配置
    print(f"Redis URL: {settings.redis_url}")
    print(f"OpenAI API Key: {settings.openai.api_key[:10]}..." if settings.
          openai.api_key else "Not set")

    # 测试模型配置
    print(f"\n支持的模型数量: {len(settings.supported_models)}")
    for model_key, model_config in list(
            settings.supported_models.items())[:3]:  # 只显示前3个
        print(f"  - {model_key}: {model_config.name} ({model_config.type})")

    # 测试Elasticsearch配置
    es_config = settings.elasticsearch_config
    print(f"\nElasticsearch配置:")
    print(f"  - Hosts: {es_config.hosts}")
    print(f"  - Username: {es_config.username}")
    print(f"  - Index Prefix: {es_config.index_prefix}")

    # 测试Tavily配置
    tavily_config = settings.tavily_config
    print(f"\nTavily配置:")
    print(f"  - API Key: {tavily_config.api_key[:10]}..." if tavily_config.
          api_key else "Not set")
    print(f"  - Search Depth: {tavily_config.search_depth}")
    print(f"  - Max Results: {tavily_config.max_results}")

    # 测试Agent配置
    agent_config = settings.agent_config
    print(f"\nAgent配置:")
    print(f"  - Task Planner: {agent_config.task_planner.name}")
    print(f"  - Composer: {agent_config.composer.name}")
    print(f"  - Validator: {agent_config.validator.name}")

    # 测试特定模型获取
    qwen_model = settings.get_model_config("qwen_2_5_235b_a22b")
    if qwen_model:
        print(f"\nQwen模型配置:")
        print(f"  - Name: {qwen_model.name}")
        print(f"  - URL: {qwen_model.url}")
        print(f"  - Type: {qwen_model.type}")

    # 测试Agent组件配置获取
    composer_config = settings.get_agent_component_config("composer")
    if composer_config:
        print(f"\nComposer组件配置:")
        print(f"  - Temperature: {composer_config.temperature}")
        print(f"  - Max Tokens: {composer_config.max_tokens}")
        print(f"  - Timeout: {composer_config.timeout}")

    print("\n=== 配置测试完成 ===")


if __name__ == "__main__":
    test_config()
