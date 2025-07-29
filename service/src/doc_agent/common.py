"""
通用工具模块，提供导入路径管理和配置访问
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from loguru import logger


def setup_import_paths():
    """
    设置导入路径，确保可以从任何目录运行代码
    """
    logger.debug("开始设置导入路径")
    current_file = Path(__file__)

    # 查找service目录
    service_dir = None
    for parent in current_file.parents:
        if parent.name == 'service':
            service_dir = parent
            break

    if service_dir and str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))
        logger.debug(f"已添加service目录到Python路径: {service_dir}")
    else:
        logger.debug("service目录已在Python路径中或未找到")

    # 查找项目根目录（包含es_retrieval_core.py的目录）
    project_root = None
    for parent in current_file.parents:
        if (parent / 'es_retrieval_core.py').exists():
            project_root = parent
            break

    if project_root and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"已添加项目根目录到Python路径: {project_root}")
    else:
        logger.debug("项目根目录已在Python路径中或未找到")


def get_settings():
    """
    动态获取settings配置
    Returns:
        配置对象
    Raises:
        ImportError: 如果无法找到配置模块
    """
    logger.debug("获取settings配置")
    setup_import_paths()

    try:
        from core.config import settings
        logger.debug("成功导入settings配置")
        return settings
    except ImportError as e:
        logger.error(f"无法导入配置模块: {e}")
        raise ImportError(f"无法导入配置模块: {e}. 请确保在正确的目录中运行。") from e


def safe_import(module_path: str, default: Any = None):
    """
    安全导入模块或对象
    Args:
        module_path: 模块路径，如 'core.config.settings'
        default: 导入失败时的默认值
    Returns:
        导入的对象或默认值
    """
    logger.debug(f"安全导入模块: {module_path}")
    try:
        setup_import_paths()
        module_parts = module_path.split('.')
        module = __import__(module_parts[0])

        for part in module_parts[1:]:
            module = getattr(module, part)

        logger.debug(f"成功导入模块: {module_path}")
        return module
    except (ImportError, AttributeError) as e:
        logger.warning(f"导入模块失败: {module_path}, 错误: {e}")
        return default


def parse_llm_json_response(response: str,
                            required_fields: list[str] = None) -> dict:
    """
    解析 LLM 的 JSON 响应
    支持 markdown 代码块包裹、各种换行和空格
    """
    logger.debug("开始解析LLM JSON响应")
    logger.debug(f"响应内容长度: {len(response)} 字符")

    try:
        response = response.strip()
        # 尝试用正则提取 markdown 代码块中的 JSON
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```",
                                     response, re.IGNORECASE)
        if code_block_match:
            response = code_block_match.group(1).strip()
            logger.debug("从markdown代码块中提取JSON")
        # 再尝试直接解析 JSON
        data = json.loads(response)
        if required_fields:
            for field in required_fields:
                if field not in data:
                    logger.error(f"缺少必需字段: {field}")
                    raise ValueError(f"Missing required field: {field}")
        logger.debug("JSON解析成功")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
        logger.debug(f"响应内容: {response[:200]}...")
        raise ValueError(f"Failed to parse JSON response: {e}") from e
    except Exception as e:
        logger.error(f"响应解析错误: {e}")
        logger.debug(f"响应内容: {response[:200]}...")
        raise ValueError(f"Failed to parse response: {e}") from e


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
        # 使用通用 JSON 解析函数，不强制要求特定字段
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

        search_queries = data["search_queries"]

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
            logger.error(f"研究计划必须是字符串，当前类型: {type(research_plan)}")
            raise ValueError("research_plan must be a string")
        if not isinstance(search_queries, list):
            logger.error(f"搜索查询必须是列表，当前类型: {type(search_queries)}")
            raise ValueError("search_queries must be a list")

        # 验证搜索查询列表
        if not search_queries:
            logger.error("搜索查询列表不能为空")
            raise ValueError("search_queries cannot be empty")

        # 确保所有搜索查询都是字符串
        search_queries = [str(query) for query in search_queries]

        logger.info(
            f"规划器响应解析成功，研究计划长度: {len(research_plan)}, 搜索查询数量: {len(search_queries)}"
        )
        return research_plan, search_queries

    except Exception as e:
        logger.error(f"规划器响应解析错误: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"完整错误信息: {traceback.format_exc()}")
        raise ValueError(f"Failed to parse planner response: {e}") from e
