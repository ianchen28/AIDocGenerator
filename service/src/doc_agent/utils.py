"""
通用工具模块，提供导入路径管理和配置访问
"""

import sys
from pathlib import Path
from typing import Any


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
