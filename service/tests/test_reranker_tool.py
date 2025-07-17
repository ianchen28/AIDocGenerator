#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RerankerTool 测试
验证 RerankerTool 与 ESSearchResult 和 RerankerClient 的集成功能
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
from src.doc_agent.tools.es_service import ESSearchResult
from src.doc_agent.tools.reranker import RerankerTool, RerankedSearchResult
from src.doc_agent.llm_clients.providers import RerankerClient
from core.config import settings


class RerankerToolTest(LLMTestCase):
    """RerankerTool 测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            self.reranker_tool = RerankerTool(base_url=reranker_config.url,
                                              api_key=reranker_config.api_key)
            self.has_config = True
        else:
            self.reranker_tool = None
            self.has_config = False
            print("⚠️  未找到reranker配置，将跳过相关测试")

    def create_test_search_results(self) -> list[ESSearchResult]:
        """创建测试用的 ESSearchResult 列表"""
        test_docs = [{
            "id": "doc1",
            "original_content": "这是一个关于天气的文档，与电力行业无关。",
            "div_content": "这是一个关于天气的文档，与电力行业无关。",
            "source": "weather.txt",
            "score": 0.1
        }, {
            "id": "doc2",
            "original_content": "电力系统是现代社会的重要基础设施。",
            "div_content": "电力系统是现代社会的重要基础设施。",
            "source": "power.txt",
            "score": 0.5
        }, {
            "id": "doc3",
            "original_content": "人工智能技术在电力行业的应用越来越广泛。",
            "div_content": "人工智能技术在电力行业的应用越来越广泛。",
            "source": "ai_power.txt",
            "score": 0.8
        }, {
            "id": "doc4",
            "original_content": "机器学习算法可以优化电力调度。",
            "div_content": "机器学习算法可以优化电力调度。",
            "source": "ml_power.txt",
            "score": 0.7
        }, {
            "id": "doc5",
            "original_content": "智能电网技术是电力行业数字化转型的关键。",
            "div_content": "智能电网技术是电力行业数字化转型的关键。",
            "source": "smart_grid.txt",
            "score": 0.6
        }]

        results = []
        for doc in test_docs:
            result = ESSearchResult(id=doc["id"],
                                    original_content=doc["original_content"],
                                    div_content=doc["div_content"],
                                    source=doc["source"],
                                    score=doc["score"],
                                    metadata={"file_name": doc["source"]})
            results.append(result)

        return results

    @skip_if_no_reranker
    def test_reranker_tool_basic_functionality(self):
        """测试 RerankerTool 基础功能"""
        print("\n" + "=" * 60)
        print("🔍 测试 RerankerTool 基础功能")
        print("=" * 60)

        # 创建测试数据
        search_results = self.create_test_search_results()
        query = "人工智能在电力行业的应用"

        print(f"🔍 查询: {query}")
        print(f"📄 原始搜索结果数量: {len(search_results)}")

        # 显示原始结果
        print(f"\n📋 原始搜索结果:")
        for i, result in enumerate(search_results, 1):
            print(
                f"  {i}. 评分: {result.score:.3f} | {result.div_content[:50]}..."
            )

        try:
            # 执行重排序
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results)

            print(f"\n✅ 重排序成功")
            print(f"📄 重排序结果数量: {len(reranked_results)}")

            # 显示重排序结果
            print(f"\n📋 重排序后结果:")
            for i, result in enumerate(reranked_results, 1):
                print(
                    f"  {i}. 原始评分: {result.score:.3f} | 重排序评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                )

            # 验证结果
            self.assertIsInstance(reranked_results, list)
            self.assertEqual(len(reranked_results), len(search_results))

            # 验证每个结果都有重排序评分
            for result in reranked_results:
                self.assertIsInstance(result, RerankedSearchResult)
                self.assertIsInstance(result.rerank_score, (int, float))
                self.assertIsInstance(result.score, (int, float))

            # 验证重排序是否生效（第一个文档应该是最相关的）
            if reranked_results:
                first_doc = reranked_results[0].div_content
                if "人工智能" in first_doc or "AI" in first_doc:
                    print(f"\n✅ 重排序生效！最相关文档排在第一位")
                else:
                    print(f"\n⚠️  重排序可能未生效，第一文档: {first_doc[:30]}...")

        except Exception as e:
            print(f"❌ 重排序测试失败: {str(e)}")
            self.fail(f"重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_with_top_k(self):
        """测试 RerankerTool 的 top_k 功能"""
        print("\n" + "=" * 60)
        print("🔍 测试 RerankerTool top_k 功能")
        print("=" * 60)

        search_results = self.create_test_search_results()
        query = "人工智能电力应用"
        top_k = 3

        print(f"🔍 查询: {query}")
        print(f"📄 原始结果数量: {len(search_results)}")
        print(f"🎯 请求 top_k: {top_k}")

        try:
            # 执行重排序，限制返回数量
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results, top_k=top_k)

            print(f"\n✅ 重排序成功")
            print(f"📄 返回结果数量: {len(reranked_results)}")

            # 显示结果
            print(f"\n📋 重排序结果 (top {top_k}):")
            for i, result in enumerate(reranked_results, 1):
                print(
                    f"  {i}. 重排序评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                )

            # 验证结果数量
            self.assertLessEqual(len(reranked_results), top_k)

            # 验证结果按重排序评分降序排列
            if len(reranked_results) > 1:
                for i in range(len(reranked_results) - 1):
                    self.assertGreaterEqual(
                        reranked_results[i].rerank_score,
                        reranked_results[i + 1].rerank_score)
                print(f"\n✅ 结果按重排序评分正确排序")

        except Exception as e:
            print(f"❌ top_k 测试失败: {str(e)}")
            self.fail(f"top_k 测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_effectiveness_analysis(self):
        """测试重排序效果分析"""
        print("\n" + "=" * 60)
        print("📊 测试重排序效果分析")
        print("=" * 60)

        search_results = self.create_test_search_results()
        query = "人工智能电力行业应用"

        try:
            # 执行重排序
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results)

            # 分析效果
            analysis = self.reranker_tool.analyze_rerank_effectiveness(
                reranked_results, query)

            print(f"\n📊 重排序效果分析:")
            print(f"  总结果数: {analysis['total_results']}")
            print(f"  评分范围: {analysis['score_range']:.3f}")
            print(f"  最高分: {analysis['top_score']:.3f}")
            print(f"  最低分: {analysis['bottom_score']:.3f}")
            print(f"  效果等级: {analysis['effectiveness']}")
            print(f"  相关性评分: {analysis['relevance_score']:.3f}")
            print(f"  关键词匹配数: {analysis['keyword_match_count']}")

            # 验证分析结果
            self.assertIsInstance(analysis, dict)
            self.assertIn('total_results', analysis)
            self.assertIn('score_range', analysis)
            self.assertIn('effectiveness', analysis)

            # 验证效果等级
            valid_effectiveness = [
                'excellent', 'good', 'moderate', 'poor', 'no_results'
            ]
            self.assertIn(analysis['effectiveness'], valid_effectiveness)

        except Exception as e:
            print(f"❌ 效果分析测试失败: {str(e)}")
            self.fail(f"效果分析测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_get_top_results(self):
        """测试获取前 top_k 个结果"""
        print("\n" + "=" * 60)
        print("🔍 测试获取前 top_k 个结果")
        print("=" * 60)

        search_results = self.create_test_search_results()
        query = "人工智能电力应用"

        try:
            # 执行重排序
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results)

            # 获取前3个结果
            top_3_results = self.reranker_tool.get_top_results(
                reranked_results, 3)

            print(f"\n📋 前3个重排序结果:")
            for i, result in enumerate(top_3_results, 1):
                print(
                    f"  {i}. 评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                )

            # 验证结果
            self.assertEqual(len(top_3_results), 3)

            # 验证排序正确
            if len(top_3_results) > 1:
                for i in range(len(top_3_results) - 1):
                    self.assertGreaterEqual(top_3_results[i].rerank_score,
                                            top_3_results[i + 1].rerank_score)
                print(f"\n✅ top_k 结果排序正确")

        except Exception as e:
            print(f"❌ get_top_results 测试失败: {str(e)}")
            self.fail(f"get_top_results 测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_empty_results(self):
        """测试空结果处理"""
        print("\n" + "=" * 60)
        print("🔍 测试空结果处理")
        print("=" * 60)

        # 测试空列表
        empty_results = []
        query = "测试查询"

        try:
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=empty_results)

            print(f"📄 空结果重排序: {len(reranked_results)} 个结果")
            self.assertEqual(len(reranked_results), 0)

            # 测试分析空结果
            analysis = self.reranker_tool.analyze_rerank_effectiveness(
                reranked_results, query)

            print(f"📊 空结果分析: {analysis}")
            self.assertEqual(analysis['total_results'], 0)
            self.assertEqual(analysis['effectiveness'], 'no_results')

        except Exception as e:
            print(f"❌ 空结果测试失败: {str(e)}")
            self.fail(f"空结果测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_error_handling(self):
        """测试错误处理"""
        print("\n" + "=" * 60)
        print("🔍 测试错误处理")
        print("=" * 60)

        # 创建包含空内容的测试结果
        problematic_results = [
            ESSearchResult(
                id="doc1",
                original_content="",  # 空内容
                div_content="",
                source="empty.txt",
                score=0.1),
            ESSearchResult(id="doc2",
                           original_content="正常文档内容",
                           div_content="正常文档内容",
                           source="normal.txt",
                           score=0.5)
        ]

        query = "测试查询"

        try:
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=problematic_results)

            print(f"📄 错误处理测试结果: {len(reranked_results)} 个结果")

            # 应该能处理空内容，返回有效结果
            self.assertIsInstance(reranked_results, list)

            # 显示结果
            for i, result in enumerate(reranked_results, 1):
                print(
                    f"  {i}. 评分: {result.rerank_score:.3f} | 内容长度: {len(result.div_content)}"
                )

        except Exception as e:
            print(f"❌ 错误处理测试失败: {str(e)}")
            self.fail(f"错误处理测试失败: {str(e)}")


def main():
    """运行所有 RerankerTool 测试"""
    print("🚀 RerankerTool 测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    # 添加所有测试方法
    test_suite.addTest(test_loader.loadTestsFromTestCase(RerankerToolTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出结果统计
    print("\n" + "=" * 80)
    print("📊 测试结果统计")
    print("=" * 80)
    print(f"运行测试: {result.testsRun}")
    print(f"失败测试: {len(result.failures)}")
    print(f"错误测试: {len(result.errors)}")
    print(f"跳过测试: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n❌ 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
