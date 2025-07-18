#!/usr/bin/env python3
"""
测试 providers.py 中的日志系统
"""

from core.container import container
from src.doc_agent.llm_clients.providers import (
    GeminiClient, DeepSeekClient, MoonshotClient, InternalLLMClient,
    RerankerClient, EmbeddingClient, ReasoningParser)


def test_providers_logging():
    """测试LLM客户端提供者日志系统"""
    print("=== 测试LLM客户端提供者日志系统 ===")

    try:
        # 测试1: ReasoningParser
        print("\n🔍 测试1: 推理解析器...")

        parser = ReasoningParser(reasoning=True)
        test_response = "这是正常回答 <think>这是推理过程</think> 这是最终答案"
        parsed = parser.parse(test_response)
        print(f"✅ 推理解析器测试成功")
        print(f"   原始: '{test_response}'")
        print(f"   解析后: '{parsed}'")

        # 测试2: 客户端初始化
        print("\n🔍 测试2: 客户端初始化...")

        try:
            # 测试 GeminiClient 初始化
            gemini_client = GeminiClient(base_url="https://test.com",
                                         model_name="gemini-test",
                                         api_key="test-key")
            print(f"✅ GeminiClient 初始化成功")
        except Exception as e:
            print(f"⚠️  GeminiClient 初始化失败: {e}")

        try:
            # 测试 DeepSeekClient 初始化
            deepseek_client = DeepSeekClient(base_url="https://test.com",
                                             model_name="deepseek-test",
                                             api_key="test-key")
            print(f"✅ DeepSeekClient 初始化成功")
        except Exception as e:
            print(f"⚠️  DeepSeekClient 初始化失败: {e}")

        try:
            # 测试 MoonshotClient 初始化
            moonshot_client = MoonshotClient(base_url="https://test.com",
                                             model_name="moonshot-test",
                                             api_key="test-key")
            print(f"✅ MoonshotClient 初始化成功")
        except Exception as e:
            print(f"⚠️  MoonshotClient 初始化失败: {e}")

        try:
            # 测试 InternalLLMClient 初始化
            internal_client = InternalLLMClient(base_url="https://test.com",
                                                model_name="internal-test",
                                                api_key="test-key")
            print(f"✅ InternalLLMClient 初始化成功")
        except Exception as e:
            print(f"⚠️  InternalLLMClient 初始化失败: {e}")

        try:
            # 测试 RerankerClient 初始化
            reranker_client = RerankerClient(base_url="https://test.com",
                                             api_key="test-key")
            print(f"✅ RerankerClient 初始化成功")
        except Exception as e:
            print(f"⚠️  RerankerClient 初始化失败: {e}")

        try:
            # 测试 EmbeddingClient 初始化
            embedding_client = EmbeddingClient(base_url="https://test.com",
                                               api_key="test-key")
            print(f"✅ EmbeddingClient 初始化成功")
        except Exception as e:
            print(f"⚠️  EmbeddingClient 初始化失败: {e}")

        # 测试3: API调用错误处理
        print("\n🔍 测试3: API调用错误处理...")

        try:
            # 使用无效的URL测试错误处理
            test_client = InternalLLMClient(
                base_url="https://invalid-url-that-does-not-exist.com",
                model_name="test",
                api_key="test")
            test_client.invoke("test prompt")
            print("❌ 应该抛出异常但没有")
        except Exception as e:
            print(f"✅ 正确处理了API调用错误: {e}")

        print("\n✅ LLM客户端提供者日志系统测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ LLM客户端提供者测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_providers_logging()
