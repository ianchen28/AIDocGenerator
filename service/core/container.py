# service/core/container.py
import sys
from pathlib import Path
from functools import partial

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent  # 获取 service 目录
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 添加src目录到Python路径
src_dir = service_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 确保环境变量已加载
from core.env_loader import setup_environment
from core.config import settings
from core.logging_config import setup_logging

setup_environment()

# 初始化日志系统
setup_logging(settings)

# 在设置路径后导入 doc_agent 模块
try:
    from doc_agent.llm_clients import get_llm_client
    from doc_agent.tools import get_web_search_tool, get_es_search_tool, get_reranker_tool, get_all_tools

    from doc_agent.graph.chapter_workflow import nodes as chapter_nodes
    from doc_agent.graph.chapter_workflow import router as chapter_router
    from doc_agent.graph.main_orchestrator import nodes as main_orchestrator_nodes

    from doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph
    from doc_agent.graph.main_orchestrator.builder import build_main_orchestrator_graph
except ImportError as e:
    print(f"❌ 导入 doc_agent 模块失败: {e}")
    print(f"当前 Python 路径: {sys.path[:3]}")
    raise
from doc_agent.tools import get_web_search_tool, get_es_search_tool, get_reranker_tool, get_all_tools

from doc_agent.graph.chapter_workflow import nodes as chapter_nodes
from doc_agent.graph.chapter_workflow import router as chapter_router
from doc_agent.graph.main_orchestrator import nodes as main_orchestrator_nodes

from doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph
from doc_agent.graph.main_orchestrator.builder import build_main_orchestrator_graph
from doc_agent.graph.fast_builder import build_fast_main_workflow


class Container:
    """
    依赖注入容器。
    现在负责实例化和组装主、子两个工作流。
    """

    def __init__(self):
        print("🚀 Initializing Container...")

        # --- 3. 实例化所有单例服务 (保持不变) ---
        # 这里的具体模型可以从配置中读取，为清晰起见，我们暂时硬编码
        from core.config import settings
        # 读取 default_llm
        default_llm = None
        if hasattr(settings, '_yaml_config') and settings._yaml_config:
            agent_cfg = settings._yaml_config.get('agent_config', {})
            default_llm = agent_cfg.get('default_llm', 'qwen_2_5_235b_a22b')
        if not default_llm:
            default_llm = 'qwen_2_5_235b_a22b'
        self.llm_client = get_llm_client(model_key=default_llm)
        self.web_search_tool = get_web_search_tool()
        self.es_search_tool = get_es_search_tool()
        self.reranker_tool = get_reranker_tool()
        self.tools = get_all_tools()
        print("   - LLM Client and Tools are ready.")

        # --- 4. 构建 "章节生成" 子工作流 (Chapter Workflow) ---
        # 原理: 这个子图是一个可复用的"工人"，专门负责处理单个章节的 "规划->研究->写作" 流程。
        # 我们先用 partial 将它需要的依赖（llm_client, tools）绑定好。
        print("   - Binding dependencies for Chapter Workflow...")

        # 为子工作流的节点和路由绑定依赖
        chapter_planner_node = partial(chapter_nodes.planner_node,
                                       llm_client=self.llm_client)
        chapter_researcher_node = partial(chapter_nodes.async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)
        chapter_writer_node = partial(chapter_nodes.writer_node,
                                      llm_client=self.llm_client)
        chapter_supervisor_router = partial(chapter_router.supervisor_router,
                                            llm_client=self.llm_client)

        # 编译子工作流图，得到一个可执行的 Runnable 对象
        # 这个 compiled_chapter_graph 本身也是一个"工具"，将被主流程调用
        self.chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router)
        print("   - Chapter Workflow Graph compiled successfully.")

        # --- 5. 构建 "总控" 主工作流 (Main Orchestrator) ---
        # 原理: 这是项目的"总指挥"，它负责进行初步研究、生成大纲，然后循环调用上面的"工人"（子图）来处理每个章节。
        print("   - Binding dependencies for Main Orchestrator Workflow...")

        # 为主工作流的节点绑定依赖
        main_initial_research_node = partial(
            main_orchestrator_nodes.initial_research_node,
            web_search_tool=self.web_search_tool,
            es_search_tool=self.es_search_tool,
            reranker_tool=self.reranker_tool,
            llm_client=self.llm_client)
        main_outline_generation_node = partial(
            main_orchestrator_nodes.outline_generation_node,
            llm_client=self.llm_client)
        # split_chapters_node 是纯逻辑节点，通常不需要外部依赖
        main_split_chapters_node = main_orchestrator_nodes.split_chapters_node

        # 编译主工作流图，这是我们整个应用最终的入口点
        # 注意: build_main_orchestrator_graph 的签名也需要更新，以接收所有它需要的节点
        self.main_graph = build_main_orchestrator_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node,
            split_chapters_node=main_split_chapters_node,
            chapter_workflow_graph=self.chapter_graph)

        # 编译快速模式的主工作流图
        self.fast_main_graph = build_fast_main_workflow(
            web_search_tool=self.web_search_tool,
            es_search_tool=self.es_search_tool,
            reranker_tool=self.reranker_tool,
            llm_client=self.llm_client)

        print("   - Main Orchestrator Graph compiled successfully.")
        print("   - Fast Main Orchestrator Graph compiled successfully.")
        print("✅ Container initialization complete.")

    async def cleanup(self):
        """清理资源 (保持不变)"""
        # 关闭ES工具等需要清理的资源
        from doc_agent.tools import close_all_es_tools
        await close_all_es_tools()
        print("🧹 Resources cleaned up.")


# --- 6. 最终实例化 (保持不变) ---
# 创建一个全局容器实例供应用使用
container = Container()
