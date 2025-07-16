#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置切换测试脚本
演示如何修改配置来使用不同的LLM服务
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


def test_different_models():
    """测试不同模型的配置切换"""
    print("🔄 测试不同模型配置切换")
    print("=" * 80)

    # 测试的模型列表
    test_configs = [{
        "name": "Moonshot K2",
        "model_key": "moonshot_k2_0711_preview",
        "description": "高性能推理模型"
    }, {
        "name": "Gemini 1.5 Pro",
        "model_key": "gemini_1_5_pro",
        "description": "Google高质量模型"
    }, {
        "name": "DeepSeek Chat",
        "model_key": "deepseek_v3",
        "description": "DeepSeek通用模型"
    }, {
        "name": "Qwen 235B",
        "model_key": "qwen_2_5_235b_a22b",
        "description": "企业内网推理模型"
    }]

    for config in test_configs:
        print(f"\n🔍 测试 {config['name']} ({config['description']})")
        print("-" * 60)

        try:
            # 获取模型配置
            model_config = settings.get_model_config(config['model_key'])
            if not model_config:
                print(f"❌ 模型配置未找到: {config['model_key']}")
                continue

            print(f"📝 模型名称: {model_config.name}")
            print(f"🔗 API地址: {model_config.url}")
            print(f"🧠 推理模式: {model_config.reasoning}")

            # 创建客户端
            client = get_llm_client(config['model_key'])
            print(f"✅ 客户端类型: {type(client).__name__}")

            # 测试调用
            test_prompt = "请用一句话解释什么是人工智能？"
            print(f"🧪 测试问题: {test_prompt}")

            response = client.invoke(test_prompt,
                                     temperature=0.7,
                                     max_tokens=100)
            print(f"📤 响应: {response}")
            print(f"✅ {config['name']} 测试成功")

        except Exception as e:
            print(f"❌ {config['name']} 测试失败: {str(e)}")


def demonstrate_container_switch():
    """演示如何切换容器中的模型"""
    print("\n🔧 演示容器模型切换")
    print("=" * 80)

    try:
        from core.container import container

        print("📋 当前容器配置:")
        print(f"  - LLM客户端: {type(container.llm_client).__name__}")
        print(f"  - 模型名称: {container.llm_client.model_name}")

        # 演示如何创建不同模型的容器
        print("\n🔄 演示创建不同模型的容器:")

        models_to_test = [
            "gemini_1_5_pro", "deepseek_v3", "moonshot_k2_0711_preview"
        ]

        for model_key in models_to_test:
            try:
                print(f"\n  🔍 测试 {model_key}:")

                # 创建新的LLM客户端
                new_client = get_llm_client(model_key)
                print(f"    ✅ 客户端创建: {type(new_client).__name__}")

                # 测试调用
                response = new_client.invoke("你好",
                                             temperature=0,
                                             max_tokens=20)
                print(f"    📤 响应: {response[:50]}...")

            except Exception as e:
                print(f"    ❌ 失败: {str(e)}")

    except Exception as e:
        print(f"❌ 容器切换演示失败: {str(e)}")


def show_configuration_guide():
    """显示配置指南"""
    print("\n📖 配置修改指南")
    print("=" * 80)

    print("1. 修改容器默认模型:")
    print("   文件: core/container.py")
    print("   修改: self.llm_client = get_llm_client(model_key='your_model')")
    print()

    print("2. 修改Agent组件配置:")
    print("   文件: core/config.yaml")
    print("   修改: agent_config 下的 provider 和 model 字段")
    print()

    print("3. 添加新模型:")
    print("   文件: core/config.yaml")
    print("   在 supported_models 下添加新配置")
    print()

    print("4. 环境变量配置:")
    print("   文件: .env")
    print("   添加: MODEL_API_KEY=your_api_key")
    print()

    print("5. 可用的模型键名:")
    for model_key in settings.supported_models.keys():
        config = settings.supported_models[model_key]
        print(f"   - {model_key}: {config.name} ({config.type})")


def main():
    """主函数"""
    print("🚀 配置切换测试开始")
    print("=" * 80)

    # 设置环境
    setup_environment()

    # 运行测试
    test_different_models()
    demonstrate_container_switch()
    show_configuration_guide()

    print("\n✅ 配置切换测试完成!")


if __name__ == "__main__":
    main()
