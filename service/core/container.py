# service/core/container.py
from ..doc_agent.llm_clients import get_llm_client
from ..doc_agent.tools import get_web_search_tool, get_all_tools
from ..doc_agent.graph.builder import build_graph


class Container:
    """依赖注入容器"""

    def __init__(self):
        # 实例化所有单例服务
        self.llm_client = get_llm_client()
        self.search_tool = get_web_search_tool()

        # 获取所有工具
        self.tools = get_all_tools()

        # 编译图，并注入依赖
        # LangGraph的 .compile() 返回一个可运行对象 (Runnable)
        # 我们可以使用 .with_config() 在运行时注入固定的依赖
        self.graph = build_graph().with_config({
            "configurable": {
                "llm_client": self.llm_client,
                "search_tool": self.search_tool,
                "tools": self.tools,
            }
        })


# 创建一个全局容器实例供应用使用
container = Container()
