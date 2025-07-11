# service/examples/researcher_node_demo.py
"""
researcher_node 使用示例

演示如何使用 researcher_node 进行搜索研究
"""

import sys
from pathlib import Path
import asyncio

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent  # 上级目录 service
src_dir = service_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from doc_agent.graph.nodes import async_researcher_node
from doc_agent.graph.state import ResearchState
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.tools.es_search import ESSearchTool


def demo_researcher_node():
    """演示 async_researcher_node 的基本使用"""
    print("=== researcher_node 演示 ===\n")

    # 创建研究状态
    state = ResearchState()
    state["search_queries"] = ["电力", "电网", "变电站"]

    # 创建搜索工具
    web_search_tool = WebSearchTool()

    print("研究状态:")
    print(f"  搜索查询: {state['search_queries']}")
    print()

    # 执行异步搜索研究
    print("执行搜索研究...")
    result = asyncio.run(async_researcher_node(state, web_search_tool))

    print("\n搜索结果:")
    print("=" * 50)
    print(result["gathered_data"])
    print("=" * 50)


def demo_researcher_node_with_custom_queries():
    """演示使用自定义搜索查询 (异步)"""
    print("\n=== 自定义搜索查询演示 ===\n")

    # 创建研究状态
    state = ResearchState()
    state["search_queries"] = ["配电", "调度", "保护"]

    # 创建搜索工具
    web_search_tool = WebSearchTool()

    print("自定义搜索查询:")
    for i, query in enumerate(state["search_queries"], 1):
        print(f"  {i}. {query}")
    print()

    # 执行异步搜索研究
    result = asyncio.run(async_researcher_node(state, web_search_tool))

    print("搜索结果摘要:")
    print("=" * 50)
    # 只显示前500个字符作为摘要
    summary = result["gathered_data"][:500] + "..." if len(
        result["gathered_data"]) > 500 else result["gathered_data"]
    print(summary)
    print("=" * 50)


if __name__ == "__main__":
    try:
        demo_researcher_node()
        demo_researcher_node_with_custom_queries()
        print("\n演示完成！")
    except Exception as e:
        print(f"演示过程中出现错误: {str(e)}")
        print("这可能是由于ES服务不可用或配置问题导致的，这是正常的。")
