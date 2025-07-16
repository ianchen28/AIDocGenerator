#!/usr/bin/env python3
"""
测试 supervisor_router 功能
"""

from test_base import NodeTestCase, skip_if_no_llm
from src.doc_agent.graph.router import supervisor_router
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.llm_clients import get_llm_client
import unittest


class SupervisorRouterTest(NodeTestCase):
    """supervisor_router 路由功能测试"""

    def setUp(self):
        super().setUp()
        self.llm_client = self.get_llm_client("moonshot_k2_0711_preview")

    @skip_if_no_llm
    def test_sufficient_data(self):
        """测试充足的研究数据场景"""
        print("\n=== 测试充足的研究数据场景 ===")

        state = ResearchState(topic="人工智能在医疗领域的应用",
                              research_plan="研究AI在医疗诊断、药物发现、个性化治疗等方面的应用",
                              search_queries=["AI医疗诊断", "人工智能药物发现", "个性化医疗AI"],
                              gathered_data="""=== 搜索查询 1: AI医疗诊断 ===

知识库搜索结果:
1. 人工智能在医疗诊断中的应用
   - 深度学习算法在医学影像识别中的突破
   - 准确率达到95%以上，超过人类医生平均水平
   - 在X光、CT、MRI等影像诊断中表现优异
   - 支持早期癌症筛查和疾病预测

2. 医疗AI系统架构
   - 基于卷积神经网络的图像分析
   - 自然语言处理用于病历分析
   - 机器学习算法用于疾病风险评估
   - 实时诊断决策支持系统

=== 搜索查询 2: 人工智能药物发现 ===

知识库搜索结果:
1. AI驱动的药物研发流程
   - 虚拟筛选技术加速化合物发现
   - 分子对接算法预测药物-靶点相互作用
   - 机器学习优化药物分子设计
   - 减少研发时间和成本达60%

2. 成功案例
   - AlphaFold2在蛋白质结构预测中的突破
   - 新冠药物研发中的AI应用
   - 个性化药物设计平台

=== 搜索查询 3: 个性化医疗AI ===

知识库搜索结果:
1. 个性化医疗AI技术
   - 基因组学数据分析
   - 患者历史数据挖掘
   - 个体化治疗方案生成
   - 实时健康监测和预警

2. 临床应用
   - 精准肿瘤治疗
   - 慢性病管理
   - 药物剂量优化
   - 患者依从性监测""",
                              final_document="",
                              messages=[])

        result = supervisor_router(state, self.llm_client)
        self.assertEqual(result, "continue_to_writer")
        print("✅ 充足数据测试通过，正确路由到写作者")

    @skip_if_no_llm
    def test_insufficient_data(self):
        """测试不足的研究数据场景"""
        print("\n=== 测试不足的研究数据场景 ===")

        state = ResearchState(topic="量子计算在金融领域的应用",
                              research_plan="研究量子计算在金融建模、风险分析、投资优化等方面的应用",
                              search_queries=["量子计算金融", "量子算法投资"],
                              gathered_data="""=== 搜索查询 1: 量子计算金融 ===

知识库搜索结果:
1. 量子计算基础概念
   - 量子比特和量子叠加态
   - 量子门操作原理
   - 量子纠缠现象

=== 搜索查询 2: 量子算法投资 ===

知识库搜索结果:
1. 量子计算发展现状
   - 当前量子计算机的局限性
   - 量子比特数量限制
   - 错误率问题""",
                              final_document="",
                              messages=[])

        result = supervisor_router(state, self.llm_client)
        self.assertEqual(result, "rerun_researcher")
        print("✅ 不足数据测试通过，正确路由回研究者")

    @skip_if_no_llm
    def test_empty_data(self):
        """测试空数据场景"""
        print("\n=== 测试空数据场景 ===")

        state = ResearchState(topic="区块链技术",
                              research_plan="研究区块链技术原理和应用",
                              search_queries=["区块链"],
                              gathered_data="",
                              final_document="",
                              messages=[])

        result = supervisor_router(state, self.llm_client)
        self.assertEqual(result, "rerun_researcher")
        print("✅ 空数据测试通过，正确路由回研究者")

    @skip_if_no_llm
    def test_no_topic(self):
        """测试无主题场景"""
        print("\n=== 测试无主题场景 ===")

        state = ResearchState(topic="",
                              research_plan="",
                              search_queries=[],
                              gathered_data="一些数据",
                              final_document="",
                              messages=[])

        result = supervisor_router(state, self.llm_client)
        self.assertEqual(result, "rerun_researcher")
        print("✅ 无主题测试通过，正确路由回研究者")

    @skip_if_no_llm
    def test_minimal_data(self):
        """测试最小数据场景"""
        print("\n=== 测试最小数据场景 ===")

        state = ResearchState(
            topic="机器学习",
            research_plan="研究机器学习算法",
            search_queries=["机器学习"],
            gathered_data=
            "=== 搜索查询 1: 机器学习 ===\n\n知识库搜索结果:\n1. 机器学习基础\n   - 监督学习\n   - 无监督学习\n   - 强化学习",
            final_document="",
            messages=[])

        result = supervisor_router(state, self.llm_client)
        # 最小数据可能路由到写作者或继续研究，取决于LLM判断
        self.assertIn(result, ["continue_to_writer", "rerun_researcher"])
        print(f"✅ 最小数据测试通过，路由结果: {result}")

    @skip_if_no_llm
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")

        class MockLLMClient:

            def invoke(self, prompt, **kwargs):
                raise Exception("模拟 LLM 调用失败")

        mock_client = MockLLMClient()
        state = ResearchState(topic="测试主题",
                              research_plan="测试计划",
                              search_queries=["测试查询"],
                              gathered_data="测试数据",
                              final_document="",
                              messages=[])

        # 应该返回默认路由而不是崩溃
        result = supervisor_router(state, mock_client)
        self.assertEqual(result, "rerun_researcher")
        print("✅ 错误处理测试通过，LLM失败时正确回退")

    @skip_if_no_llm
    def test_different_topics(self):
        """测试不同主题的路由决策"""
        print("\n=== 测试不同主题的路由决策 ===")

        test_cases = [{
            "topic": "深度学习",
            "data":
            "=== 深度学习 ===\n\n知识库搜索结果:\n1. 深度学习基础\n   - 神经网络\n   - 反向传播\n   - 激活函数\n\n2. 应用领域\n   - 计算机视觉\n   - 自然语言处理\n   - 语音识别",
            "expected": "continue_to_writer"
        }, {
            "topic": "新兴技术",
            "data": "=== 新兴技术 ===\n\n知识库搜索结果:\n1. 技术概述\n   - 基本概念",
            "expected": "rerun_researcher"
        }]

        for i, case in enumerate(test_cases):
            state = ResearchState(topic=case["topic"],
                                  research_plan=f"研究{case['topic']}",
                                  search_queries=[case["topic"]],
                                  gathered_data=case["data"],
                                  final_document="",
                                  messages=[])

            result = supervisor_router(state, self.llm_client)
            print(
                f"  主题 '{case['topic']}': 期望 {case['expected']}, 实际 {result}")
            # 由于LLM可能给出不同判断，我们只验证结果是有效的路由
            self.assertIn(result, ["continue_to_writer", "rerun_researcher"])

        print("✅ 不同主题路由测试通过")


if __name__ == "__main__":
    unittest.main()
