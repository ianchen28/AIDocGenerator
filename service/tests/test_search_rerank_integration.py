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
from loguru import logger

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
        logger.debug("初始化搜索和重排序集成测试")

        # 获取ES配置
        es_config = settings.elasticsearch_config
        if es_config:
            self.es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                               username=es_config.username,
                                               password=es_config.password,
                                               timeout=es_config.timeout)
            self.has_es = True
            logger.debug("ES配置可用")
        else:
            self.es_search_tool = None
            self.has_es = False
            logger.warning("未找到ES配置，将跳过相关测试")

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if reranker_config:
            self.reranker_tool = RerankerTool(base_url=reranker_config.url,
                                              api_key=reranker_config.api_key)
            self.has_reranker = True
            logger.debug("Reranker配置可用")
        else:
            self.reranker_tool = None
            self.has_reranker = False
            logger.warning("未找到reranker配置，将跳过相关测试")

    @skip_if_no_reranker
    async def test_search_and_rerank_basic(self):
        """测试基础搜索和重排序功能"""
        logger.info("测试基础搜索和重排序功能")

        if not self.has_es:
            logger.error("ES配置不可用，跳过测试")
            return

        query = "人工智能电力行业应用"
        logger.info(f"查询: {query}")

        try:
            # 执行搜索和重排序
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=self.es_search_tool,
                query=query,
                query_vector=None,  # 先测试文本搜索
                reranker_tool=self.reranker_tool,
                initial_top_k=10,
                final_top_k=5)

            logger.info("搜索和重排序完成")
            logger.info(f"原始搜索结果数量: {len(search_results)}")
            logger.info(f"重排序结果数量: {len(reranked_results)}")
            logger.info(f"格式化结果长度: {len(formatted_result)}")

            # 验证结果
            self.assertIsInstance(search_results, list)
            self.assertIsInstance(reranked_results, list)
            self.assertIsInstance(formatted_result, str)

            # 显示重排序结果
            if reranked_results:
                logger.info("重排序结果预览:")
                for i, result in enumerate(reranked_results[:3], 1):
                    logger.info(
                        f"  {i}. 评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                    )

            # 验证重排序结果数量不超过final_top_k
            self.assertLessEqual(len(reranked_results), 5)

        except Exception as e:
            logger.error(f"搜索和重排序测试失败: {str(e)}")
            self.fail(f"搜索和重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    async def test_search_and_rerank_without_reranker(self):
        """测试没有重排序工具的情况"""
        logger.info("测试没有重排序工具的情况")

        if not self.has_es:
            logger.error("ES配置不可用，跳过测试")
            return

        query = "电力系统技术"
        logger.info(f"查询: {query}")

        try:
            # 执行搜索，不提供重排序工具
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=self.es_search_tool,
                query=query,
                query_vector=None,
                reranker_tool=None,  # 不提供重排序工具
                initial_top_k=10,
                final_top_k=5)

            logger.info("搜索完成（无重排序）")
            logger.info(f"原始搜索结果数量: {len(search_results)}")
            logger.info(f"重排序结果数量: {len(reranked_results)}")
            logger.info(f"格式化结果长度: {len(formatted_result)}")

            # 验证结果
            self.assertIsInstance(search_results, list)
            self.assertEqual(len(reranked_results), 0)  # 应该没有重排序结果
            self.assertIsInstance(formatted_result, str)

            # 验证格式化结果包含原始搜索结果
            self.assertIn("找到", formatted_result)

        except Exception as e:
            logger.error(f"无重排序测试失败: {str(e)}")
            self.fail(f"无重排序测试失败: {str(e)}")

    @skip_if_no_reranker
    def test_format_functions(self):
        """测试格式化函数"""
        logger.info("测试格式化函数")

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
        logger.info(f"搜索格式化结果长度: {len(formatted_search)}")
        logger.debug(f"搜索格式化结果预览: {formatted_search[:200]}...")

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
        logger.info(f"重排序格式化结果长度: {len(formatted_reranked)}")
        logger.debug(f"重排序格式化结果预览: {formatted_reranked[:200]}...")

        # 验证重排序格式化结果
        self.assertIn("重排序后找到 2 个最相关文档", formatted_reranked)
        self.assertIn("原始评分", formatted_reranked)
        self.assertIn("重排序评分", formatted_reranked)

        logger.info("格式化函数测试通过")

    @skip_if_no_reranker
    async def test_search_performance(self):
        """测试搜索性能"""
        logger.info("测试搜索性能")

        if not self.has_es:
            logger.error("ES配置不可用，跳过测试")
            return

        import time

        queries = ["人工智能", "电力系统", "机器学习算法", "深度学习应用"]

        total_time = 0
        total_results = 0

        for i, query in enumerate(queries, 1):
            logger.info(f"性能测试 {i}/{len(queries)}: {query}")

            start_time = time.time()
            try:
                search_results, reranked_results, formatted_result = await search_and_rerank(
                    es_search_tool=self.es_search_tool,
                    query=query,
                    query_vector=None,
                    reranker_tool=self.reranker_tool,
                    initial_top_k=5,
                    final_top_k=3)

                end_time = time.time()
                query_time = end_time - start_time
                total_time += query_time
                total_results += len(reranked_results)

                logger.info(
                    f"查询耗时: {query_time:.2f}秒, 结果数量: {len(reranked_results)}")

            except Exception as e:
                logger.error(f"性能测试查询失败: {query}, 错误: {str(e)}")

        avg_time = total_time / len(queries) if queries else 0
        avg_results = total_results / len(queries) if queries else 0

        logger.info(f"性能测试完成:")
        logger.info(f"  平均查询时间: {avg_time:.2f}秒")
        logger.info(f"  平均结果数量: {avg_results:.1f}")
        logger.info(f"  总查询时间: {total_time:.2f}秒")

        # 性能基准测试
        self.assertLess(avg_time, 10.0)  # 平均查询时间应该小于10秒
        self.assertGreater(avg_results, 0)  # 应该有结果返回


async def run_async_tests():
    """运行异步测试"""
    logger.info("运行异步集成测试")

    test_instance = SearchRerankIntegrationTest()
    test_instance.setUp()

    try:
        await test_instance.test_search_and_rerank_basic()
        await test_instance.test_search_and_rerank_without_reranker()
        await test_instance.test_search_performance()
        test_instance.test_format_functions()

        logger.info("所有异步集成测试通过")
        return True
    except Exception as e:
        logger.error(f"异步集成测试失败: {str(e)}")
        return False
    finally:
        # 清理资源
        if hasattr(test_instance,
                   'es_search_tool') and test_instance.es_search_tool:
            try:
                await test_instance.es_search_tool.close()
                logger.info("ES搜索工具连接已关闭")
            except Exception as e:
                logger.warning(f"关闭ES搜索工具连接时出错: {str(e)}")


def main():
    """主函数"""
    logger.info("搜索和重排序集成测试")

    import asyncio
    success = asyncio.run(run_async_tests())

    if success:
        logger.info("所有集成测试通过")
    else:
        logger.error("集成测试失败")


if __name__ == "__main__":
    main()
