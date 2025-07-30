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
from ...common.prompt_selector import PromptSelector
from ...schemas import Source

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
    
    基于主题进行初始研究，收集相关信息源
    
    Args:
        state: 研究状态，包含 topic
        web_search_tool: 网络搜索工具
        es_search_tool: ES搜索工具
        reranker_tool: 重排序工具
        llm_client: LLM客户端（可选）
        
    Returns:
        dict: 包含 initial_sources 的字典，包含 Source 对象列表
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("主题不能为空")

    logger.info(f"🔍 开始初始研究: {topic}")

    # 从配置中读取搜索轮数
    from service.core.config import settings

    # 生成初始搜索查询 - 更通用和广泛的查询
    # 根据配置决定查询数量
    search_config = getattr(settings, 'search_config', None)
    if search_config and hasattr(search_config, 'max_search_rounds'):
        max_search_rounds = search_config.max_search_rounds
    else:
        max_search_rounds = 5  # 默认5轮

    # 定义所有可能的查询
    all_possible_queries = [
        f"{topic} 概述",
        f"{topic} 主要内容",
        f"{topic} 关键要点",
        f"{topic} 最新发展",
        f"{topic} 重要性",
    ]

    # 根据配置选择查询数量
    initial_queries = all_possible_queries[:max_search_rounds]

    logger.info(
        f"📊 配置搜索轮数: {max_search_rounds}，实际执行: {len(initial_queries)} 轮")

    all_sources = []  # 存储所有 Source 对象
    source_id_counter = 1  # 源ID计数器

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
            # 使用异步搜索方法
            web_results = await web_search_tool.search_async(query)
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

        # 处理网络搜索结果
        if web_results and web_results.strip():
            try:
                # 解析网络搜索结果，创建 Source 对象
                web_sources = _parse_web_search_results(
                    web_results, query, source_id_counter)
                all_sources.extend(web_sources)
                source_id_counter += len(web_sources)
                logger.info(f"✅ 从网络搜索中提取到 {len(web_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析网络搜索结果失败: {str(e)}")

        # 处理ES搜索结果
        if es_results and es_results.strip():
            try:
                # 解析ES搜索结果，创建 Source 对象
                es_sources = _parse_es_search_results(es_results, query,
                                                      source_id_counter)
                all_sources.extend(es_sources)
                source_id_counter += len(es_sources)
                logger.info(f"✅ 从ES搜索中提取到 {len(es_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析ES搜索结果失败: {str(e)}")

    # 返回结构化的源列表
    logger.info(f"✅ 初始研究完成，总共收集到 {len(all_sources)} 个信息源")
    for i, source in enumerate(all_sources[:5], 1):  # 只显示前5个源作为预览
        logger.debug(
            f"  {i}. [{source.id}] {source.title} ({source.source_type})")

    return {"initial_sources": all_sources}


def outline_generation_node(state: ResearchState,
                            llm_client: LLMClient,
                            prompt_selector: PromptSelector,
                            genre: str = "default") -> dict:
    """
    大纲生成节点
    
    基于初始研究数据生成文档的结构化大纲
    
    Args:
        state: 研究状态，包含 topic 和 initial_gathered_data
        llm_client: LLM客户端实例
        prompt_selector: PromptSelector实例，用于获取prompt模板
        genre: genre类型，默认为"default"
        
    Returns:
        dict: 包含 document_outline 的字典
    """
    topic = state.get("topic", "")
    initial_sources = state.get("initial_sources", [])
    initial_gathered_data = state.get("initial_gathered_data", "")  # 保持向后兼容

    if not topic:
        raise ValueError("主题不能为空")

    # 如果没有收集到源数据，尝试使用旧的 initial_gathered_data
    if not initial_sources and not initial_gathered_data:
        raise ValueError("初始研究数据不能为空")

    # 如果有 initial_sources，将其转换为文本格式
    if initial_sources:
        initial_gathered_data = _format_sources_to_text(initial_sources)
    elif not initial_gathered_data:
        initial_gathered_data = "没有收集到相关数据"

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

    # 获取需求文档内容
    requirements_content = state.get("requirements_content")

    # 获取文档配置以确定章节数
    doc_config = settings.get_document_config(fast_mode=True)
    target_chapter_count = doc_config.get('chapter_count', 5)
    logger.info(f"📋 目标章节数: {target_chapter_count}")

    # 使用 PromptSelector 获取 prompt 模板
    try:
        # 如果有需求文档，需要手动指定使用 v2_with_requirements 版本
        if requirements_content and requirements_content.strip():
            # 直接导入模块并获取特定版本
            import importlib
            module = importlib.import_module(
                "src.doc_agent.prompts.outline_generation")
            if hasattr(module,
                       'PROMPTS') and "v2_with_requirements" in module.PROMPTS:
                prompt_template = module.PROMPTS["v2_with_requirements"]
                logger.info(f"✅ 使用 v2_with_requirements 版本，检测到需求文档")
            else:
                # 回退到默认版本
                prompt_template = prompt_selector.get_prompt(
                    "prompts", "outline_generation", genre)
                logger.warning(f"⚠️  v2_with_requirements 版本不存在，使用默认版本")
        else:
            prompt_template = prompt_selector.get_prompt(
                "prompts", "outline_generation", genre)
            logger.info(f"✅ 使用默认版本，未检测到需求文档")

        logger.debug(f"✅ 成功获取 outline_generation prompt 模板，genre: {genre}")
    except Exception as e:
        logger.error(f"❌ 获取 outline_generation prompt 模板失败: {e}")
        # 使用默认的 prompt 模板作为备用
        prompt_template = """
你是一个专业的文档结构规划专家。请基于提供的研究数据，为指定主题生成一个结构化的文档大纲。

**文档主题:** {topic}

**研究数据摘要:**
{initial_gathered_data}

**任务要求:**
1. 分析研究数据，识别主要主题和关键信息
2. 设计一个逻辑清晰、结构合理的文档大纲
3. 确保大纲涵盖主题的各个方面
4. 每个章节应该有明确的标题和描述
5. 考虑章节之间的逻辑关系和层次结构

**输出格式:**
请以JSON格式返回结果，包含以下字段：
- title: 文档标题
- summary: 文档摘要
- chapters: 章节列表，每个章节包含：
  - chapter_number: 章节编号
  - chapter_title: 章节标题
  - description: 章节描述
  - key_points: 关键要点列表
  - estimated_sections: 预估小节数量

请立即开始生成文档大纲。
"""

    # 构建提示词
    if requirements_content and requirements_content.strip():
        # 格式化需求文档内容
        formatted_requirements = f"""
**用户需求文档:**
{requirements_content}

"""
        prompt = prompt_template.format(
            topic=topic,
            initial_gathered_data=initial_gathered_data[:8000],  # 限制输入长度
            requirements_content=formatted_requirements,
            target_chapter_count=target_chapter_count)
        logger.info(f"📋 包含需求文档的大纲生成，需求长度: {len(requirements_content)} 字符")
    else:
        # 不包含需求文档的版本
        prompt = prompt_template.format(
            topic=topic,
            initial_gathered_data=initial_gathered_data[:8000],  # 限制输入长度
            target_chapter_count=target_chapter_count)
        logger.info(f"📋 标准大纲生成，未包含需求文档")

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
            # 添加调试信息
            logger.debug(f"🔍 LLM原始响应:\n{response}")

            # 清理响应，移除可能的markdown代码块标记
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            logger.debug(f"🔍 清理后的响应:\n{cleaned_response}")

            document_outline = json.loads(cleaned_response.strip())

            # 验证大纲结构
            if "chapters" not in document_outline:
                raise ValueError("大纲缺少chapters字段")

            logger.info(f"✅ 成功生成大纲，包含 {len(document_outline['chapters'])} 个章节")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {str(e)}")
            logger.error(f"🔍 尝试解析的响应: {cleaned_response}")
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


def _parse_web_search_results(web_results: str, query: str,
                              start_id: int) -> list[Source]:
    """
    解析网络搜索结果，创建 Source 对象列表
    
    Args:
        web_results: 网络搜索的原始结果字符串
        query: 搜索查询
        start_id: 起始ID
        
    Returns:
        list[Source]: Source 对象列表
    """
    sources = []
    current_id = start_id

    try:
        # 简单的解析逻辑：按行分割，提取标题和URL
        lines = web_results.split('\n')
        current_title = ""
        current_url = ""
        current_content = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试提取标题和URL
            if line.startswith('http') or line.startswith('https'):
                # 这是一个URL
                if current_title and current_content:
                    # 创建前一个源
                    source = Source(
                        id=current_id,
                        source_type="webpage",
                        title=current_title,
                        url=current_url,
                        content=current_content[:500] + "..."
                        if len(current_content) > 500 else current_content)
                    sources.append(source)
                    current_id += 1

                current_url = line
                current_title = ""
                current_content = ""
            elif line.startswith('标题:') or line.startswith('Title:'):
                current_title = line.split(':', 1)[1].strip()
            elif line.startswith('内容:') or line.startswith('Content:'):
                current_content = line.split(':', 1)[1].strip()
            elif not current_title and len(
                    line) > 10 and not line.startswith('==='):
                # 可能是标题
                current_title = line
            elif current_title and len(line) > 20:
                # 可能是内容
                current_content += " " + line

        # 处理最后一个源
        if current_title and current_content:
            source = Source(
                id=current_id,
                source_type="webpage",
                title=current_title,
                url=current_url,
                content=current_content[:500] +
                "..." if len(current_content) > 500 else current_content)
            sources.append(source)

        # 如果没有解析到任何源，创建一个默认源
        if not sources:
            source = Source(id=current_id,
                            source_type="webpage",
                            title=f"网络搜索结果 - {query}",
                            url="",
                            content=web_results[:500] +
                            "..." if len(web_results) > 500 else web_results)
            sources.append(source)

    except Exception as e:
        logger.error(f"解析网络搜索结果失败: {str(e)}")
        # 创建默认源
        source = Source(id=start_id,
                        source_type="webpage",
                        title=f"网络搜索结果 - {query}",
                        url="",
                        content=web_results[:500] +
                        "..." if len(web_results) > 500 else web_results)
        sources.append(source)

    return sources


def bibliography_node(state: ResearchState) -> dict:
    """
    参考文献生成节点
    
    在文档生成完成后，基于全局引用的信息源生成参考文献部分
    
    Args:
        state: 研究状态，包含 final_document 和 cited_sources
        
    Returns:
        dict: 包含更新后的 final_document 的字典
    """
    final_document = state.get("final_document", "")
    cited_sources = state.get("cited_sources", {})

    if not final_document:
        logger.warning("❌ 没有找到最终文档内容")
        return {"final_document": "文档生成失败，无法添加参考文献。"}

    if not cited_sources:
        logger.info("📚 没有引用的信息源，跳过参考文献生成")
        return {"final_document": final_document}

    logger.info(f"📚 开始生成参考文献，共有 {len(cited_sources)} 个引用源")

    def format_reference_entry(source: Source, number: int) -> str:
        """根据源类型格式化参考文献条目为BibTeX风格的学术格式"""

        if source.source_type == "webpage":
            # 网页格式: [编号] 作者/网站. "标题". 网站名 (年份). URL
            content_lines = source.content.strip().split('\n')
            actual_title = "网页资源"
            url = source.url or ""
            website_name = ""
            year = "2024"  # 默认年份，可以从URL或内容中提取

            # 尝试从content中提取更好的信息
            for line in content_lines:
                if line.strip().startswith('URL:'):
                    url = line.replace('URL:', '').strip()
                    # 从URL中提取网站名称
                    import re
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)',
                                             url)
                    if domain_match:
                        domain = domain_match.group(1)
                        if 'baidu.com' in domain:
                            website_name = "百度百科"
                        elif 'csdn.net' in domain:
                            website_name = "CSDN博客"
                        elif 'juejin.cn' in domain:
                            website_name = "掘金"
                        elif 'aliyun.com' in domain:
                            website_name = "阿里云开发者社区"
                        elif 'github.io' in domain:
                            website_name = "GitHub Pages"
                        else:
                            website_name = domain

                elif '内容预览:' in line:
                    # 提取实际标题
                    preview_part = line.split('内容预览:')[-1].strip()
                    if preview_part:
                        # 提取网页标题（去掉网站后缀）
                        import re
                        title_match = re.search(
                            r'([^_]+?)(?:\s*[_\-]\s*(?:百度百科|CSDN博客|掘金|阿里云|GitHub)|$)',
                            preview_part)
                        if title_match:
                            actual_title = title_match.group(1).strip()
                        elif len(preview_part) > 10:
                            actual_title = preview_part[:60] + "..." if len(
                                preview_part) > 60 else preview_part

            # 如果没有提取到合适的标题，使用原始title
            if actual_title == "网页资源" and source.title:
                if source.title.startswith('Search results for:'):
                    query_part = source.title.replace('Search results for:',
                                                      '').strip()
                    actual_title = f"{query_part}"
                else:
                    actual_title = source.title

            # 格式化为学术引用格式
            if website_name and url:
                return f'[{number}] {website_name}. "{actual_title}". {website_name} ({year}). {url}'
            elif url:
                return f'[{number}] 网络资源. "{actual_title}". 在线资源 ({year}). {url}'
            else:
                return f'[{number}] 网络资源. "{actual_title}". 在线资源 ({year}).'

        elif source.source_type == "es_result":
            # 内部知识库格式: [编号] 作者/机构. "文档标题". 内部知识库 (年份).
            content_lines = source.content.strip().split('\n')
            doc_title = "内部知识库文档"
            author = "内部资料"
            year = "2024"

            for line in content_lines:
                if '.pdf' in line or '.doc' in line:
                    # 提取文档名称
                    import re
                    doc_match = re.search(r'([^/\]]+\.(?:pdf|doc|docx))', line)
                    if doc_match:
                        full_name = doc_match.group(1)
                        # 去掉文件扩展名
                        doc_title = re.sub(r'\.(pdf|doc|docx)$', '', full_name)
                        break
                elif '[personal_knowledge_base]' in line:
                    # 提取紧跟的文档标题
                    remaining = line.split(
                        '[personal_knowledge_base]')[-1].strip()
                    if remaining:
                        doc_title = remaining.split(
                            '.'
                        )[0] if '.' in remaining else remaining[:80] + "..."

                        # 尝试从标题中提取机构信息
                        if '【' in doc_title and '】' in doc_title:
                            import re
                            org_match = re.search(r'【([^】]+)】', doc_title)
                            if org_match:
                                author = org_match.group(1)
                        break

            return f'[{number}] {author}. "{doc_title}". 内部知识库 ({year}).'

        elif source.source_type == "document":
            # 文档格式: [编号] 作者. "文档标题". 文档类型 (年份).
            return f'[{number}] 文档资料. "{source.title}". 内部文档 (2024).'

        else:
            # 默认格式
            return f'[{number}] 未知来源. "{source.title}". {source.source_type} (2024).'

    # 生成参考文献部分
    bibliography_section = "\n\n## 参考文献\n\n"

    # 按源ID排序，确保参考文献顺序一致
    sorted_sources = sorted(cited_sources.items(), key=lambda x: x[0])

    # 使用全局连续的编号
    for global_number, (source_id, source) in enumerate(sorted_sources, 1):
        # 使用新的格式化函数
        reference_entry = format_reference_entry(source, global_number)
        bibliography_section += reference_entry + "\n"

    # 将参考文献部分添加到最终文档
    updated_document = final_document + bibliography_section

    logger.info(f"✅ 参考文献生成完成，文档总长度: {len(updated_document)} 字符")

    # 记录引用的源信息
    for global_number, (source_id, source) in enumerate(sorted_sources, 1):
        logger.debug(
            f"  📖 [{global_number}] {source.title} ({source.source_type})")

    return {"final_document": updated_document}


def _format_sources_to_text(sources: list[Source]) -> str:
    """
    将 Source 对象列表格式化为文本格式，用于向后兼容
    
    Args:
        sources: Source 对象列表
        
    Returns:
        str: 格式化的文本
    """
    if not sources:
        return "没有收集到相关数据"

    formatted_text = "收集到的信息源:\n\n"

    for i, source in enumerate(sources, 1):
        formatted_text += f"=== 信息源 {i} ===\n"
        formatted_text += f"标题: {source.title}\n"
        if source.url:
            formatted_text += f"URL: {source.url}\n"
        formatted_text += f"类型: {source.source_type}\n"
        formatted_text += f"内容: {source.content}\n\n"

    return formatted_text


def _parse_es_search_results(es_results: str, query: str,
                             start_id: int) -> list[Source]:
    """
    解析ES搜索结果，创建 Source 对象列表
    
    Args:
        es_results: ES搜索的原始结果字符串
        query: 搜索查询
        start_id: 起始ID
        
    Returns:
        list[Source]: Source 对象列表
    """
    sources = []
    current_id = start_id

    try:
        # 解析ES搜索结果
        lines = es_results.split('\n')
        current_title = ""
        current_content = ""
        current_url = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试提取文档信息
            if line.startswith('文档标题:') or line.startswith('Title:'):
                current_title = line.split(':', 1)[1].strip()
            elif line.startswith('文档内容:') or line.startswith('Content:'):
                current_content = line.split(':', 1)[1].strip()
            elif line.startswith('文档URL:') or line.startswith('URL:'):
                current_url = line.split(':', 1)[1].strip()
            elif line.startswith('---') or line.startswith('==='):
                # 分隔符，处理前一个文档
                if current_title and current_content:
                    source = Source(
                        id=current_id,
                        source_type="es_result",
                        title=current_title,
                        url=current_url,
                        content=current_content[:500] + "..."
                        if len(current_content) > 500 else current_content)
                    sources.append(source)
                    current_id += 1
                    current_title = ""
                    current_content = ""
                    current_url = ""
            elif not current_title and len(line) > 10:
                # 可能是标题
                current_title = line
            elif current_title and len(line) > 20:
                # 可能是内容
                current_content += " " + line

        # 处理最后一个文档
        if current_title and current_content:
            source = Source(
                id=current_id,
                source_type="es_result",
                title=current_title,
                url=current_url,
                content=current_content[:500] +
                "..." if len(current_content) > 500 else current_content)
            sources.append(source)

        # 如果没有解析到任何源，创建一个默认源
        if not sources:
            source = Source(id=start_id,
                            source_type="es_result",
                            title=f"知识库搜索结果 - {query}",
                            url="",
                            content=es_results[:500] +
                            "..." if len(es_results) > 500 else es_results)
            sources.append(source)

    except Exception as e:
        logger.error(f"解析ES搜索结果失败: {str(e)}")
        # 创建默认源
        source = Source(id=start_id,
                        source_type="es_result",
                        title=f"知识库搜索结果 - {query}",
                        url="",
                        content=es_results[:500] +
                        "..." if len(es_results) > 500 else es_results)
        sources.append(source)

    return sources


def fusion_editor_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    融合编辑器节点
    
    对最终文档进行润色，特别是重写引言和结论部分，使其更好地与文档主体内容协调
    
    Args:
        state: 研究状态，包含 completed_chapters 和 final_document
        llm_client: LLM客户端实例
        
    Returns:
        dict: 包含更新后的 final_document 的字典
    """
    completed_chapters = state.get("completed_chapters", [])
    topic = state.get("topic", "")

    logger.info("🎨 开始融合编辑器处理")
    logger.info(f"📚 已完成章节数量: {len(completed_chapters)}")

    # 检查是否有足够的章节进行处理
    if len(completed_chapters) <= 1:
        logger.info("📝 章节数量不足，跳过融合编辑")
        return {"final_document": state.get("final_document", "")}

    # 提取引言和结论
    intro_chapter = completed_chapters[0]
    conclusion_chapter = completed_chapters[-1]
    middle_chapters = completed_chapters[1:-1]

    logger.info(f"📖 提取引言章节: {intro_chapter.get('title', 'Unknown')}")
    logger.info(f"📖 提取结论章节: {conclusion_chapter.get('title', 'Unknown')}")
    logger.info(f"📚 中间章节数量: {len(middle_chapters)}")

    # 获取引言和结论的原始内容
    intro_content = intro_chapter.get("content", "")
    conclusion_content = conclusion_chapter.get("content", "")

    # 创建全局摘要：合并中间章节的摘要
    global_summary_parts = []
    for chapter in middle_chapters:
        if isinstance(chapter, dict):
            summary = chapter.get("summary", "")
            if summary:
                global_summary_parts.append(summary)
            else:
                # 如果没有摘要，使用内容的前200字符
                content = chapter.get("content", "")
                if content:
                    summary = content[:200] + "..." if len(
                        content) > 200 else content
                    global_summary_parts.append(summary)

    global_summary = "\n\n".join(global_summary_parts)
    logger.info(f"📋 全局摘要长度: {len(global_summary)} 字符")

    # 获取中间章节的完整内容
    middle_chapters_content = []
    for chapter in middle_chapters:
        if isinstance(chapter, dict):
            content = chapter.get("content", "")
            if content:
                middle_chapters_content.append(content)

    middle_content = "\n\n".join(middle_chapters_content)

    try:
        # 重写引言
        logger.info("✍️ 开始重写引言")
        intro_prompt = f"""你是一位资深的首席编辑，负责重写文档的引言部分。

**文档主题:** {topic}

**原始引言内容:**
{intro_content}

**文档主体章节摘要:**
{global_summary}

**任务要求:**
1. 仔细阅读原始引言和主体章节摘要
2. 重写引言，使其更好地：
   - 为读者提供清晰的文档概览
   - 准确预览主体章节将要讨论的主要观点
   - 建立逻辑连贯性，确保引言与主体内容自然衔接
   - 保持专业性和学术性
3. 保持原有的章节标题和基本结构
4. 确保重写后的引言与主体章节的内容和风格保持一致

请重写引言，使其更好地为整个文档服务。"""

        polished_intro = llm_client.invoke(intro_prompt,
                                           temperature=0.3,
                                           max_tokens=2000)

        logger.info(f"✅ 引言重写完成，长度: {len(polished_intro)} 字符")

        # 重写结论
        logger.info("✍️ 开始重写结论")
        conclusion_prompt = f"""你是一位资深的首席编辑，负责重写文档的结论部分。

**文档主题:** {topic}

**原始结论内容:**
{conclusion_content}

**文档主体章节摘要:**
{global_summary}

**任务要求:**
1. 仔细阅读原始结论和主体章节摘要
2. 重写结论，使其更好地：
   - 总结文档的核心观点和主要发现
   - 反映主体章节讨论的关键内容
   - 提供对主题的深入思考和洞察
   - 为读者提供有价值的收尾
3. 保持原有的章节标题和基本结构
4. 确保重写后的结论与主体章节的内容和风格保持一致

请重写结论，使其更好地总结和反思整个文档的核心论点。"""

        polished_conclusion = llm_client.invoke(conclusion_prompt,
                                                temperature=0.3,
                                                max_tokens=2000)

        logger.info(f"✅ 结论重写完成，长度: {len(polished_conclusion)} 字符")

        # 重新组装文档
        final_document_parts = [polished_intro]

        if middle_content:
            final_document_parts.append(middle_content)

        final_document_parts.append(polished_conclusion)

        final_document = "\n\n".join(final_document_parts)

        logger.info(f"📄 融合编辑完成，最终文档长度: {len(final_document)} 字符")

        return {"final_document": final_document}

    except Exception as e:
        logger.error(f"❌ 融合编辑器处理失败: {str(e)}")
        # 返回原始文档
        return {"final_document": state.get("final_document", "")}
