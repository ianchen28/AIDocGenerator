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


def setup_environment():
    """
    统一设置环境变量
    在所有运行文件的最开始调用此函数
    """
    # 查找并加载 .env 文件
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path, override=True)
        print(f"✅ 环境变量已加载: {env_path}")
    else:
        print("⚠️  未找到 .env 文件")

    # 设置 Python 路径
    current_file = Path(__file__)
    service_dir = current_file.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    return True


# 自动执行环境设置
setup_environment()
