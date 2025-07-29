#!/usr/bin/env python3
"""
快速测试脚本 - 只测试初始研究节点
"""

import asyncio
import os
import sys
from pathlib import Path

# --- 路径设置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from service.core.config import settings
from service.core.container import container
from service.src.doc_agent.graph.state import ResearchState


async def test_initial_research():
    """测试初始研究节点"""
    print("🔍 测试初始研究节点...")

    # 设置简化配置
    settings.search_config.max_search_rounds = 2
    print(f"✅ 设置搜索轮数: {settings.search_config.max_search_rounds}")

    # 创建初始状态
    initial_state = ResearchState(
        topic="量子计算的基本原理",
        initial_gathered_data="",
        document_outline={},
        chapters_to_process=[],
        current_chapter_index=0,
        completed_chapters=[],
        final_document="",
        messages=[],
    )

    # 获取初始研究节点
    from service.src.doc_agent.graph.main_orchestrator import nodes as main_orchestrator_nodes
    from service.src.doc_agent.tools import get_web_search_tool, get_es_search_tool, get_reranker_tool

    web_search_tool = get_web_search_tool()
    es_search_tool = get_es_search_tool()
    reranker_tool = get_reranker_tool()

    # 在调用节点前再次确认配置
    print(
        f"🔧 节点执行前确认配置: max_search_rounds={settings.search_config.max_search_rounds}"
    )

    # 调用初始研究节点
    result = await main_orchestrator_nodes.initial_research_node(
        state=initial_state,
        web_search_tool=web_search_tool,
        es_search_tool=es_search_tool,
        reranker_tool=reranker_tool)

    print(f"✅ 初始研究完成")
    print(f"   - 收集到的源数量: {len(result.get('initial_sources', []))}")

    # 显示前几个源的信息
    sources = result.get('initial_sources', [])
    for i, source in enumerate(sources[:3], 1):
        print(f"   - 源 {i}: [{source.id}] {source.title[:50]}...")

    return result


if __name__ == "__main__":
    asyncio.run(test_initial_research())
