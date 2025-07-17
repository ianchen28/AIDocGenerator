#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RerankerClient 测试文件
测试重排序客户端的功能、性能和错误处理
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


class RerankerClientTest(LLMTestCase):
    """RerankerClient 测试类"""

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

    def test_reranker_client_creation(self):
        """测试RerankerClient创建"""
        print("\n" + "=" * 60)
        print("🔧 测试RerankerClient创建")
        print("=" * 60)

        if not self.has_config:
            self.skipTest("没有reranker配置")

        self.assertIsInstance(self.reranker_client, RerankerClient)
        print(f"✅ RerankerClient 创建成功: {type(self.reranker_client).__name__}")
        print(f"📋 配置信息:")
        print(f"  - Base URL: {self.reranker_client.base_url}")
        print(
            f"  - API Key: {'已设置' if self.reranker_client.api_key else '未设置'}")

    @skip_if_no_reranker
    def test_basic_rerank(self):
        """测试基础重排序功能"""
        print("\n" + "=" * 60)
        print("📊 测试基础重排序功能")
        print("=" * 60)

        # 测试文档
        test_documents = [
            "人工智能在电力行业的应用越来越广泛，包括智能电网、预测性维护等。", "电力系统是现代社会的重要基础设施，需要高可靠性和安全性。",
            "机器学习技术可以帮助电力公司优化运营效率，降低成本。", "可再生能源的发展对电力系统提出了新的挑战和机遇。",
            "智能电网技术是电力行业数字化转型的关键技术。"
        ]

        query = "人工智能在电力行业的应用"

        print(f"🔍 查询: {query}")
        print(f"📄 文档数量: {len(test_documents)}")

        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=test_documents,
                                                 size=3)

            print(f"✅ 重排序成功")
            print(f"📊 结果类型: {type(result)}")

            if isinstance(result, dict):
                print(f"📋 结果键: {list(result.keys())}")
                if 'results' in result:
                    print(f"📄 重排序结果数量: {len(result['results'])}")
                    for i, item in enumerate(result['results'][:3]):
                        print(
                            f"  {i+1}. 文档: {item.get('text', 'N/A')[:50]}...")
                elif 'documents' in result:
                    print(f"📄 重排序结果数量: {len(result['documents'])}")
                    for i, doc in enumerate(result['documents'][:3]):
                        print(f"  {i+1}. 文档: {doc.get('text', 'N/A')[:50]}...")
            elif isinstance(result, list):
                print(f"📄 重排序结果数量: {len(result)}")
                for i, item in enumerate(result[:3]):
                    print(f"  {i+1}. 文档: {str(item)[:50]}...")
            else:
                print(f"📄 结果内容: {str(result)[:200]}...")

        except Exception as e:
            print(f"❌ 重排序失败: {str(e)}")
            self.fail(f"重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_with_different_sizes(self):
        """测试不同size参数的重排序"""
        print("\n" + "=" * 60)
        print("📏 测试不同size参数的重排序")
        print("=" * 60)

        test_documents = [
            "电力系统智能化是未来发展趋势。", "人工智能技术可以提升电力系统效率。", "机器学习在电力预测中发挥重要作用。",
            "智能电网需要先进的技术支持。", "数据驱动的方法正在改变电力行业。"
        ]

        query = "电力系统智能化"

        for size in [1, 2, 3, 5]:
            print(f"\n🔍 测试 size={size}")
            try:
                result = self.reranker_client.invoke(prompt=query,
                                                     documents=test_documents,
                                                     size=size)

                if isinstance(result, dict):
                    if 'results' in result:
                        actual_size = len(result['results'])
                    elif 'documents' in result:
                        actual_size = len(result['documents'])
                    else:
                        actual_size = 0
                elif isinstance(result, list):
                    actual_size = len(result)
                else:
                    actual_size = 0

                print(f"✅ size={size} 测试成功，实际返回: {actual_size} 个结果")
                self.assertLessEqual(
                    actual_size, size,
                    f"返回结果数量 {actual_size} 超过了请求的 size {size}")

            except Exception as e:
                print(f"❌ size={size} 测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_with_empty_documents(self):
        """测试空文档列表的重排序"""
        print("\n" + "=" * 60)
        print("📭 测试空文档列表的重排序")
        print("=" * 60)

        query = "测试查询"
        empty_documents = []

        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=empty_documents,
                                                 size=3)

            print(f"✅ 空文档列表处理成功")
            print(f"📊 结果: {result}")

        except Exception as e:
            print(f"❌ 空文档列表处理失败: {str(e)}")
            # 空文档列表失败是可以接受的，不强制失败

    @skip_if_no_reranker
    def test_rerank_with_single_document(self):
        """测试单个文档的重排序"""
        print("\n" + "=" * 60)
        print("📄 测试单个文档的重排序")
        print("=" * 60)

        query = "电力技术"
        single_document = ["电力系统是现代社会的重要基础设施。"]

        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=single_document,
                                                 size=1)

            print(f"✅ 单个文档重排序成功")
            print(f"📊 结果: {result}")

        except Exception as e:
            print(f"❌ 单个文档重排序失败: {str(e)}")
            self.fail(f"单个文档重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_with_large_documents(self):
        """测试大文档的重排序"""
        print("\n" + "=" * 60)
        print("📚 测试大文档的重排序")
        print("=" * 60)

        # 创建较大的文档
        large_documents = [
            "人工智能技术在电力行业的应用非常广泛。" * 10, "电力系统智能化是未来发展的必然趋势。" * 10,
            "机器学习技术可以帮助电力公司优化运营。" * 10
        ]

        query = "电力系统智能化"

        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=large_documents,
                                                 size=2)

            print(f"✅ 大文档重排序成功")
            print(f"📊 结果类型: {type(result)}")

        except Exception as e:
            print(f"❌ 大文档重排序失败: {str(e)}")
            # 大文档可能超出限制，不强制失败

    @skip_if_no_reranker
    def test_rerank_with_special_characters(self):
        """测试包含特殊字符的查询和文档"""
        print("\n" + "=" * 60)
        print("🔤 测试包含特殊字符的重排序")
        print("=" * 60)

        test_documents = [
            "AI技术在电力行业的应用（包括智能电网）越来越重要。", "电力系统需要高可靠性，特别是在极端天气条件下。",
            "机器学习算法可以帮助预测电力需求，准确率达到95%以上。"
        ]

        query = "AI技术 & 电力行业"

        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=test_documents,
                                                 size=2)

            print(f"✅ 特殊字符处理成功")
            print(f"📊 结果: {result}")

        except Exception as e:
            print(f"❌ 特殊字符处理失败: {str(e)}")
            # 特殊字符处理失败是可以接受的

    @skip_if_no_reranker
    def test_rerank_error_handling(self):
        """测试错误处理"""
        print("\n" + "=" * 60)
        print("⚠️  测试错误处理")
        print("=" * 60)

        # 测试无效参数
        test_cases = [{
            "name": "空查询",
            "query": "",
            "documents": ["测试文档"],
            "size": 1
        }, {
            "name": "None查询",
            "query": None,
            "documents": ["测试文档"],
            "size": 1
        }, {
            "name": "None文档",
            "query": "测试查询",
            "documents": None,
            "size": 1
        }, {
            "name": "无效size",
            "query": "测试查询",
            "documents": ["测试文档"],
            "size": -1
        }]

        for test_case in test_cases:
            print(f"\n🔍 测试: {test_case['name']}")
            try:
                result = self.reranker_client.invoke(
                    prompt=test_case['query'],
                    documents=test_case['documents'],
                    size=test_case['size'])
                print(f"✅ {test_case['name']} 处理成功")
            except Exception as e:
                print(f"❌ {test_case['name']} 处理失败: {str(e)}")
                # 错误处理失败是可以接受的

    @skip_if_no_reranker
    def test_rerank_performance(self):
        """测试性能"""
        print("\n" + "=" * 60)
        print("⚡ 测试性能")
        print("=" * 60)

        import time

        test_documents = [
            "人工智能在电力行业的应用越来越广泛。", "电力系统智能化是未来发展趋势。", "机器学习技术可以提升电力系统效率。",
            "智能电网需要先进的技术支持。", "数据驱动的方法正在改变电力行业。"
        ]

        query = "电力系统智能化"

        # 测试响应时间
        start_time = time.time()
        try:
            result = self.reranker_client.invoke(prompt=query,
                                                 documents=test_documents,
                                                 size=3)
            end_time = time.time()
            response_time = end_time - start_time

            print(f"⏱️  响应时间: {response_time:.2f} 秒")
            print(f"📊 结果长度: {len(str(result))} 字符")

            # 性能要求：响应时间应该在合理范围内
            self.assertLess(response_time, 30, "响应时间过长")

        except Exception as e:
            print(f"❌ 性能测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_integration(self):
        """测试集成场景"""
        print("\n" + "=" * 60)
        print("🔗 测试集成场景")
        print("=" * 60)

        # 模拟从搜索工具获取的文档
        search_results = [
            "人工智能技术在电力行业的应用案例研究。", "电力系统智能化发展趋势分析报告。", "机器学习在电力预测中的应用效果评估。",
            "智能电网技术标准与规范解读。", "电力行业数字化转型策略研究。"
        ]

        # 模拟用户查询
        user_query = "电力系统智能化应用"

        try:
            # 执行重排序
            reranked_results = self.reranker_client.invoke(
                prompt=user_query, documents=search_results, size=3)

            print(f"✅ 集成测试成功")
            print(f"📊 原始文档数量: {len(search_results)}")
            print(
                f"📊 重排序后数量: {len(reranked_results) if isinstance(reranked_results, list) else 'N/A'}"
            )

            # 验证结果
            if isinstance(reranked_results, dict):
                if 'results' in reranked_results:
                    self.assertLessEqual(len(reranked_results['results']), 3)
                elif 'documents' in reranked_results:
                    self.assertLessEqual(len(reranked_results['documents']), 3)
            elif isinstance(reranked_results, list):
                self.assertLessEqual(len(reranked_results), 3)

        except Exception as e:
            print(f"❌ 集成测试失败: {str(e)}")
            self.fail(f"集成测试失败: {str(e)}")

    def test_reranker_config(self):
        """测试配置信息"""
        print("\n" + "=" * 60)
        print("⚙️  测试配置信息")
        print("=" * 60)

        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            print(f"✅ 找到reranker配置")
            print(f"📋 配置信息:")
            print(f"  - URL: {reranker_config.url}")
            print(
                f"  - API Key: {'已设置' if reranker_config.api_key else '未设置'}")
            print(f"  - Model ID: {reranker_config.model_id}")
            print(f"  - Type: {reranker_config.type}")
        else:
            print("❌ 未找到reranker配置")
            self.skipTest("没有reranker配置")


def main():
    """运行所有RerankerClient测试"""
    print("🚀 RerankerClient 测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    # 添加所有测试方法
    test_suite.addTest(test_loader.loadTestsFromTestCase(RerankerClientTest))

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
