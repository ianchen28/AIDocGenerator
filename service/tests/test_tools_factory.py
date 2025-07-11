#!/usr/bin/env python3
"""
测试工具工厂函数
"""

from test_base import TestBase, setup_paths

# 设置测试环境
setup_paths()

from src.doc_agent.tools import get_web_search_tool, get_all_tools
from core.config import settings


def test_tools_factory():
    """测试工具工厂函数"""
    print("=== 工具工厂函数测试 ===")

    # 测试配置
    print("📋 配置测试:")
    tavily_config = settings.tavily_config
    print(f"  Tavily API Key: {tavily_config.api_key[:10]}..."
          if tavily_config.api_key else "Not set")
    print(f"  Search Depth: {tavily_config.search_depth}")
    print(f"  Max Results: {tavily_config.max_results}")

    # 测试WebSearchTool工厂函数
    print("\n🔧 WebSearchTool工厂函数测试:")
    try:
        web_search_tool = get_web_search_tool()
        print("  ✅ WebSearchTool 创建成功")
        print(f"     类型: {type(web_search_tool).__name__}")
        print(f"     API Key: {web_search_tool.api_key[:10]}..."
              if web_search_tool.api_key else "None")

        # 测试搜索功能
        result = web_search_tool.search("测试查询")
        print("  ✅ 搜索功能正常")
        print(f"     结果长度: {len(result)} 字符")

    except Exception as e:
        print(f"  ❌ WebSearchTool 创建失败: {str(e)}")

    # 测试get_all_tools函数
    print("\n🔧 get_all_tools函数测试:")
    try:
        all_tools = get_all_tools()
        print("  ✅ 所有工具获取成功")
        print(f"     工具数量: {len(all_tools)}")
        for tool_name, tool_instance in all_tools.items():
            print(f"     - {tool_name}: {type(tool_instance).__name__}")

    except Exception as e:
        print(f"  ❌ get_all_tools 失败: {str(e)}")

    # 测试ES搜索工具（应该抛出NotImplementedError）
    print("\n🔧 ES搜索工具测试:")
    try:
        from src.doc_agent.tools import get_es_search_tool
        es_tool = get_es_search_tool()
        print("  ✅ ES搜索工具创建成功")
    except NotImplementedError as e:
        print(f"  ⚠️  ES搜索工具尚未实现: {str(e)}")
    except Exception as e:
        print(f"  ❌ ES搜索工具测试失败: {str(e)}")

    print("\n🎯 使用示例:")
    print("""
# 使用工厂函数获取工具
from src.doc_agent.tools import get_web_search_tool, get_all_tools

# 获取单个工具
web_search = get_web_search_tool()
results = web_search.search("查询内容")

# 获取所有工具
all_tools = get_all_tools()
web_search = all_tools["web_search"]

# 在容器中使用
from core.container import container
search_tool = container.search_tool
tools = container.tools
    """)


if __name__ == "__main__":
    test_tools_factory()
