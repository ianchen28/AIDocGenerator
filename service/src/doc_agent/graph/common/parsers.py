"""
解析器模块

提供各种LLM响应和搜索结果的解析功能
"""

import json
import re

from doc_agent.core.logger import logger

from doc_agent.schemas import Source
from doc_agent.tools.reranker import RerankedSearchResult


def parse_llm_json_response(response: str) -> dict:
    """
    通用的 LLM JSON 响应解析函数
    
    Args:
        response: LLM 的原始响应
        
    Returns:
        dict: 解析后的 JSON 数据
        
    Raises:
        ValueError: 当解析失败时
    """
    try:
        # 清理响应，去除前后空白
        cleaned = response.strip()

        # 尝试直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 提取 JSON 块
        json_match = re.search(r'```json\s*\n(.*?)\n\s*```', cleaned,
                               re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)

        # 尝试提取花括号内的内容
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)

        raise ValueError("无法从响应中提取有效的 JSON")

    except Exception as e:
        logger.error(f"解析 JSON 响应失败: {e}")
        raise ValueError(f"JSON 解析失败: {str(e)}") from e


def parse_planner_response(response: str) -> tuple[str, list[str]]:
    """
    解析规划器的响应，提取研究计划和搜索查询
    
    Args:
        response: LLM 的原始响应
        
    Returns:
        tuple: (研究计划, 搜索查询列表)
        
    Raises:
        ValueError: 当 JSON 解析失败时
    """
    logger.info("开始解析规划器响应")
    logger.debug(f"响应内容长度: {len(response)} 字符")

    try:
        # 使用通用 JSON 解析函数
        data = parse_llm_json_response(response)

        # 兼容两种格式：research_plan 和 research_questions
        if "research_plan" in data:
            research_plan = data["research_plan"]
        elif "research_questions" in data:
            # 将 research_questions 转换为 research_plan 格式
            questions = data["research_questions"]
            if isinstance(questions, list):
                research_plan = "研究问题：\n" + "\n".join(
                    [f"- {q}" for q in questions])
            else:
                research_plan = str(questions)
        else:
            # 如果没有找到研究计划，使用默认值
            research_plan = "基于主题进行深入研究"

        search_queries = data.get("search_queries", [])

        logger.debug(f"提取的研究计划类型: {type(research_plan)}")
        logger.debug(f"提取的搜索查询数量: {len(search_queries)}")

        # 处理 research_plan，如果是复杂对象则转换为字符串
        if isinstance(research_plan, dict):
            # 将复杂对象转换为结构化的字符串描述
            logger.debug("将复杂的研究计划对象转换为字符串")
            plan_parts = []
            for key, value in research_plan.items():
                if isinstance(value, list):
                    plan_parts.append(f"{key}:")
                    for item in value:
                        plan_parts.append(f"  - {item}")
                else:
                    plan_parts.append(f"{key}: {value}")
            research_plan = "\n".join(plan_parts)
        elif not isinstance(research_plan, str):
            # 如果不是字符串，转换为字符串
            logger.debug(f"将研究计划从 {type(research_plan)} 转换为字符串")
            research_plan = str(research_plan)

        # 验证数据类型
        if not isinstance(research_plan, str):
            raise ValueError(f"研究计划必须是字符串，但得到 {type(research_plan)}")
        if not isinstance(search_queries, list):
            raise ValueError(f"搜索查询必须是列表，但得到 {type(search_queries)}")

        logger.info(
            f"成功解析规划器响应: 研究计划长度={len(research_plan)}, 搜索查询数量={len(search_queries)}"
        )
        return research_plan, search_queries

    except ValueError as e:
        logger.error(f"解析规划器响应失败: {e}")
        raise


def parse_reflection_response(response: str) -> list[str]:
    """
    解析 reflection 节点的 LLM 响应，提取新的搜索查询

    Args:
        response: LLM 的原始响应

    Returns:
        list[str]: 新的搜索查询列表
    """
    try:
        # 尝试解析 JSON 格式
        cleaned_response = response.strip()

        # 尝试提取 JSON 部分
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)

            if 'new_queries' in data and isinstance(data['new_queries'], list):
                queries = data['new_queries']
                # 验证查询质量
                valid_queries = [
                    q.strip() for q in queries
                    if q.strip() and len(q.strip()) > 5
                ]
                if valid_queries:
                    return valid_queries

        # 如果 JSON 解析失败，尝试从文本中提取查询
        # 查找常见的查询模式
        query_patterns = [
            r'(\d+\.\s*)([^\n]+)',  # 1. query
            r'[-•]\s*([^\n]+)',  # - query 或 • query
            r'"([^"]+)"',  # "query"
        ]

        for pattern in query_patterns:
            try:
                matches = re.findall(pattern, cleaned_response, re.MULTILINE)
                if matches:
                    queries = []
                    for match in matches:
                        if isinstance(match, tuple):
                            query = match[1] if len(match) > 1 else match[0]
                        else:
                            query = match

                        query = query.strip()
                        if query and len(query) > 5:
                            queries.append(query)

                    if queries:
                        return queries
            except Exception as e:
                logger.debug(f"正则表达式匹配失败: {e}")
                continue

        # 如果所有方法都失败，尝试简单的行分割
        lines = cleaned_response.split('\n')
        queries = []
        for line in lines:
            line = line.strip()
            # 跳过空行、数字行、标题行等
            if (line and len(line) > 10 and not line.startswith('#')
                    and not re.match(r'^\d+\.?$', line)
                    and not re.match(r'^[A-Z\s]+$', line)):  # 全大写可能是标题
                queries.append(line)

        return queries[:3]  # 最多返回3个查询

    except Exception as e:
        logger.error(f"解析 reflection 响应失败: {e}")
        return []


def parse_web_search_results(web_raw_results: list[dict], query: str,
                             start_id: int) -> list[Source]:
    """
    解析网络搜索结果，创建 Source 对象列表

    Args:
        web_raw_results: 网络搜索结果
        query: 搜索查询
        start_id: 起始ID

    Returns:
        list[Source]: Source 对象列表
    """

    sources = []

    for index, web_raw_result in enumerate(web_raw_results):
        try:
            # 🔧 修复：确保所有必需字段都存在
            source_id = start_id + index
            source_type = "web"

            # 从 meta_data 中获取标题，如果没有则使用默认值
            meta_data = web_raw_result.get('meta_data', {})
            title = meta_data.get('docName', f'网页 {source_id}')

            url = web_raw_result.get('url', '')
            content = web_raw_result.get('text', '')

            # 截断内容到500字符
            if len(content) > 500:
                content = content[:500] + "..."

            # 从 meta_data 中获取更多信息
            date = meta_data.get('datePublished', '')
            author = meta_data.get('author', '')
            site_name = meta_data.get('siteName', '')

            source = Source(id=source_id,
                            doc_id=web_raw_result.get('_id',
                                                      f'web_{source_id}'),
                            doc_from="web",
                            domain_id="web_search",
                            index="web_pages",
                            source_type=source_type,
                            title=title,
                            url=url,
                            content=content,
                            date=date,
                            date_published=date,
                            author=author,
                            site_name=site_name,
                            metadata={
                                "file_name": title,
                                "locations": [],
                                "source": "web_search"
                            })

            sources.append(source)
            logger.debug(f"✅ 成功创建网页源: {source_id} - {title}")

        except Exception as e:
            logger.error(f"❌ 创建网页源失败: {e}")
            logger.error(f"📄 原始数据: {web_raw_result}")
            continue

    logger.info(f"📊 成功解析 {len(sources)} 个网页源")
    return sources


def parse_es_search_results(es_raw_results: list[RerankedSearchResult],
                            query: str, start_id: int) -> list[Source]:
    """
    解析ES搜索结果，创建 Source 对象列表

    Args:
        es_raw_results: ES搜索结果
        query: 搜索查询
        start_id: 起始ID

    Returns:
        list[Source]: Source 对象列表
    """

    # RerankedSearchResult
    # id='bFEcIJYBwBkB_JLNVi-q',
    # doc_id='5938a73882a4f00515b3614b03dc419d',
    # index='personal_knowledge_base',
    # domain_id='documentUploadAnswer',
    # doc_from='self',
    # original_content='文本内容',
    # score=1.6947638,
    # rerank_score=3.2050650119781494,
    # metadata={
    # 	'file_name': '深圳市城市轨道交通工程无人机使用及实景建模要求（V1.0）.pdf',
    # 	'locations': [],
    # 	'source': 'self'
    # },
    # alias_name='personal_knowledge_base'

    sources = []

    for index, es_raw_result in enumerate(es_raw_results):
        try:
            # 🔧 修复：确保所有必需字段都存在
            source_id = start_id + index
            source_type = "es_result"
            title = es_raw_result.metadata.get(
                'file_name', f'文档 {source_id}'
            ) if es_raw_result.metadata else f'文档 {source_id}'
            url = es_raw_result.metadata.get(
                'url', '') if es_raw_result.metadata else ''
            content = es_raw_result.original_content or ''
            locations = es_raw_result.metadata.get('locations', [])
            source = es_raw_result.doc_from

            # 截断内容到500字符
            if len(content) > 500:
                content = content[:500] + "..."

            # 从 metadata 中获取更多信息
            metadata = es_raw_result.metadata or {}
            date = metadata.get('date', '')
            author = metadata.get('author', '')
            file_token = metadata.get('file_token', '')
            page_number = metadata.get('page_number')

            # 保留原有的 metadata，只添加必要的字段
            metadata = es_raw_result.metadata or {}
            # metadata.update({
            #     "file_name": title,
            #     "locations": locations,
            #     # 统一使用 doc_from 作为 source 值
            #     "source": es_raw_result.doc_from
            # })

            source = Source(id=source_id,
                            doc_id=es_raw_result.doc_id,
                            doc_from=es_raw_result.doc_from,
                            domain_id=es_raw_result.domain_id,
                            index=es_raw_result.index,
                            source_type=source_type,
                            title=title,
                            url=url,
                            content=content,
                            date=date,
                            author=author,
                            file_token=file_token,
                            page_number=page_number,
                            metadata=metadata)

            sources.append(source)
            logger.debug(f"✅ 成功创建ES源: {source_id} - {title}")

        except Exception as e:
            logger.error(f"❌ 创建ES源失败: {e}")
            logger.error(f"📄 原始数据: {es_raw_result}")
            continue

    logger.info(f"📊 成功解析 {len(sources)} 个ES源")
    return sources
