#!/usr/bin/env python3
"""
测试搜索查询改进效果
"""

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.tools import get_es_search_tool
from core.config import settings


async def test_search_queries():
    """测试不同的搜索查询"""

    # 测试查询列表
    test_queries = [
        "水电站设计和建设规范",  # 原始查询
        "水电站",  # 简化查询
        "电力",  # 更通用
        "能源",  # 最通用
        "水电站 建设",  # 组合查询
        "水电站 电力",  # 组合查询
    ]

    print("🔍 测试搜索查询效果")
    print("=" * 50)

    async with get_es_search_tool() as search_tool:
        for query in test_queries:
            print(f"\n📝 测试查询: {query}")
            try:
                result = await search_tool.search(query, top_k=3)
                if "未找到" in result:
                    print(f"❌ 无结果")
                else:
                    print(f"✅ 找到结果，长度: {len(result)} 字符")
                    print(f"   预览: {result[:100]}...")
            except Exception as e:
                print(f"❌ 搜索失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_search_queries())
