#!/usr/bin/env python3
"""
测试所有LLM客户端的实现
"""

from test_base import LLMTestCase, async_test
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

from src.doc_agent.llm_clients import get_llm_client, get_reranker_client, get_embedding_client
from core.config import settings

import unittest


class LLMClientsTest(LLMTestCase):
    """LLM客户端测试类"""

    def test_config_loading(self):
        """测试配置加载"""
        print("=== 测试配置加载 ===")

        try:
            models = settings.supported_models
            print(f"✅ 支持的模型数量: {len(models)}")

            for model_key, model_config in list(models.items())[:5]:  # 只显示前5个
                print(
                    f"  - {model_key}: {model_config.name} ({model_config.type})"
                )
                print(f"    URL: {model_config.url}")
                print(f"    Model ID: {model_config.model_id}")
                print(f"    Description: {model_config.description}")
                print()

        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            self.fail(f"配置加载失败: {e}")

    def test_client_creation(self):
        """测试客户端创建"""
        print("=== 测试客户端创建 ===")

        test_models = [
            "moonshot_k2_0711_preview",  # Moonshot模型
            "qwen_2_5_235b_a22b",  # 内部模型
        ]

        success_count = 0
        total = 0

        for model_key in test_models:
            try:
                client = self.get_llm_client(model_key)
                print(f"  ✅ {model_key} 客户端创建成功")
                print(f"     类型: {type(client).__name__}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ {model_key} 客户端创建失败: {e}")
            total += 1

        print(f"\n📊 客户端创建结果: {success_count}/{total} 成功")
        self.assertGreater(success_count, 0, "至少有一个客户端创建成功")

    def test_client_invoke(self):
        """测试客户端调用"""
        print("=== 测试客户端调用 ===")

        test_models = [
            "moonshot_k2_0711_preview",  # Moonshot模型
        ]

        success_count = 0
        total = 0

        for model_key in test_models:
            try:
                client = self.get_llm_client(model_key)
                response = client.invoke("你好，介绍一下你自己。",
                                         temperature=0.7,
                                         max_tokens=100)
                print(f"  ✅ {model_key} invoke 返回: {str(response)[:60]}...")
                if isinstance(response, str) and len(response.strip()) > 0:
                    success_count += 1
                else:
                    print(f"  ❌ {model_key} invoke 返回内容异常")
                total += 1
            except Exception as e:
                print(f"  ❌ {model_key} invoke 异常: {e}")
                total += 1

        print(f"\n📊 客户端调用结果: {success_count}/{total} 成功")
        self.assertGreater(success_count, 0, "至少有一个客户端调用成功")

    @async_test
    async def test_moonshot_specific(self):
        """专门测试 Moonshot 客户端"""
        print("=== 专门测试 Moonshot 客户端 ===")

        try:
            # 创建 Moonshot 客户端
            moonshot_client = self.get_llm_client("moonshot_k2_0711_preview")
            print(f"  ✅ Moonshot 客户端创建成功")
            print(f"     类型: {type(moonshot_client).__name__}")

            # 测试基本调用
            response = moonshot_client.invoke("你好，请简单介绍一下你自己。",
                                              temperature=0.7,
                                              max_tokens=50)
            print(f"  ✅ Moonshot 基本调用成功")
            print(f"     响应长度: {len(str(response))} 字符")
            print(f"     响应预览: {str(response)[:100]}...")

            # 测试带参数的调用
            response_with_params = moonshot_client.invoke("请用一句话回答：什么是人工智能？",
                                                          temperature=0.3,
                                                          max_tokens=30)
            print(f"  ✅ Moonshot 带参数调用成功")
            print(f"     响应: {str(response_with_params)[:50]}...")

            print("  ✅ Moonshot 客户端测试全部通过")

        except Exception as e:
            print(f"  ❌ Moonshot 客户端测试失败: {e}")
            self.fail(f"Moonshot 客户端测试失败: {e}")


if __name__ == "__main__":
    unittest.main()
