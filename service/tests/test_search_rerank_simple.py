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
    print("\n" + "=" * 60)
    print("🔍 测试基础搜索和重排序功能")
    print("=" * 60)

    es_search_tool = None
    reranker_tool = None

    try:
        print("📋 步骤1: 检查配置...")
        # 获取ES配置
        es_config = settings.elasticsearch_config
        if not es_config:
            print("❌ ES配置不可用，跳过测试")
            return False
        print(f"✅ ES配置可用: {es_config.hosts}")

        # 获取reranker配置
        reranker_config = settings.get_model_config("reranker")
        if not reranker_config:
            print("❌ Reranker配置不可用，跳过测试")
            return False
        print(f"✅ Reranker配置可用: {reranker_config.url}")

        print("📋 步骤2: 初始化工具...")
        # 初始化工具
        try:
            es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                          username=es_config.username,
                                          password=es_config.password,
                                          timeout=es_config.timeout)
            print("✅ ES搜索工具初始化成功")
        except Exception as e:
            print(f"❌ ES搜索工具初始化失败: {str(e)}")
            return False

        try:
            reranker_tool = RerankerTool(base_url=reranker_config.url,
                                         api_key=reranker_config.api_key)
            print("✅ Reranker工具初始化成功")
        except Exception as e:
            print(f"❌ Reranker工具初始化失败: {str(e)}")
            return False

        query = "人工智能电力行业应用"
        print(f"📋 步骤3: 执行搜索和重排序...")
        print(f"🔍 查询: {query}")

        start_time = time.time()
        try:
            # 执行搜索和重排序
            print("⏳ 调用 search_and_rerank...")
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=es_search_tool,
                query=query,
                query_vector=None,  # 先测试文本搜索
                reranker_tool=reranker_tool,
                initial_top_k=10,
                final_top_k=5)
            end_time = time.time()

            print(f"✅ 搜索和重排序完成，耗时: {end_time - start_time:.2f}秒")
            print(f"📄 原始搜索结果数量: {len(search_results)}")
            print(f"📄 重排序结果数量: {len(reranked_results)}")
            print(f"📝 格式化结果长度: {len(formatted_result)}")

            # 显示重排序结果
            if reranked_results:
                print(f"\n📋 重排序结果预览:")
                for i, result in enumerate(reranked_results[:3], 1):
                    print(
                        f"  {i}. 评分: {result.rerank_score:.3f} | {result.div_content[:50]}..."
                    )

            # 验证重排序结果数量不超过final_top_k
            if len(reranked_results) <= 5:
                print(f"✅ 重排序结果数量正确: {len(reranked_results)}")
            else:
                print(f"❌ 重排序结果数量过多: {len(reranked_results)}")
                return False

            return True

        except Exception as e:
            print(f"❌ 搜索和重排序测试失败: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return False

    finally:
        # 确保关闭连接
        print("📋 步骤4: 清理资源...")
        if es_search_tool:
            try:
                await es_search_tool.close()
                print("✅ ES搜索工具连接已关闭")
            except Exception as e:
                print(f"⚠️  关闭ES搜索工具连接时出错: {str(e)}")

        if reranker_tool and hasattr(reranker_tool.reranker_client, 'close'):
            try:
                await reranker_tool.reranker_client.close()
                print("✅ Reranker工具连接已关闭")
            except Exception as e:
                print(f"⚠️  关闭Reranker工具连接时出错: {str(e)}")


async def test_search_without_reranker():
    """测试没有重排序工具的情况"""
    print("\n" + "=" * 60)
    print("🔍 测试没有重排序工具的情况")
    print("=" * 60)

    es_search_tool = None

    try:
        print("📋 步骤1: 检查ES配置...")
        # 获取ES配置
        es_config = settings.elasticsearch_config
        if not es_config:
            print("❌ ES配置不可用，跳过测试")
            return False
        print(f"✅ ES配置可用: {es_config.hosts}")

        print("📋 步骤2: 初始化ES搜索工具...")
        # 初始化工具
        try:
            es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                          username=es_config.username,
                                          password=es_config.password,
                                          timeout=es_config.timeout)
            print("✅ ES搜索工具初始化成功")
        except Exception as e:
            print(f"❌ ES搜索工具初始化失败: {str(e)}")
            return False

        query = "电力系统技术"
        print(f"📋 步骤3: 执行搜索（无重排序）...")
        print(f"🔍 查询: {query}")

        start_time = time.time()
        try:
            # 执行搜索，不提供重排序工具
            print("⏳ 调用 search_and_rerank（无重排序）...")
            search_results, reranked_results, formatted_result = await search_and_rerank(
                es_search_tool=es_search_tool,
                query=query,
                query_vector=None,
                reranker_tool=None,  # 不提供重排序工具
                initial_top_k=10,
                final_top_k=5)
            end_time = time.time()

            print(f"✅ 搜索完成（无重排序），耗时: {end_time - start_time:.2f}秒")
            print(f"📄 原始搜索结果数量: {len(search_results)}")
            print(f"📄 重排序结果数量: {len(reranked_results)}")
            print(f"📝 格式化结果长度: {len(formatted_result)}")

            # 验证结果
            if len(reranked_results) == 0:  # 应该没有重排序结果
                print(f"✅ 无重排序结果正确")
            else:
                print(f"❌ 应该有0个重排序结果，实际有{len(reranked_results)}个")
                return False

            # 验证格式化结果包含原始搜索结果
            if "找到" in formatted_result:
                print(f"✅ 格式化结果正确")
            else:
                print(f"❌ 格式化结果异常")
                return False

            return True

        except Exception as e:
            print(f"❌ 无重排序测试失败: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return False

    finally:
        # 确保关闭连接
        print("📋 步骤4: 清理资源...")
        if es_search_tool:
            try:
                await es_search_tool.close()
                print("✅ ES搜索工具连接已关闭")
            except Exception as e:
                print(f"⚠️  关闭ES搜索工具连接时出错: {str(e)}")


def test_format_functions():
    """测试格式化函数"""
    print("\n" + "=" * 60)
    print("🔍 测试格式化函数")
    print("=" * 60)

    print("📋 步骤1: 创建模拟数据...")
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
    print(f"✅ 创建了 {len(mock_results)} 个模拟搜索结果")

    query = "测试查询"
    indices_list = ["index1", "index2"]

    print("📋 步骤2: 测试搜索格式化函数...")
    # 测试格式化搜索结果
    formatted_search = format_search_results(mock_results, query, indices_list)
    print(f"📝 搜索格式化结果长度: {len(formatted_search)}")
    print(f"📋 搜索格式化结果预览: {formatted_search[:200]}...")

    # 验证格式化结果
    if "找到 2 个相关文档" in formatted_search and "doc1.txt" in formatted_search and "doc2.txt" in formatted_search:
        print(f"✅ 搜索格式化结果正确")
    else:
        print(f"❌ 搜索格式化结果异常")
        return False

    print("📋 步骤3: 测试重排序格式化函数...")
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
    print(f"✅ 创建了 {len(mock_reranked_results)} 个模拟重排序结果")

    formatted_reranked = format_reranked_results(mock_reranked_results, query,
                                                 indices_list)
    print(f"📝 重排序格式化结果长度: {len(formatted_reranked)}")
    print(f"📋 重排序格式化结果预览: {formatted_reranked[:200]}...")

    # 验证重排序格式化结果
    if "重排序后找到 2 个最相关文档" in formatted_reranked and "原始评分" in formatted_reranked and "重排序评分" in formatted_reranked:
        print(f"✅ 重排序格式化结果正确")
    else:
        print(f"❌ 重排序格式化结果异常")
        return False

    print(f"✅ 格式化函数测试通过")
    return True


async def main():
    """运行所有测试"""
    print("🚀 搜索和重排序集成测试")
    print("=" * 80)

    # 运行测试
    results = []

    print("📋 开始运行测试...")

    # 测试格式化函数
    print("\n🔄 运行测试1: 格式化函数测试")
    results.append(test_format_functions())

    # 测试搜索和重排序
    print("\n🔄 运行测试2: 搜索和重排序测试")
    results.append(await test_search_and_rerank_basic())

    # 测试无重排序搜索
    print("\n🔄 运行测试3: 无重排序搜索测试")
    results.append(await test_search_without_reranker())

    # 统计结果
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 80)
    print("📊 测试结果统计")
    print("=" * 80)
    print(f"通过测试: {passed}/{total}")

    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    print("🚀 启动测试...")
    success = asyncio.run(main())
    print(f"🏁 测试结束，结果: {'成功' if success else '失败'}")
    exit(0 if success else 1)
