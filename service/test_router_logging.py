#!/usr/bin/env python3
"""
测试 router.py 中的日志系统
"""

from core.container import container
from src.doc_agent.graph.chapter_workflow.router import supervisor_router
from src.doc_agent.graph.state import ResearchState


def test_router_logging():
    """测试路由日志系统"""
    print("=== 测试路由日志系统 ===")

    # 测试场景1：充足的数据
    print("\n--- 测试场景1：充足的数据 ---")
    test_state_1 = ResearchState(
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
   - 个性化药物设计平台""",
        final_document="",
        messages=[])

    try:
        result = supervisor_router(test_state_1, container.llm_client)
        print(f"✅ 充足数据测试结果: {result}")
    except Exception as e:
        print(f"❌ 充足数据测试失败: {e}")

    # 测试场景2：不足的数据
    print("\n--- 测试场景2：不足的数据 ---")
    test_state_2 = ResearchState(topic="量子计算在金融领域的应用",
                                 research_plan="研究量子计算在金融建模、风险分析、投资优化等方面的应用",
                                 search_queries=["量子计算金融", "量子算法投资"],
                                 gathered_data="""=== 搜索查询 1: 量子计算金融 ===

知识库搜索结果:
1. 量子计算基础概念
   - 量子比特和量子叠加态
   - 量子门操作原理
   - 量子纠缠现象""",
                                 final_document="",
                                 messages=[])

    try:
        result = supervisor_router(test_state_2, container.llm_client)
        print(f"✅ 不足数据测试结果: {result}")
    except Exception as e:
        print(f"❌ 不足数据测试失败: {e}")

    # 测试场景3：空数据
    print("\n--- 测试场景3：空数据 ---")
    test_state_3 = ResearchState(topic="区块链技术",
                                 research_plan="研究区块链技术原理和应用",
                                 search_queries=["区块链"],
                                 gathered_data="",
                                 final_document="",
                                 messages=[])

    try:
        result = supervisor_router(test_state_3, container.llm_client)
        print(f"✅ 空数据测试结果: {result}")
    except Exception as e:
        print(f"❌ 空数据测试失败: {e}")

    # 测试场景4：无主题
    print("\n--- 测试场景4：无主题 ---")
    test_state_4 = ResearchState(topic="",
                                 research_plan="",
                                 search_queries=[],
                                 gathered_data="一些数据",
                                 final_document="",
                                 messages=[])

    try:
        result = supervisor_router(test_state_4, container.llm_client)
        print(f"✅ 无主题测试结果: {result}")
    except Exception as e:
        print(f"❌ 无主题测试失败: {e}")

    print("\n✅ 路由日志系统测试完成")
    print("请检查控制台输出和日志文件以验证日志记录")


if __name__ == "__main__":
    test_router_logging()
