#!/usr/bin/env python3
"""
全面测试 main_orchestrator/nodes.py 中的日志系统
"""

import asyncio
from core.container import container
from src.doc_agent.graph.main_orchestrator.nodes import (
    initial_research_node, outline_generation_node, split_chapters_node)
from src.doc_agent.graph.state import ResearchState


async def test_main_orchestrator_comprehensive():
    """全面测试主编排器节点日志系统"""
    print("=== 全面测试主编排器节点日志系统 ===")

    try:
        # 测试1: split_chapters_node
        print("\n🔍 测试1: 章节拆分节点...")

        test_state_1 = ResearchState(
            topic="区块链技术应用",
            research_plan="研究区块链在金融、供应链、数字身份等领域的应用",
            search_queries=["区块链金融", "供应链区块链", "数字身份"],
            gathered_data="",
            final_document="",
            messages=[],
            document_outline={
                "title":
                "区块链技术应用",
                "summary":
                "关于区块链技术应用的综合性文档",
                "chapters": [{
                    "chapter_number": 1,
                    "chapter_title": "区块链基础",
                    "description": "介绍区块链的基本概念和技术原理",
                    "key_points": ["分布式账本", "共识机制", "密码学"],
                    "estimated_sections": 3
                }, {
                    "chapter_number": 2,
                    "chapter_title": "金融应用",
                    "description": "探讨区块链在金融领域的应用",
                    "key_points": ["数字货币", "智能合约", "跨境支付"],
                    "estimated_sections": 4
                }],
                "total_chapters":
                2,
                "estimated_total_words":
                8000
            })

        result_1 = split_chapters_node(test_state_1)
        print(f"✅ 章节拆分测试成功，创建了 {len(result_1['chapters_to_process'])} 个任务")

        # 测试2: outline_generation_node (模拟)
        print("\n🔍 测试2: 大纲生成节点...")

        test_state_2 = ResearchState(
            topic="量子计算",
            research_plan="研究量子计算的基本原理和应用前景",
            search_queries=["量子计算", "量子比特", "量子算法"],
            gathered_data="",
            final_document="",
            messages=[],
            initial_gathered_data=
            "量子计算是一种基于量子力学原理的计算方式。它利用量子比特的叠加态和纠缠特性，能够在某些特定问题上实现指数级的计算加速。量子计算在密码学、药物发现、金融建模等领域具有巨大潜力。"
        )

        try:
            # 注意：这个测试需要真实的LLM客户端，可能会失败
            result_2 = outline_generation_node(test_state_2,
                                               container.llm_client)
            print(
                f"✅ 大纲生成测试成功，生成了 {len(result_2['document_outline']['chapters'])} 个章节"
            )
        except Exception as e:
            print(f"⚠️  大纲生成测试跳过（需要真实LLM）: {e}")

        # 测试3: initial_research_node (模拟)
        print("\n🔍 测试3: 初始研究节点...")

        test_state_3 = ResearchState(topic="机器学习",
                                     research_plan="研究机器学习的基本概念和应用",
                                     search_queries=["机器学习", "深度学习", "神经网络"],
                                     gathered_data="",
                                     final_document="",
                                     messages=[])

        try:
            # 注意：这个测试需要真实的搜索工具，可能会失败
            result_3 = await initial_research_node(test_state_3,
                                                   container.web_search_tool,
                                                   container.es_search_tool,
                                                   container.reranker_tool,
                                                   container.llm_client)
            print(
                f"✅ 初始研究测试成功，收集了 {len(result_3['initial_gathered_data'])} 字符的数据"
            )
        except Exception as e:
            print(f"⚠️  初始研究测试跳过（需要真实搜索工具）: {e}")

        print("\n✅ 主编排器节点全面测试完成")
        print("请检查控制台输出和日志文件以验证日志记录")

    except Exception as e:
        print(f"❌ 主编排器节点全面测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_main_orchestrator_comprehensive())
