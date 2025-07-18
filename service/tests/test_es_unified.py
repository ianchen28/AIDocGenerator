#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ES统一测试文件
包含所有ES相关的测试功能
"""

import sys
import os
import unittest
import asyncio
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import ESTestCase, skip_if_no_es
from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools.es_service import ESService
from core.config import settings


class ESUnifiedTest(ESTestCase):
    """ES统一测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化 ES 统一测试")

    @skip_if_no_es
    async def test_es_connection(self):
        """测试ES连接"""
        logger.info("测试ES连接")

        try:
            es_config = settings.elasticsearch_config
            es_service = ESService(hosts=es_config.hosts,
                                   username=es_config.username,
                                   password=es_config.password,
                                   timeout=es_config.timeout)

            # 测试连接
            await es_service.connect()
            logger.info("ES连接成功")

            # 测试健康检查
            health = await es_service.health_check()
            logger.info(f"ES健康状态: {health}")

            # 关闭连接
            await es_service.close()
            logger.info("ES连接已关闭")

        except Exception as e:
            logger.error(f"ES连接测试失败: {str(e)}")
            self.fail(f"ES连接测试失败: {str(e)}")

    @skip_if_no_es
    async def test_es_search_tool(self):
        """测试ES搜索工具"""
        logger.info("测试ES搜索工具")

        try:
            es_config = settings.elasticsearch_config
            search_tool = ESSearchTool(hosts=es_config.hosts,
                                       username=es_config.username,
                                       password=es_config.password,
                                       timeout=es_config.timeout)

            # 测试文本搜索
            query = "人工智能"
            results = await search_tool.search(query, top_k=5)

            logger.info(f"文本搜索结果数量: {len(results)}")
            for i, result in enumerate(results[:3], 1):
                logger.info(
                    f"  {i}. 评分: {result.score:.3f} | {result.div_content[:50]}..."
                )

            # 测试向量搜索
            query_vector = [0.1] * 1536  # 模拟向量
            vector_results = await search_tool.search(
                query="", query_vector=query_vector, top_k=3)

            logger.info(f"向量搜索结果数量: {len(vector_results)}")

            # 关闭连接
            await search_tool.close()
            logger.info("ES搜索工具连接已关闭")

        except Exception as e:
            logger.error(f"ES搜索工具测试失败: {str(e)}")
            self.fail(f"ES搜索工具测试失败: {str(e)}")

    @skip_if_no_es
    async def test_es_indices(self):
        """测试ES索引"""
        logger.info("测试ES索引")

        try:
            es_config = settings.elasticsearch_config
            es_service = ESService(hosts=es_config.hosts,
                                   username=es_config.username,
                                   password=es_config.password,
                                   timeout=es_config.timeout)

            await es_service.connect()

            # 获取索引列表
            indices = await es_service.list_indices()
            logger.info(f"可用索引数量: {len(indices)}")

            for index in indices[:5]:  # 只显示前5个
                logger.info(f"  索引: {index}")

            # 测试索引详情
            if indices:
                index_name = indices[0]
                mapping = await es_service.get_index_mapping(index_name)
                logger.info(f"索引 {index_name} 映射: {len(mapping)} 个字段")

            await es_service.close()

        except Exception as e:
            logger.error(f"ES索引测试失败: {str(e)}")
            self.fail(f"ES索引测试失败: {str(e)}")

    @skip_if_no_es
    async def test_es_search_with_filters(self):
        """测试带过滤条件的ES搜索"""
        logger.info("测试带过滤条件的ES搜索")

        try:
            es_config = settings.elasticsearch_config
            search_tool = ESSearchTool(hosts=es_config.hosts,
                                       username=es_config.username,
                                       password=es_config.password,
                                       timeout=es_config.timeout)

            # 测试带过滤条件的搜索
            query = "机器学习"
            filters = {
                "source": "*.pdf",  # 只搜索PDF文件
                "category": "AI"  # 只搜索AI类别
            }

            results = await search_tool.search(query=query,
                                               filters=filters,
                                               top_k=5)

            logger.info(f"过滤搜索结果数量: {len(results)}")
            for i, result in enumerate(results[:3], 1):
                logger.info(
                    f"  {i}. 评分: {result.score:.3f} | 来源: {result.source}")

            await search_tool.close()

        except Exception as e:
            logger.error(f"过滤搜索测试失败: {str(e)}")
            self.fail(f"过滤搜索测试失败: {str(e)}")

    @skip_if_no_es
    async def test_es_multi_index_search(self):
        """测试多索引搜索"""
        logger.info("测试多索引搜索")

        try:
            es_config = settings.elasticsearch_config
            search_tool = ESSearchTool(hosts=es_config.hosts,
                                       username=es_config.username,
                                       password=es_config.password,
                                       timeout=es_config.timeout)

            # 测试多索引搜索
            query = "深度学习"
            indices = ["documents", "papers", "reports"]  # 示例索引

            results = await search_tool.search(query=query,
                                               indices=indices,
                                               top_k=10)

            logger.info(f"多索引搜索结果数量: {len(results)}")

            # 按索引分组显示结果
            by_index = {}
            for result in results:
                index = result.alias_name or "unknown"
                if index not in by_index:
                    by_index[index] = []
                by_index[index].append(result)

            for index, index_results in by_index.items():
                logger.info(f"  索引 {index}: {len(index_results)} 个结果")

            await search_tool.close()

        except Exception as e:
            logger.error(f"多索引搜索测试失败: {str(e)}")
            self.fail(f"多索引搜索测试失败: {str(e)}")

    @skip_if_no_es
    async def test_es_error_handling(self):
        """测试ES错误处理"""
        logger.info("测试ES错误处理")

        try:
            es_config = settings.elasticsearch_config
            search_tool = ESSearchTool(hosts=es_config.hosts,
                                       username=es_config.username,
                                       password=es_config.password,
                                       timeout=es_config.timeout)

            # 测试空查询
            try:
                results = await search_tool.search("", top_k=5)
                logger.info("空查询处理正常")
            except Exception as e:
                logger.warning(f"空查询处理异常: {e}")

            # 测试无效索引
            try:
                results = await search_tool.search("测试",
                                                   indices=["invalid_index"],
                                                   top_k=5)
                logger.info("无效索引处理正常")
            except Exception as e:
                logger.warning(f"无效索引处理异常: {e}")

            # 测试超时处理
            try:
                # 设置很短的超时时间
                short_timeout_tool = ESSearchTool(
                    hosts=es_config.hosts,
                    username=es_config.username,
                    password=es_config.password,
                    timeout=0.001  # 1毫秒超时
                )
                results = await short_timeout_tool.search("测试", top_k=5)
                logger.warning("超时处理异常，应该抛出异常")
            except Exception as e:
                logger.info(f"超时处理正常: {e}")

            await search_tool.close()

        except Exception as e:
            logger.error(f"错误处理测试失败: {str(e)}")
            self.fail(f"错误处理测试失败: {str(e)}")

    @skip_if_no_es
    async def test_es_performance(self):
        """测试ES性能"""
        logger.info("测试ES性能")

        try:
            es_config = settings.elasticsearch_config
            search_tool = ESSearchTool(hosts=es_config.hosts,
                                       username=es_config.username,
                                       password=es_config.password,
                                       timeout=es_config.timeout)

            import time
            queries = ["人工智能", "机器学习", "深度学习", "自然语言处理", "计算机视觉"]

            total_time = 0
            total_results = 0

            for i, query in enumerate(queries, 1):
                logger.info(f"性能测试 {i}/{len(queries)}: {query}")

                start_time = time.time()
                results = await search_tool.search(query, top_k=10)
                end_time = time.time()

                query_time = end_time - start_time
                total_time += query_time
                total_results += len(results)

                logger.info(f"查询耗时: {query_time:.2f}秒, 结果数量: {len(results)}")

            avg_time = total_time / len(queries)
            avg_results = total_results / len(queries)

            logger.info(f"性能测试完成:")
            logger.info(f"  平均查询时间: {avg_time:.2f}秒")
            logger.info(f"  平均结果数量: {avg_results:.1f}")
            logger.info(f"  总查询时间: {total_time:.2f}秒")

            # 性能基准测试
            self.assertLess(avg_time, 5.0)  # 平均查询时间应该小于5秒
            self.assertGreater(avg_results, 0)  # 应该有结果返回

            await search_tool.close()

        except Exception as e:
            logger.error(f"性能测试失败: {str(e)}")
            self.fail(f"性能测试失败: {str(e)}")


async def run_async_tests():
    """运行异步测试"""
    logger.info("运行异步ES测试")

    test_instance = ESUnifiedTest()
    test_instance.setUp()

    try:
        await test_instance.test_es_connection()
        await test_instance.test_es_search_tool()
        await test_instance.test_es_indices()
        await test_instance.test_es_search_with_filters()
        await test_instance.test_es_multi_index_search()
        await test_instance.test_es_error_handling()
        await test_instance.test_es_performance()

        logger.info("所有异步ES测试通过")
        return True
    except Exception as e:
        logger.error(f"异步ES测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("ES统一测试")

    success = asyncio.run(run_async_tests())

    if success:
        logger.info("所有ES测试通过")
    else:
        logger.error("ES测试失败")


if __name__ == "__main__":
    main()
