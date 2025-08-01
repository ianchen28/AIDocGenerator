from unittest.mock import patch

import pytest

from doc_agent.tools.es_service import ESSearchResult
from doc_agent.tools.reranker import RerankedSearchResult, RerankerTool


class TestRerankerTool:
    """RerankerTool测试类"""

    @pytest.fixture
    def sample_search_results(self):
        """创建样例搜索结果"""
        return [
            ESSearchResult(id="doc1",
                           original_content="这是第一个文档的原始内容",
                           div_content="人工智能在医疗诊断中的应用",
                           source="medical_ai.pdf",
                           score=0.8,
                           metadata={"category": "AI"},
                           alias_name="documents"),
            ESSearchResult(id="doc2",
                           original_content="这是第二个文档的原始内容",
                           div_content="机器学习算法详解",
                           source="ml_algorithms.pdf",
                           score=0.9,
                           metadata={"category": "ML"},
                           alias_name="papers"),
            ESSearchResult(id="doc3",
                           original_content="这是第三个文档的原始内容",
                           div_content="深度学习与计算机视觉",
                           source="deep_learning_vision.pdf",
                           score=0.7,
                           metadata={"category": "DL"},
                           alias_name="reports")
        ]

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_sorts_documents_by_score(self, mock_invoke,
                                             sample_search_results):
        """测试重排序按评分排序文档"""
        # 配置mock返回重排序结果
        mock_invoke.return_value = {
            "sorted_doc_list": [{
                "text": "机器学习算法详解",
                "rerank_score": 0.9
            }, {
                "text": "深度学习与计算机视觉",
                "rerank_score": 0.5
            }, {
                "text": "人工智能在医疗诊断中的应用",
                "rerank_score": 0.1
            }]
        }

        # 实例化RerankerTool
        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序
        reranked_results = reranker_tool.rerank_search_results(
            query="机器学习", search_results=sample_search_results)

        # 验证结果按重排序评分正确排序
        assert len(reranked_results) == 3
        assert reranked_results[0].rerank_score == 0.9
        assert reranked_results[0].div_content == "机器学习算法详解"
        assert reranked_results[1].rerank_score == 0.5
        assert reranked_results[1].div_content == "深度学习与计算机视觉"
        assert reranked_results[2].rerank_score == 0.1
        assert reranked_results[2].div_content == "人工智能在医疗诊断中的应用"

        # 验证API调用
        mock_invoke.assert_called_once()
        call_args = mock_invoke.call_args
        assert call_args[1]["prompt"] == "机器学习"
        assert len(call_args[1]["documents"]) == 3

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_with_top_k_limit(self, mock_invoke, sample_search_results):
        """测试带top_k限制的重排序"""
        # 配置mock返回重排序结果
        mock_invoke.return_value = {
            "sorted_doc_list": [{
                "text": "机器学习算法详解",
                "rerank_score": 0.9
            }, {
                "text": "深度学习与计算机视觉",
                "rerank_score": 0.5
            }, {
                "text": "人工智能在医疗诊断中的应用",
                "rerank_score": 0.1
            }]
        }

        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序，限制返回2个结果
        reranked_results = reranker_tool.rerank_search_results(
            query="机器学习", search_results=sample_search_results, top_k=2)

        # 验证返回所有3个结果（因为_parse_rerank_result会处理所有返回的文档）
        assert len(reranked_results) == 3
        assert reranked_results[0].rerank_score == 0.9
        assert reranked_results[1].rerank_score == 0.5
        assert reranked_results[2].rerank_score == 0.1

        # 验证API调用参数
        mock_invoke.assert_called_once()
        call_args = mock_invoke.call_args
        assert call_args[1]["size"] == 2

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_with_empty_results(self, mock_invoke):
        """测试空搜索结果的重排序"""
        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序，输入空列表
        reranked_results = reranker_tool.rerank_search_results(
            query="测试查询", search_results=[])

        # 验证返回空列表
        assert reranked_results == []
        # 验证没有调用API
        mock_invoke.assert_not_called()

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_with_invalid_response(self, mock_invoke,
                                          sample_search_results):
        """测试无效API响应的处理"""
        # 配置mock返回无效响应
        mock_invoke.return_value = {"error": "Invalid response"}

        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序
        reranked_results = reranker_tool.rerank_search_results(
            query="测试查询", search_results=sample_search_results)

        # 验证回退到原始结果
        assert len(reranked_results) == 3
        # 验证重排序评分等于原始评分（回退情况）
        for result in reranked_results:
            assert result.rerank_score == result.score

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_with_missing_documents(self, mock_invoke,
                                           sample_search_results):
        """测试重排序结果中缺少文档的处理"""
        # 配置mock返回部分文档
        mock_invoke.return_value = {
            "sorted_doc_list": [{
                "text": "机器学习算法详解",
                "rerank_score": 0.9
            }
                                # 缺少其他两个文档
                                ]
        }

        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序
        reranked_results = reranker_tool.rerank_search_results(
            query="测试查询", search_results=sample_search_results)

        # 验证只返回能找到的文档
        assert len(reranked_results) == 1
        assert reranked_results[0].div_content == "机器学习算法详解"
        assert reranked_results[0].rerank_score == 0.9

    def test_get_top_results(self, sample_search_results):
        """测试获取前top_k个结果"""
        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 创建重排序结果（按评分降序）
        reranked_results = [
            RerankedSearchResult(id="doc2",
                                 original_content="第二个文档",
                                 div_content="机器学习算法详解",
                                 score=0.9,
                                 rerank_score=0.9),
            RerankedSearchResult(id="doc1",
                                 original_content="第一个文档",
                                 div_content="人工智能在医疗诊断中的应用",
                                 score=0.8,
                                 rerank_score=0.5),
            RerankedSearchResult(id="doc3",
                                 original_content="第三个文档",
                                 div_content="深度学习与计算机视觉",
                                 score=0.7,
                                 rerank_score=0.1)
        ]

        # 获取前2个结果
        top_results = reranker_tool.get_top_results(reranked_results, top_k=2)

        # 验证结果
        assert len(top_results) == 2
        assert top_results[0].rerank_score == 0.9
        assert top_results[1].rerank_score == 0.5

    def test_analyze_rerank_effectiveness(self, sample_search_results):
        """测试重排序效果分析"""
        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 创建重排序结果
        reranked_results = [
            RerankedSearchResult(id="doc1",
                                 original_content="第一个文档",
                                 div_content="机器学习算法详解",
                                 score=0.8,
                                 rerank_score=0.9),
            RerankedSearchResult(id="doc2",
                                 original_content="第二个文档",
                                 div_content="人工智能在医疗诊断中的应用",
                                 score=0.9,
                                 rerank_score=0.5),
            RerankedSearchResult(id="doc3",
                                 original_content="第三个文档",
                                 div_content="深度学习与计算机视觉",
                                 score=0.7,
                                 rerank_score=0.1)
        ]

        # 分析效果
        analysis = reranker_tool.analyze_rerank_effectiveness(
            reranked_results, "机器学习")

        # 验证分析结果
        assert analysis["total_results"] == 3
        assert analysis["top_score"] == 0.9
        assert analysis["bottom_score"] == 0.1
        assert analysis["score_range"] == 0.8
        assert analysis["effectiveness"] == "moderate"
        assert analysis["relevance_score"] > 0  # 应该有相关性

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_with_empty_document_content(self, mock_invoke):
        """测试文档内容为空的情况"""
        # 创建包含空内容的搜索结果
        search_results = [
            ESSearchResult(id="doc1",
                           original_content="",
                           div_content="",
                           source="empty.pdf",
                           score=0.8),
            ESSearchResult(id="doc2",
                           original_content="有内容的文档",
                           div_content="机器学习算法详解",
                           source="valid.pdf",
                           score=0.9)
        ]

        # 配置mock
        mock_invoke.return_value = {
            "sorted_doc_list": [{
                "text": "机器学习算法详解",
                "rerank_score": 0.9
            }]
        }

        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序
        reranked_results = reranker_tool.rerank_search_results(
            query="机器学习", search_results=search_results)

        # 验证只处理有内容的文档
        assert len(reranked_results) == 1
        assert reranked_results[0].div_content == "机器学习算法详解"

        # 验证API调用只包含有内容的文档
        mock_invoke.assert_called_once()
        call_args = mock_invoke.call_args
        assert len(call_args[1]["documents"]) == 1
        assert call_args[1]["documents"][0] == "机器学习算法详解"

    def test_reranked_search_result_creation(self):
        """测试RerankedSearchResult的创建"""
        # 创建重排序结果
        reranked_result = RerankedSearchResult(id="test_doc",
                                               original_content="原始内容",
                                               div_content="切分内容",
                                               source="test.pdf",
                                               score=0.8,
                                               rerank_score=0.9,
                                               metadata={"category": "test"},
                                               alias_name="test_index")

        # 验证所有字段
        assert reranked_result.id == "test_doc"
        assert reranked_result.original_content == "原始内容"
        assert reranked_result.div_content == "切分内容"
        assert reranked_result.source == "test.pdf"
        assert reranked_result.score == 0.8
        assert reranked_result.rerank_score == 0.9
        assert reranked_result.metadata["category"] == "test"
        assert reranked_result.alias_name == "test_index"

    @patch('src.doc_agent.tools.reranker.RerankerClient.invoke')
    def test_rerank_api_error_handling(self, mock_invoke,
                                       sample_search_results):
        """测试API错误处理"""
        # 配置mock抛出异常
        mock_invoke.side_effect = Exception("API调用失败")

        reranker_tool = RerankerTool(base_url="http://fake", api_key="fake")

        # 执行重排序
        reranked_results = reranker_tool.rerank_search_results(
            query="测试查询", search_results=sample_search_results)

        # 验证回退到原始结果
        assert len(reranked_results) == 3
        # 验证重排序评分等于原始评分（回退情况）
        for result in reranked_results:
            assert result.rerank_score == result.score
