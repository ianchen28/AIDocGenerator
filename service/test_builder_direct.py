#!/usr/bin/env python3
"""
直接测试 builder.py 中的日志系统
"""

from core.container import container
from src.doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph
from functools import partial


def test_builder_direct():
    """直接测试构建器函数"""
    print("=== 直接测试构建器函数 ===")

    try:
        # 创建模拟的节点函数
        def mock_planner_node(state):
            return {"topic": "测试主题", "research_plan": "测试计划"}

        def mock_researcher_node(state):
            return {"gathered_data": "测试数据"}

        def mock_writer_node(state):
            return {"final_document": "测试文档"}

        def mock_supervisor_router(state):
            return "continue_to_writer"

        # 使用 partial 绑定依赖
        planner_node = partial(mock_planner_node)
        researcher_node = partial(mock_researcher_node)
        writer_node = partial(mock_writer_node)
        supervisor_router_func = partial(mock_supervisor_router)

        print("🔨 开始构建章节工作流图...")

        # 调用构建函数，这会触发日志记录
        graph = build_chapter_workflow_graph(
            planner_node=planner_node,
            researcher_node=researcher_node,
            writer_node=writer_node,
            supervisor_router_func=supervisor_router_func,
        )

        print("✅ 章节工作流图构建成功")
        print(f"📊 图节点数量: {len(graph.nodes)}")

        # 验证图结构（包含 __start__ 节点）
        expected_nodes = {"planner", "researcher", "writer", "__start__"}
        actual_nodes = set(graph.nodes.keys())

        if actual_nodes == expected_nodes:
            print("✅ 图节点结构正确")
        else:
            print(f"❌ 图节点结构不匹配")
            print(f"   期望: {expected_nodes}")
            print(f"   实际: {actual_nodes}")

        # 测试图是否已编译
        print("🧪 验证图编译状态...")
        if hasattr(graph, 'invoke'):
            print("✅ 图已正确编译，可以执行")
        else:
            print("❌ 图编译状态异常")

        print("\n✅ 构建器直接测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ 构建器直接测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_builder_direct()
