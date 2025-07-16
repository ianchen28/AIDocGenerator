#!/usr/bin/env python3
"""
测试 Qwen LLM 的 400 错误诊断
"""

import asyncio
import sys
import os

# 添加 service 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from service.core.env_loader import setup_environment
from service.src.doc_agent.llm_clients import get_llm_client
from service.core.config import settings


def test_qwen_connection():
    """测试 Qwen LLM 连接"""
    print("🔍 开始诊断 Qwen LLM 连接问题...")

    # 设置环境
    setup_environment()

    # 获取模型配置
    model_config = settings.get_model_config("qwen_2_5_235b_a22b")
    print(f"📋 模型配置:")
    print(f"   URL: {model_config.url}")
    print(f"   Model ID: {model_config.model_id}")
    print(f"   API Key: {model_config.api_key}")
    print(f"   Reasoning: {model_config.reasoning}")

    # 创建客户端
    try:
        llm_client = get_llm_client("qwen_2_5_235b_a22b")
        print("✅ LLM 客户端创建成功")
    except Exception as e:
        print(f"❌ LLM 客户端创建失败: {e}")
        return

    # 测试简单请求
    simple_prompt = "你好，请回答：1+1等于几？"
    print(f"\n🧪 测试简单请求:")
    print(f"   Prompt: {simple_prompt}")
    print(f"   Prompt 长度: {len(simple_prompt)} 字符")

    try:
        response = llm_client.invoke(simple_prompt,
                                     temperature=0,
                                     max_tokens=10)
        print(f"✅ 简单请求成功: {response}")
    except Exception as e:
        print(f"❌ 简单请求失败: {e}")
        return

    # 测试中等长度请求
    medium_prompt = "请详细介绍一下人工智能在中国电力行业的应用趋势，包括技术发展、政策支持、实际案例等方面。" * 10
    print(f"\n🧪 测试中等长度请求:")
    print(f"   Prompt 长度: {len(medium_prompt)} 字符")

    try:
        response = llm_client.invoke(medium_prompt,
                                     temperature=0,
                                     max_tokens=50)
        print(f"✅ 中等长度请求成功: {response}")
    except Exception as e:
        print(f"❌ 中等长度请求失败: {e}")
        return

    # 测试长请求（模拟 supervisor_router 的 prompt）
    long_prompt = "**角色：** 你是一位研究主管，需要判断下方资料是否足够撰写完整文档。\n\n**主题：**「人工智能在中国电力行业的应用趋势和政策支持」\n\n**已收集的研究资料：**" + "这是一个很长的研究资料内容。" * 1000
    print(f"\n🧪 测试长请求:")
    print(f"   Prompt 长度: {len(long_prompt)} 字符")

    try:
        response = llm_client.invoke(long_prompt, temperature=0, max_tokens=10)
        print(f"✅ 长请求成功: {response}")
    except Exception as e:
        print(f"❌ 长请求失败: {e}")
        print(f"💡 建议: 可能是 prompt 长度超过了模型的最大输入限制")
        return

    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    test_qwen_connection()
