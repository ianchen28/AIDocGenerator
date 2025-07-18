#!/usr/bin/env python3
"""
测试 main_orchestrator/nodes.py 中的日志系统
"""

from core.container import container
from src.doc_agent.graph.main_orchestrator.nodes import split_chapters_node
from src.doc_agent.graph.state import ResearchState


def test_main_orchestrator_nodes_logging():
    """测试主编排器节点日志系统"""
    print("=== 测试主编排器节点日志系统 ===")

    try:
        # 测试 split_chapters_node
        print("🔍 测试章节拆分节点...")

        # 创建测试状态
        test_state = ResearchState(
            topic="人工智能在医疗领域的应用",
            research_plan="研究AI在医疗诊断、药物发现、个性化治疗等方面的应用",
            search_queries=["AI医疗诊断", "人工智能药物发现", "个性化医疗AI"],
            gathered_data="",
            final_document="",
            messages=[],
            document_outline={
                "title":
                "人工智能在医疗领域的应用",
                "summary":
                "关于AI在医疗领域应用的综合性文档",
                "chapters": [{
                    "chapter_number": 1,
                    "chapter_title": "AI医疗诊断技术",
                    "description": "介绍AI在医疗诊断中的应用和技术原理",
                    "key_points": ["深度学习", "图像识别", "诊断准确率"],
                    "estimated_sections": 3
                }, {
                    "chapter_number": 2,
                    "chapter_title": "AI药物发现",
                    "description": "探讨AI在药物研发中的应用",
                    "key_points": ["虚拟筛选", "分子设计", "临床试验"],
                    "estimated_sections": 4
                }, {
                    "chapter_number": 3,
                    "chapter_title": "个性化医疗",
                    "description": "分析AI在个性化治疗中的应用",
                    "key_points": ["基因组学", "精准医疗", "治疗方案"],
                    "estimated_sections": 3
                }],
                "total_chapters":
                3,
                "estimated_total_words":
                12000
            })

        # 执行章节拆分
        result = split_chapters_node(test_state)

        print("✅ 章节拆分节点测试成功")
        print(f"📊 创建的章节任务数量: {len(result['chapters_to_process'])}")
        print(f"📊 当前章节索引: {result['current_chapter_index']}")

        # 验证结果
        chapters = result['chapters_to_process']
        if len(chapters) == 3:
            print("✅ 章节数量正确")
        else:
            print(f"❌ 章节数量不匹配，期望3，实际{len(chapters)}")

        # 检查章节内容
        for i, chapter in enumerate(chapters):
            print(
                f"  📄 第{chapter['chapter_number']}章: {chapter['chapter_title']}"
            )
            print(f"     描述: {chapter['description'][:50]}...")
            print(f"     关键要点: {len(chapter['key_points'])} 个")

        print("\n✅ 主编排器节点日志系统测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ 主编排器节点测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_main_orchestrator_nodes_logging()
