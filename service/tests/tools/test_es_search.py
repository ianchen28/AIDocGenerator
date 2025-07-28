from unittest.mock import patch

import pytest

from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools.es_service import ESSearchResult


class TestESSearchTool:
    """ESSearchTool测试类"""

    @pytest.fixture
    def mock_es_search_results(self):
        """模拟ES搜索结果"""
        return [
            ESSearchResult(id="doc1",
                           original_content="这是第一个文档的原始内容，包含人工智能相关信息。",
                           div_content="人工智能在医疗诊断中的应用",
                           source="medical_ai.pdf",
                           score=0.95,
                           metadata={
                               "category": "AI",
                               "date": "2024-01-01"
                           },
                           alias_name="documents"),
            ESSearchResult(id="doc2",
                           original_content="第二个文档关于机器学习算法的详细说明。",
                           div_content="机器学习算法详解",
                           source="ml_algorithms.pdf",
                           score=0.87,
                           metadata={
                               "category": "ML",
                               "date": "2024-01-02"
                           },
                           alias_name="papers"),
            ESSearchResult(id="doc3",
                           original_content="深度学习在计算机视觉中的最新进展。",
                           div_content="深度学习与计算机视觉",
                           source="deep_learning_vision.pdf",
                           score=0.82,
                           metadata={
                               "category": "DL",
                               "date": "2024-01-03"
                           },
                           alias_name="reports")
        ]

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @patch('src.doc_agent.tools.es_service.ESService.search_multiple_indices')
    @pytest.mark.asyncio
    async def test_search_logic(self, mock_search_multiple,
                                mock_discover_indices, mock_es_search_results):
        """测试搜索逻辑"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }, {
            "name": "papers",
            "vector_dims": 1536
        }, {
            "name": "reports",
            "vector_dims": 1536
        }]
        mock_search_multiple.return_value = mock_es_search_results

        # 实例化ESSearchTool - 使用正确的ES配置
        search_tool = ESSearchTool(hosts=[
            "https://10.238.130.43:9200",
            "https://10.238.130.44:9200",
            "https://10.238.130.45:9200",
        ],
                                   username="devops",
                                   password="mQxMg8wEKnN1WExz",
                                   index_prefix="test",
                                   timeout=30)

        # 执行搜索
        results = await search_tool.search("人工智能", top_k=3)

        # 验证结果
        assert len(results) == 3
        assert isinstance(results[0], ESSearchResult)
        assert results[0].id == "doc1"
        assert results[0].score == 0.95
        assert "人工智能" in results[0].div_content
        assert results[0].source == "medical_ai.pdf"

        # 验证搜索调用
        mock_search_multiple.assert_called_once()
        call_args = mock_search_multiple.call_args
        assert call_args[1]["query"] == "人工智能"
        assert call_args[1]["top_k"] == 3

        # 清理
        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @patch('src.doc_agent.tools.es_service.ESService.search')
    @pytest.mark.asyncio
    async def test_search_with_vector(self, mock_search, mock_discover_indices,
                                      mock_es_search_results):
        """测试带向量的搜索"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }]
        mock_search.return_value = mock_es_search_results

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 模拟查询向量
        query_vector = [0.1] * 1536

        # 执行向量搜索
        results = await search_tool.search(query="机器学习",
                                           query_vector=query_vector,
                                           top_k=2)

        # 验证结果
        assert len(results) == 3  # mock返回3个结果
        assert results[0].score > 0

        # 验证向量搜索调用
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]["query_vector"] == query_vector
        assert call_args[1]["top_k"] == 2

        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @patch('src.doc_agent.tools.es_service.ESService.search_multiple_indices')
    @pytest.mark.asyncio
    async def test_multiple_indices_search(self, mock_search_multiple,
                                           mock_discover_indices,
                                           mock_es_search_results):
        """测试多索引搜索"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }, {
            "name": "papers",
            "vector_dims": 1536
        }, {
            "name": "reports",
            "vector_dims": 1536
        }]
        mock_search_multiple.return_value = mock_es_search_results

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 执行多索引搜索
        results = await search_tool.search(query="深度学习",
                                           use_multiple_indices=True,
                                           top_k=5)

        # 验证结果
        assert len(results) == 3
        assert all(isinstance(r, ESSearchResult) for r in results)

        # 验证多索引搜索调用
        mock_search_multiple.assert_called_once()
        call_args = mock_search_multiple.call_args
        assert len(call_args[1]["indices"]) == 3
        assert call_args[1]["query"] == "深度学习"

        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @patch('src.doc_agent.tools.es_service.ESService.search')
    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_search,
                                       mock_discover_indices,
                                       mock_es_search_results):
        """测试带过滤条件的搜索"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }]
        mock_search.return_value = mock_es_search_results

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 定义过滤条件
        filters = {"source": "*.pdf", "category": "AI"}

        # 执行带过滤条件的搜索
        results = await search_tool.search(query="人工智能",
                                           filters=filters,
                                           top_k=3)

        # 验证结果
        assert len(results) == 3

        # 验证过滤条件传递
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]["filters"] == filters

        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @pytest.mark.asyncio
    async def test_no_available_indices(self, mock_discover_indices):
        """测试没有可用索引的情况"""
        # 配置mock返回空列表
        mock_discover_indices.return_value = []

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 执行搜索
        results = await search_tool.search("测试查询")

        # 验证返回空列表
        assert results == []

        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @patch('src.doc_agent.tools.es_service.ESService.search')
    @pytest.mark.asyncio
    async def test_hybrid_search(self, mock_search, mock_discover_indices,
                                 mock_es_search_results):
        """测试混合搜索"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }]
        mock_search.return_value = mock_es_search_results

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 模拟查询向量
        query_vector = [0.1] * 1536

        # 执行混合搜索
        results = await search_tool.search_with_hybrid(
            query="自然语言处理", query_vector=query_vector, top_k=3)

        # 验证结果
        assert len(results) == 3
        assert all(isinstance(r, ESSearchResult) for r in results)

        # 验证混合搜索调用
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]["query_vector"] == query_vector
        assert call_args[1]["query"] == "自然语言处理"

        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @pytest.mark.asyncio
    async def test_get_available_indices(self, mock_discover_indices):
        """测试获取可用索引"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }, {
            "name": "papers",
            "vector_dims": 1536
        }]

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 获取可用索引
        indices = await search_tool.get_available_indices()

        # 验证结果
        assert len(indices) == 2
        assert "documents" in indices
        assert "papers" in indices

        await search_tool.close()

    @patch(
        'src.doc_agent.tools.es_discovery.ESDiscovery.discover_knowledge_indices'
    )
    @patch('src.doc_agent.tools.es_service.ESService.search')
    @pytest.mark.asyncio
    async def test_search_with_config(self, mock_search, mock_discover_indices,
                                      mock_es_search_results):
        """测试带配置参数的搜索"""
        # 配置mock
        mock_discover_indices.return_value = [{
            "name": "documents",
            "vector_dims": 1536
        }]
        mock_search.return_value = mock_es_search_results

        search_tool = ESSearchTool(hosts=["localhost:9200"],
                                   username="test_user",
                                   password="test_pass")

        # 定义配置参数
        config = {"vector_recall_size": 5, "min_score": 0.5}

        # 执行带配置的搜索
        results = await search_tool.search(query="机器学习",
                                           config=config,
                                           top_k=3)

        # 验证结果
        assert len(results) == 3

        # 验证配置参数传递
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]["top_k"] == 5  # vector_recall_size

        await search_tool.close()
