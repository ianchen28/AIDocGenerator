# service/src/doc_agent/graph/main_orchestrator/nodes.py
from loguru import logger
import pprint
from typing import Dict, List
import json
from ..state import ResearchState
from ...llm_clients.base import LLMClient
from ...tools.web_search import WebSearchTool
from ...tools.es_search import ESSearchTool
from ...tools.reranker import RerankerTool
from ...llm_clients.providers import EmbeddingClient, RerankerClient

# 添加配置导入
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
from src.doc_agent.utils.search_utils import search_and_rerank


async def initial_research_node(state: ResearchState,
                                web_search_tool: WebSearchTool,
                                es_search_tool: ESSearchTool,
                                reranker_tool: RerankerTool = None,
                                llm_client: LLMClient = None) -> dict:
    """
    初始研究节点
    
    执行高层次的研究，收集关于主题的概览信息，并进行数据压缩
    
    Args:
        state: 研究状态，包含 topic
        web_search_tool: 网络搜索工具
        es_search_tool: Elasticsearch搜索工具
        reranker_tool: 重排序工具（可选）
        llm_client: LLM客户端（用于数据处理）
        
    Returns:
        dict: 包含 initial_gathered_data 的字典
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("主题不能为空")

    logger.info(f"🔍 开始初始研究: {topic}")

    # 生成初始搜索查询 - 更通用和广泛的查询
    initial_queries = [
        f"{topic} 概述", f"{topic} 主要内容", f"{topic} 关键要点", f"{topic} 最新发展",
        f"{topic} 重要性"
    ]

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
        logger.info(f"执行初始搜索 {i}/{len(initial_queries)}: {query}")

        # 网络搜索
        web_results = ""
        try:
            web_results = web_search_tool.search(query)
            if "模拟" in web_results or "mock" in web_results.lower():
                web_results = ""
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_results = ""

        # ES搜索 - 使用新的搜索和重排序功能
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

                    if query_vector and len(query_vector) == 1536:
                        # 使用新的搜索和重排序功能
                        _, reranked_results, formatted_es_results = await search_and_rerank(
                            es_search_tool=es_search_tool,
                            query=query,
                            query_vector=query_vector,
                            reranker_tool=reranker_tool,
                            initial_top_k=8,  # 初始研究获取更多结果
                            final_top_k=5  # 重排序后返回top5
                        )
                        es_results = formatted_es_results
                        logger.info(
                            f"✅ 向量检索+重排序执行成功，结果长度: {len(formatted_es_results)}"
                        )
                    else:
                        # 回退到文本搜索
                        _, reranked_results, formatted_es_results = await search_and_rerank(
                            es_search_tool=es_search_tool,
                            query=query,
                            query_vector=None,
                            reranker_tool=reranker_tool,
                            initial_top_k=8,
                            final_top_k=5)
                        es_results = formatted_es_results
                        logger.info(
                            f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}"
                        )
                except Exception as e:
                    logger.error(f"向量检索失败: {str(e)}")
                    # 回退到文本搜索
                    _, reranked_results, formatted_es_results = await search_and_rerank(
                        es_search_tool=es_search_tool,
                        query=query,
                        query_vector=None,
                        reranker_tool=reranker_tool,
                        initial_top_k=8,
                        final_top_k=5)
                    es_results = formatted_es_results
                    logger.info(
                        f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}")
            else:
                # 没有embedding客户端，直接使用文本搜索
                _, reranked_results, formatted_es_results = await search_and_rerank(
                    es_search_tool=es_search_tool,
                    query=query,
                    query_vector=None,
                    reranker_tool=reranker_tool,
                    initial_top_k=8,
                    final_top_k=5)
                es_results = formatted_es_results
                logger.info(
                    f"✅ 文本搜索+重排序执行成功，结果长度: {len(formatted_es_results)}")

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            es_results = f"ES搜索失败: {str(e)}"

        # 聚合结果
        query_results = f"=== 初始搜索 {i}: {query} ===\n\n"
        if web_results:
            query_results += f"网络搜索结果:\n{web_results}\n\n"
        if es_results:
            query_results += f"知识库搜索结果:\n{es_results}\n\n"
        if not web_results and not es_results:
            query_results += "未找到相关搜索结果\n\n"

        all_results.append(query_results)

    # 合并所有结果
    raw_initial_gathered_data = "\n\n".join(all_results)
    logger.info(f"✅ 初始研究完成，收集到 {len(raw_initial_gathered_data)} 字符的原始数据")

    # 如果数据量过大，进行压缩处理
    if len(raw_initial_gathered_data) > 10000:  # 超过10K字符时压缩
        logger.info("📊 数据量较大，进行压缩处理...")

        if llm_client:
            try:
                # 导入内容处理工具
                from ...utils.content_processor import process_research_data

                # 处理研究数据
                processed_data = process_research_data(
                    raw_initial_gathered_data,
                    llm_client,
                    summary_length=4000,  # 摘要长度
                    key_points_count=10  # 关键要点数量
                )

                # 构建压缩后的数据
                compressed_data = f"""
# 研究数据摘要

## 关键要点
{chr(10).join([f"{i+1}. {point}" for i, point in enumerate(processed_data['key_points'])])}

## 详细摘要
{processed_data['summary']}

---
*原始数据长度: {processed_data['original_length']} 字符*
*压缩后长度: {processed_data['processed_length']} 字符*
*压缩率: {((processed_data['original_length'] - processed_data['processed_length']) / processed_data['original_length'] * 100):.1f}%*
"""

                logger.info(f"✅ 数据压缩完成: {len(compressed_data)} 字符")
                return {"initial_gathered_data": compressed_data}

            except Exception as e:
                logger.warning(f"⚠️  数据压缩失败: {str(e)}，使用简单截断")
                # 后备方案：简单截断
                truncated_data = raw_initial_gathered_data[:8000] + "\n\n... (内容已截断)"
                return {"initial_gathered_data": truncated_data}
        else:
            logger.warning("⚠️  未提供LLM客户端，使用简单截断")
            truncated_data = raw_initial_gathered_data[:8000] + "\n\n... (内容已截断)"
            return {"initial_gathered_data": truncated_data}
    else:
        # 数据量不大，直接返回
        return {"initial_gathered_data": raw_initial_gathered_data}


def outline_generation_node(state: ResearchState,
                            llm_client: LLMClient) -> dict:
    """
    大纲生成节点
    
    基于初始研究数据生成文档的结构化大纲
    
    Args:
        state: 研究状态，包含 topic 和 initial_gathered_data
        llm_client: LLM客户端实例
        
    Returns:
        dict: 包含 document_outline 的字典
    """
    topic = state.get("topic", "")
    initial_gathered_data = state.get("initial_gathered_data", "")

    if not topic:
        raise ValueError("主题不能为空")

    if not initial_gathered_data:
        raise ValueError("初始研究数据不能为空")

    logger.info(f"📋 开始生成文档大纲: {topic}")

    # 获取配置
    outline_config = settings.get_agent_component_config("task_planner")
    if not outline_config:
        temperature = 0.3  # 大纲生成需要更低的温度以确保结构性
        max_tokens = 2000
        extra_params = {}
    else:
        temperature = outline_config.temperature * 0.7  # 降低温度
        max_tokens = outline_config.max_tokens
        extra_params = outline_config.extra_params

    # 导入提示词模板
    from ...prompts import OUTLINE_GENERATION_PROMPT

    # 构建提示词
    prompt = OUTLINE_GENERATION_PROMPT.format(
        topic=topic,
        initial_gathered_data=initial_gathered_data[:8000]  # 限制输入长度
    )

    logger.debug(
        f"Invoking LLM with outline generation prompt:\n{pprint.pformat(prompt)}"
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

            logger.info(f"✅ 成功生成大纲，包含 {len(document_outline['chapters'])} 个章节")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {str(e)}")
            # 返回默认大纲
            document_outline = {
                "title":
                topic,
                "summary":
                f"关于{topic}的综合性文档",
                "chapters": [{
                    "chapter_number": 1,
                    "chapter_title": "概述与背景",
                    "description": f"介绍{topic}的基本概念、历史背景和重要性",
                    "key_points": ["基本定义", "历史发展", "现实意义"],
                    "estimated_sections": 3
                }, {
                    "chapter_number": 2,
                    "chapter_title": "核心内容分析",
                    "description": f"深入分析{topic}的核心要素和关键特征",
                    "key_points": ["主要特征", "关键要素", "技术细节"],
                    "estimated_sections": 4
                }, {
                    "chapter_number": 3,
                    "chapter_title": "应用与实践",
                    "description": f"探讨{topic}的实际应用场景和最佳实践",
                    "key_points": ["应用场景", "案例分析", "实施方法"],
                    "estimated_sections": 3
                }, {
                    "chapter_number": 4,
                    "chapter_title": "未来展望",
                    "description": f"分析{topic}的发展趋势和未来可能性",
                    "key_points": ["发展趋势", "挑战机遇", "前景预测"],
                    "estimated_sections": 2
                }],
                "total_chapters":
                4,
                "estimated_total_words":
                12000
            }

        return {"document_outline": document_outline}

    except Exception as e:
        logger.error(f"❌ 大纲生成失败: {str(e)}")
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


def split_chapters_node(state: ResearchState) -> dict:
    """
    章节拆分节点
    
    将文档大纲拆分为独立的章节任务列表
    
    Args:
        state: 研究状态，包含 document_outline
        
    Returns:
        dict: 包含 chapters_to_process 和 current_chapter_index 的字典
    """
    document_outline = state.get("document_outline", {})

    if not document_outline or "chapters" not in document_outline:
        raise ValueError("文档大纲不存在或格式无效")

    logger.info(f"📂 开始拆分章节任务")

    # 从大纲中提取章节信息
    chapters = document_outline.get("chapters", [])

    # 创建章节任务列表
    chapters_to_process = []
    for chapter in chapters:
        chapter_task = {
            "chapter_number":
            chapter.get("chapter_number",
                        len(chapters_to_process) + 1),
            "chapter_title":
            chapter.get("chapter_title", f"第{len(chapters_to_process) + 1}章"),
            "description":
            chapter.get("description", ""),
            "key_points":
            chapter.get("key_points", []),
            "estimated_sections":
            chapter.get("estimated_sections", 3),
            "research_data":
            ""  # 将在章节工作流中填充
        }
        chapters_to_process.append(chapter_task)

    logger.info(f"✅ 成功创建 {len(chapters_to_process)} 个章节任务")

    # 打印章节列表
    for i, chapter in enumerate(chapters_to_process):
        logger.info(
            f"  📄 第{chapter['chapter_number']}章: {chapter['chapter_title']}")

    return {
        "chapters_to_process": chapters_to_process,
        "current_chapter_index": 0,
        "completed_chapters_content": []  # 初始化已完成章节列表
    }
