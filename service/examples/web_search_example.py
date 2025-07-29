#!/usr/bin/env python3
"""
Web Search 工具使用示例
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
src_dir = service_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 设置环境
from core.env_loader import setup_environment
from core.logging_config import setup_logging
from core.config import settings

setup_environment()
setup_logging(settings)


async def main():
    """主函数"""
    from src.doc_agent.tools.web_search import WebSearchTool

    # 创建 web search 工具
    web_search = WebSearchTool()

    # 测试查询
    query = "人工智能技术发展"
    print(f"🔍 搜索查询: {query}")

    # 异步搜索
    result = await web_search.search_async(query)
    print(f"\n📋 搜索结果:\n{result}")

    # 获取结构化文档
    print(f"\n📄 获取结构化文档...")
    docs = await web_search.get_web_docs(query)
    print(f"✅ 获取到 {len(docs)} 个文档")

    if docs:
        print(f"\n📊 文档统计:")
        total_chars = sum(len(doc['text']) for doc in docs)
        avg_chars = total_chars / len(docs)
        full_content_count = sum(1 for doc in docs
                                 if doc.get('full_content_fetched', False))

        print(f"  总字符数: {total_chars:,}")
        print(f"  平均字符数: {avg_chars:.0f}")
        print(f"  获取完整内容的文档数: {full_content_count}/{len(docs)}")


if __name__ == "__main__":
    asyncio.run(main())
