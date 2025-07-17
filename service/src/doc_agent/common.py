"""
通用工具模块，提供导入路径管理和配置访问
"""

import sys
import json
from pathlib import Path
from typing import Any, Tuple, List
import re


def setup_import_paths():
    """
    设置导入路径，确保可以从任何目录运行代码
    """
    current_file = Path(__file__)

    # 查找service目录
    service_dir = None
    for parent in current_file.parents:
        if parent.name == 'service':
            service_dir = parent
            break

    if service_dir and str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    # 查找项目根目录（包含es_retrieval_core.py的目录）
    project_root = None
    for parent in current_file.parents:
        if (parent / 'es_retrieval_core.py').exists():
            project_root = parent
            break

    if project_root and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def get_settings():
    """
    动态获取settings配置
    
    Returns:
        配置对象
        
    Raises:
        ImportError: 如果无法找到配置模块
    """
    setup_import_paths()

    try:
        from core.config import settings
        return settings
    except ImportError as e:
        raise ImportError(f"无法导入配置模块: {e}. 请确保在正确的目录中运行。")


def safe_import(module_path: str, default: Any = None):
    """
    安全导入模块或对象
    
    Args:
        module_path: 模块路径，如 'core.config.settings'
        default: 导入失败时的默认值
        
    Returns:
        导入的对象或默认值
    """
    try:
        setup_import_paths()
        module_parts = module_path.split('.')
        module = __import__(module_parts[0])

        for part in module_parts[1:]:
            module = getattr(module, part)

        return module
    except (ImportError, AttributeError):
        return default


def parse_llm_json_response(response: str,
                            required_fields: List[str] = None) -> dict:
    """
    解析 LLM 的 JSON 响应
    支持 markdown 代码块包裹、各种换行和空格
    """
    try:
        response = response.strip()
        # 尝试用正则提取 markdown 代码块中的 JSON
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```",
                                     response, re.IGNORECASE)
        if code_block_match:
            response = code_block_match.group(1).strip()
        # 再尝试直接解析 JSON
        data = json.loads(response)
        if required_fields:
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
        return data
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response content: {response[:200]}...")
        raise ValueError(f"Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"Response parsing error: {e}")
        print(f"Response content: {response[:200]}...")
        raise ValueError(f"Failed to parse response: {e}")


def parse_planner_response(response: str) -> Tuple[str, List[str]]:
    """
    解析规划器的响应，提取研究计划和搜索查询
    
    Args:
        response: LLM 的原始响应
        
    Returns:
        tuple: (研究计划, 搜索查询列表)
        
    Raises:
        ValueError: 当 JSON 解析失败时
    """
    try:
        # 使用通用 JSON 解析函数
        data = parse_llm_json_response(response,
                                       ["research_plan", "search_queries"])

        research_plan = data["research_plan"]
        search_queries = data["search_queries"]

        # 处理 research_plan，如果是复杂对象则转换为字符串
        if isinstance(research_plan, dict):
            # 将复杂对象转换为结构化的字符串描述
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
            research_plan = str(research_plan)

        # 验证数据类型
        if not isinstance(research_plan, str):
            raise ValueError("research_plan must be a string")
        if not isinstance(search_queries, list):
            raise ValueError("search_queries must be a list")

        # 验证搜索查询列表
        if not search_queries:
            raise ValueError("search_queries cannot be empty")

        # 确保所有搜索查询都是字符串
        search_queries = [str(query) for query in search_queries]

        return research_plan, search_queries

    except Exception as e:
        print(f"Planner response parsing error: {e}")
        raise ValueError(f"Failed to parse planner response: {e}")
