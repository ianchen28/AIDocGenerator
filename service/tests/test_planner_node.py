#!/usr/bin/env python3
"""
测试 planner_node 功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test_base import TestBase, setup_paths

# 设置测试环境
setup_paths()

from src.doc_agent.graph.nodes import planner_node
from src.doc_agent.utils import parse_planner_response
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.llm_clients import get_llm_client


class TestPlannerNode(TestBase):
    """测试 planner_node 功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 获取 LLM 客户端
        self.llm_client = get_llm_client("qwen_2_5_235b_a22b")

    def test_planner_node_basic(self):
        """测试基本的 planner_node 功能"""
        print("=== 测试 planner_node 基本功能 ===")

        # 创建测试状态
        state = ResearchState(topic="人工智能在医疗领域的应用",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        # 调用 planner_node
        result = planner_node(state, self.llm_client)

        # 验证结果
        assert "research_plan" in result
        assert "search_queries" in result
        assert isinstance(result["research_plan"], str)
        assert isinstance(result["search_queries"], list)
        assert len(result["search_queries"]) > 0

        print(f"✅ 研究计划生成成功")
        print(f"研究计划长度: {len(result['research_plan'])} 字符")
        print(f"搜索查询数量: {len(result['search_queries'])}")
        print(f"前3个搜索查询: {result['search_queries'][:3]}")

    def test_planner_node_empty_topic(self):
        """测试空主题的情况"""
        print("=== 测试空主题处理 ===")

        state = ResearchState(topic="",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        try:
            result = planner_node(state, self.llm_client)
            print("❌ 应该抛出异常但没有")
        except ValueError as e:
            print(f"✅ 正确处理空主题: {e}")

    def test_parse_json_response_valid(self):
        """测试有效的 JSON 响应解析"""
        print("=== 测试有效的 JSON 响应解析 ===")

        # 测试正常的 JSON 响应
        response = '''
{
    "research_plan": "1. 了解人工智能的基本概念和技术 2. 研究医疗领域的应用场景 3. 分析现有案例和效果",
    "search_queries": ["人工智能医疗应用案例", "AI诊断技术最新发展", "医疗AI伦理问题", "智能医疗设备介绍"]
}
'''

        research_plan, search_queries = parse_planner_response(response)

        assert "人工智能的基本概念" in research_plan
        assert len(search_queries) == 4
        assert "人工智能医疗应用案例" in search_queries

        print(f"✅ JSON 响应解析成功")
        print(f"研究计划: {research_plan[:100]}...")
        print(f"搜索查询: {search_queries}")

    def test_parse_json_response_with_code_blocks(self):
        """测试带有代码块的 JSON 响应解析"""
        print("=== 测试带有代码块的 JSON 响应解析 ===")

        # 测试带有 ```json 代码块的响应
        response = '''```json
{
    "research_plan": "详细的研究计划内容",
    "search_queries": ["查询1", "查询2", "查询3"]
}
```'''

        research_plan, search_queries = parse_planner_response(response)

        assert research_plan == "详细的研究计划内容"
        assert len(search_queries) == 3
        assert "查询1" in search_queries

        print(f"✅ 代码块 JSON 响应解析成功")
        print(f"研究计划: {research_plan}")
        print(f"搜索查询: {search_queries}")

    def test_parse_json_response_invalid(self):
        """测试无效的 JSON 响应解析"""
        print("=== 测试无效的 JSON 响应解析 ===")

        # 测试格式不正确的响应
        response = "这是一个没有 JSON 格式的响应"

        try:
            research_plan, search_queries = parse_planner_response(response)
            print("❌ 应该抛出异常但没有")
        except ValueError as e:
            print(f"✅ 正确处理无效 JSON: {e}")

    def test_parse_json_response_missing_fields(self):
        """测试缺少必需字段的 JSON 响应"""
        print("=== 测试缺少必需字段的 JSON 响应 ===")

        # 测试缺少必需字段的响应
        response = '{"research_plan": "只有研究计划"}'

        try:
            research_plan, search_queries = parse_planner_response(response)
            print("❌ 应该抛出异常但没有")
        except ValueError as e:
            print(f"✅ 正确处理缺少字段: {e}")

    def test_parse_json_response_wrong_types(self):
        """测试数据类型错误的 JSON 响应"""
        print("=== 测试数据类型错误的 JSON 响应 ===")

        # 测试数据类型错误的响应
        response = '{"research_plan": 123, "search_queries": "不是列表"}'

        try:
            research_plan, search_queries = parse_planner_response(response)
            print("❌ 应该抛出异常但没有")
        except ValueError as e:
            print(f"✅ 正确处理类型错误: {e}")

    def test_planner_node_error_handling(self):
        """测试错误处理"""
        print("=== 测试错误处理 ===")

        # 创建一个会失败的 LLM 客户端（通过传递无效参数）
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

        # 应该返回默认计划而不是崩溃
        result = planner_node(state, mock_client)

        assert "research_plan" in result
        assert "search_queries" in result
        assert "测试主题" in result["research_plan"]

        print(f"✅ 错误处理成功")
        print(f"默认研究计划: {result['research_plan']}")
        print(f"默认搜索查询: {result['search_queries']}")


def test_planner_node_integration():
    """集成测试"""
    print("=== planner_node 集成测试 ===")

    try:
        # 获取 LLM 客户端
        llm_client = get_llm_client("qwen_2_5_235b_a22b")

        # 创建测试状态
        state = ResearchState(topic="区块链技术在供应链管理中的应用",
                              research_plan="",
                              search_queries=[],
                              gathered_data="",
                              final_document="",
                              messages=[])

        # 调用 planner_node
        result = planner_node(state, llm_client)

        print(f"✅ 集成测试成功")
        print(f"主题: {state['topic']}")
        print(f"研究计划长度: {len(result['research_plan'])} 字符")
        print(f"搜索查询数量: {len(result['search_queries'])}")
        print(f"研究计划预览: {result['research_plan'][:200]}...")
        print(f"搜索查询: {result['search_queries']}")

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        raise


if __name__ == "__main__":
    # 运行测试
    test_planner_node_integration()
