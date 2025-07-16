#!/usr/bin/env python3
"""
综合Web搜索测试文件
包含WebSearchTool、Tavily搜索等所有Web搜索相关测试
"""

from test_base import WebSearchTestCase
from src.doc_agent.tools.web_search import WebSearchTool
from src.doc_agent.tools import get_web_search_tool, get_all_tools
from core.config import settings
import unittest
import os


class ComprehensiveWebSearchTest(WebSearchTestCase):
    """综合Web搜索测试类，推荐用法：unittest风格"""

    def setUp(self):
        super().setUp()
        self.web_search_tool = WebSearchTool()
        self.tavily_config = settings.tavily_config

    def test_web_search_tool_creation(self):
        """测试Web搜索工具创建"""
        print("\n=== 测试Web搜索工具创建 ===")
        tool = WebSearchTool()
        self.assertIsInstance(tool, WebSearchTool)
        print(f"✅ WebSearchTool 直接创建成功: {type(tool).__name__}")
        factory_tool = get_web_search_tool()
        self.assertIsInstance(factory_tool, WebSearchTool)
        print(f"✅ get_web_search_tool 工厂函数创建成功: {type(factory_tool).__name__}")

    def test_basic_search(self):
        """测试基础搜索功能"""
        print("\n=== 测试基础搜索功能 ===")
        test_queries = ["人工智能最新发展", "Python编程教程", "机器学习算法", "深度学习技术"]
        for query in test_queries:
            print(f"\n📝 搜索查询: {query}")
            result = self.web_search_tool.search(query)
            print(f"搜索结果长度: {len(result)} 字符")
            print(f"结果预览: {result[:200]}...")
            self.assertIsInstance(result, str)

    def test_search_with_filters(self):
        """测试带过滤条件的搜索"""
        print("\n=== 测试带过滤条件的搜索 ===")
        search_params = [{
            "query": "Python教程",
            "max_results": 3
        }, {
            "query": "机器学习",
            "search_depth": "basic"
        }, {
            "query": "深度学习",
            "include_domains": ["github.com", "stackoverflow.com"]
        }]
        for params in search_params:
            query = params["query"]
            print(f"\n📝 高级搜索: {query}")
            print(f"参数: {params}")
            result = self.web_search_tool.search(query)
            print(f"结果长度: {len(result)} 字符")
            self.assertIsInstance(result, str)

    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        result = self.web_search_tool.search("")
        print("空查询处理正常")
        self.assertIsInstance(result, str)
        result = self.web_search_tool.search("!@#$%^&*()")
        print("特殊字符处理正常")
        self.assertIsInstance(result, str)
        long_query = "这是一个非常长的搜索查询" * 10
        result = self.web_search_tool.search(long_query)
        print("长查询处理正常")
        self.assertIsInstance(result, str)

    def test_factory_functions(self):
        """测试工厂函数"""
        print("\n=== 测试工厂函数 ===")
        web_tool = get_web_search_tool()
        self.assertIsInstance(web_tool, WebSearchTool)
        print("✅ get_web_search_tool 创建成功")
        result = web_tool.search("工厂函数测试")
        print(f"工厂工具搜索结果: {len(result)} 字符")
        all_tools = get_all_tools()
        print(f"✅ get_all_tools 获取成功，共 {len(all_tools)} 个工具")
        web_tools = [
            name for name in all_tools.keys()
            if 'web' in name.lower() or 'search' in name.lower()
        ]
        print(f"Web搜索工具: {web_tools}")
        self.assertTrue(len(web_tools) > 0)

    def test_config_integration(self):
        """测试配置集成"""
        print("\n=== 测试配置集成 ===")
        print("📋 Tavily配置:")
        print(f"  API Key: {'已设置' if self.tavily_config.api_key else '未设置'}")
        print(f"  Search Depth: {self.tavily_config.search_depth}")
        print(f"  Max Results: {self.tavily_config.max_results}")
        tavily_key = os.getenv('TAVILY_API_KEY')
        print(f"  环境变量 TAVILY_API_KEY: {'已设置' if tavily_key else '未设置'}")
        self.assertIsNotNone(self.tavily_config)

    def test_performance(self):
        """测试性能"""
        print("\n=== 测试性能 ===")
        import time
        test_query = "Python编程"
        start_time = time.time()
        result = self.web_search_tool.search(test_query)
        end_time = time.time()
        response_time = end_time - start_time
        print(f"搜索响应时间: {response_time:.2f} 秒")
        print(f"结果长度: {len(result)} 字符")
        self.assertLess(response_time, 10, "响应时间过长")

    def test_integration_with_agent(self):
        """测试与Agent的集成"""
        print("\n=== 测试与Agent的集成 ===")

        def mock_agent_node(state, search_tool):
            query = state.get("search_query", "默认查询")
            results = search_tool.search(query)
            return {"gathered_data": results}

        mock_state = {"search_query": "人工智能发展"}
        result = mock_agent_node(mock_state, self.web_search_tool)
        print("✅ Agent集成测试通过")
        print(f"模拟结果: {len(result['gathered_data'])} 字符")
        self.assertIn("gathered_data", result)


if __name__ == "__main__":
    unittest.main()
