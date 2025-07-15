#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 supervisor_router 函数
验证路由决策的正确性
"""

from test_base import TestBase, setup_paths

# 设置测试环境
setup_paths()

# 导入需要测试的模块
from src.doc_agent.graph.router import supervisor_router
from src.doc_agent.graph.state import ResearchState
from core.config import settings


class SupervisorRouterTest(TestBase):
    """supervisor_router 函数测试类"""

    def __init__(self):
        super().__init__()
        self.llm_client = None

    def setup_llm_client(self):
        """设置LLM客户端"""
        try:
            # 使用工厂函数创建LLM客户端
            from src.doc_agent.llm_clients import get_llm_client
            # self.llm_client = get_llm_client(model_key="gemini_2_5_pro")
            self.llm_client = get_llm_client(model_key="qwen_2_5_235b_a22b")
            print("✅ LLM客户端初始化成功")
            return True
        except Exception as e:
            print(f"❌ LLM客户端初始化失败: {str(e)}")
            print(f"可用的模型: {list(settings.supported_models.keys())}")
            return False

    def test_sufficient_data(self):
        """测试充足的研究数据场景"""
        print("=== 测试充足的研究数据场景 ===")

        if not self.llm_client:
            print("❌ LLM客户端未初始化，跳过测试")
            return False

        try:
            # 创建充足数据的测试状态
            state = ResearchState(
                topic="人工智能在医疗领域的应用",
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

            # 调用路由函数
            result = supervisor_router(state, self.llm_client)
            print(f"结果: {result}")

            # 验证结果
            expected = "continue_to_writer"
            assert result == expected, f"期望 {expected}，实际得到 {result}"
            print("✅ 充足数据测试通过")
            return True

        except Exception as e:
            print(f"❌ 充足数据测试失败: {str(e)}")
            return False

    def test_insufficient_data(self):
        """测试不足的研究数据场景"""
        print("=== 测试不足的研究数据场景 ===")

        if not self.llm_client:
            print("❌ LLM客户端未初始化，跳过测试")
            return False

        try:
            # 创建不足数据的测试状态
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

            # 调用路由函数
            result = supervisor_router(state, self.llm_client)
            print(f"结果: {result}")

            # 验证结果
            expected = "rerun_researcher"
            assert result == expected, f"期望 {expected}，实际得到 {result}"
            print("✅ 不足数据测试通过")
            return True

        except Exception as e:
            print(f"❌ 不足数据测试失败: {str(e)}")
            return False

    def test_empty_data(self):
        """测试空数据场景"""
        print("=== 测试空数据场景 ===")

        if not self.llm_client:
            print("❌ LLM客户端未初始化，跳过测试")
            return False

        try:
            # 创建空数据的测试状态
            state = ResearchState(topic="区块链技术",
                                  research_plan="研究区块链技术原理和应用",
                                  search_queries=["区块链"],
                                  gathered_data="",
                                  final_document="",
                                  messages=[])

            # 调用路由函数
            result = supervisor_router(state, self.llm_client)
            print(f"结果: {result}")

            # 验证结果
            expected = "rerun_researcher"
            assert result == expected, f"期望 {expected}，实际得到 {result}"
            print("✅ 空数据测试通过")
            return True

        except Exception as e:
            print(f"❌ 空数据测试失败: {str(e)}")
            return False

    def test_no_topic(self):
        """测试无主题场景"""
        print("=== 测试无主题场景 ===")

        if not self.llm_client:
            print("❌ LLM客户端未初始化，跳过测试")
            return False

        try:
            # 创建无主题的测试状态
            state = ResearchState(topic="",
                                  research_plan="",
                                  search_queries=[],
                                  gathered_data="一些数据",
                                  final_document="",
                                  messages=[])

            # 调用路由函数
            result = supervisor_router(state, self.llm_client)
            print(f"结果: {result}")

            # 验证结果
            expected = "rerun_researcher"
            assert result == expected, f"期望 {expected}，实际得到 {result}"
            print("✅ 无主题测试通过")
            return True

        except Exception as e:
            print(f"❌ 无主题测试失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行 supervisor_router 测试...")

        # 初始化LLM客户端
        if not self.setup_llm_client():
            print("❌ 无法初始化LLM客户端，跳过所有测试")
            return

        test_results = []

        # 添加测试方法
        test_results.append(("充足数据测试", self.test_sufficient_data()))
        test_results.append(("不足数据测试", self.test_insufficient_data()))
        test_results.append(("空数据测试", self.test_empty_data()))
        test_results.append(("无主题测试", self.test_no_topic()))

        # 显示结果汇总
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print("=" * 50)

        passed = 0
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1

        print(f"\n总计: {passed}/{len(test_results)} 项测试通过")

        if passed == len(test_results):
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败")


def main():
    """主测试函数"""
    tester = SupervisorRouterTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
