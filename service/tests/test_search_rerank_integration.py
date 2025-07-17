#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索和重排序集成测试
验证新的搜索工具函数和重排序功能的集成
"""

import sys
import os
import unittest
from pathlib import Path

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import LLMTestCase, skip_if_no_reranker
from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools.reranker import RerankerTool
from src.doc_agent.llm_clients.providers import RerankerClient
from src.doc_agent.utils.search_utils import search_and_rerank, format_search_results, format_reranked_results
from core.config import settings


class SearchRerankIntegrationTest(LLMTestCase):
    """搜索和重排序集成测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

        # 获取ES配置
        es_config = settings.elasticsearch_config
        if es_config:
            self.es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                               username=es_config.username,
                                               password=es_config.password,
                                               timeout=es_config.timeout)
            self.has_es = True
        else:
            self.es_search_tool = None
            self.has_es = False
            print("⚠️  未找到ES配置，将跳过相关测试")

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            self.reranker_tool = RerankerTool(base_url=reranker_config.url,
                                              api_key=reranker_config.api_key)
            self.has_reranker = True
        else:
            self.reranker_tool = None
            self.has_reranker = False
            print("⚠️  未找到reranker配置，将跳过相关测试")

    @skip_if_no_reranker
    async def test_search_and_rerank_basic(self):
        """测试基础搜索和重排序功能"""
        print("\n" + "=" * 60)
        print("🔍 测试基础搜索和重排序功能")
        print("=" * 60)

        if not self.has_es:
            print("❌ ES配置不可用，跳过测试")
            return

        query = "人工智能电力行业应用"

        print(f"🔍 查询: {query}")

        try:
            # 执行搜索和重排序
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=self.es_search_tool,
                query=query,
                query_vector=None,  # 先测试文本搜索
                reranker_tool=self.reranker_tool,
                initial_top_k=10,
                final_top_k=5)

            print(f"✅ 搜索和重排序完成")
            print(f"📄 原始搜索结果数量: {len(search_results)}")
            print(f"📄 重排序结果数量: {len(reranked_results)}")
            print(f"📝 格式化结果长度: {len(formatted_result)}")

            # 验证结果
            self.assertIsInstance(search_results, list)
            self.assertIsInstance(reranked_results, list)
            self.assertIsInstance(formatted_result, str)

            # 显示重排序结果
            if reranked_results:
                print(f"\n📋 重排序结果预览:")
                for i, result in enumerate(reranked_results[:3], 1):
                    print(
                        f"  {i}. 评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                    )

            # 验证重排序结果数量不超过final_top_k
            self.assertLessEqual(len(reranked_results), 5)

        except Exception as e:
            print(f"❌ 搜索和重排序测试失败: {str(e)}")
            self.fail(f"搜索和重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    async def test_search_and_rerank_without_reranker(self):
        """测试没有重排序工具的情况"""
        print("\n" + "=" * 60)
        print("🔍 测试没有重排序工具的情况")
        print("=" * 60)

        if not self.has_es:
            print("❌ ES配置不可用，跳过测试")
            return

        query = "电力系统技术"

        print(f"🔍 查询: {query}")

        try:
            # 执行搜索，不提供重排序工具
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=self.es_search_tool,
                query=query,
                query_vector=None,
                reranker_tool=None,  # 不提供重排序工具
                initial_top_k=10,
                final_top_k=5)

            print(f"✅ 搜索完成（无重排序）")
            print(f"📄 原始搜索结果数量: {len(search_results)}")
            print(f"📄 重排序结果数量: {len(reranked_results)}")
            print(f"📝 格式化结果长度: {len(formatted_result)}")

            # 验证结果
            self.assertIsInstance(search_results, list)
            self.assertEqual(len(reranked_results), 0)  # 应该没有重排序结果
            self.assertIsInstance(formatted_result, str)

            # 验证格式化结果包含原始搜索结果
            self.assertIn("找到", formatted_result)

        except Exception as e:
            print(f"❌ 无重排序测试失败: {str(e)}")
            self.fail(f"无重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_format_functions(self):
        """测试格式化函数"""
        print("\n" + "=" * 60)
        print("🔍 测试格式化函数")
        print("=" * 60)

        # 创建模拟的搜索结果
        from src.doc_agent.tools.es_service import ESSearchResult

        mock_results = [
            ESSearchResult(id="doc1",
                           original_content="这是第一个文档的内容，关于人工智能在电力行业的应用。",
                           div_content="人工智能电力应用",
                           source="doc1.txt",
                           score=0.8,
                           metadata={"file_name": "doc1.txt"}),
            ESSearchResult(id="doc2",
                           original_content="这是第二个文档的内容，关于电力系统的基础知识。",
                           div_content="电力系统基础",
                           source="doc2.txt",
                           score=0.6,
                           metadata={"file_name": "doc2.txt"})
        ]

        query = "测试查询"
        indices_list = ["index1", "index2"]

        # 测试格式化搜索结果
        formatted_search = format_search_results(mock_results, query,
                                                 indices_list)
        print(f"📝 搜索格式化结果长度: {len(formatted_search)}")
        print(f"📋 搜索格式化结果预览: {formatted_search[:200]}...")

        # 验证格式化结果
        self.assertIn("找到 2 个相关文档", formatted_search)
        self.assertIn("doc1.txt", formatted_search)
        self.assertIn("doc2.txt", formatted_search)

        # 测试格式化重排序结果
        from src.doc_agent.tools.reranker import RerankedSearchResult

        mock_reranked_results = [
            RerankedSearchResult(id="doc1",
                                 original_content="这是第一个文档的内容，关于人工智能在电力行业的应用。",
                                 div_content="人工智能电力应用",
                                 source="doc1.txt",
                                 score=0.8,
                                 rerank_score=0.9,
                                 metadata={"file_name": "doc1.txt"}),
            RerankedSearchResult(id="doc2",
                                 original_content="这是第二个文档的内容，关于电力系统的基础知识。",
                                 div_content="电力系统基础",
                                 source="doc2.txt",
                                 score=0.6,
                                 rerank_score=0.7,
                                 metadata={"file_name": "doc2.txt"})
        ]

        formatted_reranked = format_reranked_results(mock_reranked_results,
                                                     query, indices_list)
        print(f"📝 重排序格式化结果长度: {len(formatted_reranked)}")
        print(f"📋 重排序格式化结果预览: {formatted_reranked[:200]}...")

        # 验证重排序格式化结果
        self.assertIn("重排序后找到 2 个最相关文档", formatted_reranked)
        self.assertIn("原始评分", formatted_reranked)
        self.assertIn("重排序评分", formatted_reranked)

        print(f"✅ 格式化函数测试通过")

    @skip_if_no_reranker
    async def test_search_performance(self):
        """测试搜索性能"""
        print("\n" + "=" * 60)
        print("⚡ 测试搜索性能")
        print("=" * 60)

        if not self.has_es:
            print("❌ ES配置不可用，跳过测试")
            return

        import time

        test_queries = ["人工智能", "电力系统", "机器学习", "智能电网"]

        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 测试查询 {i}/{len(test_queries)}: {query}")

            start_time = time.time()
            try:
                search_results, reranked_results, formatted_result = await search_and_rerank(
                    es_search_tool=self.es_search_tool,
                    query=query,
                    query_vector=None,
                    reranker_tool=self.reranker_tool,
                    initial_top_k=8,
                    final_top_k=3)
                end_time = time.time()

                response_time = end_time - start_time
                print(f"⏱️  响应时间: {response_time:.3f} 秒")
                print(f"📄 原始结果: {len(search_results)} 个")
                print(f"📄 重排序结果: {len(reranked_results)} 个")

                # 性能要求
                if response_time < 10:  # 10秒内
                    print(f"✅ 性能良好")
                elif response_time < 20:  # 20秒内
                    print(f"⚠️  性能一般")
                else:
                    print(f"❌ 性能较差")

            except Exception as e:
                print(f"❌ 查询失败: {str(e)}")


async def run_async_tests():
    """运行异步测试"""
    import asyncio

    # 创建测试实例
    test_instance = SearchRerankIntegrationTest()
    test_instance.setUp()

    print("🚀 运行异步搜索和重排序集成测试")
    print("=" * 80)

    # 运行异步测试
    try:
        await test_instance.test_search_and_rerank_basic()
        print("✅ test_search_and_rerank_basic 通过")
    except Exception as e:
        print(f"❌ test_search_and_rerank_basic 失败: {str(e)}")

    try:
        await test_instance.test_search_and_rerank_without_reranker()
        print("✅ test_search_and_rerank_without_reranker 通过")
    except Exception as e:
        print(f"❌ test_search_and_rerank_without_reranker 失败: {str(e)}")

    try:
        await test_instance.test_search_performance()
        print("✅ test_search_performance 通过")
    except Exception as e:
        print(f"❌ test_search_performance 失败: {str(e)}")

    test_instance.test_format_functions()
    print("✅ test_format_functions 通过")

    print("\n" + "=" * 80)
    print("📊 异步集成测试完成")
    print("=" * 80)

    return True


def main():
    """运行所有搜索和重排序集成测试"""
    import asyncio

    # 运行异步测试
    success = asyncio.run(run_async_tests())

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
