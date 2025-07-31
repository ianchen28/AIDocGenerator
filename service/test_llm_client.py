#!/usr/bin/env python3
"""
LLM 客户端测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

from src.doc_agent.llm_clients import get_llm_client
from loguru import logger


def test_llm_client():
    """测试 LLM 客户端"""
    print("🔍 测试 LLM 客户端...")

    try:
        # 获取 LLM 客户端
        llm_client = get_llm_client()
        print(f"✅ LLM 客户端创建成功: {type(llm_client)}")

        # 测试简单的 prompt
        test_prompt = "请简单介绍一下人工智能。"
        print(f"📝 测试 prompt: {test_prompt}")

        # 调用 LLM
        response = llm_client.invoke(test_prompt)
        print(f"✅ LLM 调用成功")
        print(f"📄 响应内容: {response[:100]}...")

        return True

    except Exception as e:
        print(f"❌ LLM 客户端测试失败: {e}")
        return False


if __name__ == "__main__":
    test_llm_client()
