# service/tests/test_researcher_node.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.doc_agent.graph.nodes import async_researcher_node
from src.doc_agent.graph.state import ResearchState


class TestResearcherNode:
    """测试 async_researcher_node 函数"""

    @pytest.mark.asyncio
    async def test_researcher_node_no_queries(self):
        """测试没有搜索查询的情况"""
        state = ResearchState()
        web_search_tool = Mock()

        result = await async_researcher_node(state, web_search_tool)

        assert result["gathered_data"] == "没有搜索查询需要执行"
        web_search_tool.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_researcher_node_with_queries(self):
        """测试有搜索查询的情况"""
        state = ResearchState()
        state["search_queries"] = ["电力", "电网"]

        # 模拟网络搜索工具
        web_search_tool = Mock()
        web_search_tool.search.return_value = "网络搜索结果内容"

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            # 验证调用次数
            assert web_search_tool.search.call_count == 2
            assert mock_es_instance.search.call_count == 2

            # 验证结果包含搜索内容
            gathered_data = result["gathered_data"]
            assert "电力" in gathered_data
            assert "电网" in gathered_data
            assert "网络搜索结果内容" in gathered_data
            assert "ES搜索结果内容" in gathered_data

    @pytest.mark.asyncio
    async def test_researcher_node_web_search_failure(self):
        """测试网络搜索失败的情况"""
        state = ResearchState()
        state["search_queries"] = ["变电站"]

        # 模拟网络搜索失败
        web_search_tool = Mock()
        web_search_tool.search.side_effect = Exception("网络搜索失败")

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]
            assert "网络搜索失败" not in gathered_data  # 错误信息不应该出现在结果中
            assert "ES搜索结果内容" in gathered_data

    @pytest.mark.asyncio
    async def test_researcher_node_es_search_failure(self):
        """测试ES搜索失败的情况"""
        state = ResearchState()
        state["search_queries"] = ["配电"]

        # 模拟网络搜索成功
        web_search_tool = Mock()
        web_search_tool.search.return_value = "网络搜索结果内容"

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(
                side_effect=Exception("ES搜索失败"))
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]
            assert "网络搜索结果内容" in gathered_data
            assert "ES搜索失败" not in gathered_data  # 错误信息不应该出现在结果中

    @pytest.mark.asyncio
    async def test_researcher_node_mock_web_search_results(self):
        """测试网络搜索返回模拟结果的情况"""
        state = ResearchState()
        state["search_queries"] = ["调度"]

        # 模拟网络搜索返回模拟结果
        web_search_tool = Mock()
        web_search_tool.search.return_value = "这是模拟的搜索结果，包含模拟关键词"

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]
            # 模拟结果应该被跳过
            assert "这是模拟的搜索结果" not in gathered_data
            assert "ES搜索结果内容" in gathered_data

    @pytest.mark.asyncio
    async def test_researcher_node_async_es_search(self):
        """测试异步ES搜索的情况"""
        state = ResearchState()
        state["search_queries"] = ["设备"]

        # 模拟网络搜索
        web_search_tool = Mock()
        web_search_tool.search.return_value = "网络搜索结果内容"

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="异步ES搜索结果内容")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]
            assert "网络搜索结果内容" in gathered_data
            assert "异步ES搜索结果内容" in gathered_data

    @pytest.mark.asyncio
    async def test_researcher_node_no_search_tools(self):
        """测试搜索工具不可用的情况"""
        state = ResearchState()
        state["search_queries"] = ["保护"]

        # 模拟搜索工具不可用
        web_search_tool = Mock()
        web_search_tool.search.side_effect = Exception("工具不可用")

        # 使用patch模拟ESSearchTool，让async with能正常工作但搜索失败
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            # 模拟ESSearchTool实例，但搜索方法失败
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(
                side_effect=Exception("ES搜索失败"))
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]
            # 应该包含查询信息，但显示未找到结果
            assert "保护" in gathered_data
            assert "未找到相关搜索结果" in gathered_data

    @pytest.mark.asyncio
    async def test_researcher_node_multiple_queries(self):
        """测试多个搜索查询的情况"""
        state = ResearchState()
        state["search_queries"] = ["变电站", "配电", "调度"]

        # 模拟搜索工具
        web_search_tool = Mock()
        web_search_tool.search.return_value = "网络搜索结果"

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="ES搜索结果")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]

            # 验证所有查询都被执行
            assert "变电站" in gathered_data
            assert "配电" in gathered_data
            assert "调度" in gathered_data

            # 验证调用次数
            assert web_search_tool.search.call_count == 3
            assert mock_es_instance.search.call_count == 3

    @pytest.mark.asyncio
    async def test_researcher_node_empty_search_results(self):
        """测试搜索结果为空的情况"""
        state = ResearchState()
        state["search_queries"] = ["电力监控"]

        # 模拟搜索工具返回空结果
        web_search_tool = Mock()
        web_search_tool.search.return_value = ""

        # 使用patch模拟ESSearchTool
        with patch('src.doc_agent.graph.nodes.ESSearchTool') as mock_es_tool:
            mock_es_instance = Mock()
            mock_es_instance.search = AsyncMock(return_value="")
            mock_es_tool.return_value.__aenter__.return_value = mock_es_instance
            mock_es_tool.return_value.__aexit__.return_value = None

            result = await async_researcher_node(state, web_search_tool)

            gathered_data = result["gathered_data"]
            assert "未找到相关搜索结果" in gathered_data


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
