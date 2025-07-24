#!/usr/bin/env python3
"""
测试快速模式的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
project_root = current_file.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from service.core.container import container
from service.src.doc_agent.graph.state import ResearchState


async def test_fast_mode():
    """测试快速模式"""
    print("🚀 开始测试快速模式...")

    # 创建测试状态
    initial_state = ResearchState(topic="人工智能在医疗领域的应用",
                                  messages=[],
                                  initial_gathered_data="",
                                  document_outline={},
                                  chapters_to_process=[],
                                  current_chapter_index=0,
                                  completed_chapters_content=[],
                                  final_document="")

    print("✅ 初始状态创建成功")
    print(f"📝 主题: {initial_state.get('topic', 'N/A')}")

    # 使用快速图
    fast_graph = container.fast_main_graph
    print("✅ 快速图加载成功")

    # 运行快速模式
    print("🔄 开始执行快速模式...")
    step_count = 0

    try:
        async for step_output in fast_graph.astream(initial_state):
            step_count += 1
            node_name = list(step_output.keys())[0]
            node_data = list(step_output.values())[0]

            print(f"📋 步骤 {step_count}: {node_name}")

            # 显示一些关键信息
            if "document_outline" in node_data:
                outline = node_data["document_outline"]
                if "chapters" in outline:
                    print(f"   📚 大纲章节数: {len(outline['chapters'])}")

            if "chapters_to_process" in node_data:
                chapters = node_data["chapters_to_process"]
                print(f"   📄 待处理章节数: {len(chapters)}")

            if "final_document" in node_data:
                doc = node_data["final_document"]
                print(f"   📖 最终文档长度: {len(doc)} 字符")
                break

        print(f"✅ 快速模式执行完成，共 {step_count} 个步骤")

    except Exception as e:
        print(f"❌ 快速模式执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_fast_mode())
