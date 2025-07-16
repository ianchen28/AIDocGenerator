# service/core/container.py
import sys
from pathlib import Path
from functools import partial

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.llm_clients import get_llm_client
from src.doc_agent.tools import get_web_search_tool, get_all_tools
from src.doc_agent.graph import nodes, router
from src.doc_agent.graph.builder import build_graph


class Container:
    """依赖注入容器"""

    def __init__(self):
        # 实例化所有单例服务 - 使用 Qwen235B 模型
        self.llm_client = get_llm_client(model_key="qwen_2_5_235b_a22b")
        self.search_tool = get_web_search_tool()
        self.tools = get_all_tools()

        # 用partial绑定依赖
        planner_node = partial(nodes.planner_node, llm_client=self.llm_client)
        researcher_node = partial(nodes.async_researcher_node,
                                  web_search_tool=self.search_tool)
        writer_node = partial(nodes.writer_node, llm_client=self.llm_client)
        supervisor_router_func = partial(router.supervisor_router,
                                         llm_client=self.llm_client)

        # 编译图
        self.graph = build_graph(planner_node, researcher_node, writer_node,
                                 supervisor_router_func)


# 创建一个全局容器实例供应用使用
container = Container()
