#!/usr/bin/env python3
"""
简单的配置测试脚本
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


def test_config():
    """测试配置设置"""
    print("🔧 测试配置设置...")

    # 检查 search_config 是否存在
    if hasattr(settings, 'search_config'):
        print(f"✅ search_config 存在")
        print(f"   - max_queries: {settings.search_config.max_queries}")
        print(
            f"   - max_results_per_query: {settings.search_config.max_results_per_query}"
        )
        print(
            f"   - max_search_rounds: {settings.search_config.max_search_rounds}"
        )

        # 尝试修改配置
        settings.search_config.max_search_rounds = 2
        print(
            f"   - 修改后 max_search_rounds: {settings.search_config.max_search_rounds}"
        )
    else:
        print("❌ search_config 不存在")

    # 检查其他配置
    print("\n📊 其他配置:")
    print(f"   - 支持模型数量: {len(settings.supported_models)}")
    print(f"   - ES配置: {settings.elasticsearch_config.hosts}")

    print("\n✅ 配置测试完成")


if __name__ == "__main__":
    test_config()
