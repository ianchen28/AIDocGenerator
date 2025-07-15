# service/test_graph_builder.py
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.container import container
from src.doc_agent.graph.state import ResearchState


async def test_graph_execution():
    """测试图执行流程"""
    print("🧪 测试图构建和条件路由...")

    # 创建初始状态
    initial_state = ResearchState(topic="人工智能在医疗领域的应用",
                                  research_plan="",
                                  search_queries=[],
                                  gathered_data="",
                                  final_document="",
                                  messages=[])

    try:
        # 执行图
        print("🚀 开始执行图...")
        result = await container.graph.ainvoke(initial_state)

        print("✅ 图执行成功!")
        print(f"📝 最终文档长度: {len(result.get('final_document', ''))}")
        print(f"🔍 收集数据长度: {len(result.get('gathered_data', ''))}")

        # 显示最终文档的前500字符
        final_doc = result.get('final_document', '')
        if final_doc:
            print(f"📄 文档预览:\n{final_doc[:500]}...")

        return result

    except Exception as e:
        print(f"❌ 图执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_supervisor_router():
    """测试监督路由函数"""
    print("\n🧪 测试监督路由函数...")

    from src.doc_agent.graph.router import supervisor_router
    from src.doc_agent.graph.state import ResearchState

    # 测试数据充足的情况
    state_with_data = ResearchState(topic="测试主题",
                                    research_plan="研究计划",
                                    search_queries=["查询1", "查询2"],
                                    gathered_data="""
=== 搜索查询 1: 查询1 ===

网络搜索结果:
人工智能在医疗领域的应用非常广泛，包括医学影像分析、药物发现、个性化治疗等方面。

知识库搜索结果:
AI在医疗诊断中的应用已经取得了显著进展，特别是在影像识别和病理分析方面。

=== 搜索查询 2: 查询2 ===

网络搜索结果:
机器学习算法在疾病预测和预防方面发挥着重要作用，能够分析大量患者数据。

知识库搜索结果:
深度学习在医学影像处理中的应用，如CT、MRI等影像的自动分析和诊断。
""",
                                    final_document="",
                                    messages=[])

    # 获取LLM客户端
    llm_client = container.llm_client

    # 测试路由决策
    decision = supervisor_router(state_with_data, llm_client)
    print(f"🔍 路由决策: {decision}")

    # 测试数据不足的情况
    state_without_data = ResearchState(topic="测试主题",
                                       research_plan="研究计划",
                                       search_queries=["查询1"],
                                       gathered_data="没有找到相关数据",
                                       final_document="",
                                       messages=[])

    decision2 = supervisor_router(state_without_data, llm_client)
    print(f"🔍 数据不足时的路由决策: {decision2}")


if __name__ == "__main__":
    print("🚀 开始测试图构建和条件路由...")

    # 测试监督路由
    test_supervisor_router()

    # 测试完整图执行
    asyncio.run(test_graph_execution())
