#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的端到端测试脚本
限制执行步骤避免递归限制问题
"""

import sys
import os
import asyncio
from pathlib import Path

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.env_loader import setup_environment
from core.container import container


async def test_graph_with_limit():
    """测试图流程，限制执行步骤"""
    print("🚀 简化端到端测试")
    print("=" * 80)

    # 1. 定义初始输入
    initial_input = {
        "messages": [],
        "topic": "人工智能的发展趋势",
        "research_plan": "",
        "search_queries": [],
        "gathered_data": "",
        "final_document": ""
    }

    print("📝 初始主题:")
    print(f"   {initial_input['topic']}")
    print()

    try:
        # 2. 使用 stream() 方法执行图，限制步骤
        print("🔄 开始执行图流程（限制10步）...")
        print("=" * 80)

        step_count = 0
        max_steps = 10  # 限制最大步骤数
        final_state = None

        async for step in container.graph.astream(initial_input):
            step_count += 1
            print(f"\n{'='*20} 步骤 {step_count} {'='*20}")

            # 获取节点名称和输出
            node_name = list(step.keys())[0]
            node_output = list(step.values())[0]
            final_state = node_output

            print(f"📋 节点: {node_name}")
            print(f"⏱️  状态: 完成")
            print()

            # 显示关键信息
            if node_name == "planner":
                if "research_plan" in node_output:
                    print("📋 研究计划:")
                    print(f"   {node_output['research_plan'][:200]}...")
                if "search_queries" in node_output:
                    print(f"🔍 搜索查询数量: {len(node_output['search_queries'])}")
                    for i, query in enumerate(
                            node_output['search_queries'][:3], 1):
                        print(f"   {i}. {query}")

            elif node_name == "researcher":
                if "gathered_data" in node_output:
                    data_length = len(node_output['gathered_data'])
                    print(f"📚 收集数据长度: {data_length} 字符")
                    if data_length > 0:
                        print("📖 数据预览:")
                        preview = node_output['gathered_data'][:300]
                        print(f"   {preview}...")

            elif node_name == "writer":
                if "final_document" in node_output:
                    doc_length = len(node_output['final_document'])
                    print(f"📄 生成文档长度: {doc_length} 字符")
                    if doc_length > 0:
                        print("📝 文档预览:")
                        preview = node_output['final_document'][:500]
                        print(f"   {preview}...")

            print("-" * 80)

            # 检查是否达到最大步骤数
            if step_count >= max_steps:
                print(f"⚠️  达到最大步骤数限制 ({max_steps})，停止执行")
                break

        # 3. 显示结果
        print(f"\n🎯 执行完成，共 {step_count} 步")
        print("=" * 80)

        if final_state:
            print("📊 最终状态:")
            for key, value in final_state.items():
                if key != "messages":  # 跳过消息历史
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {len(value)} 字符")
                    else:
                        print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ 图执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_different_models():
    """测试不同模型的图执行"""
    print("\n🔄 测试不同模型的图执行")
    print("=" * 80)

    # 测试的模型列表
    test_models = ["moonshot_k2_0711_preview", "gemini_1_5_pro", "deepseek_v3"]

    for model_key in test_models:
        print(f"\n🔍 测试模型: {model_key}")
        print("-" * 60)

        try:
            # 创建新的容器配置
            from src.doc_agent.llm_clients import get_llm_client
            from src.doc_agent.tools import get_web_search_tool
            from src.doc_agent.graph import nodes, router
            from src.doc_agent.graph.builder import build_graph
            from functools import partial

            # 创建新的LLM客户端
            new_llm_client = get_llm_client(model_key)
            search_tool = get_web_search_tool()

            # 用partial绑定依赖
            planner_node = partial(nodes.planner_node,
                                   llm_client=new_llm_client)
            researcher_node = partial(nodes.async_researcher_node,
                                      web_search_tool=search_tool)
            writer_node = partial(nodes.writer_node, llm_client=new_llm_client)
            supervisor_router_func = partial(router.supervisor_router,
                                             llm_client=new_llm_client)

            # 编译图
            new_graph = build_graph(planner_node, researcher_node, writer_node,
                                    supervisor_router_func)

            print(f"✅ 图编译成功，使用 {model_key}")

            # 简单测试
            initial_input = {
                "messages": [],
                "topic": "测试主题",
                "research_plan": "",
                "search_queries": [],
                "gathered_data": "",
                "final_document": ""
            }

            # 只执行一步测试
            step_count = 0
            async for step in new_graph.astream(initial_input):
                step_count += 1
                node_name = list(step.keys())[0]
                print(f"  ✅ 节点 {node_name} 执行成功")
                if step_count >= 1:  # 只执行一步
                    break

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")


def main():
    """主函数"""
    print("🧪 简化端到端测试")
    print("=" * 80)

    # 设置环境
    setup_environment()

    # 运行测试
    success = asyncio.run(test_graph_with_limit())

    if success:
        print("\n✅ 简化端到端测试完成!")
    else:
        print("\n❌ 简化端到端测试失败!")

    # 测试不同模型
    asyncio.run(test_different_models())


if __name__ == "__main__":
    main()
