#!/usr/bin/env python3
"""
演示修改后的researcher_node的向量搜索功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent  # service 目录
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 添加src目录到Python路径
src_dir = service_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.doc_agent.graph.nodes import async_researcher_node
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.tools.web_search import WebSearchTool
from core.config import settings


async def test_researcher_node_with_vector():
    """测试带有向量搜索的researcher_node"""

    print("🚀 开始测试researcher_node向量搜索功能...")

    # 创建测试状态
    state = ResearchState()
    state["search_queries"] = ["电力系统运行", "变电站设备维护", "输电线路故障处理", "配电网络优化"]

    # 创建网络搜索工具
    web_search_tool = WebSearchTool()

    print(f"📝 测试查询: {state['search_queries']}")
    print("=" * 60)

    # 执行researcher_node
    try:
        result = await async_researcher_node(state, web_search_tool)

        print("\n" + "=" * 60)
        print("📊 搜索结果汇总:")
        print("=" * 60)

        gathered_data = result.get("gathered_data", "")
        print(f"总结果长度: {len(gathered_data)} 字符")
        print(f"结果预览:\n{gathered_data[:1000]}...")

        # 分析结果
        if "混合搜索执行成功" in gathered_data:
            print("\n✅ 向量搜索功能正常工作")
        elif "文本搜索执行成功" in gathered_data:
            print("\n⚠️  向量搜索失败，但文本搜索正常工作")
        else:
            print("\n❌ 搜索功能可能存在问题")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


async def main():
    """主函数"""
    success = await test_researcher_node_with_vector()

    if success:
        print("\n🎉 测试完成！")
    else:
        print("\n⚠️  测试失败！")


if __name__ == "__main__":
    asyncio.run(main())
