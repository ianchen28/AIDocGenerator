#!/usr/bin/env python3
"""
统一环境变量加载模块
确保所有运行文件都能自动加载 .env 文件
"""

from dotenv import find_dotenv, load_dotenv
from loguru import logger


def setup_environment():
    """
    统一设置环境变量
    在所有运行文件的最开始调用此函数
    """
    logger.info("开始设置环境变量")

    # 查找并加载 .env 文件
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path, override=True)
        logger.info(f"环境变量已加载: {env_path}")
    else:
        logger.warning("未找到 .env 文件")

    logger.info("环境变量设置完成")
    return True


# 自动执行环境设置
setup_environment()
