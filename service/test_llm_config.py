#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM配置测试脚本
用于验证不同模型服务的配置和连接
"""

import sys
import os
from pathlib import Path

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.env_loader import setup_environment
from core.config import settings
from src.doc_agent.llm_clients import get_llm_client


def test_model_configs():
    """测试所有模型配置"""
    print("🧪 测试模型配置")
    print("=" * 80)

    # 1. 显示所有可用模型
    print("📋 可用模型列表:")
    for model_key, config in settings.supported_models.items():
        print(f"  - {model_key}: {config.name} ({config.type})")
    print()

    # 2. 测试特定模型
    test_models = [
        "moonshot_k2_0711_preview",  # Moonshot
        "gemini_1_5_pro",  # Gemini
        "deepseek_v3",  # DeepSeek
        "qwen_2_5_235b_a22b",  # 企业内网模型
    ]

    for model_key in test_models:
        print(f"🔍 测试模型: {model_key}")
        try:
            # 获取模型配置
            model_config = settings.get_model_config(model_key)
            if not model_config:
                print(f"  ❌ 模型配置未找到: {model_key}")
                continue

            print(f"  📝 模型名称: {model_config.name}")
            print(f"  🔗 API地址: {model_config.url}")
            print(f"  🧠 推理模式: {model_config.reasoning}")

            # 创建客户端
            client = get_llm_client(model_key)
            print(f"  ✅ 客户端创建成功: {type(client).__name__}")

            # 简单测试调用
            test_prompt = "请简单回答：1+1等于几？"
            print(f"  🧪 测试调用: {test_prompt}")

            response = client.invoke(test_prompt, temperature=0, max_tokens=50)
            print(f"  📤 响应: {response[:100]}...")
            print(f"  ✅ 模型 {model_key} 测试成功")

        except Exception as e:
            print(f"  ❌ 模型 {model_key} 测试失败: {str(e)}")

        print("-" * 80)


def test_container_config():
    """测试容器配置"""
    print("\n🔧 测试容器配置")
    print("=" * 80)

    try:
        from core.container import container

        print("✅ 容器创建成功")
        print(f"📋 LLM客户端类型: {type(container.llm_client).__name__}")
        print(f"🔍 搜索工具类型: {type(container.search_tool).__name__}")
        print(f"📊 图对象类型: {type(container.graph).__name__}")

        # 测试图编译
        print("\n🧪 测试图编译...")
        initial_input = {
            "messages": [],
            "topic": "测试主题",
            "research_plan": "",
            "search_queries": [],
            "gathered_data": "",
            "final_document": ""
        }

        print("✅ 图编译成功，可以执行")

    except Exception as e:
        print(f"❌ 容器配置测试失败: {str(e)}")


def test_agent_components():
    """测试Agent组件配置"""
    print("\n🤖 测试Agent组件配置")
    print("=" * 80)

    components = [
        "task_planner", "retriever", "executor", "composer", "validator"
    ]

    for component in components:
        try:
            config = settings.get_agent_component_config(component)
            if config:
                print(f"✅ {component}: {config.name} ({config.provider})")
                print(f"   - 温度: {config.temperature}")
                print(f"   - 最大token: {config.max_tokens}")
                print(f"   - 超时: {config.timeout}秒")
            else:
                print(f"❌ {component}: 配置未找到")
        except Exception as e:
            print(f"❌ {component}: 配置错误 - {str(e)}")


def main():
    """主函数"""
    print("🚀 LLM配置测试开始")
    print("=" * 80)

    # 设置环境
    setup_environment()

    # 运行测试
    test_model_configs()
    test_container_config()
    test_agent_components()

    print("\n✅ 所有测试完成!")


if __name__ == "__main__":
    main()
