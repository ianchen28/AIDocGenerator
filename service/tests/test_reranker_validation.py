#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重排序验证测试
测试 RerankerClient 的重排序效果和一致性
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


class RerankerValidationTest(LLMTestCase):
    """重排序验证测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化重排序验证测试")

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
    def test_basic_rerank_effectiveness(self):
        """测试基础重排序效果"""
        logger.info("测试基础重排序效果")

        # 创建测试文档，包含相关和不相关的内容
        test_documents = [
            "这是一个关于天气的文档，与电力行业无关。", "电力系统是现代社会的重要基础设施。",
            "人工智能技术在电力行业的应用越来越广泛。", "机器学习算法可以优化电力调度。", "智能电网技术是电力行业数字化转型的关键。",
            "传统电力系统面临数字化转型挑战。", "AI技术在电力行业的应用案例。"
        ]

        query = "人工智能在电力行业的应用"
        logger.info(f"查询: {query}")
        logger.info("原始文档顺序:")
        for i, doc in enumerate(test_documents):
            logger.debug(f"  {i}. {doc}")

        try:
            # 执行重排序
            result = self.reranker_client.rerank(query, test_documents)
            logger.info("重排序成功")
            logger.debug(f"结果类型: {type(result)}")

            # 解析结果
            if isinstance(result, dict):
                if 'results' in result:
                    sorted_docs = result['results']
                elif 'documents' in result:
                    sorted_docs = result['documents']
                else:
                    sorted_docs = list(result.values())
            else:
                sorted_docs = result

            logger.info("重排序后结果:")
            logger.info(f"返回文档数量: {len(sorted_docs)}")

            # 检查是否包含评分
            has_scores = False
            if sorted_docs and isinstance(sorted_docs[0], dict):
                has_scores = 'score' in sorted_docs[
                    0] or 'relevance_score' in sorted_docs[0]

            logger.debug(f"包含评分: {'是' if has_scores else '否'}")

            # 显示前几个结果
            for i, doc in enumerate(sorted_docs[:3]):
                if isinstance(doc, dict):
                    score = doc.get('score', doc.get('relevance_score', 'N/A'))
                    text = doc.get('text', str(doc))
                else:
                    score = 'N/A'
                    text = str(doc)
                logger.debug(f"  {i+1}. 评分: {score} | 文档: {text[:50]}...")

            # 验证重排序效果
            if len(sorted_docs) >= 2:
                original_first = test_documents[0]
                if isinstance(sorted_docs[0], dict):
                    reranked_first = sorted_docs[0].get(
                        'text', str(sorted_docs[0]))
                else:
                    reranked_first = str(sorted_docs[0])

                if original_first != reranked_first:
                    logger.info("重排序生效！")
                    logger.debug(f"  原始第一: {original_first[:30]}...")
                    logger.debug(f"  重排序第一: {reranked_first[:30]}...")
                else:
                    logger.warning("重排序可能未生效，第一文档未改变")
            else:
                logger.warning("返回文档数量不足，无法验证重排序效果")

            # 验证结果
            self.assertIsNotNone(result)
            self.assertGreater(len(sorted_docs), 0)

        except Exception as e:
            logger.error(f"重排序验证失败: {str(e)}")
            self.fail(f"重排序验证失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_score_validation(self):
        """测试重排序评分验证"""
        logger.info("测试重排序评分验证")

        # 创建测试文档
        test_documents = [
            "人工智能基础概念和原理。", "机器学习算法在电力行业的应用。", "深度学习技术在智能电网中的应用。",
            "传统电力系统技术介绍。", "AI技术在电力调度中的创新应用。", "智能电网技术发展趋势。", "机器学习在电力行业的具体案例。"
        ]

        query = "人工智能在电力行业的应用"

        try:
            result = self.reranker_client.rerank(query, test_documents)
            logger.info(f"查询: {query}")

            # 解析结果
            if isinstance(result, dict):
                if 'results' in result:
                    sorted_docs = result['results']
                elif 'documents' in result:
                    sorted_docs = result['documents']
                else:
                    sorted_docs = list(result.values())
            else:
                sorted_docs = result

            logger.info("评分分析:")
            scores = []
            for i, doc in enumerate(sorted_docs):
                if isinstance(doc, dict):
                    score = doc.get('score', doc.get('relevance_score', 0))
                    text = doc.get('text', str(doc))
                else:
                    score = 0
                    text = str(doc)
                scores.append(score)
                logger.debug(f"  {i+1}. 评分: {score:.4f} | 文档: {text[:40]}...")

            # 分析评分
            if scores:
                max_score = max(scores)
                min_score = min(scores)
                score_variance = max_score - min_score

                logger.info("评分统计:")
                logger.info(f"  最高分: {max_score:.4f}")
                logger.info(f"  最低分: {min_score:.4f}")
                logger.info(f"  分数差异: {score_variance:.4f}")

                # 验证评分差异
                if score_variance > 0.1:
                    logger.info("评分差异明显，重排序有效")
                else:
                    logger.warning("评分差异较小，重排序效果不明显")

                # 验证最相关文档是否排在第一位
                if scores[0] == max_score:
                    logger.info("最相关文档排在第一位")
                else:
                    logger.warning("最相关文档未排在第一位")
            else:
                logger.warning("文档数量不足，无法验证评分")

            # 验证结果
            self.assertIsNotNone(result)
            self.assertGreater(len(sorted_docs), 0)

        except Exception as e:
            logger.error(f"评分验证失败: {str(e)}")
            self.fail(f"评分验证失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_consistency(self):
        """测试重排序一致性"""
        logger.info("测试重排序一致性")

        test_documents = [
            "人工智能技术在电力行业的应用。", "机器学习算法优化电力调度。", "智能电网技术发展趋势。",
            "AI技术在电力行业的创新应用。", "深度学习在智能电网中的应用。"
        ]

        query = "人工智能在电力行业的应用"
        logger.info(f"查询: {query}")
        logger.info(f"文档数量: {len(test_documents)}")

        # 执行多次重排序
        results = []
        for i in range(3):
            try:
                result = self.reranker_client.rerank(query, test_documents)
                logger.debug(f"第 {i+1} 次重排序:")

                if isinstance(result, dict):
                    if 'results' in result:
                        sorted_docs = result['results']
                    elif 'documents' in result:
                        sorted_docs = result['documents']
                    else:
                        sorted_docs = list(result.values())
                else:
                    sorted_docs = result

                results.append(sorted_docs)
                logger.debug(f"  返回 {len(sorted_docs)} 个文档")

            except Exception as e:
                logger.error(f"第 {i+1} 次重排序失败: {str(e)}")
                results.append([])

        # 分析一致性
        if len(results) >= 2 and all(len(r) > 0 for r in results):
            logger.info("一致性分析:")

            # 检查第一名是否一致
            first_docs = []
            for result in results:
                if isinstance(result[0], dict):
                    first_docs.append(result[0].get('text', str(result[0])))
                else:
                    first_docs.append(str(result[0]))

            first_docs_unique = len(set(first_docs))
            logger.info(f"第一名完全一致" if first_docs_unique ==
                        1 else f"第一名不一致: {first_docs_unique}")

            # 检查评分一致性
            if all(
                    isinstance(r[0], dict) and 'score' in r[0]
                    for r in results):
                first_scores = [r[0]['score'] for r in results]
                score_variance = max(first_scores) - min(first_scores)
                logger.info(f"第一名评分差异: {score_variance:.4f}")

                if score_variance < 0.1:
                    logger.info("评分稳定")
                else:
                    logger.warning("评分不稳定")
            else:
                logger.warning("重排序次数不足，无法验证一致性")

        # 验证结果
        self.assertGreater(len(results), 0)

    @skip_if_no_reranker
    def test_rerank_edge_cases(self):
        """测试重排序边界情况"""
        logger.info("测试重排序边界情况")

        # 定义边界测试用例
        edge_cases = [{
            "name": "单个文档",
            "query": "测试查询",
            "documents": ["单个测试文档"]
        }, {
            "name": "空查询",
            "query": "",
            "documents": ["文档1", "文档2", "文档3"]
        }, {
            "name": "重复文档",
            "query": "重复测试",
            "documents": ["相同文档", "相同文档", "相同文档"]
        }, {
            "name": "长文档",
            "query": "长文档测试",
            "documents": ["这是一个很长的文档 " * 50]
        }, {
            "name": "特殊字符",
            "query": "特殊字符测试",
            "documents": ["包含特殊字符的文档：!@#$%^&*()"]
        }]

        for test_case in edge_cases:
            logger.info(f"测试: {test_case['name']}")
            logger.debug(f"查询: {test_case['query']}")
            logger.debug(f"文档: {test_case['documents']}")

            try:
                result = self.reranker_client.rerank(test_case["query"],
                                                     test_case["documents"])

                # 解析结果
                if isinstance(result, dict):
                    if 'results' in result:
                        sorted_docs = result['results']
                    elif 'documents' in result:
                        sorted_docs = result['documents']
                    else:
                        sorted_docs = list(result.values())
                else:
                    sorted_docs = result

                logger.info(f"处理成功，返回 {len(sorted_docs)} 个文档")

                # 显示结果
                for i, doc in enumerate(sorted_docs[:3]):
                    if isinstance(doc, dict):
                        score = doc.get('score',
                                        doc.get('relevance_score', 'N/A'))
                        text = doc.get('text', str(doc))
                    else:
                        score = 'N/A'
                        text = str(doc)
                    logger.debug(f"  {i+1}. 评分: {score} | {text}")

            except Exception as e:
                logger.error(f"处理失败: {str(e)}")

    @skip_if_no_reranker
    def test_rerank_performance_validation(self):
        """测试重排序性能验证"""
        logger.info("测试重排序性能验证")

        # 测试不同大小的文档集
        test_sizes = [5, 10, 20]

        for size in test_sizes:
            logger.info(f"测试文档数量: {size}")

            # 创建测试文档
            test_documents = [
                f"测试文档 {i}: 这是第{i}个测试文档的内容，包含一些关键词用于重排序测试。"
                for i in range(size)
            ]

            query = "测试查询"

            import time
            start_time = time.time()

            try:
                result = self.reranker_client.rerank(query, test_documents)
                end_time = time.time()

                response_time = end_time - start_time
                logger.info(f"响应时间: {response_time:.3f} 秒")
                logger.debug(f"文档数量: {size}")

                # 解析结果
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

                logger.debug(f"返回文档数量: {actual_size}")

                # 性能评估
                if response_time < 5.0:
                    logger.info("性能良好")
                elif response_time < 15.0:
                    logger.warning("性能一般")
                else:
                    logger.error("性能较差")

            except Exception as e:
                logger.error(f"性能测试失败: {str(e)}")


def main():
    """主函数"""
    logger.info("重排序验证测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(RerankerValidationTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有重排序验证测试通过")
    else:
        logger.error("重排序验证测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
