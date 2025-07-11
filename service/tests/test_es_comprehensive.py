#!/usr/bin/env python3
"""
综合ES测试文件
包含连接测试、索引检查、映射分析、搜索功能等所有ES相关测试
并演示如何用async with优雅管理ES连接
"""

import asyncio
import logging
from test_base import setup_paths

# 设置测试环境
setup_paths()

from src.doc_agent.tools.es_service import ESService
from src.doc_agent.tools.es_discovery import ESDiscovery
from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools import get_es_search_tool, get_all_tools
from core.config import settings


class ComprehensiveESTest:
    """综合ES测试类，推荐用法：async with管理所有ES资源"""

    def __init__(self):
        self.es_config = settings.elasticsearch_config

    async def test_connection(self):
        print("\n=== 测试ES连接 ===")
        async with ESService(hosts=self.es_config.hosts,
                             username=self.es_config.username,
                             password=self.es_config.password,
                             timeout=self.es_config.timeout) as es_service:
            connected = await es_service.connect()
            print(f"ES连接状态: {'成功' if connected else '失败'}")
            if connected:
                info = await es_service._client.info()
                print(f"集群名称: {info.get('cluster_name', 'unknown')}")
                print(
                    f"版本: {info.get('version', {}).get('number', 'unknown')}")
            return connected

    async def test_indices_discovery(self):
        print("\n=== 测试索引发现 ===")
        async with ESService(hosts=self.es_config.hosts,
                             username=self.es_config.username,
                             password=self.es_config.password,
                             timeout=self.es_config.timeout) as es_service:
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
            return len(knowledge_indices) > 0

    async def test_index_mapping(self):
        print("\n=== 测试索引映射分析 ===")
        async with ESService(hosts=self.es_config.hosts,
                             username=self.es_config.username,
                             password=self.es_config.password,
                             timeout=self.es_config.timeout) as es_service:
            discovery = ESDiscovery(es_service)
            indices = await discovery.discover_knowledge_indices()
            if not indices:
                print("❌ 没有可用的知识库索引")
                return False
            target_index = indices[0]['name']
            print(f"分析索引: {target_index}")
            mapping = await es_service.get_index_mapping(target_index)
            if not mapping:
                print("❌ 无法获取索引映射")
                return False
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
            return True

    async def test_basic_search(self):
        print("\n=== 测试基础搜索功能 ===")
        async with ESSearchTool(hosts=self.es_config.hosts,
                                username=self.es_config.username,
                                password=self.es_config.password,
                                timeout=self.es_config.timeout) as search_tool:
            await search_tool._ensure_initialized()
            if not search_tool._current_index:
                print("❌ 没有可用的搜索索引")
                return False
            test_queries = [
                "电力系统", "变电站", "输电", "配电", "设备", "电网", "调度", "电力系统"
            ]
            for query in test_queries:
                print(f"\n📝 搜索查询: {query}")
                result = await search_tool.search(query, top_k=3)
                print(f"结果长度: {len(result)} 字符")
                print(f"结果预览: {result[:200]}...")
            return True

    async def test_vector_search(self):
        print("\n=== 测试向量搜索功能 ===")
        async with ESSearchTool(hosts=self.es_config.hosts,
                                username=self.es_config.username,
                                password=self.es_config.password,
                                timeout=self.es_config.timeout) as search_tool:
            test_vector = [0.1] * 1536
            result = await search_tool.search(query="电力系统运行",
                                              query_vector=test_vector,
                                              top_k=3)
            print(f"向量搜索结果长度: {len(result)} 字符")
            print(f"结果预览: {result[:300]}...")
            return True

    async def test_factory_functions(self):
        print("\n=== 测试工厂函数和with用法 ===")
        # 推荐用法：async with
        async with get_es_search_tool() as factory_tool:
            print("✅ get_es_search_tool 创建成功")
            print(f"工具类型: {type(factory_tool).__name__}")
            result = await factory_tool.search("变电站设备", top_k=2)
            print(f"工厂工具搜索结果: {len(result)} 字符")
        all_tools = get_all_tools()
        print(f"✅ get_all_tools 获取成功，共 {len(all_tools)} 个工具")
        for tool_name, tool_instance in all_tools.items():
            print(f"  - {tool_name}: {type(tool_instance).__name__}")
            if isinstance(tool_instance, ESSearchTool):
                async with tool_instance:
                    pass
        return True

    async def test_error_handling(self):
        print("\n=== 测试错误处理 ===")
        async with ESSearchTool(hosts=self.es_config.hosts,
                                username=self.es_config.username,
                                password=self.es_config.password,
                                timeout=self.es_config.timeout) as search_tool:
            result = await search_tool.search("", top_k=1)
            print("空查询处理正常")
        async with ESSearchTool(hosts=self.es_config.hosts,
                                username=self.es_config.username,
                                password=self.es_config.password,
                                timeout=1) as invalid_tool:
            result = await invalid_tool.search("测试", top_k=1)
            print("错误处理正常")
        return True

    async def run_all_tests(self):
        print("🚀 开始综合ES测试...")
        test_results = []
        test_results.append(("连接测试", await self.test_connection()))
        test_results.append(("索引发现", await self.test_indices_discovery()))
        test_results.append(("映射分析", await self.test_index_mapping()))
        test_results.append(("基础搜索", await self.test_basic_search()))
        test_results.append(("向量搜索", await self.test_vector_search()))
        test_results.append(("工厂函数", await self.test_factory_functions()))
        test_results.append(("错误处理", await self.test_error_handling()))
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print("=" * 50)
        passed = 0
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        print(f"\n总计: {passed}/{len(test_results)} 项测试通过")
        if passed == len(test_results):
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败，请检查配置和连接")


async def main():
    tester = ComprehensiveESTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
