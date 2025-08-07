#!/usr/bin/env python3
"""
测试 initial_research_node 的脚本
调用大纲生成流程来触发 initial_research_node 的执行
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "src"))

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.core.container import container
from doc_agent.core.logging_config import setup_logging
from doc_agent.graph.state import ResearchState


async def test_initial_research_node():
    """测试 initial_research_node"""

    # 设置日志
    setup_logging(settings)
    logger.info("🚀 开始测试 initial_research_node")

    # 创建测试状态
    test_state = ResearchState(topic="人工智能在医疗领域的应用",
                               initial_sources=[],
                               document_outline={},
                               chapters_to_process=[],
                               current_chapter_index=0,
                               completed_chapters=[],
                               final_document="",
                               research_plan="",
                               search_queries=[],
                               gathered_sources=[],
                               sources=[],
                               all_sources=[],
                               current_citation_index=1,
                               cited_sources=[],
                               cited_sources_in_chapter=[],
                               messages=[])

    logger.info(f"📝 测试主题: {test_state['topic']}")

    try:
        # 获取大纲生成图
        outline_graph = container.outline_graph
        logger.info("✅ 成功获取大纲生成图")

        # 执行大纲生成流程
        logger.info("🔄 开始执行大纲生成流程...")
        result = await outline_graph.ainvoke(test_state)

        logger.info("✅ 大纲生成流程执行完成")
        logger.info(f"📊 结果类型: {type(result)}")

        # 检查结果
        if 'initial_sources' in result:
            initial_sources = result['initial_sources']
            logger.info(f"📚 初始研究结果: 收集到 {len(initial_sources)} 个信息源")

            for i, source in enumerate(initial_sources[:3], 1):  # 只显示前3个
                logger.info(
                    f"  源 {i}: [{source.id}] {source.title} ({source.source_type})"
                )

        if 'document_outline' in result:
            outline = result['document_outline']
            logger.info(f"📋 生成的大纲: {outline}")

        return result

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    asyncio.run(test_initial_research_node())
