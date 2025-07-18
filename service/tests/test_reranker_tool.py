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
from loguru import logger

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
        logger.debug("初始化 RerankerTool 测试")

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            self.reranker_tool = RerankerTool(base_url=reranker_config.url,
                                              api_key=reranker_config.api_key)
            self.has_config = True
            logger.debug("Reranker配置可用")
        else:
            self.reranker_tool = None
            self.has_config = False
            logger.warning("未找到reranker配置，将跳过相关测试")

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
        logger.info("测试 RerankerTool 基础功能")

        # 创建测试数据
        search_results = self.create_test_search_results()
        query = "人工智能在电力行业的应用"

        logger.info(f"查询: {query}")
        logger.info(f"原始搜索结果数量: {len(search_results)}")

        # 显示原始结果
        logger.info("原始搜索结果:")
        for i, result in enumerate(search_results, 1):
            logger.info(
                f"  {i}. 评分: {result.score:.3f} | {result.div_content[:50]}..."
            )

        try:
            # 执行重排序
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results)

            logger.info("重排序成功")
            logger.info(f"重排序结果数量: {len(reranked_results)}")

            # 显示重排序结果
            logger.info("重排序后结果:")
            for i, result in enumerate(reranked_results, 1):
                logger.info(
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
                    logger.info("重排序生效！最相关文档排在第一位")
                else:
                    logger.warning(f"重排序可能未生效，第一文档: {first_doc[:30]}...")

        except Exception as e:
            logger.error(f"重排序测试失败: {str(e)}")
            self.fail(f"重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_with_top_k(self):
        """测试 RerankerTool 的 top_k 功能"""
        logger.info("测试 RerankerTool top_k 功能")

        search_results = self.create_test_search_results()
        query = "人工智能电力应用"
        top_k = 3

        logger.info(f"查询: {query}")
        logger.info(f"原始结果数量: {len(search_results)}")
        logger.info(f"请求 top_k: {top_k}")

        try:
            # 执行重排序，限制返回数量
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results, top_k=top_k)

            logger.info("重排序成功")
            logger.info(f"返回结果数量: {len(reranked_results)}")

            # 显示结果
            logger.info(f"重排序结果 (top {top_k}):")
            for i, result in enumerate(reranked_results, 1):
                logger.info(
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
                logger.info("结果按重排序评分正确排序")

        except Exception as e:
            logger.error(f"top_k 测试失败: {str(e)}")
            self.fail(f"top_k 测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_effectiveness_analysis(self):
        """测试重排序效果分析"""
        logger.info("测试重排序效果分析")

        search_results = self.create_test_search_results()
        query = "电力系统技术"

        logger.info(f"查询: {query}")
        logger.info(f"原始结果数量: {len(search_results)}")

        try:
            # 执行重排序
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=search_results)

            logger.info("重排序完成，开始效果分析")

            # 分析重排序效果
            original_order = [(i, result.score)
                              for i, result in enumerate(search_results)]
            reranked_order = [(i, result.rerank_score)
                              for i, result in enumerate(reranked_results)]

            logger.info("原始排序:")
            for i, score in original_order:
                logger.info(f"  {i+1}. 文档{i+1}: {score:.3f}")

            logger.info("重排序后:")
            for i, score in reranked_order:
                logger.info(f"  {i+1}. 文档{i+1}: {score:.3f}")

            # 计算排序变化
            changes = 0
            for i in range(len(original_order)):
                if original_order[i][0] != reranked_order[i][0]:
                    changes += 1

            logger.info(f"排序变化数量: {changes}/{len(original_order)}")

            # 验证重排序结果
            self.assertEqual(len(reranked_results), len(search_results))
            self.assertIsInstance(reranked_results[0], RerankedSearchResult)

        except Exception as e:
            logger.error(f"重排序效果分析失败: {str(e)}")
            self.fail(f"重排序效果分析失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_get_top_results(self):
        """测试获取 top 结果功能"""
        logger.info("测试获取 top 结果功能")

        search_results = self.create_test_search_results()
        query = "智能电网技术"
        top_k = 2

        logger.info(f"查询: {query}")
        logger.info(f"请求 top {top_k} 结果")

        try:
            # 获取 top 结果
            top_results = self.reranker_tool.get_top_results(
                query=query, search_results=search_results, top_k=top_k)

            logger.info(f"获取到 {len(top_results)} 个 top 结果")

            # 显示 top 结果
            for i, result in enumerate(top_results, 1):
                logger.info(
                    f"  {i}. 评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                )

            # 验证结果
            self.assertLessEqual(len(top_results), top_k)
            self.assertIsInstance(top_results, list)

            if len(top_results) > 1:
                # 验证按评分排序
                for i in range(len(top_results) - 1):
                    self.assertGreaterEqual(top_results[i].rerank_score,
                                            top_results[i + 1].rerank_score)

        except Exception as e:
            logger.error(f"获取 top 结果测试失败: {str(e)}")
            self.fail(f"获取 top 结果测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_empty_results(self):
        """测试空结果处理"""
        logger.info("测试空结果处理")

        empty_results = []
        query = "测试查询"

        logger.info(f"查询: {query}")
        logger.info("输入空结果列表")

        try:
            # 测试空结果
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=empty_results)

            logger.info(f"重排序结果数量: {len(reranked_results)}")

            # 验证结果
            self.assertEqual(len(reranked_results), 0)
            self.assertIsInstance(reranked_results, list)

            # 测试获取 top 结果
            top_results = self.reranker_tool.get_top_results(
                query=query, search_results=empty_results, top_k=5)

            logger.info(f"Top 结果数量: {len(top_results)}")

            # 验证结果
            self.assertEqual(len(top_results), 0)
            self.assertIsInstance(top_results, list)

        except Exception as e:
            logger.error(f"空结果处理测试失败: {str(e)}")
            self.fail(f"空结果处理测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_reranker_tool_error_handling(self):
        """测试错误处理"""
        logger.info("测试错误处理")

        # 创建无效的查询
        invalid_query = ""
        search_results = self.create_test_search_results()

        logger.info("测试空查询")

        try:
            # 测试空查询
            reranked_results = self.reranker_tool.rerank_search_results(
                query=invalid_query, search_results=search_results)

            logger.info(f"空查询重排序结果数量: {len(reranked_results)}")

            # 验证结果
            self.assertIsInstance(reranked_results, list)

        except Exception as e:
            logger.error(f"空查询处理失败: {str(e)}")
            # 空查询可能抛出异常，这是正常的

        # 测试无效的搜索结果
        invalid_results = None
        query = "正常查询"

        logger.info("测试无效搜索结果")

        try:
            # 测试无效搜索结果
            reranked_results = self.reranker_tool.rerank_search_results(
                query=query, search_results=invalid_results)

            logger.info("无效搜索结果处理成功")

        except Exception as e:
            logger.error(f"无效搜索结果处理失败: {str(e)}")
            # 无效搜索结果应该抛出异常

        logger.info("错误处理测试完成")


def main():
    """主函数"""
    logger.info("RerankerTool 测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_instance = RerankerToolTest()
    test_instance.setUp()

    test_suite.addTest(unittest.makeSuite(RerankerToolTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有 RerankerTool 测试通过")
    else:
        logger.error("RerankerTool 测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
