#!/usr/bin/env python3
"""
直接测试配置的脚本
"""

import os
import sys
from pathlib import Path

# --- 路径设置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from service.core.config import settings


def test_direct_config():
    """直接测试配置"""
    print("🔧 直接测试配置...")

    # 设置配置
    settings.search_config.max_search_rounds = 2
    print(
        f"✅ 设置 max_search_rounds = {settings.search_config.max_search_rounds}")

    # 模拟节点中的配置读取逻辑
    search_config = getattr(settings, 'search_config', None)
    if search_config and hasattr(search_config, 'max_search_rounds'):
        max_search_rounds = search_config.max_search_rounds
        print(f"✅ 节点读取到 max_search_rounds = {max_search_rounds}")
    else:
        max_search_rounds = 5
        print(f"❌ 使用默认值 max_search_rounds = {max_search_rounds}")

    # 定义查询列表
    all_possible_queries = [
        "量子计算的基本原理 概述",
        "量子计算的基本原理 主要内容",
        "量子计算的基本原理 关键要点",
        "量子计算的基本原理 最新发展",
        "量子计算的基本原理 重要性",
    ]

    # 根据配置选择查询数量
    initial_queries = all_possible_queries[:max_search_rounds]

    print(f"📊 配置搜索轮数: {max_search_rounds}，实际执行: {len(initial_queries)} 轮")
    print(f"🔍 查询列表: {initial_queries}")

    return max_search_rounds, initial_queries


if __name__ == "__main__":
    test_direct_config()
