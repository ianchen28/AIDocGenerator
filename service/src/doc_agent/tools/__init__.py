# service/src/doc_agent/tools/__init__.py

import asyncio
from typing import Set, Optional
from .web_search import WebSearchTool
from .es_search import ESSearchTool
from .code_execute import CodeExecuteTool
from .reranker import RerankerTool

# 修复相对导入
try:
    from ..utils import get_settings
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from src.doc_agent.utils import get_settings
    except ImportError:
        # 如果都失败，创建一个简单的设置函数
        def get_settings():
            """简单的设置获取函数"""
            import sys
            from pathlib import Path

            # 添加项目根目录到Python路径
            current_file = Path(__file__)
            service_dir = None
            for parent in current_file.parents:
                if parent.name == 'service':
                    service_dir = parent
                    break

            if service_dir and str(service_dir) not in sys.path:
                sys.path.insert(0, str(service_dir))

            from core.config import settings
            return settings


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


def get_reranker_tool() -> RerankerTool:
    """
    获取重排序工具实例
    
    Returns:
        RerankerTool: 配置好的重排序工具
    """
    settings = get_settings()
    # 从配置中获取reranker配置
    reranker_config = settings.get_model_config("reranker")
    if reranker_config:
        return RerankerTool(base_url=reranker_config.url,
                            api_key=reranker_config.api_key)
    else:
        raise ValueError("未找到reranker配置")


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
