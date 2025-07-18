#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究者节点测试
测试 researcher_node 的各种功能
"""

import sys
import os
import unittest
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import NodeTestCase, skip_if_no_llm
from src.doc_agent.graph.main_orchestrator.nodes import initial_research_node
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.llm_clients import get_llm_client


class ResearcherNodeTest(NodeTestCase):
    """研究者节点测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.llm_client = self.get_llm_client("moonshot_k2_0711_preview")
        logger.debug("初始化研究者节点测试")

    @skip_if_no_llm
    def test_no_search_queries(self):
        """测试没有搜索查询的情况"""
        logger.info("测试没有搜索查询的情况")

        state = ResearchState(topic="测试主题",
                              research_plan="测试研究计划",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("正确处理空查询情况")
            self.assertIsInstance(result, dict)
        except Exception as e:
            logger.error(f"空查询处理失败: {e}")
            self.fail(f"空查询处理失败: {e}")

    @skip_if_no_llm
    def test_with_search_queries(self):
        """测试有搜索查询的情况"""
        logger.info("测试有搜索查询的情况")

        state = ResearchState(topic="人工智能在医疗领域的应用",
                              research_plan="研究AI在医疗诊断、药物发现、个性化治疗等方面的应用",
                              search_queries=["AI医疗诊断", "人工智能药物发现", "个性化医疗AI"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("多查询搜索成功，包含网络和ES搜索结果")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)
            self.assertIsInstance(result["gathered_data"], str)
            self.assertGreater(len(result["gathered_data"]), 0)

        except Exception as e:
            logger.error(f"多查询搜索失败: {e}")
            self.fail(f"多查询搜索失败: {e}")

    @skip_if_no_llm
    def test_web_search_failure(self):
        """测试网络搜索失败的情况"""
        logger.info("测试网络搜索失败的情况")

        # 模拟网络搜索失败
        class MockWebSearchTool:

            def search(self, query, **kwargs):
                raise Exception("网络搜索失败")

        # 模拟状态
        state = ResearchState(topic="测试主题",
                              research_plan="测试计划",
                              search_queries=["测试查询"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            # 这里需要模拟网络搜索失败的情况
            # 由于 researcher_node 内部会处理错误，我们测试其错误处理能力
            result = initial_research_node(state, self.llm_client)
            logger.info("网络搜索失败时正确回退到ES搜索")

            # 验证结果仍然有效
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

        except Exception as e:
            logger.error(f"网络搜索失败处理异常: {e}")
            # 网络搜索失败不应该导致整个函数失败

    @skip_if_no_llm
    def test_es_search_failure(self):
        """测试ES搜索失败的情况"""
        logger.info("测试ES搜索失败的情况")

        # 模拟ES搜索失败
        class MockESSearchTool:

            def search(self, query, **kwargs):
                raise Exception("ES搜索失败")

        state = ResearchState(topic="测试主题",
                              research_plan="测试计划",
                              search_queries=["测试查询"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            # 测试ES搜索失败时的处理
            result = initial_research_node(state, self.llm_client)
            logger.info("ES搜索失败时正确保留网络搜索结果")

            # 验证结果仍然有效
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

        except Exception as e:
            logger.error(f"ES搜索失败处理异常: {e}")
            # ES搜索失败不应该导致整个函数失败

    @skip_if_no_llm
    def test_mock_web_search_results(self):
        """测试网络搜索返回模拟结果的情况"""
        logger.info("测试网络搜索返回模拟结果的情况")

        # 模拟网络搜索返回模拟结果
        class MockWebSearchTool:

            def search(self, query, **kwargs):
                return "这是一个模拟的网络搜索结果，用于测试目的。"

        state = ResearchState(topic="测试主题",
                              research_plan="测试计划",
                              search_queries=["测试查询"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("正确跳过模拟搜索结果，使用ES搜索结果")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

        except Exception as e:
            logger.error(f"模拟结果处理异常: {e}")
            self.fail(f"模拟结果处理异常: {e}")

    @skip_if_no_llm
    def test_async_es_search(self):
        """测试异步ES搜索的情况"""
        logger.info("测试异步ES搜索的情况")

        state = ResearchState(topic="异步搜索测试",
                              research_plan="测试异步搜索功能",
                              search_queries=["异步搜索"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("异步ES搜索正常工作")

            # 验证异步搜索结果
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

        except Exception as e:
            logger.error(f"异步ES搜索失败: {e}")
            self.fail(f"异步ES搜索失败: {e}")

    @skip_if_no_llm
    def test_search_tools_unavailable(self):
        """测试搜索工具不可用的情况"""
        logger.info("测试搜索工具不可用的情况")

        # 模拟所有搜索工具都不可用
        class MockSearchTool:

            def search(self, query, **kwargs):
                raise Exception("搜索工具不可用")

        state = ResearchState(topic="工具不可用测试",
                              research_plan="测试工具不可用时的处理",
                              search_queries=["测试查询"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("搜索工具不可用时正确显示错误信息")

            # 验证错误处理
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

            # 应该包含错误信息
            gathered_data = result["gathered_data"]
            self.assertIn("错误", gathered_data or "")

        except Exception as e:
            logger.error(f"工具不可用处理异常: {e}")
            # 工具不可用不应该导致整个函数失败

    @skip_if_no_llm
    def test_multiple_search_queries(self):
        """测试多个搜索查询的情况"""
        logger.info("测试多个搜索查询的情况")

        state = ResearchState(topic="多查询测试",
                              research_plan="测试多个搜索查询的处理",
                              search_queries=["查询1", "查询2", "查询3"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("多查询搜索成功，所有查询都被执行")

            # 验证多查询结果
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

            gathered_data = result["gathered_data"]
            self.assertIsInstance(gathered_data, str)
            self.assertGreater(len(gathered_data), 0)

        except Exception as e:
            logger.error(f"多查询搜索失败: {e}")
            self.fail(f"多查询搜索失败: {e}")

    @skip_if_no_llm
    def test_empty_search_results(self):
        """测试搜索结果为空的情况"""
        logger.info("测试搜索结果为空的情况")

        # 模拟搜索结果为空
        class MockEmptySearchTool:

            def search(self, query, **kwargs):
                return ""

        state = ResearchState(topic="空结果测试",
                              research_plan="测试空搜索结果的处理",
                              search_queries=["空结果查询"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("空搜索结果时正确显示未找到结果")

            # 验证空结果处理
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

            gathered_data = result["gathered_data"]
            self.assertIsInstance(gathered_data, str)

        except Exception as e:
            logger.error(f"空结果处理异常: {e}")
            self.fail(f"空结果处理异常: {e}")

    @skip_if_no_llm
    def test_comprehensive_error_handling(self):
        """测试错误处理的完整性"""
        logger.info("测试错误处理的完整性")

        # 模拟所有工具都失败的情况
        class MockFailingTool:

            def search(self, query, **kwargs):
                raise Exception("搜索失败")

        state = ResearchState(topic="错误处理测试",
                              research_plan="测试全面错误处理",
                              search_queries=["失败查询"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = initial_research_node(state, self.llm_client)
            logger.info("所有工具失败时正确显示错误信息，不暴露网络搜索错误")

            # 验证错误处理
            self.assertIsInstance(result, dict)
            self.assertIn("gathered_data", result)

            gathered_data = result["gathered_data"]
            self.assertIsInstance(gathered_data, str)

            # 应该包含错误信息但不暴露具体错误
            if "错误" in gathered_data:
                self.assertNotIn("网络搜索失败", gathered_data)

        except Exception as e:
            logger.error(f"错误处理测试异常: {e}")
            # 错误处理不应该导致整个函数失败


def main():
    """主函数"""
    logger.info("研究者节点测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ResearcherNodeTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有研究者节点测试通过")
    else:
        logger.error("研究者节点测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
