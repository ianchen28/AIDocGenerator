#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一环境变量加载模块
确保所有运行文件都能自动加载 .env 文件
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
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

    # 设置 Python 路径
    current_file = Path(__file__)
    service_dir = current_file.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))
        logger.debug(f"已添加服务目录到 Python 路径: {service_dir}")
    else:
        logger.debug("服务目录已在 Python 路径中")

    logger.info("环境变量设置完成")
    return True


# 自动执行环境设置
setup_environment()
