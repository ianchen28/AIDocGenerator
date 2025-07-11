#!/usr/bin/env python3
"""
环境变量加载器
自动查找并加载.env文件，支持多种运行位置
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_env_file():
    """
    自动查找并加载.env文件
    支持以下位置：
    1. 当前目录的.env
    2. 上级目录的.env
    3. 项目根目录的.env
    """
    # 获取当前文件所在目录
    current_dir = Path(__file__).parent

    # 可能的.env文件路径
    possible_paths = [
        current_dir / ".env",  # 当前目录
        current_dir.parent / ".env",  # 上级目录
        current_dir.parent.parent / ".env",  # 上上级目录
        current_dir.parent.parent.parent / ".env",  # 项目根目录
    ]

    # 尝试加载.env文件
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            print(f"🔧 加载环境变量文件: {env_path}")
            load_dotenv(env_path, override=True)
            loaded = True
            break

    if not loaded:
        print("⚠️  未找到.env文件，使用系统环境变量")

    # 验证关键环境变量是否加载
    key_vars = ['CHATAI_BASE_URL', 'DEEPSEEK_BASE_URL']
    for var in key_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未设置")


# 在模块导入时自动加载
load_env_file()
