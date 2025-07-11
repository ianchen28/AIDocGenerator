#!/usr/bin/env python3
"""
测试aiohttp警告的来源
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置路径
current_dir = Path(__file__).parent
service_dir = current_dir.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import setup_paths

setup_paths()

from src.doc_agent.tools.es_search import ESSearchTool
from src.doc_agent.tools.web_search import WebSearchTool
from src.doc_agent.llm_clients.providers import GeminiClient, DeepSeekClient
from core.config import AgentConfig


async def test_aiohttp_warnings():
    """测试aiohttp警告的来源"""
    print("🔍 检查aiohttp警告来源...")

    try:
        # 测试ES搜索工具
        print("1. 测试ES搜索工具...")
        config = AgentConfig()
        es_tool = ESSearchTool(hosts=config.elasticsearch.hosts,
                               username=config.elasticsearch.username,
                               password=config.elasticsearch.password)

        # 确保初始化
        await es_tool._ensure_initialized()

        # 执行搜索
        result = await es_tool.search("测试", top_k=1)
        print(f"ES搜索结果长度: {len(result)}")

        # 关闭连接
        await es_tool.close()
        print("✅ ES搜索工具测试完成")

    except Exception as e:
        print(f"❌ ES搜索工具测试失败: {e}")

    try:
        # 测试Web搜索工具
        print("2. 测试Web搜索工具...")
        web_tool = WebSearchTool()
        result = web_tool.search("测试")
        print(f"Web搜索结果长度: {len(result)}")
        print("✅ Web搜索工具测试完成")

    except Exception as e:
        print(f"❌ Web搜索工具测试失败: {e}")

    try:
        # 测试LLM客户端
        print("3. 测试LLM客户端...")
        config = AgentConfig()

        # 测试Gemini客户端
        if config.llm.gemini.api_key:
            gemini_client = GeminiClient(api_key=config.llm.gemini.api_key,
                                         base_url=config.llm.gemini.base_url)
            result = gemini_client.invoke("你好", max_tokens=10)
            print(f"Gemini响应长度: {len(result)}")
            print("✅ Gemini客户端测试完成")

    except Exception as e:
        print(f"❌ LLM客户端测试失败: {e}")

    print("🔍 aiohttp警告检查完成")


if __name__ == "__main__":
    asyncio.run(test_aiohttp_warnings())
