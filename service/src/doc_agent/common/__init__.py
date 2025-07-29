"""
Common utilities and components for the doc_agent package.
"""

from .prompt_selector import PromptSelector, get_prompt


# 直接导入parse_planner_response函数
def parse_planner_response(response: str):
    """解析规划器的响应，提取研究计划和搜索查询"""
    import json
    import re
    from loguru import logger

    logger.info("开始解析规划器响应")
    logger.debug(f"响应内容长度: {len(response)} 字符")
    logger.debug(f"原始响应内容: {repr(response)}")

    try:
        response = response.strip()
        # 尝试用正则提取 markdown 代码块中的 JSON
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```",
                                     response, re.IGNORECASE)
        if code_block_match:
            response = code_block_match.group(1).strip()
            logger.debug("从markdown代码块中提取JSON")

        logger.debug(f"准备解析的JSON内容: {repr(response)}")

        # 解析 JSON
        data = json.loads(response)
        logger.debug(f"解析后的数据: {data}")

        research_plan = data["research_plan"]
        search_queries = data["search_queries"]

        # 处理 research_plan，如果是复杂对象则转换为字符串
        if isinstance(research_plan, dict):
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
            research_plan = str(research_plan)

        # 确保所有搜索查询都是字符串
        search_queries = [str(query) for query in search_queries]

        logger.info(
            f"规划器响应解析成功，研究计划长度: {len(research_plan)}, 搜索查询数量: {len(search_queries)}"
        )
        return research_plan, search_queries

    except Exception as e:
        logger.error(f"规划器响应解析错误: {e}")
        logger.debug(f"原始响应: {response[:200]}...")
        raise ValueError(f"Failed to parse planner response: {e}") from e


__all__ = ['PromptSelector', 'get_prompt', 'parse_planner_response']
