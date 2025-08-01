"""
解析器模块

提供各种LLM响应和搜索结果的解析功能
"""

import json
import re

from loguru import logger

from doc_agent.schemas import Source


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


def parse_web_search_results(web_results: str, query: str,
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


def parse_es_search_results(es_results: str, query: str,
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
