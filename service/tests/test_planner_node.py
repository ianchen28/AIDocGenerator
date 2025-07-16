#!/usr/bin/env python3
"""
测试 planner_node 功能
"""

from test_base import NodeTestCase, skip_if_no_llm
from src.doc_agent.graph.nodes import planner_node
from src.doc_agent.utils import parse_planner_response
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.llm_clients import get_llm_client
import unittest


class PlannerNodeTest(NodeTestCase):
    """planner_node 节点功能测试"""

    def setUp(self):
        super().setUp()
        self.llm_client = self.get_llm_client("qwen_2_5_235b_a22b")

    @skip_if_no_llm
    def test_planner_node_basic(self):
        """测试基本 planner_node 功能"""
        print("\n=== 测试 planner_node 基本功能 ===")
        state = ResearchState(topic="人工智能在医疗领域的应用",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])
        result = planner_node(state, self.llm_client)
        self.assertIn("research_plan", result)
        self.assertIn("search_queries", result)
        self.assertIsInstance(result["research_plan"], str)
        self.assertIsInstance(result["search_queries"], list)
        self.assertGreater(len(result["search_queries"]), 0)
        print(
            f"✅ 研究计划生成成功，长度: {len(result['research_plan'])} 字符，搜索查询数: {len(result['search_queries'])}"
        )

    def test_planner_node_empty_topic(self):
        """测试空主题处理"""
        print("\n=== 测试空主题处理 ===")
        state = ResearchState(topic="",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])
        with self.assertRaises(ValueError):
            planner_node(state, self.llm_client)
        print("✅ 正确处理空主题异常")

    def test_parse_json_response_valid(self):
        """测试有效 JSON 响应解析"""
        print("\n=== 测试有效 JSON 响应解析 ===")
        response = '''
{
    "research_plan": "1. 了解人工智能的基本概念和技术 2. 研究医疗领域的应用场景 3. 分析现有案例和效果",
    "search_queries": ["人工智能医疗应用案例", "AI诊断技术最新发展", "医疗AI伦理问题", "智能医疗设备介绍"]
}
'''
        research_plan, search_queries = parse_planner_response(response)
        self.assertIn("人工智能的基本概念", research_plan)
        self.assertEqual(len(search_queries), 4)
        self.assertIn("人工智能医疗应用案例", search_queries)
        print(
            f"✅ JSON 响应解析成功，研究计划: {research_plan[:30]}...，搜索查询: {search_queries}"
        )

    def test_parse_json_response_with_code_blocks(self):
        """测试带代码块的 JSON 响应解析"""
        print("\n=== 测试带代码块的 JSON 响应解析 ===")
        response = '''```json\n{\n    "research_plan": "详细的研究计划内容",\n    "search_queries": ["查询1", "查询2", "查询3"]\n}\n```'''
        research_plan, search_queries = parse_planner_response(response)
        self.assertEqual(research_plan, "详细的研究计划内容")
        self.assertEqual(len(search_queries), 3)
        self.assertIn("查询1", search_queries)
        print(
            f"✅ 代码块 JSON 响应解析成功，研究计划: {research_plan}，搜索查询: {search_queries}")

    def test_parse_json_response_invalid(self):
        """测试无效 JSON 响应解析"""
        print("\n=== 测试无效 JSON 响应解析 ===")
        response = "这是一个没有 JSON 格式的响应"
        with self.assertRaises(ValueError):
            parse_planner_response(response)
        print("✅ 正确处理无效 JSON 异常")

    def test_parse_json_response_missing_fields(self):
        """测试缺少字段的 JSON 响应"""
        print("\n=== 测试缺少字段的 JSON 响应 ===")
        response = '{"research_plan": "只有研究计划"}'
        with self.assertRaises(ValueError):
            parse_planner_response(response)
        print("✅ 正确处理缺少字段异常")

    def test_parse_json_response_wrong_types(self):
        """测试类型错误的 JSON 响应"""
        print("\n=== 测试类型错误的 JSON 响应 ===")
        response = '{"research_plan": 123, "search_queries": "不是列表"}'
        with self.assertRaises(ValueError):
            parse_planner_response(response)
        print("✅ 正确处理类型错误异常")

    @skip_if_no_llm
    def test_planner_node_error_handling(self):
        """测试 LLM 调用失败时的容错"""
        print("\n=== 测试 LLM 调用失败容错 ===")

        class MockLLMClient:

            def invoke(self, prompt, **kwargs):
                raise Exception("模拟 LLM 调用失败")

        mock_client = MockLLMClient()
        state = ResearchState(topic="测试主题",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])
        result = planner_node(state, mock_client)
        self.assertIn("research_plan", result)
        self.assertIn("search_queries", result)
        self.assertIn("测试主题", result["research_plan"])
        print(
            f"✅ 错误处理成功，默认研究计划: {result['research_plan']}，默认搜索查询: {result['search_queries']}"
        )

    @skip_if_no_llm
    def test_planner_node_different_topics(self):
        """测试不同主题的 planner_node"""
        print("\n=== 测试不同主题的 planner_node ===")
        topics = ["区块链技术在供应链管理中的应用", "量子计算的发展现状和前景", "可再生能源技术的创新"]
        for topic in topics:
            state = ResearchState(topic=topic,
                                  research_plan="",
                                  search_queries=[],
                                  gathered_data="",
                                  final_document="",
                                  messages=[])
            result = planner_node(state, self.llm_client)
            self.assertIn("research_plan", result)
            self.assertIn("search_queries", result)
            self.assertGreater(len(result["search_queries"]), 0)
            print(
                f"✅ 主题 '{topic}' 处理成功，研究计划长度: {len(result['research_plan'])} 字符，搜索查询数: {len(result['search_queries'])}"
            )


if __name__ == "__main__":
    unittest.main()
