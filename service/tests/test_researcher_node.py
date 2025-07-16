#!/usr/bin/env python3
"""
测试 researcher_node 功能
"""

from test_base import NodeTestCase, skip_if_no_llm, async_test
from src.doc_agent.graph.nodes import async_researcher_node
from src.doc_agent.graph.state import ResearchState
from unittest.mock import Mock, AsyncMock, patch
import unittest


class ResearcherNodeTest(NodeTestCase):
    """researcher_node 节点功能测试"""

    def setUp(self):
        super().setUp()
        # 初始化模拟的搜索工具
        self.web_search_tool = Mock()

    @async_test
    async def test_researcher_node_no_queries(self):
        """测试没有搜索查询的情况"""
        print("\n=== 测试没有搜索查询的情况 ===")
        state = ResearchState()
        result = await async_researcher_node(state, self.web_search_tool)
        self.assertEqual(result["gathered_data"], "没有搜索查询需要执行")
        self.web_search_tool.search.assert_not_called()
        print("✅ 正确处理空查询情况")

    @async_test
    async def test_researcher_node_with_queries(self):
        """测试有搜索查询的情况"""
        print("\n=== 测试有搜索查询的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["电力", "电网"]
        self.web_search_tool.search.return_value = "网络搜索结果内容"

        # Mock 所有外部依赖
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:

            # Mock ES 搜索
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)

            self.assertEqual(self.web_search_tool.search.call_count, 2)
            self.assertEqual(mock_es_instance.search.call_count, 2)
            gathered_data = result["gathered_data"]
            self.assertIn("电力", gathered_data)
            self.assertIn("电网", gathered_data)
            self.assertIn("网络搜索结果内容", gathered_data)
            self.assertIn("ES搜索结果内容", gathered_data)
            print("✅ 多查询搜索成功，包含网络和ES搜索结果")

    @async_test
    async def test_researcher_node_web_search_failure(self):
        """测试网络搜索失败的情况"""
        print("\n=== 测试网络搜索失败的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["变电站"]
        self.web_search_tool.search.side_effect = Exception("网络搜索失败")

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]
            self.assertNotIn("网络搜索失败", gathered_data)
            self.assertIn("ES搜索结果内容", gathered_data)
            print("✅ 网络搜索失败时正确回退到ES搜索")

    @async_test
    async def test_researcher_node_es_search_failure(self):
        """测试ES搜索失败的情况"""
        print("\n=== 测试ES搜索失败的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["配电"]
        self.web_search_tool.search.return_value = "网络搜索结果内容"

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(
                side_effect=Exception("ES搜索失败"))
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]
            self.assertIn("网络搜索结果内容", gathered_data)
            self.assertIn("向量检索异常: ES搜索失败", gathered_data)
            print("✅ ES搜索失败时正确保留网络搜索结果")

    @async_test
    async def test_researcher_node_mock_web_search_results(self):
        """测试网络搜索返回模拟结果的情况"""
        print("\n=== 测试网络搜索返回模拟结果的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["调度"]
        self.web_search_tool.search.return_value = "这是模拟的搜索结果，包含模拟关键词"

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]
            self.assertNotIn("这是模拟的搜索结果", gathered_data)
            self.assertIn("ES搜索结果内容", gathered_data)
            print("✅ 正确跳过模拟搜索结果，使用ES搜索结果")

    @async_test
    async def test_researcher_node_async_es_search(self):
        """测试异步ES搜索的情况"""
        print("\n=== 测试异步ES搜索的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["设备"]
        self.web_search_tool.search.return_value = "网络搜索结果内容"

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="异步ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]
            self.assertIn("网络搜索结果内容", gathered_data)
            self.assertIn("异步ES搜索结果内容", gathered_data)
            print("✅ 异步ES搜索正常工作")

    @async_test
    async def test_researcher_node_no_search_tools(self):
        """测试搜索工具不可用的情况"""
        print("\n=== 测试搜索工具不可用的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["保护"]
        self.web_search_tool.search.side_effect = Exception("工具不可用")

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(
                side_effect=Exception("ES搜索失败"))
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]
            self.assertIn("保护", gathered_data)
            self.assertIn("向量检索异常: ES搜索失败", gathered_data)
            print("✅ 搜索工具不可用时正确显示错误信息")

    @async_test
    async def test_researcher_node_multiple_queries(self):
        """测试多个搜索查询的情况"""
        print("\n=== 测试多个搜索查询的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["变电站", "配电", "调度"]
        self.web_search_tool.search.return_value = "网络搜索结果"

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]

            self.assertIn("变电站", gathered_data)
            self.assertIn("配电", gathered_data)
            self.assertIn("调度", gathered_data)
            self.assertEqual(self.web_search_tool.search.call_count, 3)
            self.assertEqual(mock_es_instance.search.call_count, 3)
            print("✅ 多查询搜索成功，所有查询都被执行")

    @async_test
    async def test_researcher_node_empty_search_results(self):
        """测试搜索结果为空的情况"""
        print("\n=== 测试搜索结果为空的情况 ===")
        state = ResearchState()
        state["search_queries"] = ["电力监控"]
        self.web_search_tool.search.return_value = ""

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]
            self.assertIn("未找到相关搜索结果", gathered_data)
            print("✅ 空搜索结果时正确显示未找到结果")

    @async_test
    async def test_researcher_node_error_handling(self):
        """测试错误处理的完整性"""
        print("\n=== 测试错误处理的完整性 ===")
        state = ResearchState()
        state["search_queries"] = ["测试查询"]

        # 测试所有工具都失败的情况
        self.web_search_tool.search.side_effect = Exception("网络搜索失败")

        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool, \
             patch('src.doc_agent.graph.nodes.EmbeddingClient') as mock_embedding_client:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(
                side_effect=Exception("ES搜索失败"))
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            # Mock Embedding 客户端
            mock_embedding_instance = Mock()
            mock_embedding_instance.invoke.return_value = "[" + ",".join(
                ["0.1"] * 1536) + "]"
            mock_embedding_client.return_value = mock_embedding_instance

            result = await async_researcher_node(state, self.web_search_tool)
            gathered_data = result["gathered_data"]

            # 应该包含查询信息但显示错误信息
            self.assertIn("测试查询", gathered_data)
            self.assertIn("向量检索异常: ES搜索失败", gathered_data)
            self.assertNotIn("网络搜索失败", gathered_data)
            print("✅ 所有工具失败时正确显示错误信息，不暴露网络搜索错误")


if __name__ == "__main__":
    unittest.main()
