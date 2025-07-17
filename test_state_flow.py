#!/usr/bin/env python3
"""
简化的状态流测试脚本
专门测试 planner 和 researcher 节点之间的状态传递
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
current_file = Path(__file__)
project_root = current_file.parent
service_dir = project_root / "service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.common import setup_import_paths
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.graph.chapter_workflow.nodes import planner_node, async_researcher_node
from src.doc_agent.llm_clients.providers import LLMClient
from src.doc_agent.tools.web_search import WebSearchTool
from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools.reranker import RerankerTool
from core.config import settings


async def test_state_flow():
    """测试状态流"""
    print("🧪 开始状态流测试...")

    # 设置导入路径
    setup_import_paths()

    # 创建初始状态
    initial_state = ResearchState(topic="人工智能在中国电力行业的应用趋势和政策支持",
                                  current_chapter_index=0,
                                  chapters_to_process=[{
                                      "chapter_title":
                                      "人工智能与电力行业融合发展背景",
                                      "description":
                                      "阐述人工智能技术演进历程及其在电力行业的应用价值"
                                  }],
                                  completed_chapters_content=[],
                                  search_queries=[],
                                  research_plan="",
                                  gathered_data="",
                                  messages=[])

    print(f"📋 初始状态:")
    print(f"  - topic: {initial_state['topic']}")
    print(f"  - search_queries: {initial_state['search_queries']}")
    print(f"  - research_plan: {initial_state['research_plan']}")

    # 初始化工具
    try:
        # 获取LLM配置
        llm_config = settings.get_agent_component_config("task_planner")
        if not llm_config:
            print("❌ 未找到LLM配置")
            return False

        # 根据provider获取对应的模型配置
        model_config = settings.get_model_config(llm_config.model)
        if not model_config:
            print(f"❌ 未找到模型配置: {llm_config.model}")
            return False

        llm_client = LLMClient(base_url=model_config.url,
                               api_key=model_config.api_key)
        print("✅ LLM客户端初始化成功")

        # 初始化搜索工具
        web_search_tool = WebSearchTool()
        print("✅ Web搜索工具初始化成功")

        # 初始化ES工具
        es_config = settings.elasticsearch_config
        if es_config:
            es_search_tool = ESSearchTool(hosts=es_config.hosts,
                                          username=es_config.username,
                                          password=es_config.password,
                                          timeout=es_config.timeout)
            print("✅ ES搜索工具初始化成功")
        else:
            print("❌ ES配置不可用")
            return False

        # 初始化重排序工具
        reranker_config = settings.reranker_config
        if reranker_config:
            reranker_tool = RerankerTool(base_url=reranker_config.url,
                                         api_key=reranker_config.api_key)
            print("✅ 重排序工具初始化成功")
        else:
            reranker_tool = None
            print("⚠️  重排序工具不可用")

    except Exception as e:
        print(f"❌ 工具初始化失败: {str(e)}")
        return False

    # 测试 planner 节点
    print("\n🔍 测试 planner 节点...")
    try:
        planner_result = planner_node(initial_state, llm_client)
        print(f"✅ Planner节点执行成功")
        print(f"📤 Planner返回结果: {planner_result}")

        # 更新状态
        updated_state = initial_state.copy()
        updated_state.update(planner_result)

        print(f"\n📋 更新后的状态:")
        print(f"  - search_queries: {updated_state['search_queries']}")
        print(f"  - research_plan: {updated_state['research_plan'][:100]}...")

    except Exception as e:
        print(f"❌ Planner节点执行失败: {str(e)}")
        return False

    # 测试 researcher 节点
    print("\n🔍 测试 researcher 节点...")
    try:
        researcher_result = await async_researcher_node(
            updated_state, web_search_tool, es_search_tool, reranker_tool)
        print(f"✅ Researcher节点执行成功")
        print(f"📤 Researcher返回结果: {researcher_result}")

    except Exception as e:
        print(f"❌ Researcher节点执行失败: {str(e)}")
        return False

    print("\n✅ 状态流测试完成")
    return True


async def main():
    """主函数"""
    success = await test_state_flow()
    if success:
        print("🎉 测试通过")
    else:
        print("❌ 测试失败")


if __name__ == "__main__":
    asyncio.run(main())
