# service/src/doc_agent/graph/fast_nodes.py
"""
快速版本的节点实现
使用简化的prompts，目标：3-5分钟内完成文档生成
"""

import json
import pprint

from loguru import logger

from doc_agent.core.config import settings
from doc_agent.fast_prompts import (
    FAST_OUTLINE_GENERATION_PROMPT,
    FAST_PLANNER_PROMPT,
)
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.llm_clients.providers import EmbeddingClient
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.reranker import RerankerTool
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.utils.search_utils import search_and_rerank


async def fast_initial_research_node(state: ResearchState,
                                     web_search_tool: WebSearchTool,
                                     es_search_tool: ESSearchTool,
                                     reranker_tool: RerankerTool = None,
                                     llm_client: LLMClient = None) -> dict:
    """
    快速初始研究节点 - 简化版本
    执行快速的研究，收集关于主题的概览信息
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("主题不能为空")

    logger.info(f"🔍 开始快速初始研究: {topic}")

    # 生成简化的初始搜索查询 - 只使用2个查询
    initial_queries = [f"{topic} 概述", f"{topic} 主要内容"]

    all_results = []

    # 获取embedding配置
    embedding_config = settings.supported_models.get("gte_qwen")
    embedding_client = None
    if embedding_config:
        try:
            embedding_client = EmbeddingClient(
                base_url=embedding_config.url,
                api_key=embedding_config.api_key)
            logger.info("✅ Embedding客户端初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  Embedding客户端初始化失败: {str(e)}")
            embedding_client = None

    # 执行搜索
    for i, query in enumerate(initial_queries, 1):
        logger.info(f"执行快速初始搜索 {i}/{len(initial_queries)}: {query}")

        # 网络搜索
        web_results = ""
        try:
            # 使用异步搜索方法
            web_results = await web_search_tool.search_async(query)
            if "模拟" in web_results or "mock" in web_results.lower():
                web_results = ""
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_results = ""

        # ES搜索 - 使用简化的搜索
        es_results = ""
        try:
            if embedding_client:
                # 尝试向量检索
                try:
                    embedding_response = embedding_client.invoke(query)
                    embedding_data = json.loads(embedding_response)

                    # 解析向量
                    if isinstance(embedding_data, list):
                        query_vector = embedding_data[0] if len(
                            embedding_data) > 0 and isinstance(
                                embedding_data[0], list) else embedding_data
                    elif isinstance(embedding_data,
                                    dict) and 'data' in embedding_data:
                        query_vector = embedding_data['data']
                    else:
                        query_vector = None

                    if query_vector:
                        # 使用向量检索
                        es_results = await search_and_rerank(
                            query, es_search_tool, reranker_tool, query_vector)
                        logger.info(f"✅ 向量检索+重排序执行成功，结果长度: {len(es_results)}")
                    else:
                        # 回退到文本搜索
                        es_results = es_search_tool.search(query)
                        logger.info(f"✅ 文本搜索执行成功，结果长度: {len(es_results)}")

                except Exception as e:
                    logger.warning(f"⚠️  向量检索失败，使用文本搜索: {str(e)}")
                    es_results = es_search_tool.search(query)
            else:
                # 直接使用文本搜索
                es_results = es_search_tool.search(query)

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            es_results = ""

        # 合并结果
        combined_results = f"=== 查询: {query} ===\n"
        if web_results:
            combined_results += f"网络搜索结果:\n{web_results}\n\n"
        if es_results:
            combined_results += f"知识库搜索结果:\n{es_results}\n\n"

        all_results.append(combined_results)

    # 合并所有结果
    raw_initial_gathered_data = "\n".join(all_results)
    logger.info(f"✅ 快速初始研究完成，收集到 {len(raw_initial_gathered_data)} 字符的原始数据")

    # 简化数据处理 - 如果数据量过大，进行简单截断
    if len(raw_initial_gathered_data) > 5000:  # 降低阈值
        logger.info("📊 数据量较大，进行简单截断...")
        truncated_data = raw_initial_gathered_data[:5000] + "\n\n... (内容已截断)"
        return {"initial_gathered_data": truncated_data}

    return {"initial_gathered_data": raw_initial_gathered_data}


def fast_outline_generation_node(state: ResearchState,
                                 llm_client: LLMClient) -> dict:
    """
    快速大纲生成节点 - 简化版本
    
    基于初始研究数据生成简化的文档大纲
    """
    topic = state.get("topic", "")
    initial_gathered_data = state.get("initial_gathered_data", "")

    if not topic:
        raise ValueError("主题不能为空")

    if not initial_gathered_data:
        raise ValueError("初始研究数据不能为空")

    logger.info(f"📋 开始生成快速文档大纲: {topic}")

    # 获取配置
    outline_config = settings.get_agent_component_config("task_planner")
    if not outline_config:
        temperature = 0.3
        max_tokens = 1000  # 减少token数量
        extra_params = {}
    else:
        temperature = outline_config.temperature * 0.7
        max_tokens = min(outline_config.max_tokens, 1000)  # 限制最大token
        extra_params = outline_config.extra_params

    # 构建提示词
    prompt = FAST_OUTLINE_GENERATION_PROMPT.format(
        topic=topic,
        initial_gathered_data=initial_gathered_data[:4000]  # 减少输入长度
    )

    logger.debug(
        f"Invoking LLM with fast outline generation prompt:\n{pprint.pformat(prompt)}"
    )

    try:
        # 调用LLM生成大纲
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        # 解析JSON响应
        try:
            # 清理响应，移除可能的markdown代码块标记
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            document_outline = json.loads(cleaned_response.strip())

            # 验证大纲结构
            if "chapters" not in document_outline:
                raise ValueError("大纲缺少chapters字段")

            logger.info(
                f"✅ 成功生成快速大纲，包含 {len(document_outline['chapters'])} 个章节")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {str(e)}")
            # 返回默认大纲
            document_outline = {
                "title":
                topic,
                "summary":
                f"关于{topic}的简化文档",
                "chapters": [{
                    "chapter_number": 1,
                    "chapter_title": "概述与背景",
                    "description": f"介绍{topic}的基本概念和重要性",
                    "key_points": ["基本定义", "重要性"],
                    "estimated_sections": 2
                }, {
                    "chapter_number": 2,
                    "chapter_title": "核心内容分析",
                    "description": f"分析{topic}的核心要素",
                    "key_points": ["主要特征", "关键要素"],
                    "estimated_sections": 2
                }],
                "total_chapters":
                2,
                "estimated_total_words":
                5000
            }

        return {"document_outline": document_outline}

    except Exception as e:
        logger.error(f"❌ 快速大纲生成失败: {str(e)}")
        # 返回基础大纲
        return {
            "document_outline": {
                "title":
                topic,
                "summary":
                f"关于{topic}的文档",
                "chapters": [{
                    "chapter_number": 1,
                    "chapter_title": "引言",
                    "description": f"介绍{topic}的基本信息",
                    "key_points": ["概述"],
                    "estimated_sections": 2
                }],
                "total_chapters":
                1,
                "estimated_total_words":
                3000
            }
        }


def fast_planner_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    快速规划节点 - 简化版本
    从状态中获取 topic 和当前章节信息，创建简化的研究计划
    """
    topic = state.get("topic", "")
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])

    if not topic:
        raise ValueError("Topic is required in state")

    # 获取当前章节信息
    current_chapter = None
    if current_chapter_index < len(chapters_to_process):
        current_chapter = chapters_to_process[current_chapter_index]

    chapter_title = current_chapter.get("chapter_title",
                                        "") if current_chapter else ""
    chapter_description = current_chapter.get("description",
                                              "") if current_chapter else ""

    logger.info(f"📋 快速规划章节研究: {chapter_title}")

    # 获取任务规划器配置
    task_planner_config = settings.get_agent_component_config("task_planner")
    if not task_planner_config:
        raise ValueError("Task planner configuration not found")

    # 创建简化的研究计划生成的 prompt
    prompt = FAST_PLANNER_PROMPT.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description)

    logger.debug(
        f"Invoking LLM with fast planner prompt:\n{pprint.pformat(prompt)}")

    try:
        # 调用 LLM 生成研究计划
        response = llm_client.invoke(
            prompt,
            temperature=task_planner_config.temperature,
            max_tokens=min(task_planner_config.max_tokens, 800),  # 减少token
            **task_planner_config.extra_params)

        logger.debug(f"🔍 LLM原始响应: {repr(response)}")

        # 解析 JSON 响应
        research_plan, search_queries = parse_planner_response(response)

        logger.info(f"✅ 生成快速研究计划: {len(search_queries)} 个搜索查询")
        for i, query in enumerate(search_queries, 1):
            logger.debug(f"  {i}. {query}")

        return {
            "research_plan": research_plan,
            "search_queries": search_queries
        }

    except Exception as e:
        # 如果 LLM 调用失败，返回默认计划
        logger.error(f"Fast planner node error: {str(e)}")
        default_queries = [
            f"{topic} {chapter_title} 概述", f"{topic} {chapter_title} 主要内容"
        ]
        logger.warning(f"⚠️  使用默认快速搜索查询: {len(default_queries)} 个")

        return {
            "research_plan": f"快速研究计划：对章节 {chapter_title} 进行简要研究，收集关键信息。",
            "search_queries": default_queries
        }


async def fast_researcher_node(state: ResearchState,
                               web_search_tool: WebSearchTool,
                               es_search_tool: ESSearchTool,
                               reranker_tool: RerankerTool = None) -> dict:
    """
    快速研究节点 - 简化版本
    从状态中获取 search_queries，使用搜索工具收集相关信息
    """
    search_queries = state.get("search_queries", [])

    if not search_queries:
        logger.warning("❌ 没有搜索查询，返回默认消息")
        return {"gathered_data": "没有搜索查询需要执行"}

    all_results = []

    # 获取embedding配置
    embedding_config = settings.supported_models.get("gte_qwen")
    embedding_client = None
    if embedding_config:
        try:
            embedding_client = EmbeddingClient(
                base_url=embedding_config.url,
                api_key=embedding_config.api_key)
            logger.info("✅ Embedding客户端初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  Embedding客户端初始化失败: {str(e)}")
            embedding_client = None

    # 执行搜索 - 只处理前2个查询
    limited_queries = search_queries[:2]  # 限制查询数量
    for i, query in enumerate(limited_queries, 1):
        logger.info(f"执行快速搜索查询 {i}/{len(limited_queries)}: {query}")

        # 网络搜索
        web_results = ""
        try:
            # 使用异步搜索方法
            web_results = await web_search_tool.search_async(query)
            if "模拟" in web_results or "mock" in web_results.lower():
                web_results = ""
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_results = ""

        # ES搜索 - 使用简化的搜索
        es_results = ""
        try:
            if embedding_client:
                # 尝试向量检索
                try:
                    embedding_response = embedding_client.invoke(query)
                    embedding_data = json.loads(embedding_response)

                    # 解析向量
                    if isinstance(embedding_data, list):
                        query_vector = embedding_data[0] if len(
                            embedding_data) > 0 and isinstance(
                                embedding_data[0], list) else embedding_data
                    elif isinstance(embedding_data,
                                    dict) and 'data' in embedding_data:
                        query_vector = embedding_data['data']
                    else:
                        query_vector = None

                    if query_vector:
                        # 使用向量检索
                        es_results = await search_and_rerank(
                            query, es_search_tool, reranker_tool, query_vector)
                        logger.info(f"✅ 向量检索+重排序执行成功，结果长度: {len(es_results)}")
                    else:
                        # 回退到文本搜索
                        es_results = es_search_tool.search(query)
                        logger.info(f"✅ 文本搜索执行成功，结果长度: {len(es_results)}")

                except Exception as e:
                    logger.warning(f"⚠️  向量检索失败，使用文本搜索: {str(e)}")
                    es_results = es_search_tool.search(query)
            else:
                # 直接使用文本搜索
                es_results = es_search_tool.search(query)

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            es_results = ""

        # 合并结果
        combined_results = f"=== 查询: {query} ===\n"
        if web_results:
            combined_results += f"网络搜索结果:\n{web_results}\n\n"
        if es_results:
            combined_results += f"知识库搜索结果:\n{es_results}\n\n"

        all_results.append(combined_results)

    # 合并所有结果
    gathered_data = "\n".join(all_results)
    logger.info(f"✅ 收集到 {len(limited_queries)} 条快速搜索结果")
    logger.info(f"📊 总数据长度: {len(gathered_data)} 字符")

    return {"gathered_data": gathered_data}


def fast_writer_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    快速章节写作节点 - 简化版本
    基于当前章节的研究数据，生成简洁的章节内容
    """
    # 获取基本信息
    topic = state.get("topic", "")
    current_chapter_index = state.get("current_chapter_index", 0)
    chapters_to_process = state.get("chapters_to_process", [])
    completed_chapters_content = state.get("completed_chapters_content", [])

    # 验证当前章节索引
    if current_chapter_index >= len(chapters_to_process):
        raise ValueError(f"章节索引 {current_chapter_index} 超出范围")

    # 获取当前章节信息
    current_chapter = chapters_to_process[current_chapter_index]
    chapter_title = current_chapter.get("chapter_title", "")
    chapter_description = current_chapter.get("description", "")

    # 从状态中获取研究数据
    gathered_data = state.get("gathered_data", "")

    if not chapter_title:
        raise ValueError("章节标题不能为空")

    if not gathered_data:
        return {
            "final_document": f"## {chapter_title}\n\n由于没有收集到相关数据，无法生成章节内容。"
        }

    # 获取文档生成器配置
    document_writer_config = settings.get_agent_component_config(
        "document_writer")
    if not document_writer_config:
        temperature = 0.7
        max_tokens = 2000  # 减少token数量
        extra_params = {}
    else:
        temperature = document_writer_config.temperature
        max_tokens = min(document_writer_config.max_tokens, 2000)  # 限制最大token
        extra_params = document_writer_config.extra_params

    # 构建已完成章节的上下文摘要 - 简化版本
    previous_chapters_context = ""
    if completed_chapters_content:
        previous_chapters_context = "\n\n".join([
            f"第{i+1}章摘要:\n{content[:200]}..."  # 减少摘要长度
            for i, content in enumerate(completed_chapters_content)
        ])

    # 导入快速提示词模板
    from ..fast_prompts import FAST_WRITER_PROMPT

    # 构建简化的提示词
    prompt = FAST_WRITER_PROMPT.format(
        topic=topic,
        chapter_title=chapter_title,
        chapter_description=chapter_description,
        chapter_number=current_chapter_index + 1,
        total_chapters=len(chapters_to_process),
        previous_chapters_context=previous_chapters_context
        if previous_chapters_context else "这是第一章，没有前置内容。",
        gathered_data=gathered_data[:8000]  # 限制输入长度
    )

    logger.debug(
        f"Invoking LLM with fast writer prompt:\n{pprint.pformat(prompt)}")

    try:
        # 调用LLM生成章节内容
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        # 确保响应格式正确
        if not response.strip():
            response = f"## {chapter_title}\n\n无法生成章节内容。"
        elif not response.startswith("##"):
            # 如果没有二级标题，添加章节标题
            response = f"## {chapter_title}\n\n{response}"

        # 返回当前章节的内容
        return {"final_document": response}

    except Exception as e:
        # 如果LLM调用失败，返回错误信息
        logger.error(f"Fast writer node error: {str(e)}")
        error_content = f"""## {chapter_title}

### 章节生成错误

由于技术原因，无法生成本章节的内容。

**错误信息:** {str(e)}

**章节描述:** {chapter_description}

请检查系统配置或稍后重试。
"""
        return {"final_document": error_content}


def fast_supervisor_router(state: ResearchState, llm_client: LLMClient) -> str:
    """
    快速监督器路由 - 简化版本
    评估收集的研究数据是否足够撰写文档，降低要求
    """
    logger.info("🚀 ====== 进入快速 supervisor_router 路由节点 ======")

    # 从状态中提取 topic 和 gathered_data
    topic = state.get("topic", "")
    gathered_data = state.get("gathered_data", "")

    if not topic:
        logger.warning("❌ 没有主题，返回 rerun_researcher")
        return "rerun_researcher"

    if not gathered_data:
        logger.warning("❌ 没有收集到数据，返回 rerun_researcher")
        return "rerun_researcher"

    # 预分析步骤：计算元数据
    num_sources = gathered_data.count("===")
    total_length = len(gathered_data)

    logger.info(f"📋 Topic: {topic}")
    logger.info(f"📊 Gathered data 长度: {total_length} 字符")
    logger.info(f"🔍 来源数量: {num_sources}")

    # 导入快速提示词模板
    from ..fast_prompts import FAST_SUPERVISOR_PROMPT

    # 构建简化的评估提示词
    prompt = FAST_SUPERVISOR_PROMPT.format(topic=topic,
                                           num_sources=num_sources,
                                           total_length=total_length)

    logger.debug(
        f"Invoking LLM with fast supervisor prompt:\n{pprint.pformat(prompt)}")

    try:
        # 调用 LLM 客户端
        max_tokens = 10

        logger.info("🤖 调用 LLM 进行快速决策判断...")
        logger.debug(f"📝 Prompt 长度: {len(prompt)} 字符")

        # 添加重试机制
        max_retries = 2  # 减少重试次数
        for attempt in range(max_retries):
            try:
                response = llm_client.invoke(prompt,
                                             temperature=0,
                                             max_tokens=max_tokens)
                break
            except Exception as e:
                if "400" in str(e) and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️  第 {attempt + 1} 次尝试失败 (400错误)，正在重试...")
                    import time
                    time.sleep(1)  # 减少等待时间
                    continue
                else:
                    raise e

        # 解析响应
        decision = response.strip().upper()
        clean_response = response

        # 如果响应被截断或包含推理过程，尝试提取决策关键词
        if "FINISH" not in decision and "CONTINUE" not in decision:
            import re
            clean_response = re.sub(r'<think>.*',
                                    '',
                                    response,
                                    flags=re.IGNORECASE)
            clean_response = re.sub(r'<THINK>.*',
                                    '',
                                    clean_response,
                                    flags=re.IGNORECASE)
            decision = clean_response.strip().upper()

        logger.debug(f"🔍 LLM原始响应: '{response}'")
        logger.debug(f"🔍 处理后决策: '{decision}'")

        # 根据响应决定路由
        if "FINISH" in decision:
            logger.info("✅ 决策: FINISH -> continue_to_writer")
            return "continue_to_writer"
        else:
            logger.info("✅ 决策: CONTINUE/其他 -> rerun_researcher")
            return "rerun_researcher"

    except Exception as e:
        # 如果 LLM 调用失败，默认继续研究以确保安全
        logger.error(f"❌ Fast supervisor router error: {str(e)}")
        return "rerun_researcher"


def parse_planner_response(response: str) -> tuple:
    """
    解析规划器响应 - 简化版本
    """
    try:
        # 清理响应
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        # 解析JSON
        data = json.loads(cleaned_response.strip())

        research_plan = data.get("research_plan", "")
        search_queries = data.get("search_queries", [])

        # 确保search_queries是列表
        if isinstance(search_queries, str):
            search_queries = [search_queries]

        return research_plan, search_queries

    except Exception as e:
        logger.error(f"解析规划器响应失败: {str(e)}")
        logger.debug(f"原始响应: {repr(response)}")

        # 返回默认值
        return "快速研究计划", ["概述", "主要内容"]
