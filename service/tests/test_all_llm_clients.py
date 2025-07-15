#!/usr/bin/env python3
"""
测试所有LLM客户端的实现
"""

from test_base import TestBase, setup_paths

# 设置测试环境
setup_paths()

from src.doc_agent.llm_clients import get_llm_client, get_reranker_client, get_embedding_client
from core.config import settings


class LLMClientsTest(TestBase):
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

            return True

        except Exception as e:
            print(f"❌ 配置加载失败: {str(e)}")
            return False

    def test_client_creation(self):
        """测试客户端创建"""
        print("=== 测试客户端创建 ===")

        try:
            # 测试不同模型的客户端创建
            test_models = [
                "qwen_2_5_235b_a22b",  # 企业模型
                "gemini_1_5_pro",  # Gemini模型
                "deepseek_v3",  # DeepSeek模型
            ]

            success_count = 0
            for model_key in test_models:
                try:
                    client = get_llm_client(model_key=model_key)
                    print(f"  ✅ {model_key}: 客户端创建成功")
                    print(f"     类型: {type(client).__name__}")

                    # 检查URL配置
                    if hasattr(client, 'base_url'):
                        print(f"     Base URL: {client.base_url}")
                    elif hasattr(client, 'api_key'):
                        print(f"     API Key: {client.api_key}")

                    success_count += 1

                except Exception as e:
                    print(f"  ❌ {model_key}: {str(e)}")

            return success_count > 0

        except Exception as e:
            print(f"❌ 客户端创建测试失败: {str(e)}")
            return False

    def test_specialized_clients(self):
        """测试专门的客户端"""
        print("=== 测试专门客户端 ===")

        try:
            success_count = 0

            # 测试Reranker客户端
            try:
                reranker_client = get_reranker_client()
                print(f"  ✅ Reranker: 客户端创建成功")
                print(f"     类型: {type(reranker_client).__name__}")
                print(f"     Base URL: {reranker_client.base_url}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Reranker: {str(e)}")

            # 测试Embedding客户端
            try:
                embedding_client = get_embedding_client()
                print(f"  ✅ Embedding: 客户端创建成功")
                print(f"     类型: {type(embedding_client).__name__}")
                print(f"     Base URL: {embedding_client.base_url}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Embedding: {str(e)}")

            return success_count > 0

        except Exception as e:
            print(f"❌ 专门客户端测试失败: {str(e)}")
            return False

    def test_client_invoke(self):
        """实际调用各类 client 的 invoke 方法并检查返回值有效性"""
        print("=== 测试客户端实际调用 ===")
        success_count = 0
        total = 0
        # 1. LLM Client
        try:
            client = get_llm_client(model_key="qwen_2_5_235b_a22b")
            response = client.invoke("你好，介绍一下你自己。",
                                     temperature=0.7,
                                     max_tokens=100)
            print(f"  ✅ LLM invoke 返回: {str(response)[:60]}...")
            if isinstance(response, str) and len(response.strip()) > 0:
                success_count += 1
            else:
                print("  ❌ LLM invoke 返回内容异常")
            total += 1
        except Exception as e:
            print(f"  ❌ LLM invoke 异常: {e}")
            total += 1
        # 2. Gemini Client
        try:
            gemini_client = get_llm_client(model_key="gemini_1_5_pro")
            response = gemini_client.invoke("你好，介绍一下你自己。",
                                            temperature=0.7,
                                            max_tokens=100)
            print(f"  ✅ Gemini invoke 返回: {str(response)[:60]}...")
            if isinstance(response, str) and len(response.strip()) > 0:
                success_count += 1
            else:
                print("  ❌ Gemini invoke 返回内容异常")
            total += 1
        except Exception as e:
            print(f"  ❌ Gemini invoke 异常: {e}")
            total += 1
        # 3. Reranker
        try:
            reranker = get_reranker_client()
            test_docs = [
                "机器学习是人工智能的一个分支", "深度学习在图像识别方面取得了突破", "自然语言处理让机器能够理解人类语言",
                "强化学习通过奖励机制训练智能体"
            ]
            result = reranker.invoke("人工智能",
                                     documents=test_docs,
                                     size=len(test_docs))
            print("  ✅ Reranker invoke 完整返回:", result)
            if result and isinstance(
                    result, dict) and "sorted_doc_list" in result and len(
                        result["sorted_doc_list"]) > 0:
                sorted_docs = result["sorted_doc_list"]
                print("     排序结果：")
                for i, doc in enumerate(sorted_docs):
                    print(
                        f"     {i+1}. 分数: {doc.get('rerank_score', 'N/A')}, 内容: {doc.get('text', '')[:30]}"
                    )
                success_count += 1
            else:
                print("  ❌ Reranker invoke 返回内容异常")
            total += 1
        except Exception as e:
            print(f"  ❌ Reranker invoke 异常: {e}")
            total += 1
        # 4. Embedding
        try:
            embedding = get_embedding_client()
            vector = embedding.invoke("文本内容")
            print(f"  ✅ Embedding invoke 返回: {str(vector)[:60]}...")
            if vector is not None and hasattr(vector,
                                              "__len__") and len(vector) > 0:
                success_count += 1
            else:
                print("  ❌ Embedding invoke 返回内容异常")
            total += 1
        except Exception as e:
            print(f"  ❌ Embedding invoke 异常: {e}")
            total += 1
        print(f"\n实际调用通过: {success_count}/{total}")
        return success_count == total

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始LLM客户端测试...")

        test_results = []

        # 运行各项测试
        test_results.append(("配置加载", self.test_config_loading()))
        test_results.append(("客户端创建", self.test_client_creation()))
        test_results.append(("专门客户端", self.test_specialized_clients()))
        test_results.append(("实际调用", self.test_client_invoke()))

        # 显示测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print("=" * 50)

        passed = 0
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1

        print(f"\n总计: {passed}/{len(test_results)} 项测试通过")

        if passed == len(test_results):
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败")

        # 显示使用示例
        print("\n🎯 使用示例:")
        print("""
# 使用特定模型（URL从配置自动获取）
client = get_llm_client(model_key="qwen_2_5_235b_a22b")
response = client.invoke("你好", temperature=0.7, max_tokens=1000)

# 使用Gemini（URL从配置获取）
gemini_client = get_llm_client(model_key="gemini_1_5_pro")
response = gemini_client.invoke("你好", temperature=0.7, max_tokens=1000)

# 使用Reranker
reranker = get_reranker_client()
result = reranker.invoke("查询", documents=["文档1", "文档2"])

# 使用Embedding
embedding = get_embedding_client()
vector = embedding.invoke("文本内容")
        """)


def main():
    """主测试函数"""
    tester = LLMClientsTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
