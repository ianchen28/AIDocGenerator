# service/src/doc_agent/tools/__init__.py

import asyncio
from typing import Set, Optional
from .web_search import WebSearchTool
from .es_search import ESSearchTool
from .code_execute import CodeExecuteTool
from ..utils import get_settings

# 全局工具注册表，用于跟踪需要关闭的ES工具
_es_tools_registry: Set[ESSearchTool] = set()


def register_es_tool(tool: ESSearchTool):
    """注册ES工具到全局注册表"""
    _es_tools_registry.add(tool)


def unregister_es_tool(tool: ESSearchTool):
    """从全局注册表移除ES工具"""
    _es_tools_registry.discard(tool)


async def close_all_es_tools():
    """关闭所有注册的ES工具"""
    if _es_tools_registry:
        print(f"🔧 正在关闭 {len(_es_tools_registry)} 个ES工具...")
        for tool in list(_es_tools_registry):
            try:
                await tool.close()
                unregister_es_tool(tool)
            except Exception as e:
                print(f"⚠️  关闭ES工具时出错: {e}")
        print("✅ 所有ES工具已关闭")


def get_web_search_tool() -> WebSearchTool:
    """
    获取网络搜索工具实例
    
    Returns:
        WebSearchTool: 配置好的网络搜索工具
    """
    settings = get_settings()
    # 从配置中获取Tavily API密钥
    tavily_config = settings.tavily_config
    api_key = tavily_config.api_key if tavily_config else None

    return WebSearchTool(api_key=api_key)


def get_es_search_tool() -> ESSearchTool:
    """
    获取Elasticsearch搜索工具实例
    
    Returns:
        ESSearchTool: 配置好的ES搜索工具
    """
    settings = get_settings()
    # 从配置中获取ES配置
    es_config = settings.elasticsearch_config

    tool = ESSearchTool(hosts=es_config.hosts,
                        username=es_config.username,
                        password=es_config.password,
                        index_prefix=es_config.index_prefix,
                        timeout=es_config.timeout)

    # 注册到全局注册表
    register_es_tool(tool)
    return tool


def get_code_execute_tool() -> CodeExecuteTool:
    """
    获取代码执行工具实例
    
    Returns:
        CodeExecuteTool: 配置好的代码执行工具
    """
    return CodeExecuteTool()


def get_all_tools():
    """
    获取所有可用的工具
    
    Returns:
        dict: 包含所有工具实例的字典
    """
    tools = {
        "web_search": get_web_search_tool(),
        "es_search": get_es_search_tool(),
        "code_execute": get_code_execute_tool(),
    }
    return tools
