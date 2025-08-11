"""
研究节点模块

负责初始研究，收集主题相关的信息源
"""

import json

from doc_agent.core.config import settings
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event, safe_serialize
from doc_agent.graph.common import (
    parse_es_search_results,
    parse_web_search_results,
)
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.llm_clients.providers import EmbeddingClient
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.reranker import RerankerTool
from doc_agent.tools.web_search import WebSearchTool
from doc_agent.utils.search_utils import search_and_rerank


async def initial_research_node(state: ResearchState,
                                web_search_tool: WebSearchTool,
                                es_search_tool: ESSearchTool,
                                reranker_tool: RerankerTool = None,
                                llm_client: LLMClient = None) -> dict:
    """
    初始研究节点 - 统一版本
    基于主题进行初始研究，收集相关信息源
    根据配置自动调整搜索深度和查询数量
    
    Args:
        state: 研究状态，包含 topic
        web_search_tool: 网络搜索工具
        es_search_tool: ES搜索工具
        reranker_tool: 重排序工具
        llm_client: LLM客户端（可选）
        
    Returns:
        dict: 包含 initial_sources 的字典，包含 Source 对象列表
    """
    task_prompt = state.get("task_prompt", "")
    if not task_prompt:
        raise ValueError("主 task_prompt 不能为空")

    # LLM 提取 topic，要求字数（如有），其他格式内容要求
    # 返回
    # ```json
    # {
    #     "topic": "任务的主题",
    #     "word_count": "任务的字数要求",
    #     "other_requirements": "任务的其他格式内容要求"
    # }
    # ```
    prompt = f"""
你是一个专业的任务分析引擎。你的唯一目标是解析用户提供的文本，并从中提取关键的任务要求。

你必须严格遵循以下指令：
1.  分析文本，识别出任务的【主题】、【字数要求】和【其他要求】。
2.  你的输出必须是一个单一、有效的 JSON 对象，不能包含任何 JSON 格式之外的额外文本、解释或注释。
3.  严格按照下面的 schema 和字段规则生成 JSON：

```json
{{
    "topic": "任务的核心主题或标题。",
    "word_count": "从文本中提取明确的字数要求，只保留数字部分作为字符串。如果没有提到任何字数要求，则该字段的值必须是 '-1'。",
    "other_requirements": "除了主题和字数外的所有其他具体要求，例如格式、风格、需要包含的要点、受众等。如果没有，则该字段为空字符串 ''。"
}}
```

示例学习:

示例 1:
用户输入: "帮我写一篇关于人工智能对未来社会影响的文章，要求 800 字左右，需要包含正反两方面的观点。"
JSON 输出:

```JSON
{{
    "topic": "人工智能对未来社会影响",
    "word_count": "800",
    "other_requirements": "需要包含正反两方面的观点"
}}
```

示例 2:
用户输入: "写一份关于下季度市场营销活动的策划方案，要包括目标受众分析和预算分配。"
JSON 输出:

```JSON
{{
    "topic": "下季度市场营销活动的策划方案",
    "word_count": "-1",
    "other_requirements": "要包括目标受众分析和预算分配"
}}
```
示例 3:
用户输入: "给我讲讲全球变暖的原因"
JSON 输出:

```JSON
{{
    "topic": "全球变暖的原因",
    "word_count": "-1",
    "other_requirements": ""
}}
```
示例 4:
用户输入: "请为我们公司的季度总结报告写一个开场白，大约 200 字，风格要正式、鼓舞人心，并且要提到我们团队第二季度的主要成就：'项目A成功上线'和'客户满意度提升15%'"
JSON 输出:

```JSON
{{
    "topic": "公司季度总结报告的开场白",
    "word_count": "200",
    "other_requirements": "风格要求正式、鼓舞人心；需要提到第二季度的主要成就：'项目A成功上线'和'客户满意度提升15%'"
}}
```

任务开始

用户输入:
{task_prompt}
    """
    response = llm_client.invoke(prompt)
    logger.info(f"🔍 初始研究: {response}")
    # 去除 ```json 和 ```
    response = response.replace("```json", "").replace("```", "")
    response = json.loads(response)
    topic = response.get("topic", "")
    word_count = response.get("word_count", "-1")
    other_requirements = response.get("other_requirements", "")
    if not topic:
        raise ValueError("主题不能为空")
    try:
        word_count = int(word_count)
    except ValueError:
        word_count = 5000  # 默认值
    if word_count < 0:
        word_count = 5000  # 默认值
    if other_requirements:
        other_requirements = other_requirements.split("\n")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    job_id = state.get("job_id", "")
    task_prompt = state.get("task_prompt", "")

    logger.info(f"🔍 开始初始研究 (模式: {complexity_config['level']}): {task_prompt}")

    # Outline-1a & 1b: 开始初步调研，并包含 query
    publish_event(job_id, "初步调研", "outline_generation", "START", {
        "task_prompt": task_prompt,
        "description": "开始根据您的要求进行初步调研和信息搜索..."
    })

    # 根据配置生成查询数量
    num_queries = complexity_config['initial_search_queries']

    # 用 LLM 生成初始搜索查询
    prompt = f"""
你是一个专业的研究策略师和信息检索专家。

你的任务是根据用户提供的【主题】和【具体要求】，生成一组用于在多个信息源（如 Google 搜索、Elasticsearch 数据库）进行检索的高质量、多样化的搜索查询(Search Queries)。

**核心指令:**

1.  **深入理解**: 分析【主题】和【具体要求】，理解用户的核心意图。
2.  **拆解与扩展**: 将复杂的任务拆解成多个更小、更具体的子问题。从不同角度进行思考，例如：
    * **核心定义**: 关于主题本身是什么。
    * **关键方面**: 任务要求中提到的每个要点。
    * **案例/数据**: 寻找相关的实例、统计数据或证据。
    * **方法/过程**: 如果是“如何做”的问题，寻找具体步骤和方法。
    * **对比/评价**: 寻找正反观点、优缺点对比。
3.  **生成查询**: 基于上述分析，生成一组简洁、有效的搜索查询。查询应该像真人专家会输入到搜索引擎中的那样。数量不宜过多，一般以 2-5 个为宜。
4.  **格式化输出**: 你的输出必须是一个单一、有效的 JSON 对象，格式为 `{{{{"search_queries": ["查询1", "查询2", ...]}}}}`。除此之外，不要包含任何解释性文字。

---
**示例学习:**

**示例 1:**
输入:
{{
    "topic": "人工智能对未来社会影响",
    "other_requirements": "需要包含正反两方面的观点"
}}
JSON 输出:
```json
{{
    "search_queries": [
        "人工智能对社会的影响",
        "AI 技术的积极应用案例",
        "人工智能带来的好处和机遇",
    ]
}}
```

任务开始

请根据下面的输入生成搜索查询：

输入:

JSON

{{
    "topic": "{topic}",
    "other_requirements": "{other_requirements or ''}"
}}
```
    """

    response = llm_client.invoke(prompt)
    logger.info(f"🔍 初始搜索查询: {response}")
    # 去除 ```json 和 ```
    response = response.replace("```json", "").replace("```", "")
    try:
        response = json.loads(response)
        initial_queries = response.get("search_queries", [])
        assert isinstance(initial_queries, list)
        assert len(initial_queries) > 0
        assert all(isinstance(query, str) for query in initial_queries)
        num_queries = len(initial_queries)
    except Exception as e:
        logger.error(f"❌ 解析初始搜索查询失败: {str(e)}，回退到默认搜索")

        # 生成搜索查询
        if num_queries == 2:  # 快速模式
            initial_queries = [f"{topic} 概述", f"{topic} 主要内容"]
        elif num_queries <= 5:  # 标准模式
            initial_queries = [
                f"{topic} 概述", f"{topic} 主要内容", f"{topic} 关键要点",
                f"{topic} 最新发展", f"{topic} 重要性"
            ][:num_queries]
        else:  # 全面模式
            initial_queries = [
                f"{topic} 概述", f"{topic} 主要内容", f"{topic} 关键要点",
                f"{topic} 最新发展", f"{topic} 重要性", f"{topic} 实践案例",
                f"{topic} 未来趋势", f"{topic} 相关技术"
            ][:num_queries]

    logger.info(f"📊 配置搜索轮数: {num_queries}，实际执行: {len(initial_queries)} 轮")

    publish_event(job_id, "初步调研", "outline_generation", "RUNNING", {
        "queries": initial_queries,
        "description": "开始进行信息搜索..."
    })

    all_sources = []  # 存储所有 Source 对象
    source_id_counter = 1  # 源ID计数器
    web_sources = []  # 存储网络搜索源
    es_sources = []  # 存储ES搜索源

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
        web_raw_results = []
        web_str_results = ""
        try:
            # 使用异步搜索方法
            web_raw_results, web_str_results = await web_search_tool.search_async(
                query)
            if "模拟" in web_str_results or "mock" in web_str_results.lower():
                web_str_results = ""
                web_raw_results = []
        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            web_str_results = ""
            web_raw_results = []

        # ES搜索
        es_raw_results = []
        es_str_results = ""
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
                        _, es_raw_results, es_str_results = await search_and_rerank(
                            es_search_tool, query, query_vector, reranker_tool)
                        logger.info(
                            f"✅ 向量检索+重排序执行成功，结果长度: {len(es_raw_results)}")
                    else:
                        # 回退到文本搜索
                        es_raw_results = await es_search_tool.search(query)
                        logger.info(f"✅ 文本搜索执行成功，结果长度: {len(es_raw_results)}")

                except Exception as e:
                    logger.warning(f"⚠️  向量检索失败，使用文本搜索: {str(e)}")
                    es_raw_results = await es_search_tool.search(query)
            else:
                # 直接使用文本搜索
                es_raw_results = await es_search_tool.search(query)

        except Exception as e:
            logger.error(f"ES搜索失败: {str(e)}")
            es_raw_results = []

        # 处理搜索结果并创建Source对象
        if web_str_results and web_str_results.strip():
            try:
                current_web_sources = parse_web_search_results(
                    web_raw_results, query, source_id_counter)
                web_sources.extend(current_web_sources)
                all_sources.extend(current_web_sources)
                source_id_counter += len(current_web_sources)
                logger.info(f"✅ 从网络搜索中提取到 {len(current_web_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析网络搜索结果失败: {str(e)}")

        if es_raw_results and len(es_raw_results) > 0:
            try:
                current_es_sources = parse_es_search_results(
                    es_raw_results, query, source_id_counter)
                es_sources.extend(current_es_sources)
                all_sources.extend(current_es_sources)
                source_id_counter += len(current_es_sources)
                logger.info(f"✅ 从ES搜索中提取到 {len(current_es_sources)} 个源")
            except Exception as e:
                logger.error(f"❌ 解析ES搜索结果失败: {str(e)}")

    # 根据配置决定是否截断数据
    truncate_length = complexity_config.get('data_truncate_length', -1)
    if truncate_length > 0:
        # 限制每个源的内容长度
        for source in all_sources:
            if len(source.content) > truncate_length // len(all_sources):
                source.content = source.content[:truncate_length //
                                                len(all_sources
                                                    )] + "... (内容已截断)"

    logger.info(f"✅ 初始研究完成，收集到 {len(all_sources)} 个信息源")

    publish_event(
        job_id, "初步调研", "outline_generation", "SUCCESS", {
            "web_sources": [safe_serialize(source) for source in web_sources],
            "es_sources": [safe_serialize(source) for source in es_sources],
            "description":
            f"初步调研完成，收集到信息源：内部搜索结果 {len(es_sources)} 个，网络搜索结果 {len(web_sources)} 个..."
        })

    return {
        "initial_sources": all_sources,
        "topic": topic,
        "word_count": word_count,
        "prompt_requirements": other_requirements
    }
