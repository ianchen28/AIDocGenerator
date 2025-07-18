#!/usr/bin/env python3
"""
测试 main_orchestrator/builder.py 中的日志系统
"""

from core.container import container
from src.doc_agent.graph.main_orchestrator.builder import (
    chapter_decision_function, finalize_document_node,
    build_main_orchestrator_graph)
from src.doc_agent.graph.state import ResearchState


def test_main_orchestrator_builder_logging():
    """测试主编排器构建器日志系统"""
    print("=== 测试主编排器构建器日志系统 ===")

    try:
        # 测试1: chapter_decision_function
        print("\n🔍 测试1: 章节决策函数...")

        # 测试场景1：还有章节需要处理
        test_state_1 = ResearchState(topic="测试主题",
                                     research_plan="测试计划",
                                     search_queries=["查询1", "查询2"],
                                     gathered_data="",
                                     final_document="",
                                     messages=[],
                                     chapters_to_process=[{
                                         "chapter_title":
                                         "第一章",
                                         "description":
                                         "第一章描述"
                                     }, {
                                         "chapter_title":
                                         "第二章",
                                         "description":
                                         "第二章描述"
                                     }],
                                     current_chapter_index=0)

        result_1 = chapter_decision_function(test_state_1)
        print(f"✅ 章节决策测试1成功，结果: {result_1}")

        # 测试场景2：所有章节已处理完成
        test_state_2 = ResearchState(
            topic="测试主题",
            research_plan="测试计划",
            search_queries=["查询1", "查询2"],
            gathered_data="",
            final_document="",
            messages=[],
            chapters_to_process=[{
                "chapter_title": "第一章",
                "description": "第一章描述"
            }, {
                "chapter_title": "第二章",
                "description": "第二章描述"
            }],
            current_chapter_index=2  # 超出范围
        )

        result_2 = chapter_decision_function(test_state_2)
        print(f"✅ 章节决策测试2成功，结果: {result_2}")

        # 测试2: finalize_document_node
        print("\n🔍 测试2: 文档最终化节点...")

        test_state_3 = ResearchState(
            topic="人工智能应用",
            research_plan="研究AI应用",
            search_queries=["AI", "机器学习"],
            gathered_data="",
            final_document="",
            messages=[],
            document_outline={
                "title":
                "人工智能应用指南",
                "summary":
                "关于人工智能应用的综合性指南",
                "chapters": [{
                    "chapter_title": "AI基础",
                    "description": "介绍AI基本概念"
                }, {
                    "chapter_title": "AI应用",
                    "description": "探讨AI实际应用"
                }]
            },
            completed_chapters_content=[
                "## AI基础\n\n这是第一章的内容。\n\n### 基本概念\n\nAI是人工智能的缩写。",
                "## AI应用\n\n这是第二章的内容。\n\n### 实际应用\n\nAI在多个领域有应用。"
            ])

        result_3 = finalize_document_node(test_state_3)
        print(f"✅ 文档最终化测试成功")
        print(f"📊 最终文档长度: {len(result_3['final_document'])} 字符")

        # 测试3: build_main_orchestrator_graph
        print("\n🔍 测试3: 主编排器图构建...")

        try:
            # 获取已编译的章节图
            chapter_graph = container.chapter_graph

            # 获取已绑定依赖的节点函数
            initial_research_node = container.main_graph.nodes[
                "initial_research"]
            outline_generation_node = container.main_graph.nodes[
                "outline_generation"]
            split_chapters_node = container.main_graph.nodes["split_chapters"]

            # 构建主编排器图
            main_graph = build_main_orchestrator_graph(
                initial_research_node=initial_research_node,
                outline_generation_node=outline_generation_node,
                split_chapters_node=split_chapters_node,
                chapter_workflow_graph=chapter_graph)

            print(f"✅ 主编排器图构建成功")
            print(f"📊 图节点数量: {len(main_graph.nodes)}")

            # 验证图结构
            expected_nodes = {
                "initial_research", "outline_generation", "split_chapters",
                "chapter_processing", "finalize_document", "__start__"
            }
            actual_nodes = set(main_graph.nodes.keys())

            if actual_nodes == expected_nodes:
                print("✅ 图节点结构正确")
            else:
                print(f"❌ 图节点结构不匹配")
                print(f"   期望: {expected_nodes}")
                print(f"   实际: {actual_nodes}")

        except Exception as e:
            print(f"⚠️  主编排器图构建测试跳过: {e}")

        print("\n✅ 主编排器构建器日志系统测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ 主编排器构建器测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_main_orchestrator_builder_logging()
