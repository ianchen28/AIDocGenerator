#!/usr/bin/env python3
"""
测试配置持久性的脚本
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


def test_config_persistence():
    """测试配置持久性"""
    print("🔧 测试配置持久性...")

    # 第一次设置
    print(
        f"📝 原始配置: max_search_rounds = {settings.search_config.max_search_rounds}"
    )

    # 设置新值
    settings.search_config.max_search_rounds = 2
    print(
        f"✅ 设置后: max_search_rounds = {settings.search_config.max_search_rounds}"
    )

    # 模拟导入其他模块（可能重置配置）
    print("🔄 模拟导入其他模块...")
    try:
        from service.core.container import container
        print("✅ 容器导入成功")
        print(
            f"📊 容器导入后配置: max_search_rounds = {settings.search_config.max_search_rounds}"
        )
    except Exception as e:
        print(f"❌ 容器导入失败: {e}")

    # 再次检查配置
    print(
        f"🔍 最终配置: max_search_rounds = {settings.search_config.max_search_rounds}"
    )

    # 重新设置配置
    settings.search_config.max_search_rounds = 2
    print(
        f"🔄 重新设置: max_search_rounds = {settings.search_config.max_search_rounds}"
    )


if __name__ == "__main__":
    test_config_persistence()
