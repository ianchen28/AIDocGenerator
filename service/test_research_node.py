#!/usr/bin/env python3
"""
测试 initial_research_node 函数
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.graph.main_orchestrator.nodes.research import initial_research_node
from doc_agent.graph.state import ResearchState


async def test_initial_research_node():
    """测试 initial_research_node 函数"""
    logger.info("=== 开始测试 initial_research_node ===")

    try:
        # 创建模拟的搜索工具
        web_search_tool = Mock()
        web_search_tool.search_async = AsyncMock(return_value=([], "模拟搜索结果"))

        es_search_tool = Mock()
        es_search_tool.search = AsyncMock(return_value=[])

        reranker_tool = Mock()

        # 创建模拟的 LLM 客户端
        llm_client = Mock()
        llm_client.invoke = Mock(
            return_value=
            '{"topic": "测试主题", "word_count": "1000", "other_requirements": "测试要求"}'
        )

        # 创建测试状态
        state = ResearchState({
            "task_prompt": "请写一篇关于人工智能的文章，要求1000字",
            "job_id": "test_job_001"
        })

        logger.info("✅ 模拟对象创建成功")

        # 调用函数
        logger.info("🔍 开始调用 initial_research_node...")
        result = await initial_research_node(state=state,
                                             web_search_tool=web_search_tool,
                                             es_search_tool=es_search_tool,
                                             reranker_tool=reranker_tool,
                                             llm_client=llm_client)

        logger.info(f"✅ 函数调用成功，返回结果: {result}")
        logger.info(
            f"📊 返回的 initial_sources 数量: {len(result.get('initial_sources', []))}"
        )

        # 验证状态更新
        logger.info(f"📝 状态中的 topic: {state.get('topic')}")
        logger.info(f"📝 状态中的 word_count: {state.get('word_count')}")
        logger.info(
            f"📝 状态中的 prompt_requirements: {state.get('prompt_requirements')}")

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"完整错误信息: {traceback.format_exc()}")
        return False


async def test_with_embedding_client():
    """测试包含 embedding 客户端的情况"""
    logger.info("=== 开始测试包含 embedding 客户端的情况 ===")

    try:
        # 创建模拟的搜索工具
        web_search_tool = Mock()
        web_search_tool.search_async = AsyncMock(return_value=([], "模拟搜索结果"))

        es_search_tool = Mock()
        es_search_tool.search = AsyncMock(return_value=[])

        reranker_tool = Mock()

        # 创建模拟的 LLM 客户端
        llm_client = Mock()
        llm_client.invoke = Mock(side_effect=[
            '{"topic": "测试主题", "word_count": "1000", "other_requirements": "测试要求"}',
            '{"search_queries": ["测试查询1", "测试查询2"]}'
        ])

        # 创建测试状态
        state = ResearchState({
            "task_prompt": "请写一篇关于人工智能的文章，要求1000字",
            "job_id": "test_job_002"
        })

        logger.info("✅ 模拟对象创建成功")

        # 调用函数
        logger.info("🔍 开始调用 initial_research_node...")
        result = await initial_research_node(state=state,
                                             web_search_tool=web_search_tool,
                                             es_search_tool=es_search_tool,
                                             reranker_tool=reranker_tool,
                                             llm_client=llm_client)

        logger.info(f"✅ 函数调用成功，返回结果: {result}")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"完整错误信息: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    # 运行测试
    async def main():
        logger.info("🚀 开始运行 research node 测试")

        # 测试1: 基本功能
        success1 = await test_initial_research_node()

        # 测试2: 包含 embedding 客户端
        success2 = await test_with_embedding_client()

        if success1 and success2:
            logger.success("🎉 所有测试通过！")
        else:
            logger.error("❌ 部分测试失败")

    # 运行异步测试
    asyncio.run(main())
