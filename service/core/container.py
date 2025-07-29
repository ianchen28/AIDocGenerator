# service/core/container.py
import sys
from functools import partial
from pathlib import Path

from loguru import logger

# 添加项目根目录到Python路径
# 添加src目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent  # 获取 service 目录
src_dir = service_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 确保环境变量已加载
from core.config import settings
from core.env_loader import setup_environment
from core.logging_config import setup_logging

setup_environment()

# 初始化日志系统
setup_logging(settings)

# 在设置路径后导入 doc_agent 模块
try:
    from doc_agent.common.prompt_selector import PromptSelector
    from doc_agent.graph.callbacks import create_redis_callback_handler
    from doc_agent.graph.chapter_workflow import nodes as chapter_nodes
    from doc_agent.graph.chapter_workflow import router as chapter_router
    from doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph
    from doc_agent.graph.fast_builder import build_fast_main_workflow
    from doc_agent.graph.main_orchestrator import nodes as main_orchestrator_nodes
    from doc_agent.graph.main_orchestrator.builder import build_main_orchestrator_graph
    from doc_agent.llm_clients import get_llm_client
    from doc_agent.tools import (
        get_all_tools,
        get_es_search_tool,
        get_reranker_tool,
        get_web_search_tool,
    )
except ImportError as e:
    print(f"❌ 导入 doc_agent 模块失败: {e}")
    print(f"当前 Python 路径: {sys.path[:3]}")
    raise


class Container:
    """
    依赖注入容器。
    现在负责实例化和组装主、子两个工作流。
    """

    def __init__(self):
        print("🚀 Initializing Container...")

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

        # 初始化 PromptSelector
        self.prompt_selector = PromptSelector()

        print("   - LLM Client, Tools and PromptSelector are ready.")

        print("   - Binding dependencies for Chapter Workflow...")
        chapter_planner_node = partial(chapter_nodes.planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       prompt_version="v1_default")
        chapter_researcher_node = partial(chapter_nodes.async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)
        chapter_writer_node = partial(chapter_nodes.writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      prompt_version="v1_default")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            prompt_version="v1_default")

        # 编译子工作流图，得到一个可执行的 Runnable 对象
        # 这个 compiled_chapter_graph 本身也是一个"工具"，将被主流程调用
        self.chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router)
        print("   - Chapter Workflow Graph compiled successfully.")

        # 构建 "总控" 主工作流 (Main Orchestrator)
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
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            prompt_version="v1_default")
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

    def get_graph_runnable_for_job(self, job_id: str):
        """
        为指定作业获取带有Redis回调处理器的图执行器

        Args:
            job_id: 作业ID，用于创建特定的回调处理器

        Returns:
            配置了Redis回调处理器的图执行器
        """
        # 创建Redis回调处理器
        redis_handler = create_redis_callback_handler(job_id)

        # 使用回调处理器配置主图
        configured_graph = self.main_graph.with_config(
            {"callbacks": [redis_handler]})

        logger.info(f"为作业 {job_id} 创建了带回调处理器的图执行器")
        return configured_graph

    def get_fast_graph_runnable_for_job(self, job_id: str):
        """
        为指定作业获取带有Redis回调处理器的快速图执行器
        Args:
            job_id: 作业ID，用于创建特定的回调处理器
        """
        # 创建Redis回调处理器
        redis_handler = create_redis_callback_handler(job_id)

        # 使用回调处理器配置快速图
        configured_fast_graph = self.fast_main_graph.with_config(
            {"callbacks": [redis_handler]})

        logger.info(f"为作业 {job_id} 创建了带回调处理器的快速图执行器")
        return configured_fast_graph

    async def cleanup(self):
        """清理资源 (保持不变)"""
        # 关闭ES工具等需要清理的资源
        from doc_agent.tools import close_all_es_tools
        await close_all_es_tools()
        print("🧹 Resources cleaned up.")


# --- 6. 最终实例化 (保持不变) ---
# 创建一个全局容器实例供应用使用
container = Container()
