#!/usr/bin/env python3
"""
测试OpenAI客户端实现
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doc_agent.llm_clients.providers import OpenAIClient


def test_openai_client():
    """测试OpenAI客户端"""
    print("=== OpenAI客户端测试 ===")

    # 从环境变量获取API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未设置OPENAI_API_KEY环境变量")
        print("请设置环境变量: export OPENAI_API_KEY=your_api_key")
        return

    try:
        # 创建客户端
        client = OpenAIClient(api_key=api_key, model="gpt-4o")
        print("✅ OpenAI客户端创建成功")

        # 测试简单调用
        prompt = "请用一句话介绍Python编程语言"
        print(f"\n📝 测试提示: {prompt}")

        response = client.invoke(prompt)
        print(f"🤖 模型响应: {response}")

        # 测试带参数的调用
        print(f"\n📝 测试带参数的调用...")
        response_with_params = client.invoke(prompt="请生成一个Python函数来计算斐波那契数列",
                                             temperature=0.8,
                                             max_tokens=500)
        print(f"🤖 带参数的响应: {response_with_params}")

        print("\n✅ 所有测试通过!")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    test_openai_client()
