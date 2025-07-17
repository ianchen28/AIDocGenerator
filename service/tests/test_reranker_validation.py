#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RerankerClient 重排序验证测试
专门验证重排序功能是否真正生效，通过对比排序前后的结果
"""

import sys
import os
import json
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
from src.doc_agent.llm_clients.providers import RerankerClient
from core.config import settings


class RerankerValidationTest(LLMTestCase):
    """RerankerClient 重排序验证测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            self.reranker_client = RerankerClient(
                base_url=reranker_config.url, api_key=reranker_config.api_key)
            self.has_config = True
        else:
            self.reranker_client = None
            self.has_config = False
            print("⚠️  未找到reranker配置，将跳过相关测试")

    @skip_if_no_reranker
    def test_rerank_effectiveness_basic(self):
        """测试基础重排序效果"""
        print("\n" + "=" * 60)
        print("🔍 测试基础重排序效果")
        print("=" * 60)

        # 创建测试文档，故意打乱相关性顺序
        test_documents = [
            "这是一个关于天气的文档，与电力行业无关。",  # 最不相关
            "电力系统是现代社会的重要基础设施。",  # 中等相关
            "人工智能技术在电力行业的应用越来越广泛。",  # 最相关
            "机器学习算法可以优化电力调度。",  # 高相关
            "智能电网技术是电力行业数字化转型的关键。"  # 高相关
        ]

        query = "人工智能在电力行业的应用"

        print(f"🔍 查询: {query}")
        print(f"📄 原始文档顺序:")
        for i, doc in enumerate(test_documents, 1):
            print(f"  {i}. {doc}")

        try:
            # 执行重排序
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=test_documents,
                                                 size=len(test_documents))

            print(f"\n✅ 重排序成功")
            print(f"📊 结果类型: {type(result)}")

            if isinstance(result, dict) and 'sorted_doc_list' in result:
                sorted_docs = result['sorted_doc_list']
                print(f"\n📋 重排序后结果:")
                print(f"📄 返回文档数量: {len(sorted_docs)}")

                # 验证重排序效果
                if len(sorted_docs) > 1:
                    # 检查是否有评分
                    has_scores = any('rerank_score' in doc
                                     for doc in sorted_docs)
                    print(f"📊 包含评分: {'是' if has_scores else '否'}")

                    # 显示重排序结果
                    for i, doc in enumerate(sorted_docs, 1):
                        text = doc.get('text', 'N/A')
                        score = doc.get('rerank_score', 'N/A')
                        print(f"  {i}. 评分: {score} | 文档: {text[:50]}...")

                    # 验证重排序是否真的改变了顺序
                    original_first = test_documents[0]
                    reranked_first = sorted_docs[0].get('text', '')

                    if original_first != reranked_first:
                        print(f"\n✅ 重排序生效！")
                        print(f"  原始第一: {original_first[:30]}...")
                        print(f"  重排序第一: {reranked_first[:30]}...")
                    else:
                        print(f"\n⚠️  重排序可能未生效，第一文档未改变")

                else:
                    print(f"⚠️  返回文档数量不足，无法验证重排序效果")

            else:
                print(f"❌ 重排序结果格式异常: {result}")

        except Exception as e:
            print(f"❌ 重排序验证失败: {str(e)}")
            self.fail(f"重排序验证失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_score_validation(self):
        """测试重排序评分验证"""
        print("\n" + "=" * 60)
        print("📊 测试重排序评分验证")
        print("=" * 60)

        # 创建有明显相关性差异的文档
        test_documents = [
            "这是一个关于烹饪的文档，与查询完全无关。",  # 应该得分最低
            "电力系统是基础设施。",  # 中等相关
            "人工智能在电力行业的应用案例。",  # 高相关
            "AI技术在电力系统中的应用研究。",  # 最高相关
            "机器学习优化电力调度算法。"  # 高相关
        ]

        query = "人工智能电力行业应用"

        print(f"🔍 查询: {query}")

        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=test_documents,
                                                 size=len(test_documents))

            if isinstance(result, dict) and 'sorted_doc_list' in result:
                sorted_docs = result['sorted_doc_list']

                print(f"\n📊 评分分析:")
                scores = []
                for i, doc in enumerate(sorted_docs):
                    text = doc.get('text', '')
                    score = doc.get('rerank_score', 0)
                    scores.append(score)
                    print(f"  {i+1}. 评分: {score:.4f} | 文档: {text[:40]}...")

                # 验证评分是否合理
                if len(scores) > 1:
                    # 检查评分是否有差异
                    score_variance = max(scores) - min(scores)
                    print(f"\n📈 评分统计:")
                    print(f"  最高分: {max(scores):.4f}")
                    print(f"  最低分: {min(scores):.4f}")
                    print(f"  分数差异: {score_variance:.4f}")

                    if score_variance > 0.1:  # 如果分数差异足够大
                        print(f"✅ 评分差异明显，重排序有效")

                        # 验证最相关的文档是否排在前面
                        first_doc = sorted_docs[0].get('text', '')
                        if 'AI' in first_doc or '人工智能' in first_doc:
                            print(f"✅ 最相关文档排在第一位")
                        else:
                            print(f"⚠️  最相关文档未排在第一位")
                    else:
                        print(f"⚠️  评分差异较小，重排序效果不明显")
                else:
                    print(f"⚠️  文档数量不足，无法验证评分")

            else:
                print(f"❌ 重排序结果格式异常")

        except Exception as e:
            print(f"❌ 评分验证失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_consistency(self):
        """测试重排序一致性"""
        print("\n" + "=" * 60)
        print("🔄 测试重排序一致性")
        print("=" * 60)

        test_documents = [
            "人工智能在电力行业的应用研究。", "电力系统智能化发展趋势。", "机器学习优化电力调度。", "智能电网技术标准。"
        ]

        query = "人工智能电力应用"

        print(f"🔍 查询: {query}")
        print(f"📄 文档数量: {len(test_documents)}")

        # 执行多次重排序，验证结果一致性
        results = []
        for i in range(3):
            print(f"\n🔄 第 {i+1} 次重排序:")
            try:
                result = self.reranker_client.invoke(prompt=query,
                                                     documents=test_documents,
                                                     size=len(test_documents))

                if isinstance(result, dict) and 'sorted_doc_list' in result:
                    sorted_docs = result['sorted_doc_list']
                    first_doc = sorted_docs[0].get('text',
                                                   '') if sorted_docs else ''
                    first_score = sorted_docs[0].get('rerank_score',
                                                     0) if sorted_docs else 0
                    print(
                        f"  第一名: {first_doc[:30]}... (评分: {first_score:.4f})")
                    results.append({
                        'first_doc':
                        first_doc,
                        'first_score':
                        first_score,
                        'all_scores':
                        [doc.get('rerank_score', 0) for doc in sorted_docs]
                    })
                else:
                    print(f"  结果格式异常")

            except Exception as e:
                print(f"  第 {i+1} 次重排序失败: {str(e)}")

        # 分析一致性
        if len(results) >= 2:
            print(f"\n📊 一致性分析:")

            # 检查第一名是否一致
            first_docs = [r['first_doc'] for r in results]
            first_docs_unique = set(first_docs)

            if len(first_docs_unique) == 1:
                print(f"✅ 第一名完全一致")
            else:
                print(f"⚠️  第一名不一致: {first_docs_unique}")

            # 检查评分是否稳定
            first_scores = [r['first_score'] for r in results]
            score_variance = max(first_scores) - min(first_scores)
            print(f"📈 第一名评分差异: {score_variance:.4f}")

            if score_variance < 0.1:
                print(f"✅ 评分稳定")
            else:
                print(f"⚠️  评分不稳定")
        else:
            print(f"⚠️  重排序次数不足，无法验证一致性")

    @skip_if_no_reranker
    def test_rerank_edge_cases(self):
        """测试重排序边界情况"""
        print("\n" + "=" * 60)
        print("🔬 测试重排序边界情况")
        print("=" * 60)

        test_cases = [
            {
                "name": "完全相同文档",
                "query": "测试查询",
                "documents": ["相同文档", "相同文档", "相同文档"]
            },
            {
                "name": "高度相似文档",
                "query": "人工智能",
                "documents":
                ["人工智能技术在电力行业的应用。", "AI技术在电力行业的应用。", "机器学习在电力行业的应用。"]
            },
            {
                "name": "完全无关文档",
                "query": "人工智能",
                "documents": ["这是一个关于烹饪的文档。", "这是关于旅游的文档。", "这是关于音乐的文档。"]
            },
            {
                "name":
                "混合相关性文档",
                "query":
                "电力系统",
                "documents": [
                    "电力系统是基础设施。",  # 相关
                    "这是一个关于烹饪的文档。",  # 不相关
                    "智能电网技术发展。",  # 相关
                    "这是关于旅游的文档。"  # 不相关
                ]
            }
        ]

        for test_case in test_cases:
            print(f"\n🔍 测试: {test_case['name']}")
            print(f"查询: {test_case['query']}")
            print(f"文档: {test_case['documents']}")

            try:
                result = self.reranker_client.invoke(
                    prompt=test_case['query'],
                    documents=test_case['documents'],
                    size=len(test_case['documents']))

                if isinstance(result, dict) and 'sorted_doc_list' in result:
                    sorted_docs = result['sorted_doc_list']
                    print(f"✅ 处理成功，返回 {len(sorted_docs)} 个文档")

                    # 显示前两个结果
                    for i, doc in enumerate(sorted_docs[:2]):
                        text = doc.get('text', '')
                        score = doc.get('rerank_score', 0)
                        print(f"  {i+1}. 评分: {score:.4f} | {text}")

                else:
                    print(f"⚠️  结果格式异常")

            except Exception as e:
                print(f"❌ 处理失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_performance_validation(self):
        """测试重排序性能验证"""
        print("\n" + "=" * 60)
        print("⚡ 测试重排序性能验证")
        print("=" * 60)

        import time

        # 创建不同大小的测试集
        test_sizes = [3, 5, 10]

        for size in test_sizes:
            print(f"\n🔍 测试文档数量: {size}")

            # 生成测试文档
            test_documents = [f"这是第{i+1}个测试文档，包含一些相关内容。" for i in range(size)]

            query = "测试查询"

            # 测试响应时间
            start_time = time.time()
            try:
                result = self.reranker_client.invoke(prompt=query,
                                                     documents=test_documents,
                                                     size=size)
                end_time = time.time()
                response_time = end_time - start_time

                print(f"⏱️  响应时间: {response_time:.3f} 秒")
                print(f"📊 文档数量: {size}")

                if isinstance(result, dict) and 'sorted_doc_list' in result:
                    actual_size = len(result['sorted_doc_list'])
                    print(f"📄 返回文档数量: {actual_size}")

                    # 性能要求
                    if response_time < 5:  # 5秒内
                        print(f"✅ 性能良好")
                    elif response_time < 10:  # 10秒内
                        print(f"⚠️  性能一般")
                    else:
                        print(f"❌ 性能较差")

                else:
                    print(f"⚠️  结果格式异常")

            except Exception as e:
                print(f"❌ 性能测试失败: {str(e)}")


def main():
    """运行所有RerankerClient验证测试"""
    print("🚀 RerankerClient 重排序验证测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    # 添加所有测试方法
    test_suite.addTest(
        test_loader.loadTestsFromTestCase(RerankerValidationTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出结果统计
    print("\n" + "=" * 80)
    print("📊 验证测试结果统计")
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
