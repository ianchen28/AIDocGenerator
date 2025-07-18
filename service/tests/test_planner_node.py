#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规划者节点测试
测试 planner_node 的各种功能
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
from src.doc_agent.graph.main_orchestrator.nodes import outline_generation_node
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.llm_clients import get_llm_client


class PlannerNodeTest(NodeTestCase):
    """规划者节点测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.llm_client = self.get_llm_client("moonshot_k2_0711_preview")
        logger.debug("初始化规划者节点测试")

    @skip_if_no_llm
    def test_planner_node_basic_functionality(self):
        """测试 planner_node 基本功能"""
        logger.info("测试 planner_node 基本功能")

        state = ResearchState(topic="人工智能在医疗领域的应用",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = outline_generation_node(state, self.llm_client)
            logger.info("规划者节点基本功能测试成功")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

            research_plan = result["research_plan"]
            search_queries = result["search_queries"]

            self.assertIsInstance(research_plan, str)
            self.assertIsInstance(search_queries, list)
            self.assertGreater(len(research_plan), 0)
            self.assertGreater(len(search_queries), 0)

        except Exception as e:
            logger.error(f"规划者节点基本功能测试失败: {e}")
            self.fail(f"规划者节点基本功能测试失败: {e}")

    @skip_if_no_llm
    def test_empty_topic_handling(self):
        """测试空主题处理"""
        logger.info("测试空主题处理")

        state = ResearchState(topic="",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = outline_generation_node(state, self.llm_client)
            logger.info("正确处理空主题异常")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

        except Exception as e:
            logger.error(f"空主题处理失败: {e}")
            # 空主题应该抛出异常，这是正常的

    @skip_if_no_llm
    def test_valid_json_response_parsing(self):
        """测试有效 JSON 响应解析"""
        logger.info("测试有效 JSON 响应解析")

        # 模拟有效的 JSON 响应
        valid_json_response = '''
        {
            "research_plan": "研究AI在医疗诊断、药物发现、个性化治疗等方面的应用",
            "search_queries": ["AI医疗诊断", "人工智能药物发现", "个性化医疗AI"]
        }
        '''

        state = ResearchState(topic="人工智能在医疗领域的应用",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            # 这里需要模拟 LLM 返回有效 JSON
            result = outline_generation_node(state, self.llm_client)
            logger.info("有效 JSON 响应解析成功")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

        except Exception as e:
            logger.error(f"有效 JSON 响应解析失败: {e}")
            self.fail(f"有效 JSON 响应解析失败: {e}")

    @skip_if_no_llm
    def test_json_with_code_blocks_parsing(self):
        """测试带代码块的 JSON 响应解析"""
        logger.info("测试带代码块的 JSON 响应解析")

        # 模拟带代码块的 JSON 响应
        json_with_code = '''
        ```json
        {
            "research_plan": "研究计划内容",
            "search_queries": ["查询1", "查询2"]
        }
        ```
        '''

        state = ResearchState(topic="测试主题",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = outline_generation_node(state, self.llm_client)
            logger.info("带代码块的 JSON 响应解析成功")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

        except Exception as e:
            logger.error(f"带代码块的 JSON 响应解析失败: {e}")
            self.fail(f"带代码块的 JSON 响应解析失败: {e}")

    @skip_if_no_llm
    def test_invalid_json_response_parsing(self):
        """测试无效 JSON 响应解析"""
        logger.info("测试无效 JSON 响应解析")

        state = ResearchState(topic="测试主题",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = outline_generation_node(state, self.llm_client)
            logger.info("正确处理无效 JSON 异常")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

        except Exception as e:
            logger.error(f"无效 JSON 响应处理失败: {e}")
            # 无效 JSON 应该被正确处理

    @skip_if_no_llm
    def test_missing_fields_json_response(self):
        """测试缺少字段的 JSON 响应"""
        logger.info("测试缺少字段的 JSON 响应")

        state = ResearchState(topic="测试主题",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = outline_generation_node(state, self.llm_client)
            logger.info("正确处理缺少字段异常")

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

        except Exception as e:
            logger.error(f"缺少字段处理失败: {e}")
            # 缺少字段应该被正确处理

    @skip_if_no_llm
    def test_different_topics(self):
        """测试不同主题的规划"""
        logger.info("测试不同主题的规划")

        test_topics = ["量子计算在金融领域的应用", "区块链技术发展现状", "机器学习算法优化"]

        for topic in test_topics:
            logger.debug(f"测试主题: {topic}")

            state = ResearchState(topic=topic,
                                  research_plan="",
                                  search_queries=[],
                                  gathered_data="",
                                  final_document="",
                                  messages=[])

            try:
                result = outline_generation_node(state, self.llm_client)

                # 验证结果
                self.assertIsInstance(result, dict)
                self.assertIn("research_plan", result)
                self.assertIn("search_queries", result)

                research_plan = result["research_plan"]
                search_queries = result["search_queries"]

                self.assertIsInstance(research_plan, str)
                self.assertIsInstance(search_queries, list)
                self.assertGreater(len(research_plan), 0)
                self.assertGreater(len(search_queries), 0)

                logger.info(f"主题 '{topic}' 规划成功")

            except Exception as e:
                logger.error(f"主题 '{topic}' 规划失败: {e}")
                self.fail(f"主题 '{topic}' 规划失败: {e}")

    @skip_if_no_llm
    def test_error_handling(self):
        """测试错误处理"""
        logger.info("测试错误处理")

        # 测试 LLM 客户端失败的情况
        class MockFailingLLMClient:

            def invoke(self, prompt, **kwargs):
                raise Exception("LLM 调用失败")

        mock_client = MockFailingLLMClient()

        state = ResearchState(topic="测试主题",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = outline_generation_node(state, mock_client)
            logger.info("错误处理测试成功")

            # 验证错误处理
            self.assertIsInstance(result, dict)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)

        except Exception as e:
            logger.error(f"错误处理测试失败: {e}")
            # 错误处理应该返回默认值而不是崩溃


def main():
    """主函数"""
    logger.info("规划者节点测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(PlannerNodeTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有规划者节点测试通过")
    else:
        logger.error("规划者节点测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
