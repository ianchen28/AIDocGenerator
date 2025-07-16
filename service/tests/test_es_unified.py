#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一ES测试文件
整合所有ES相关测试：连接测试、索引发现、映射分析、搜索功能等
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import ESTestCase, async_test, skip_if_no_es
from src.doc_agent.tools.es_service import ESService
from src.doc_agent.tools.es_discovery import ESDiscovery
from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.llm_clients import get_embedding_client
from core.config import settings
import unittest


class UnifiedESTest(ESTestCase):
    """统一ES测试类，包含所有ES相关测试"""

    @async_test
    @skip_if_no_es
    async def test_es_connection(self):
        """测试ES连接"""
        print("\n" + "=" * 60)
        print("🔌 测试ES连接")
        print("=" * 60)

        async with ESService(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as es_service:
            connected = await es_service.connect()
            print(f"ES连接状态: {'✅ 成功' if connected else '❌ 失败'}")
            if connected:
                info = await es_service._client.info()
                print(f"集群名称: {info.get('cluster_name', 'unknown')}")
                print(
                    f"版本: {info.get('version', {}).get('number', 'unknown')}")
            self.assertTrue(connected, "ES连接失败")

    @async_test
    @skip_if_no_es
    async def test_indices_discovery(self):
        """测试索引发现"""
        print("\n" + "=" * 60)
        print("🔍 测试索引发现")
        print("=" * 60)

        async with ESService(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as es_service:
            discovery = ESDiscovery(es_service)
            indices = await es_service.get_indices()
            print(f"发现 {len(indices)} 个索引")
            for i, idx in enumerate(indices[:10]):
                index_name = idx.get('index', 'N/A')
                docs_count = idx.get('docs.count', '0')
                store_size = idx.get('store.size', '0b')
                print(
                    f"  {i+1}. {index_name} - {docs_count} 文档 ({store_size})")

            knowledge_indices = await discovery.discover_knowledge_indices()
            print(f"\n发现 {len(knowledge_indices)} 个知识库索引")
            if knowledge_indices:
                best_index = discovery.get_best_index()
                vector_dims = discovery.get_vector_dims()
                print(f"最佳索引: {best_index}")
                print(f"向量维度: {vector_dims}")
                for i, idx in enumerate(knowledge_indices[:5]):
                    print(f"  {i+1}. {idx['name']} ({idx['docs_count']} 文档)")
            self.assertGreater(len(knowledge_indices), 0, "未发现知识库索引")

    @async_test
    @skip_if_no_es
    async def test_index_mapping(self):
        """测试索引映射分析"""
        print("\n" + "=" * 60)
        print("📋 测试索引映射分析")
        print("=" * 60)

        async with ESService(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as es_service:
            discovery = ESDiscovery(es_service)
            indices = await discovery.discover_knowledge_indices()
            self.assertTrue(indices, "没有可用的知识库索引")
            target_index = indices[0]['name']
            print(f"分析索引: {target_index}")
            mapping = await es_service.get_index_mapping(target_index)
            self.assertTrue(mapping, "无法获取索引映射")
            properties = mapping.get('properties', {})
            print(f"字段数量: {len(properties)}")
            print("主要字段:")
            for field_name, field_config in list(properties.items())[:10]:
                field_type = field_config.get('type', 'unknown')
                print(f"  - {field_name}: {field_type}")
            vector_fields = [
                f for f, c in properties.items()
                if c.get('type') == 'dense_vector'
            ]
            if vector_fields:
                print(f"向量字段: {vector_fields}")
            else:
                print("⚠️  没有找到向量字段")

    @async_test
    @skip_if_no_es
    async def test_text_search(self):
        """测试文本搜索"""
        print("\n" + "=" * 60)
        print("📝 测试文本搜索")
        print("=" * 60)

        async with ESSearchTool(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as search_tool:
            await search_tool._ensure_initialized()
            self.assertTrue(search_tool._current_index, "没有可用的搜索索引")

            test_queries = ["水电站", "工程", "设计", "技术", "标准"]
            for query in test_queries:
                print(f"\n🔍 搜索查询: {query}")
                result = await search_tool.search(query, top_k=3)
                print(f"结果长度: {len(result)} 字符")
                if "未找到" not in result:
                    print(f"✅ 成功召回")
                    print(f"结果预览: {result[:200]}...")
                else:
                    print(f"❌ 无召回结果")

    @async_test
    @skip_if_no_es
    async def test_vector_search(self):
        """测试向量搜索"""
        print("\n" + "=" * 60)
        print("🔢 测试向量搜索")
        print("=" * 60)

        async with ESSearchTool(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as search_tool:
            # 使用模拟向量测试
            mock_vector = [0.1] * 1536
            result = await search_tool.search(query="",
                                              query_vector=mock_vector,
                                              top_k=3)
            print(f"向量搜索结果长度: {len(result)} 字符")
            if "未找到" not in result:
                print(f"✅ 向量搜索成功召回")
                print(f"结果预览: {result[:200]}...")
            else:
                print(f"❌ 向量搜索无召回结果")

    @async_test
    @skip_if_no_es
    async def test_hybrid_search(self):
        """测试混合搜索"""
        print("\n" + "=" * 60)
        print("🔀 测试混合搜索")
        print("=" * 60)

        # 初始化embedding客户端
        embedding_client = get_embedding_client()

        async with ESSearchTool(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as search_tool:

            test_queries = ["水电站设计", "工程标准", "技术规范"]
            for query in test_queries:
                print(f"\n🔍 测试查询: {query}")
                try:
                    # 生成embedding向量
                    print("📊 生成embedding向量...")
                    embedding_result = embedding_client.invoke(query)
                    try:
                        embedding_data = json.loads(embedding_result)
                        if isinstance(embedding_data,
                                      list) and len(embedding_data) > 0:
                            embedding = embedding_data[0] if isinstance(
                                embedding_data[0], list) else embedding_data
                        else:
                            embedding = embedding_data
                        print(f"✅ 向量维度: {len(embedding)}")
                    except:
                        print("⚠️  无法解析embedding向量，使用模拟向量")
                        embedding = [0.1] * 1536

                    # 测试混合搜索
                    print("🔀 执行混合搜索...")
                    hybrid_result = await search_tool.search_with_hybrid(
                        query, embedding, top_k=3)
                    print(f"混合搜索结果长度: {len(hybrid_result)} 字符")
                    if "未找到" not in hybrid_result:
                        print(f"✅ 混合搜索成功召回")
                        print(f"结果预览: {hybrid_result[:200]}...")
                    else:
                        print(f"❌ 混合搜索无召回结果")

                except Exception as e:
                    print(f"❌ 混合搜索失败: {str(e)}")

    @async_test
    @skip_if_no_es
    async def test_comprehensive_search(self):
        """综合搜索测试"""
        print("\n" + "=" * 60)
        print("🧪 综合搜索测试")
        print("=" * 60)

        # 初始化embedding客户端
        embedding_client = get_embedding_client()

        async with ESSearchTool(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as search_tool:

            test_queries = ["水电站设计", "工程标准", "技术规范", "施工要求"]

            for i, query in enumerate(test_queries, 1):
                print(f"\n🔍 测试查询 {i}: {query}")
                print("-" * 40)

                try:
                    # 生成embedding向量
                    print("📊 生成embedding向量...")
                    embedding_result = embedding_client.invoke(query)
                    try:
                        embedding_data = json.loads(embedding_result)
                        if isinstance(embedding_data,
                                      list) and len(embedding_data) > 0:
                            embedding = embedding_data[0] if isinstance(
                                embedding_data[0], list) else embedding_data
                        else:
                            embedding = embedding_data
                        print(f"✅ 向量维度: {len(embedding)}")
                    except:
                        print("⚠️  无法解析embedding向量，使用模拟向量")
                        embedding = [0.1] * 1536

                    # 测试1: 纯文本搜索
                    print("\n📝 1. 纯文本搜索:")
                    text_results = await search_tool.search(query,
                                                            None,
                                                            top_k=3)
                    print(f"文本搜索结果: {len(text_results)} 字符")
                    if "未找到" not in text_results:
                        print("✅ 文本搜索成功")

                    # 测试2: 纯向量搜索
                    print("\n🔢 2. 纯向量搜索:")
                    vector_results = await search_tool.search("",
                                                              embedding,
                                                              top_k=3)
                    print(f"向量搜索结果: {len(vector_results)} 字符")
                    if "未找到" not in vector_results:
                        print("✅ 向量搜索成功")

                    # 测试3: 混合搜索
                    print("\n🔀 3. 混合搜索:")
                    hybrid_results = await search_tool.search_with_hybrid(
                        query, embedding, top_k=3)
                    print(f"混合搜索结果: {len(hybrid_results)} 字符")
                    if "未找到" not in hybrid_results:
                        print("✅ 混合搜索成功")

                except Exception as e:
                    print(f"❌ 测试失败: {str(e)}")

    @async_test
    @skip_if_no_es
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n" + "=" * 60)
        print("⚠️  测试错误处理")
        print("=" * 60)

        async with ESSearchTool(
                hosts=settings.elasticsearch_config.hosts,
                username=settings.elasticsearch_config.username,
                password=settings.elasticsearch_config.password,
                timeout=settings.elasticsearch_config.timeout) as search_tool:

            # 测试无效查询
            print("🔍 测试无效查询...")
            result = await search_tool.search("", None, top_k=3)
            print(f"空查询结果: {len(result)} 字符")

            # 测试无效向量
            print("🔢 测试无效向量...")
            invalid_vector = [0.1] * 100  # 维度不匹配
            result = await search_tool.search("测试", invalid_vector, top_k=3)
            print(f"无效向量结果: {len(result)} 字符")

            print("✅ 错误处理测试完成")


def main():
    """运行所有ES测试"""
    print("🚀 统一ES测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    # 添加所有测试方法
    test_suite.addTest(test_loader.loadTestsFromTestCase(UnifiedESTest))

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
