# service/core/container.py
from functools import partial
from pathlib import Path

import yaml
from doc_agent.core.logger import logger

# 确保环境变量已加载
from doc_agent.core.config import settings
from doc_agent.core.env_loader import setup_environment
from doc_agent.core.logging_config import setup_logging

setup_environment()

# 初始化日志系统
setup_logging(settings)

# 导入 doc_agent 模块
from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
from doc_agent.graph.callbacks import create_redis_callback_handler
from doc_agent.graph.chapter_workflow import nodes as chapter_nodes
from doc_agent.graph.chapter_workflow import router as chapter_router
from doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph
# 快速构建器已删除，统一使用配置控制复杂度
from doc_agent.graph.main_orchestrator import nodes as main_orchestrator_nodes
from doc_agent.graph.main_orchestrator.builder import (
    build_document_graph,
    build_main_orchestrator_graph,
    build_outline_graph,
)
from doc_agent.llm_clients import get_llm_client
from doc_agent.tools import (
    get_all_tools,
    get_es_search_tool,
    get_reranker_tool,
    get_web_search_tool,
)
from doc_agent.tools.ai_editing_tool import AIEditingTool


class Container:
    """
    依赖注入容器。
    现在负责实例化和组装主、子两个工作流。
    """

    def _load_genre_strategies(self):
        """
        加载 genre 策略配置

        Returns:
            dict: genre 策略字典
        """
        try:
            # 尝试从 service/core/genres.yaml 加载
            genres_file = Path(__file__).parent / "genres.yaml"
            if not genres_file.exists():
                logger.warning(f"genres.yaml 文件不存在: {genres_file}")
                return self._get_default_genre_strategies()

            with open(genres_file, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                strategies = data.get('genres', {})
                logger.info(f"成功加载 {len(strategies)} 个 genre 策略")
                return strategies

        except Exception as e:
            logger.error(f"加载 genre 策略失败: {e}")
            return self._get_default_genre_strategies()

    def _get_default_genre_strategies(self):
        """
        获取默认的 genre 策略
        
        Returns:
            dict: 默认的 genre 策略字典
        """
        return {
            "default": {
                "name": "通用文档",
                "description": "适用于大多数标准报告和分析。",
                "prompt_versions": {
                    "planner": "v1_default",
                    "supervisor": "v1_metadata_based",
                    "writer": "v1_default",
                    "outline_generation": "v1_default",
                    "reflection": "v1_default"
                }
            },
            "simple": {
                "name": "简化文档",
                "description": "适用于快速测试和简化任务。",
                "prompt_versions": {
                    "planner": "v1_simple",
                    "supervisor": "v1_simple",
                    "writer": "v2_simple_citations",
                    "outline_generation": "v1_simple",
                    "reflection": "v1_default"
                }
            }
        }

    def __init__(self):
        logger.info("🚀 Initializing Container...")

        # 加载 genre 策略
        self.genre_strategies = self._load_genre_strategies()
        logger.info(f"加载了 {len(self.genre_strategies)} 个 genre 策略")

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

        # 使用加载的 genre 策略初始化 PromptSelector
        self.prompt_selector = PromptSelector(self.genre_strategies)

        # 初始化 AI 编辑工具
        self.ai_editing_tool = AIEditingTool(
            llm_client=self.llm_client, prompt_selector=self.prompt_selector)

        logger.info("   - LLM Client, Tools and PromptSelector are ready.")

        logger.info("   - Binding dependencies for Chapter Workflow...")
        chapter_planner_node = partial(chapter_nodes.planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre="default")
        chapter_researcher_node = partial(chapter_nodes.async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)
        chapter_writer_node = partial(chapter_nodes.writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      genre="default",
                                      prompt_version="v4_with_style_guide")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre="default")

        # 编译子工作流图，得到一个可执行的 Runnable 对象
        # 这个 compiled_chapter_graph 本身也是一个"工具"，将被主流程调用
        self.chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router,
            reflection_node=None)  # 在初始化时不使用 reflection_node
        logger.info("   - Chapter Workflow Graph compiled successfully.")

        # 构建拆分后的图架构
        logger.info(
            "   - Binding dependencies for Split Graph Architecture...")

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
            genre="default")
        # split_chapters_node 是纯逻辑节点，通常不需要外部依赖
        main_split_chapters_node = main_orchestrator_nodes.split_chapters_node
        # fusion_editor_node 需要 llm_client 依赖
        main_fusion_editor_node = partial(
            main_orchestrator_nodes.fusion_editor_node,
            llm_client=self.llm_client)

        # 编译大纲生成图
        self.outline_graph = build_outline_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node)
        logger.info("   - Outline Graph compiled successfully.")

        # 编译文档生成图
        self.document_graph = build_document_graph(
            chapter_workflow_graph=self.chapter_graph,
            split_chapters_node=main_split_chapters_node,
            fusion_editor_node=main_fusion_editor_node)
        logger.info("   - Document Graph compiled successfully.")

        # 保留原有的主工作流图（向后兼容）
        self.main_graph = build_main_orchestrator_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node,
            split_chapters_node=main_split_chapters_node,
            chapter_workflow_graph=self.chapter_graph,
            fusion_editor_node=main_fusion_editor_node)

        logger.info("   - Main Orchestrator Graph compiled successfully.")
        logger.info("   - 快速模式已统一到配置控制中")
        logger.info("✅ Container initialization complete.")

    def get_graph_runnable_for_job(self, job_id: str, genre: str = "default"):
        """
        为指定作业获取带有Redis回调处理器的图执行器

        Args:
            job_id: 作业ID，用于创建特定的回调处理器
            genre: 文档类型，用于选择相应的prompt策略

        Returns:
            配置了Redis回调处理器的图执行器
        """
        # 创建Redis回调处理器
        redis_handler = create_redis_callback_handler(
            job_id, self._get_redis_publisher())

        # 根据genre创建相应的节点绑定
        configured_graph = self._get_genre_aware_graph(genre, redis_handler)

        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了带回调处理器的图执行器")
        return configured_graph

    def _get_redis_publisher(self):
        """
        获取Redis发布器实例
        
        Returns:
            RedisStreamPublisher: Redis发布器实例
        """
        try:
            from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
            from doc_agent.core.redis_health_check import get_redis_connection_manager
            import asyncio

            # 使用连接管理器获取Redis客户端
            async def create_publisher():
                manager = await get_redis_connection_manager()
                redis_client = await manager.get_client()
                return RedisStreamPublisher(redis_client)

            # 在事件循环中创建发布器
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，使用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run,
                                                 create_publisher())
                        publisher = future.result(timeout=10)
                else:
                    publisher = loop.run_until_complete(create_publisher())
            except RuntimeError:
                # 如果没有事件循环，创建新的
                publisher = asyncio.run(create_publisher())

            logger.info("RedisStreamPublisher 创建成功")
            return publisher

        except Exception as e:
            logger.error(f"无法创建Redis发布器: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def _get_genre_aware_graph(self, genre: str, redis_handler):
        """
        根据genre获取相应的图执行器

        Args:
            genre: 文档类型
            redis_handler: Redis回调处理器

        Returns:
            配置了回调处理器的图执行器
        """
        # 验证genre是否存在
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"

        # 根据genre创建节点绑定
        chapter_planner_node = partial(chapter_nodes.planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre=genre)
        chapter_writer_node = partial(chapter_nodes.writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      genre=genre,
                                      prompt_version="v4_with_style_guide")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)

        # 创建reflection_node绑定
        reflection_node = partial(chapter_nodes.reflection_node,
                                  llm_client=self.llm_client,
                                  prompt_selector=self.prompt_selector,
                                  genre=genre)

        # 创建researcher_node绑定（使用现有的绑定）
        chapter_researcher_node = partial(chapter_nodes.async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)

        # 创建chapter workflow graph
        chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router,
            reflection_node=reflection_node)  # 添加 reflection_node

        # 创建main orchestrator节点绑定
        main_outline_generation_node = partial(
            main_orchestrator_nodes.outline_generation_node,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)

        # 创建initial_research_node绑定（使用现有的绑定）
        main_initial_research_node = partial(
            main_orchestrator_nodes.initial_research_node,
            web_search_tool=self.web_search_tool,
            es_search_tool=self.es_search_tool,
            reranker_tool=self.reranker_tool)

        # 创建split_chapters_node绑定（使用现有的绑定）
        main_split_chapters_node = partial(
            main_orchestrator_nodes.split_chapters_node)

        # 创建bibliography_node绑定
        bibliography_node = partial(main_orchestrator_nodes.bibliography_node)

        # 创建fusion_editor_node绑定
        fusion_editor_node = partial(
            main_orchestrator_nodes.fusion_editor_node,
            llm_client=self.llm_client)

        # 创建main orchestrator graph
        main_graph = build_main_orchestrator_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node,
            split_chapters_node=main_split_chapters_node,
            chapter_workflow_graph=chapter_graph,
            fusion_editor_node=fusion_editor_node,
            bibliography_node_func=bibliography_node)

        # 使用回调处理器配置图
        configured_graph = main_graph.with_config(
            {"callbacks": [redis_handler]})

        return configured_graph

    def _get_genre_aware_outline_graph(self, genre: str, redis_handler):
        """
        根据genre获取大纲生成图的执行器

        Args:
            genre: 文档类型
            redis_handler: Redis回调处理器

        Returns:
            配置了回调处理器的大纲生成图执行器
        """
        # 验证genre是否存在
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"

        # 创建大纲生成节点绑定
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
            genre=genre)

        # 创建大纲生成图
        outline_graph = build_outline_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node)

        # 使用回调处理器配置图
        configured_graph = outline_graph.with_config(
            {"callbacks": [redis_handler]})

        return configured_graph

    def _get_genre_aware_document_graph(self, genre: str, redis_handler):
        """
        根据genre获取文档生成图的执行器

        Args:
            genre: 文档类型
            redis_handler: Redis回调处理器

        Returns:
            配置了回调处理器的文档生成图执行器
        """
        # 验证genre是否存在
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"

        # 根据genre创建章节工作流节点绑定
        chapter_planner_node = partial(chapter_nodes.planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre=genre)
        chapter_writer_node = partial(chapter_nodes.writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      genre=genre,
                                      prompt_version="v4_with_style_guide")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)

        # 创建reflection_node绑定
        reflection_node = partial(chapter_nodes.reflection_node,
                                  llm_client=self.llm_client,
                                  prompt_selector=self.prompt_selector,
                                  genre=genre)

        # 创建researcher_node绑定
        chapter_researcher_node = partial(chapter_nodes.async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)

        # 创建章节工作流图
        chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router,
            reflection_node=reflection_node)

        # 创建文档生成节点绑定
        main_split_chapters_node = main_orchestrator_nodes.split_chapters_node
        fusion_editor_node = partial(
            main_orchestrator_nodes.fusion_editor_node,
            llm_client=self.llm_client)

        # 创建文档生成图
        document_graph = build_document_graph(
            chapter_workflow_graph=chapter_graph,
            split_chapters_node=main_split_chapters_node,
            fusion_editor_node=fusion_editor_node,
            bibliography_node_func=main_orchestrator_nodes.bibliography_node)

        # 使用回调处理器配置图
        configured_graph = document_graph.with_config(
            {"callbacks": [redis_handler]})

        return configured_graph

    def get_outline_graph_runnable_for_job(self,
                                           job_id: str,
                                           genre: str = "default"):
        """
        为指定作业获取大纲生成图的执行器

        Args:
            job_id: 作业ID，用于创建特定的回调处理器
            genre: 文档类型，用于选择相应的prompt策略

        Returns:
            配置了Redis回调处理器的大纲生成图执行器
        """
        # 创建Redis回调处理器
        redis_handler = create_redis_callback_handler(
            job_id, self._get_redis_publisher())

        # 根据genre创建相应的节点绑定
        configured_graph = self._get_genre_aware_outline_graph(
            genre, redis_handler)

        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了大纲生成图执行器")
        return configured_graph

    def get_document_graph_runnable_for_job(self,
                                            job_id: str,
                                            genre: str = "default"):
        """
        为指定作业获取文档生成图的执行器

        Args:
            job_id: 作业ID，用于创建特定的回调处理器
            genre: 文档类型，用于选择相应的prompt策略

        Returns:
            配置了Redis回调处理器的文档生成图执行器
        """
        # 创建Redis回调处理器
        redis_handler = create_redis_callback_handler(
            job_id, self._get_redis_publisher())

        # 根据genre创建相应的节点绑定
        configured_graph = self._get_genre_aware_document_graph(
            genre, redis_handler)

        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了文档生成图执行器")
        return configured_graph

    def get_fast_graph_runnable_for_job(self, job_id: str):
        """
        为指定作业获取快速模式的图执行器（已统一到配置控制）
        Args:
            job_id: 作业ID，用于创建特定的回调处理器
        """
        # 创建Redis回调处理器
        redis_handler = create_redis_callback_handler(
            job_id, self._get_redis_publisher())

        # 使用标准图，但通过配置控制快速模式
        configured_graph = self._get_genre_aware_graph("default",
                                                       redis_handler)

        logger.info(f"为作业 {job_id} 创建了快速模式图执行器（通过配置控制）")
        return configured_graph

    async def cleanup(self):
        """清理资源 (保持不变)"""
        # 关闭ES工具等需要清理的资源
        from doc_agent.tools import close_all_es_tools
        await close_all_es_tools()
        print("🧹 Resources cleaned up.")


# --- 6. 延迟实例化 ---
# 创建一个全局容器实例供应用使用，但延迟到实际使用时
_container_instance = None


def get_container():
    """获取容器实例，延迟初始化"""
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance


# 为了向后兼容，保留 container 变量，但延迟初始化
def container():
    return get_container()
