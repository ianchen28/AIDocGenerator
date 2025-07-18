#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的搜索和重排序测试
验证新的搜索工具函数和重排序功能的集成
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools.reranker import RerankerTool
from src.doc_agent.llm_clients.providers import RerankerClient
from src.doc_agent.utils.search_utils import search_and_rerank, format_search_results, format_reranked_results
from core.config import settings


async def test_search_and_rerank_basic():
    """测试基础搜索和重排序功能"""
    logger.info("测试基础搜索和重排序功能")

    es_search_tool = None
    reranker_tool = None

    try:
        logger.info("步骤1: 检查配置...")
        # 获取ES配置
        es_config = settings.elasticsearch_config
        if not es_config:
            logger.error("ES配置不可用，跳过测试")
            return False
        logger.info(f"ES配置可用: {es_config.hosts}")

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if not reranker_config:
            logger.error("Reranker配置不可用，跳过测试")
            return False
        logger.info(f"Reranker配置可用: {reranker_config.url}")

        logger.info("步骤2: 初始化工具...")
        # 初始化工具
        try:
            es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                          username=es_config.username,
                                          password=es_config.password,
                                          timeout=es_config.timeout)
            logger.info("ES搜索工具初始化成功")
        except Exception as e:
            logger.error(f"ES搜索工具初始化失败: {str(e)}")
            return False

        try:
            reranker_tool = RerankerTool(base_url=reranker_config.url,
                                         api_key=reranker_config.api_key)
            logger.info("Reranker工具初始化成功")
        except Exception as e:
            logger.error(f"Reranker工具初始化失败: {str(e)}")
            return False

        query = "人工智能电力行业应用"
        logger.info("步骤3: 执行搜索和重排序...")
        logger.info(f"查询: {query}")

        start_time = time.time()
        try:
            # 执行搜索和重排序
            logger.info("调用 search_and_rerank...")
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=es_search_tool,
                query=query,
                query_vector=None,  # 先测试文本搜索
                reranker_tool=reranker_tool,
                initial_top_k=10,
                final_top_k=5)
            end_time = time.time()

            logger.info(f"搜索和重排序完成，耗时: {end_time - start_time:.2f}秒")
            logger.info(f"原始搜索结果数量: {len(search_results)}")
            logger.info(f"重排序结果数量: {len(reranked_results)}")
            logger.info(f"格式化结果长度: {len(formatted_result)}")

            # 显示重排序结果
            if reranked_results:
                logger.info("重排序结果预览:")
                for i, result in enumerate(reranked_results[:3], 1):
                    logger.info(
                        f"  {i}. 评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                    )

            # 验证重排序结果数量不超过final_top_k
            if len(reranked_results) <= 5:
                logger.info(f"重排序结果数量正确: {len(reranked_results)}")
            else:
                logger.error(f"重排序结果数量过多: {len(reranked_results)}")
                return False

            return True

        except Exception as e:
            logger.error(f"搜索和重排序测试失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    finally:
        # 确保关闭连接
        logger.info("步骤4: 清理资源...")
        if es_search_tool:
            try:
                await es_search_tool.close()
                logger.info("ES搜索工具连接已关闭")
            except Exception as e:
                logger.warning(f"关闭ES搜索工具连接时出错: {str(e)}")

        if reranker_tool and hasattr(reranker_tool.reranker_client, 'close'):
            try:
                await reranker_tool.reranker_client.close()
                logger.info("Reranker工具连接已关闭")
            except Exception as e:
                logger.warning(f"关闭Reranker工具连接时出错: {str(e)}")


async def test_search_without_reranker():
    """测试没有重排序工具的情况"""
    logger.info("测试没有重排序工具的情况")

    es_search_tool = None

    try:
        logger.info("步骤1: 检查ES配置...")
        # 获取ES配置
        es_config = settings.elasticsearch_config
        if not es_config:
            logger.error("ES配置不可用，跳过测试")
            return False
        logger.info(f"ES配置可用: {es_config.hosts}")

        logger.info("步骤2: 初始化ES搜索工具...")
        # 初始化工具
        try:
            es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                          username=es_config.username,
                                          password=es_config.password,
                                          timeout=es_config.timeout)
            logger.info("ES搜索工具初始化成功")
        except Exception as e:
            logger.error(f"ES搜索工具初始化失败: {str(e)}")
            return False

        query = "电力系统技术"
        logger.info("步骤3: 执行搜索（无重排序）...")
        logger.info(f"查询: {query}")

        start_time = time.time()
        try:
            # 执行搜索，不提供重排序工具
            logger.info("调用 search_and_rerank（无重排序）...")
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=es_search_tool,
                query=query,
                query_vector=None,
                reranker_tool=None,  # 不提供重排序工具
                initial_top_k=10,
                final_top_k=5)
            end_time = time.time()

            logger.info(f"搜索完成（无重排序），耗时: {end_time - start_time:.2f}秒")
            logger.info(f"原始搜索结果数量: {len(search_results)}")
            logger.info(f"重排序结果数量: {len(reranked_results)}")
            logger.info(f"格式化结果长度: {len(formatted_result)}")

            # 验证结果
            if len(reranked_results) == 0:  # 应该没有重排序结果
                logger.info("无重排序结果正确")
            else:
                logger.error(f"应该有0个重排序结果，实际有{len(reranked_results)}个")
                return False

            # 验证格式化结果包含原始搜索结果
            if "找到" in formatted_result:
                logger.info("格式化结果正确")
            else:
                logger.error("格式化结果异常")
                return False

            return True

        except Exception as e:
            logger.error(f"搜索测试失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    finally:
        # 确保关闭连接
        if es_search_tool:
            try:
                await es_search_tool.close()
                logger.info("ES搜索工具连接已关闭")
            except Exception as e:
                logger.warning(f"关闭ES搜索工具连接时出错: {str(e)}")


def test_format_functions():
    """测试格式化函数"""
    logger.info("测试格式化函数")

    from src.doc_agent.tools.es_service import ESSearchResult

    # 创建测试数据
    test_results = [
        ESSearchResult(id="1",
                       original_content="这是第一个测试文档的内容，包含了一些关于人工智能的信息。",
                       div_content="人工智能测试文档",
                       source="test_doc_1.md",
                       score=0.95,
                       metadata={"category": "AI"},
                       alias_name="test_index"),
        ESSearchResult(id="2",
                       original_content="这是第二个测试文档的内容，主要讨论机器学习算法。",
                       div_content="机器学习算法",
                       source="test_doc_2.md",
                       score=0.87,
                       metadata={"category": "ML"},
                       alias_name="test_index")
    ]

    query = "人工智能 机器学习"
    indices_list = ["test_index"]

    # 测试 format_search_results
    logger.info("测试 format_search_results...")
    formatted_search = format_search_results(test_results, query, indices_list)
    logger.debug(f"格式化搜索结果长度: {len(formatted_search)}")
    logger.info("format_search_results 测试通过")

    # 测试 format_reranked_results
    logger.info("测试 format_reranked_results...")
    from src.doc_agent.tools.reranker import RerankedSearchResult

    reranked_results = [
        RerankedSearchResult(id="1",
                             original_content="这是第一个测试文档的内容，包含了一些关于人工智能的信息。",
                             div_content="人工智能测试文档",
                             source="test_doc_1.md",
                             score=0.95,
                             rerank_score=0.98,
                             metadata={"category": "AI"},
                             alias_name="test_index"),
        RerankedSearchResult(id="2",
                             original_content="这是第二个测试文档的内容，主要讨论机器学习算法。",
                             div_content="机器学习算法",
                             source="test_doc_2.md",
                             score=0.87,
                             rerank_score=0.92,
                             metadata={"category": "ML"},
                             alias_name="test_index")
    ]

    formatted_reranked = format_reranked_results(reranked_results, query,
                                                 indices_list)
    logger.debug(f"格式化重排序结果长度: {len(formatted_reranked)}")
    logger.info("format_reranked_results 测试通过")

    return True


async def main():
    """主测试函数"""
    logger.info("开始搜索和重排序集成测试")

    # 测试格式化函数
    logger.info("=" * 60)
    logger.info("测试格式化函数")
    logger.info("=" * 60)
    format_success = test_format_functions()
    if not format_success:
        logger.error("格式化函数测试失败")
        return False

    # 测试基础搜索和重排序
    logger.info("=" * 60)
    logger.info("测试基础搜索和重排序功能")
    logger.info("=" * 60)
    basic_success = await test_search_and_rerank_basic()
    if not basic_success:
        logger.error("基础搜索和重排序测试失败")
        return False

    # 测试无重排序的情况
    logger.info("=" * 60)
    logger.info("测试无重排序工具的情况")
    logger.info("=" * 60)
    no_rerank_success = await test_search_without_reranker()
    if not no_rerank_success:
        logger.error("无重排序测试失败")
        return False

    logger.info("=" * 60)
    logger.info("✅ 所有测试通过!")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    asyncio.run(main())
