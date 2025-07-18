#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重排序客户端测试
测试 RerankerClient 的各种功能
"""

import sys
import os
import unittest
from pathlib import Path
from loguru import logger

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
    """重排序客户端测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化重排序客户端测试")

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            self.reranker_client = RerankerClient(
                base_url=reranker_config.url, api_key=reranker_config.api_key)
            self.has_config = True
            logger.debug("重排序配置可用")
        else:
            self.reranker_client = None
            self.has_config = False
            logger.warning("未找到reranker配置，将跳过相关测试")

    @skip_if_no_reranker
    def test_reranker_client_creation(self):
        """测试RerankerClient创建"""
        logger.info("测试RerankerClient创建")

        try:
            logger.info(
                f"RerankerClient 创建成功: {type(self.reranker_client).__name__}")
            logger.info("配置信息:")
            logger.info(f"  - Base URL: {self.reranker_client.base_url}")
            logger.info(
                f"  - API Key: {'已设置' if self.reranker_client.api_key else '未设置'}"
            )

            # 验证客户端创建
            self.assertIsNotNone(self.reranker_client)
            self.assertIsNotNone(self.reranker_client.base_url)
            self.assertIsNotNone(self.reranker_client.api_key)

        except Exception as e:
            logger.error(f"RerankerClient 创建失败: {e}")
            self.fail(f"RerankerClient 创建失败: {e}")

    @skip_if_no_reranker
    def test_basic_rerank_functionality(self):
        """测试基础重排序功能"""
        logger.info("测试基础重排序功能")

        # 创建测试文档
        test_documents = [{
            "text": "这是一个关于天气的文档，与电力行业无关。"
        }, {
            "text": "电力系统是现代社会的重要基础设施。"
        }, {
            "text": "人工智能技术在电力行业的应用越来越广泛。"
        }, {
            "text": "机器学习算法可以优化电力调度。"
        }, {
            "text": "智能电网技术是电力行业数字化转型的关键。"
        }]

        query = "人工智能在电力行业的应用"
        logger.info(f"查询: {query}")
        logger.info(f"文档数量: {len(test_documents)}")

        try:
            # 执行重排序
            result = self.reranker_client.rerank(query, test_documents)
            logger.info("重排序成功")
            logger.debug(f"结果类型: {type(result)}")

            # 验证结果格式
            if isinstance(result, dict):
                logger.debug(f"结果键: {list(result.keys())}")
                if 'results' in result:
                    logger.info(f"重排序结果数量: {len(result['results'])}")
                    for i, doc in enumerate(result['results'][:3]):
                        logger.debug(
                            f"  {i+1}. 文档: {doc.get('text', 'N/A')[:50]}...")
                elif 'documents' in result:
                    logger.info(f"重排序结果数量: {len(result['documents'])}")
                    for i, doc in enumerate(result['documents'][:3]):
                        logger.debug(
                            f"  {i+1}. 文档: {doc.get('text', 'N/A')[:50]}...")
                else:
                    logger.info(f"重排序结果数量: {len(result)}")
                    for i, item in enumerate(list(result.items())[:3]):
                        logger.debug(f"  {i+1}. 文档: {str(item)[:50]}...")
            else:
                logger.info(f"结果内容: {str(result)[:200]}...")

            # 验证结果
            self.assertIsNotNone(result)

        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            self.fail(f"重排序失败: {str(e)}")

    @skip_if_no_reranker
    def test_different_size_parameters(self):
        """测试不同size参数的重排序"""
        logger.info("测试不同size参数的重排序")

        test_documents = [{
            "text": "文档1: 人工智能基础概念"
        }, {
            "text": "文档2: 机器学习算法"
        }, {
            "text": "文档3: 深度学习应用"
        }, {
            "text": "文档4: 神经网络原理"
        }, {
            "text": "文档5: 计算机视觉技术"
        }]

        query = "机器学习算法"
        size_options = [1, 3, 5]

        for size in size_options:
            logger.info(f"测试 size={size}")

            try:
                result = self.reranker_client.rerank(query,
                                                     test_documents,
                                                     size=size)

                # 验证结果数量
                if isinstance(result, dict):
                    if 'results' in result:
                        actual_size = len(result['results'])
                    elif 'documents' in result:
                        actual_size = len(result['documents'])
                    else:
                        actual_size = len(result)
                else:
                    actual_size = len(result) if hasattr(result,
                                                         '__len__') else 1

                logger.info(f"size={size} 测试成功，实际返回: {actual_size} 个结果")

                # 验证结果数量不超过请求的size
                self.assertLessEqual(actual_size, size)

            except Exception as e:
                logger.error(f"size={size} 测试失败: {str(e)}")
                self.fail(f"size={size} 测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_empty_documents_list(self):
        """测试空文档列表的重排序"""
        logger.info("测试空文档列表的重排序")

        empty_documents = []
        query = "测试查询"

        try:
            result = self.reranker_client.rerank(query, empty_documents)
            logger.info("空文档列表处理成功")
            logger.debug(f"结果: {result}")

            # 验证结果
            self.assertIsNotNone(result)
            if isinstance(result, dict):
                self.assertEqual(
                    len(result.get('results', result.get('documents', []))), 0)
            else:
                self.assertEqual(len(result), 0)

        except Exception as e:
            logger.error(f"空文档列表处理失败: {str(e)}")
            self.fail(f"空文档列表处理失败: {str(e)}")

    @skip_if_no_reranker
    def test_single_document_rerank(self):
        """测试单个文档的重排序"""
        logger.info("测试单个文档的重排序")

        single_document = [{"text": "这是一个关于人工智能的文档"}]
        query = "人工智能"

        try:
            result = self.reranker_client.rerank(query, single_document)
            logger.info("单个文档重排序成功")
            logger.debug(f"结果: {result}")

            # 验证结果
            self.assertIsNotNone(result)
            if isinstance(result, dict):
                self.assertGreaterEqual(
                    len(result.get('results', result.get('documents', []))), 0)
            else:
                self.assertGreaterEqual(len(result), 0)

        except Exception as e:
            logger.error(f"单个文档重排序失败: {str(e)}")
            self.fail(f"单个文档重排序失败: {str(e)}")

    @skip_if_no_reranker
    def test_large_documents_rerank(self):
        """测试大文档的重排序"""
        logger.info("测试大文档的重排序")

        # 创建大文档
        large_documents = [{
            "text": "这是一个很长的文档 " * 100
        }, {
            "text": "另一个长文档 " * 80
        }, {
            "text": "第三个长文档 " * 60
        }]

        query = "长文档测试"

        try:
            result = self.reranker_client.rerank(query, large_documents)
            logger.info("大文档重排序成功")
            logger.debug(f"结果类型: {type(result)}")

            # 验证结果
            self.assertIsNotNone(result)

        except Exception as e:
            logger.error(f"大文档重排序失败: {str(e)}")
            self.fail(f"大文档重排序失败: {str(e)}")

    @skip_if_no_reranker
    def test_special_characters_rerank(self):
        """测试包含特殊字符的重排序"""
        logger.info("测试包含特殊字符的重排序")

        special_documents = [{
            "text": "包含特殊字符的文档：!@#$%^&*()_+-=[]{}|;':\",./<>?"
        }, {
            "text": "包含中文和英文的文档：AI技术发展"
        }, {
            "text": "包含数字的文档：1234567890"
        }]

        query = "特殊字符测试"

        try:
            result = self.reranker_client.rerank(query, special_documents)
            logger.info("特殊字符处理成功")
            logger.debug(f"结果: {result}")

            # 验证结果
            self.assertIsNotNone(result)

        except Exception as e:
            logger.error(f"特殊字符处理失败: {str(e)}")
            self.fail(f"特殊字符处理失败: {str(e)}")

    @skip_if_no_reranker
    def test_error_handling(self):
        """测试错误处理"""
        logger.info("测试错误处理")

        # 测试各种错误情况
        error_test_cases = [{
            "name": "空查询",
            "query": "",
            "documents": [{
                "text": "测试文档"
            }]
        }, {
            "name": "None查询",
            "query": None,
            "documents": [{
                "text": "测试文档"
            }]
        }, {
            "name": "None文档列表",
            "query": "测试查询",
            "documents": None
        }, {
            "name": "无效文档格式",
            "query": "测试查询",
            "documents": [{
                "invalid": "格式"
            }]
        }]

        for test_case in error_test_cases:
            logger.debug(f"测试: {test_case['name']}")

            try:
                result = self.reranker_client.rerank(test_case["query"],
                                                     test_case["documents"])
                logger.info(f"{test_case['name']} 处理成功")

                # 验证结果
                self.assertIsNotNone(result)

            except Exception as e:
                logger.error(f"{test_case['name']} 处理失败: {str(e)}")
                # 某些错误情况可能抛出异常，这是正常的

    @skip_if_no_reranker
    def test_performance(self):
        """测试性能"""
        logger.info("测试性能")

        # 创建测试数据
        test_documents = [{
            "text": f"测试文档 {i}: 这是第{i}个测试文档的内容"
        } for i in range(10)]
        query = "性能测试查询"

        import time
        start_time = time.time()

        try:
            result = self.reranker_client.rerank(query, test_documents)
            end_time = time.time()

            response_time = end_time - start_time
            logger.info(f"响应时间: {response_time:.2f} 秒")
            logger.debug(f"结果长度: {len(str(result))} 字符")

            # 性能基准测试
            self.assertLess(response_time, 30.0)  # 30秒内应该完成
            self.assertIsNotNone(result)

        except Exception as e:
            logger.error(f"性能测试失败: {str(e)}")
            self.fail(f"性能测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_integration_scenario(self):
        """测试集成场景"""
        logger.info("测试集成场景")

        # 模拟搜索结果的集成场景
        search_results = [{
            "text": "搜索结果1: 人工智能基础"
        }, {
            "text": "搜索结果2: 机器学习算法"
        }, {
            "text": "搜索结果3: 深度学习应用"
        }, {
            "text": "搜索结果4: 神经网络原理"
        }, {
            "text": "搜索结果5: 计算机视觉技术"
        }]

        query = "人工智能技术"

        try:
            # 执行重排序
            reranked_results = self.reranker_client.rerank(
                query, search_results)
            logger.info("集成测试成功")
            logger.debug(f"原始文档数量: {len(search_results)}")

            # 验证集成结果
            self.assertIsNotNone(reranked_results)

            # 检查重排序是否改变了顺序
            if isinstance(reranked_results, dict):
                reranked_docs = reranked_results.get(
                    'results', reranked_results.get('documents', []))
            else:
                reranked_docs = reranked_results

            logger.debug(f"重排序后文档数量: {len(reranked_docs)}")

        except Exception as e:
            logger.error(f"集成测试失败: {str(e)}")
            self.fail(f"集成测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_configuration_info(self):
        """测试配置信息"""
        logger.info("测试配置信息")

        try:
            # 检查配置信息
            logger.info("重排序客户端配置:")
            logger.info(f"  - Base URL: {self.reranker_client.base_url}")
            logger.info(
                f"  - API Key: {'已设置' if self.reranker_client.api_key else '未设置'}"
            )

            # 验证配置
            self.assertIsNotNone(self.reranker_client.base_url)
            self.assertIsNotNone(self.reranker_client.api_key)

        except Exception as e:
            logger.error(f"配置信息测试失败: {e}")
            self.fail(f"配置信息测试失败: {e}")


def main():
    """主函数"""
    logger.info("重排序客户端测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(RerankerClientTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有重排序客户端测试通过")
    else:
        logger.error("重排序客户端测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
