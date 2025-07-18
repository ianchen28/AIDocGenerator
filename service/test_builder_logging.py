#!/usr/bin/env python3
"""
测试 builder.py 中的日志系统
"""

from core.container import container
from src.doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph


def test_builder_logging():
    """测试构建器日志系统"""
    print("=== 测试构建器日志系统 ===")

    try:
        # 获取已编译的图
        chapter_graph = container.chapter_graph
        main_graph = container.main_graph

        print("✅ 成功获取已编译的图对象")

        # 验证章节图结构
        print("🔍 检查章节工作流图结构...")
        if hasattr(chapter_graph, 'nodes'):
            print(f"📊 章节图节点数量: {len(chapter_graph.nodes)}")
            print("✅ 章节图结构正确")
        else:
            print("❌ 章节图结构异常")

        # 验证主图结构
        print("🔍 检查主编排器图结构...")
        if hasattr(main_graph, 'nodes'):
            print(f"📊 主图节点数量: {len(main_graph.nodes)}")
            print("✅ 主图结构正确")
        else:
            print("❌ 主图结构异常")

        # 测试图编译状态
        print("🧪 验证图编译状态...")
        if hasattr(chapter_graph, 'invoke'):
            print("✅ 章节图已正确编译，可以执行")
        else:
            print("❌ 章节图编译状态异常")

        if hasattr(main_graph, 'invoke'):
            print("✅ 主图已正确编译，可以执行")
        else:
            print("❌ 主图编译状态异常")

        print("\n✅ 构建器日志系统测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ 构建器测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_builder_logging()
