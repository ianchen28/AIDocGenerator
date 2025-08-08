#!/usr/bin/env python3
"""
测试 writer 节点的流式输出功能
"""

import asyncio
import json
from doc_agent.llm_clients import get_llm_client
from doc_agent.graph.chapter_workflow.nodes.writer import writer_node
from doc_agent.graph.state import ResearchState
from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.logger import logger


def test_writer_streaming():
    """测试 writer 节点的流式输出"""
    print("🚀 开始测试 writer 节点流式输出...")

    # 创建测试状态
    state = ResearchState(topic="人工智能技术发展趋势",
                          job_id="test_job_001",
                          current_chapter_index=0,
                          chapters_to_process=[{
                              "chapter_title":
                              "人工智能概述",
                              "description":
                              "介绍人工智能的基本概念和发展历程"
                          }],
                          gathered_sources=[],
                          completed_chapters=[],
                          completed_chapters_content=[],
                          style_guide_content="",
                          current_citation_index=1)

    # 获取 LLM 客户端
    llm_client = get_llm_client("qwen_2_5_235b_a22b")

    # 创建 PromptSelector
    prompt_selector = PromptSelector()

    print("📝 开始调用 writer 节点...")

    try:
        # 调用 writer 节点
        result = writer_node(state=state,
                             llm_client=llm_client,
                             prompt_selector=prompt_selector,
                             genre="default",
                             prompt_version="v3_context_aware")

        print("✅ writer 节点调用成功")
        print(f"📄 生成的内容长度: {len(result.get('final_document', ''))}")
        print(f"📚 引用源数量: {len(result.get('cited_sources_in_chapter', []))}")

        # 显示生成内容的前200个字符
        content = result.get('final_document', '')
        if content:
            print(f"📝 内容预览: {content[:200]}...")

    except Exception as e:
        print(f"❌ writer 节点调用失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_writer_streaming()
