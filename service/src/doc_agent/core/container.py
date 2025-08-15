from functools import partial
from pathlib import Path

import yaml
from doc_agent.core.logger import logger

# 确保环境变量已加载
from doc_agent.core.config import settings
from doc_agent.core.env_loader import setup_environment

setup_environment()

# 导入 doc_agent 模块
import redis  # 导入同步 redis
import redis.asyncio as aredis
from redis.cluster import ClusterNode

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
from doc_agent.graph.callbacks import create_redis_callback_handler
from doc_agent.graph.chapter_workflow import router as chapter_router
from doc_agent.graph.chapter_workflow.builder import build_chapter_workflow_graph
from doc_agent.graph.chapter_workflow.nodes import (
    async_researcher_node,
    planner_node,
    reflection_node,
    writer_node,
)
from doc_agent.graph.main_orchestrator.builder import (
    build_document_graph,
    build_main_orchestrator_graph,
    build_outline_graph,
    build_outline_loader_graph,
)
from doc_agent.graph.main_orchestrator.nodes import (
    bibliography_node,
    fusion_editor_node,
    initial_research_node,
    outline_generation_node,
    outline_loader_node,
    split_chapters_node,
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

        # --- 1. 初始化 Redis 客户端和发布器 ---
        logger.info("  - Initializing Redis connections...")
        redis_config = settings.redis_config
        mode = redis_config.get('mode', 'single')
        stream_name = "default"

        if mode == 'cluster':
            # 集群模式
            logger.info("    - Initializing Redis Cluster connections...")
            cluster_config = redis_config.get('cluster', {})

            # 构建集群连接参数
            startup_nodes = []
            for node in cluster_config.get('nodes', []):
                host, port = node.split(':')
                startup_nodes.append(ClusterNode(host, int(port)))

            # 为 SSE 端点创建异步集群客户端
            self.async_redis_client = aredis.RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                password=cluster_config.get('password'))
            logger.info("    - Asynchronous Redis Cluster client created.")

            # 为回调处理器创建同步集群客户端
            self.sync_redis_client = redis.RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                password=cluster_config.get('password'),
                skip_full_coverage_check=True)
            logger.info("    - Synchronous Redis Cluster client created.")
        else:
            # 单节点模式
            logger.info("    - Initializing Redis Single Node connections...")
            redis_url = settings.redis_url

            # 为 SSE 端点创建异步客户端
            self.async_redis_client = aredis.from_url(redis_url,
                                                      encoding="utf-8",
                                                      decode_responses=True)
            logger.info("    - Asynchronous Redis client created.")

            # 为回调处理器创建同步客户端
            self.sync_redis_client = redis.from_url(redis_url,
                                                    encoding="utf-8",
                                                    decode_responses=True)
            logger.info("    - Synchronous Redis client created.")

        # 创建并存储同步的 RedisStreamPublisher 实例
        self.redis_publisher = RedisStreamPublisher(
            redis_client=self.sync_redis_client, stream_name=stream_name)
        logger.info("    - Synchronous RedisStreamPublisher created.")
        # --- Redis 初始化结束 ---

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

        logger.info("    - LLM Client, Tools and PromptSelector are ready.")

        logger.info("    - Binding dependencies for Chapter Workflow...")
        chapter_planner_node = partial(planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre="default")
        chapter_researcher_node = partial(async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)
        chapter_writer_node = partial(writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      genre="default",
                                      prompt_version="v4_with_style_guide")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre="default")

        # 编译子工作流图
        self.chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router,
            reflection_node=None)
        logger.info("    - Chapter Workflow Graph compiled successfully.")

        # 构建拆分后的图架构
        logger.info(
            "    - Binding dependencies for Split Graph Architecture...")

        # 为主工作流的节点绑定依赖
        main_initial_research_node = partial(
            initial_research_node,
            web_search_tool=self.web_search_tool,
            es_search_tool=self.es_search_tool,
            reranker_tool=self.reranker_tool,
            llm_client=self.llm_client)
        main_outline_generation_node = partial(
            outline_generation_node,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre="default")
        main_split_chapters_node = partial(split_chapters_node,
                                           llm_client=self.llm_client)
        main_fusion_editor_node = partial(fusion_editor_node,
                                          llm_client=self.llm_client)

        # 编译大纲生成图
        self.outline_graph = build_outline_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node)
        logger.info("    - Outline Graph compiled successfully.")

        # 编译大纲加载器图
        main_outline_loader_node = partial(outline_loader_node,
                                           llm_client=self.llm_client,
                                           es_search_tool=self.es_search_tool)
        self.outline_loader_graph = build_outline_loader_graph(
            outline_loader_node=main_outline_loader_node)
        logger.info("    - Outline Loader Graph compiled successfully.")

        # 编译文档生成图
        self.document_graph = build_document_graph(
            chapter_workflow_graph=self.chapter_graph,
            split_chapters_node=main_split_chapters_node,
            fusion_editor_node=main_fusion_editor_node)
        logger.info("    - Document Graph compiled successfully.")

        # 保留原有的主工作流图（向后兼容）
        self.main_graph = build_main_orchestrator_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node,
            split_chapters_node=main_split_chapters_node,
            chapter_workflow_graph=self.chapter_graph,
            fusion_editor_node=main_fusion_editor_node)

        logger.info("    - Main Orchestrator Graph compiled successfully.")
        logger.info("    - 快速模式已统一到配置控制中")
        logger.info("✅ Container initialization complete.")

    def get_graph_runnable_for_job(self, job_id: str, genre: str = "default"):
        """
        为指定作业获取带有Redis回调处理器的图执行器
        """
        redis_handler = create_redis_callback_handler(job_id)
        configured_graph = self._get_genre_aware_graph(genre, redis_handler)
        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了带回调处理器的图执行器")
        return configured_graph

    # 这个方法现在已经不需要了，可以安全删除
    # def _get_redis_publisher(self): ...

    def _get_genre_aware_graph(self, genre: str, redis_handler):
        """
        根据genre获取相应的图执行器
        """
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"

        chapter_planner_node = partial(planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre=genre)
        chapter_writer_node = partial(writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      genre=genre,
                                      prompt_version="v4_with_style_guide")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)
        reflection_node_func = partial(reflection_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre=genre)
        chapter_researcher_node = partial(async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)
        chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router,
            reflection_node=reflection_node_func)
        main_outline_generation_node = partial(
            outline_generation_node,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)
        main_initial_research_node = partial(
            initial_research_node,
            web_search_tool=self.web_search_tool,
            es_search_tool=self.es_search_tool,
            reranker_tool=self.reranker_tool)
        main_split_chapters_node = partial(split_chapters_node,
                                           llm_client=self.llm_client)
        bibliography_node_func = partial(bibliography_node)
        fusion_editor_node_func = partial(fusion_editor_node,
                                          llm_client=self.llm_client)
        main_graph = build_main_orchestrator_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node,
            split_chapters_node=main_split_chapters_node,
            chapter_workflow_graph=chapter_graph,
            fusion_editor_node=fusion_editor_node_func,
            bibliography_node_func=bibliography_node_func)
        configured_graph = main_graph.with_config(
            {"callbacks": [redis_handler]})
        return configured_graph

    def _get_genre_aware_outline_graph(self, genre: str, redis_handler):
        """
        根据genre获取大纲生成图的执行器
        """
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"
        main_initial_research_node = partial(
            initial_research_node,
            web_search_tool=self.web_search_tool,
            es_search_tool=self.es_search_tool,
            reranker_tool=self.reranker_tool,
            llm_client=self.llm_client)
        main_outline_generation_node = partial(
            outline_generation_node,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)
        outline_graph = build_outline_graph(
            initial_research_node=main_initial_research_node,
            outline_generation_node=main_outline_generation_node)
        configured_graph = outline_graph.with_config(
            {"callbacks": [redis_handler]})
        return configured_graph

    def _get_genre_aware_outline_loader_graph(self, genre: str, redis_handler):
        """
        根据genre获取大纲加载器图的执行器
        """
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"
        main_outline_loader_node = partial(outline_loader_node,
                                           llm_client=self.llm_client,
                                           es_search_tool=self.es_search_tool)
        outline_loader_graph = build_outline_loader_graph(
            outline_loader_node=main_outline_loader_node)
        configured_graph = outline_loader_graph.with_config(
            {"callbacks": [redis_handler]})
        return configured_graph

    def _get_genre_aware_document_graph(self, genre: str, redis_handler):
        """
        根据genre获取文档生成图的执行器
        """
        if genre not in self.genre_strategies:
            logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
            genre = "default"
        chapter_planner_node = partial(planner_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre=genre)
        chapter_writer_node = partial(writer_node,
                                      llm_client=self.llm_client,
                                      prompt_selector=self.prompt_selector,
                                      genre=genre,
                                      prompt_version="v4_with_style_guide")
        chapter_supervisor_router = partial(
            chapter_router.supervisor_router,
            llm_client=self.llm_client,
            prompt_selector=self.prompt_selector,
            genre=genre)
        reflection_node_func = partial(reflection_node,
                                       llm_client=self.llm_client,
                                       prompt_selector=self.prompt_selector,
                                       genre=genre)
        chapter_researcher_node = partial(async_researcher_node,
                                          web_search_tool=self.web_search_tool,
                                          es_search_tool=self.es_search_tool,
                                          reranker_tool=self.reranker_tool)
        chapter_graph = build_chapter_workflow_graph(
            planner_node=chapter_planner_node,
            researcher_node=chapter_researcher_node,
            writer_node=chapter_writer_node,
            supervisor_router_func=chapter_supervisor_router,
            reflection_node=reflection_node_func)
        main_split_chapters_node = partial(split_chapters_node,
                                           llm_client=self.llm_client)
        bibliography_node_func = partial(bibliography_node)
        fusion_editor_node_func = partial(fusion_editor_node,
                                          llm_client=self.llm_client)
        document_graph = build_document_graph(
            chapter_workflow_graph=chapter_graph,
            split_chapters_node=main_split_chapters_node,
            fusion_editor_node=fusion_editor_node_func,
            bibliography_node_func=bibliography_node_func)
        configured_graph = document_graph.with_config(
            {"callbacks": [redis_handler]})
        return configured_graph

    def get_outline_graph_runnable_for_job(self,
                                           job_id: str,
                                           genre: str = "default"):
        """
        为指定作业获取大纲生成图的执行器
        """
        redis_handler = create_redis_callback_handler(job_id)
        configured_graph = self._get_genre_aware_outline_graph(
            genre, redis_handler)
        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了大纲生成图执行器")
        return configured_graph

    def get_outline_loader_graph_runnable_for_job(self,
                                                  job_id: str,
                                                  genre: str = "default"):
        """
        为指定作业获取大纲加载器图的执行器
        """
        redis_handler = create_redis_callback_handler(job_id)
        configured_graph = self._get_genre_aware_outline_loader_graph(
            genre, redis_handler)
        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了大纲加载器图执行器")
        return configured_graph

    def get_document_graph_runnable_for_job(self,
                                            job_id: str,
                                            genre: str = "default"):
        """
        为指定作业获取文档生成图的执行器
        """
        redis_handler = create_redis_callback_handler(job_id)
        configured_graph = self._get_genre_aware_document_graph(
            genre, redis_handler)
        logger.info(f"为作业 {job_id} (genre: {genre}) 创建了文档生成图执行器")
        return configured_graph

    def get_fast_graph_runnable_for_job(self, job_id: str):
        """
        为指定作业获取快速模式的图执行器（已统一到配置控制）
        """
        redis_handler = create_redis_callback_handler(job_id)
        configured_graph = self._get_genre_aware_graph("default",
                                                       redis_handler)
        logger.info(f"为作业 {job_id} 创建了快速模式图执行器（通过配置控制）")
        return configured_graph

    async def cleanup(self):
        """清理资源 (保持不变)"""
        from doc_agent.tools import close_all_es_tools
        await close_all_es_tools()
        print("🧹 Resources cleaned up.")


# --- 延迟实例化 ---
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
