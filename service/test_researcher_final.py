#!/usr/bin/env python3
"""
最终测试 researcher.py 中用户文档搜索功能
"""

import asyncio
import os
import sys
from typing import Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.reranker import RerankerTool
from doc_agent.graph.chapter_workflow.nodes.researcher import async_researcher_node
from doc_agent.graph.state import ResearchState


async def test_researcher_final():
    """最终测试 researcher.py 中用户文档搜索功能"""
    logger.info("开始最终测试 researcher.py 中用户文档搜索功能")

    # 测试参数
    query = "人工智能"
    # 使用真实存在的 doc_id
    user_data_reference_files = ["3e1e5b97fd91f53140b7a6588ad9a502"]
    user_style_guide_content = ["342732fad09727c9a2f4ef95aaa01e1b"]
    user_requirements_content = ["32fd1921c5344544e03481946cdfed6e"]
    top_k = 10

    # 从配置文件获取ES配置
    es_config = settings.elasticsearch_config
    es_hosts = es_config.hosts
    es_username = es_config.username
    es_password = es_config.password

    logger.info(f"测试参数:")
    logger.info(f"  - query: {query}")
    logger.info(f"  - user_data_reference_files: {user_data_reference_files}")
    logger.info(f"  - user_style_guide_content: {user_style_guide_content}")
    logger.info(f"  - user_requirements_content: {user_requirements_content}")

    # 创建ES搜索工具实例
    es_search_tool = ESSearchTool(hosts=es_hosts,
                                  username=es_username,
                                  password=es_password)

    # 创建重排序工具实例（模拟）
    reranker_tool = None  # 暂时设为None，专注于ES搜索测试

    # 创建模拟的WebSearchTool
    class MockWebSearchTool:

        async def search_async(self, query):
            return [], ""

    web_search_tool = MockWebSearchTool()

    try:
        # 确保初始化
        await es_search_tool._ensure_initialized()

        # 创建测试状态
        test_state = ResearchState({
            "topic": "人工智能技术发展",
            "current_chapter_index": 1,
            "research_plan": "研究人工智能的发展历程和应用",
            "search_queries": [query],
            "gathered_data": "",
            "job_id": "test_job_final",
            "is_online": False,  # 关闭网络搜索，专注于ES搜索
            "user_data_reference_files": user_data_reference_files,
            "user_style_guide_content": user_style_guide_content,
            "user_requirements_content": user_requirements_content,
            "gathered_sources": [],
            "current_citation_index": 1
        })

        logger.info("开始执行 researcher 节点...")

        # 执行 researcher 节点
        result = await async_researcher_node(state=test_state,
                                             web_search_tool=web_search_tool,
                                             es_search_tool=es_search_tool,
                                             reranker_tool=reranker_tool)

        logger.info("researcher 节点执行完成")
        logger.info(f"返回结果类型: {type(result)}")
        logger.info(f"返回结果键: {list(result.keys())}")

        # 分析结果
        gathered_sources = result.get("gathered_sources", [])
        user_data_sources = result.get("user_data_reference_sources", [])
        user_style_sources = result.get("user_style_guide_sources", [])
        user_requirement_sources = result.get("user_requirement_sources", [])

        logger.info(f"搜索结果统计:")
        logger.info(f"  - gathered_sources 数量: {len(gathered_sources)}")
        logger.info(
            f"  - user_data_reference_sources 数量: {len(user_data_sources)}")
        logger.info(
            f"  - user_style_guide_sources 数量: {len(user_style_sources)}")
        logger.info(
            f"  - user_requirement_sources 数量: {len(user_requirement_sources)}"
        )

        # 验证逻辑正确性
        logger.info("验证逻辑正确性:")

        # 1. 验证 gathered_sources 只包含参考文档
        gathered_ids = [source.id for source in gathered_sources]
        user_data_ids = [source.id for source in user_data_sources]

        logger.info(f"  - gathered_sources IDs: {gathered_ids}")
        logger.info(f"  - user_data_sources IDs: {user_data_ids}")

        # 验证 gathered_sources 和 user_data_sources 应该相同
        if set(gathered_ids) == set(user_data_ids):
            logger.info("✅ gathered_sources 和 user_data_sources 一致")
        else:
            logger.error("❌ gathered_sources 和 user_data_sources 不一致")

        # 2. 验证用户需求文档和风格指南不在 gathered_sources 中
        user_requirement_ids = [
            source.id for source in user_requirement_sources
        ]
        user_style_ids = [source.id for source in user_style_sources]

        logger.info(
            f"  - user_requirement_sources IDs: {user_requirement_ids}")
        logger.info(f"  - user_style_sources IDs: {user_style_ids}")

        # 验证这些ID不应该在 gathered_sources 中
        if not any(rid in gathered_ids for rid in user_requirement_ids):
            logger.info("✅ 用户需求文档不在 gathered_sources 中")
        else:
            logger.error("❌ 用户需求文档错误地包含在 gathered_sources 中")

        if not any(sid in gathered_ids for sid in user_style_ids):
            logger.info("✅ 用户风格指南不在 gathered_sources 中")
        else:
            logger.error("❌ 用户风格指南错误地包含在 gathered_sources 中")

        # 显示详细信息
        if user_data_sources:
            logger.info("用户参考文档信源详情:")
            for i, source in enumerate(user_data_sources[:3], 1):
                logger.info(
                    f"  {i}. ID: {source.id}, 标题: {source.title[:50]}...")
                logger.info(
                    f"     类型: {source.source_type}, doc_id: {source.doc_id}")

        if user_style_sources:
            logger.info("用户风格指南信源详情:")
            for i, source in enumerate(user_style_sources[:3], 1):
                logger.info(
                    f"  {i}. ID: {source.id}, 标题: {source.title[:50]}...")
                logger.info(
                    f"     类型: {source.source_type}, doc_id: {source.doc_id}")

        if user_requirement_sources:
            logger.info("用户需求文档信源详情:")
            for i, source in enumerate(user_requirement_sources[:3], 1):
                logger.info(
                    f"  {i}. ID: {source.id}, 标题: {source.title[:50]}...")
                logger.info(
                    f"     类型: {source.source_type}, doc_id: {source.doc_id}")

        # 验证结果
        if gathered_sources and user_style_sources and user_requirement_sources:
            logger.info("✅ 测试成功：所有用户文档搜索都正常工作")
        else:
            logger.warning("⚠️ 测试警告：部分用户文档搜索没有结果")

        return result

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return None

    finally:
        # 关闭ES连接
        if es_search_tool:
            await es_search_tool.close()


if __name__ == "__main__":
    asyncio.run(test_researcher_final())
    logger.info("测试完成")
