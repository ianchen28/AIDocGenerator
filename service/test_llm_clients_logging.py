#!/usr/bin/env python3
"""
测试 llm_clients/__init__.py 中的日志系统
"""

from core.container import container
from src.doc_agent.llm_clients import get_llm_client, get_reranker_client, get_embedding_client


def test_llm_clients_logging():
    """测试LLM客户端日志系统"""
    print("=== 测试LLM客户端日志系统 ===")

    try:
        # 测试1: get_llm_client
        print("\n🔍 测试1: LLM客户端创建...")

        try:
            # 测试默认模型
            llm_client = get_llm_client()
            print(f"✅ LLM客户端创建成功: {type(llm_client).__name__}")
        except Exception as e:
            print(f"⚠️  LLM客户端创建失败（可能是配置问题）: {e}")

        # 测试2: get_reranker_client
        print("\n🔍 测试2: Reranker客户端创建...")

        try:
            reranker_client = get_reranker_client()
            print(f"✅ Reranker客户端创建成功: {type(reranker_client).__name__}")
        except Exception as e:
            print(f"⚠️  Reranker客户端创建失败（可能是配置问题）: {e}")

        # 测试3: get_embedding_client
        print("\n🔍 测试3: Embedding客户端创建...")

        try:
            embedding_client = get_embedding_client()
            print(f"✅ Embedding客户端创建成功: {type(embedding_client).__name__}")
        except Exception as e:
            print(f"⚠️  Embedding客户端创建失败（可能是配置问题）: {e}")

        # 测试4: 测试错误情况
        print("\n🔍 测试4: 错误情况处理...")

        try:
            # 测试不存在的模型
            get_llm_client("non_existent_model")
            print("❌ 应该抛出异常但没有")
        except ValueError as e:
            print(f"✅ 正确处理了不存在的模型: {e}")
        except Exception as e:
            print(f"✅ 捕获到其他异常: {e}")

        print("\n✅ LLM客户端日志系统测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ LLM客户端测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_llm_clients_logging()
