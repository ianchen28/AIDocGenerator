#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试基础架构
支持 LLM、ES、WebSearch、Node、Graph 等多种测试类型
"""

import sys
import os
import asyncio
import unittest
from pathlib import Path
from typing import Optional, Dict, Any, List
from unittest.mock import Mock, patch

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 统一环境变量加载
from core.env_loader import setup_environment

# 导入配置
from core.config import settings


class TestEnvironment:
    """测试环境管理类"""

    def __init__(self):
        self.es_available = False
        self.llm_available = False
        self.web_search_available = False
        self._check_services()

    def _check_services(self):
        """检查各种服务是否可用"""
        # 检查 ES 服务
        try:
            from src.doc_agent.tools.es_service import ESService
            es_config = settings.elasticsearch_config
            # 简单检查配置是否完整
            if es_config.hosts and es_config.username and es_config.password:
                self.es_available = True
                print("✅ ES 服务配置可用")
            else:
                print("⚠️  ES 服务配置不完整")
        except Exception as e:
            print(f"❌ ES 服务检查失败: {e}")

        # 检查 LLM 服务
        try:
            from src.doc_agent.llm_clients import get_llm_client
            # 检查是否有可用的 LLM 配置
            if settings.supported_models:
                self.llm_available = True
                print("✅ LLM 服务配置可用")
            else:
                print("⚠️  LLM 服务配置不完整")
        except Exception as e:
            print(f"❌ LLM 服务检查失败: {e}")

        # 检查 WebSearch 服务
        try:
            from src.doc_agent.tools.web_search import WebSearchTool
            # 检查 Tavily 配置
            if settings.tavily_config.api_key:
                self.web_search_available = True
                print("✅ WebSearch 服务配置可用")
            else:
                print("⚠️  WebSearch 服务配置不完整")
        except Exception as e:
            print(f"❌ WebSearch 服务检查失败: {e}")


class BaseTestCase(unittest.TestCase):
    """基础测试类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类环境"""
        cls.env = TestEnvironment()
        print(f"\n{'='*50}")
        print(f"测试环境检查:")
        print(f"  ES 服务: {'✅' if cls.env.es_available else '❌'}")
        print(f"  LLM 服务: {'✅' if cls.env.llm_available else '❌'}")
        print(
            f"  WebSearch 服务: {'✅' if cls.env.web_search_available else '❌'}")
        print(f"{'='*50}")

    def setUp(self):
        """设置每个测试用例"""
        pass

    def tearDown(self):
        """清理每个测试用例"""
        pass


class LLMTestCase(BaseTestCase):
    """LLM 测试基类"""

    def setUp(self):
        super().setUp()
        if not self.env.llm_available:
            self.skipTest("LLM 服务不可用")

    def get_llm_client(self, model_key: str = "moonshot_k2_0711_preview"):
        """获取 LLM 客户端"""
        from src.doc_agent.llm_clients import get_llm_client
        return get_llm_client(model_key)


class ESTestCase(BaseTestCase):
    """ES 测试基类"""

    def setUp(self):
        super().setUp()
        if not self.env.es_available:
            self.skipTest("ES 服务不可用")

    async def get_es_search_tool(self):
        """获取 ES 搜索工具"""
        from src.doc_agent.tools import get_es_search_tool
        return await get_es_search_tool().__aenter__()

    async def get_es_service(self):
        """获取 ES 服务"""
        from src.doc_agent.tools.es_service import ESService
        es_config = settings.elasticsearch_config
        return await ESService(hosts=es_config.hosts,
                               username=es_config.username,
                               password=es_config.password,
                               timeout=es_config.timeout).__aenter__()


class WebSearchTestCase(BaseTestCase):
    """WebSearch 测试基类"""

    def setUp(self):
        super().setUp()
        if not self.env.web_search_available:
            self.skipTest("WebSearch 服务不可用")

    def get_web_search_tool(self):
        """获取 WebSearch 工具"""
        from src.doc_agent.tools import get_web_search_tool
        return get_web_search_tool()


class NodeTestCase(BaseTestCase):
    """Node 测试基类"""

    def setUp(self):
        super().setUp()
        if not self.env.llm_available:
            self.skipTest("LLM 服务不可用")

    def get_llm_client(self, model_key: str = "moonshot_k2_0711_preview"):
        """获取 LLM 客户端"""
        from src.doc_agent.llm_clients import get_llm_client
        return get_llm_client(model_key)

    def get_mock_state(self, **kwargs) -> Dict[str, Any]:
        """获取模拟状态"""
        default_state = {
            "messages": [],
            "topic": "测试主题",
            "research_plan": "",
            "search_queries": [],
            "gathered_data": "",
            "final_document": ""
        }
        default_state.update(kwargs)
        return default_state

    def get_mock_llm_client(self):
        """获取模拟 LLM 客户端"""
        mock_client = Mock()
        mock_client.invoke.return_value = "模拟 LLM 响应"
        return mock_client


class GraphTestCase(BaseTestCase):
    """Graph 测试基类"""

    def setUp(self):
        super().setUp()
        if not self.env.llm_available:
            self.skipTest("LLM 服务不可用")

    def get_test_graph(self):
        """获取测试图"""
        from core.container import container
        return container.graph

    async def run_graph_test(self, initial_input: Dict[str, Any]):
        """运行图测试"""
        graph = self.get_test_graph()
        results = []
        async for step in graph.astream(initial_input):
            results.append(step)
        return results


# 测试装饰器
def skip_if_no_es(func):
    """如果 ES 不可用则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'env') or not self.env.es_available:
            self.skipTest("ES 服务不可用")
        return func(self, *args, **kwargs)

    return wrapper


def skip_if_no_llm(func):
    """如果 LLM 不可用则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'env') or not self.env.llm_available:
            self.skipTest("LLM 服务不可用")
        return func(self, *args, **kwargs)

    return wrapper


def skip_if_no_web_search(func):
    """如果 WebSearch 不可用则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'env') or not self.env.web_search_available:
            self.skipTest("WebSearch 服务不可用")
        return func(self, *args, **kwargs)

    return wrapper


def skip_if_no_reranker(func):
    """如果 Reranker 不可用则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'env') or not self.env.llm_available:
            self.skipTest("Reranker 服务不可用")
        return func(self, *args, **kwargs)

    return wrapper


# 异步测试支持
def async_test(func):
    """异步测试装饰器"""

    def wrapper(self, *args, **kwargs):
        return asyncio.run(func(self, *args, **kwargs))

    return wrapper


# 测试工具函数
def create_mock_embedding_response(dim: int = 1536) -> str:
    """创建模拟的 embedding 响应"""
    import json
    vector = [0.1] * dim
    return json.dumps([vector])


def create_mock_es_response() -> str:
    """创建模拟的 ES 响应"""
    return """搜索查询: 测试查询
找到 3 个相关文档:

1. 测试文档1.pdf
   评分: 1.5
   原始内容: 这是一个测试文档的内容...

2. 测试文档2.pdf
   评分: 1.3
   原始内容: 这是另一个测试文档的内容...

3. 测试文档3.pdf
   评分: 1.1
   原始内容: 这是第三个测试文档的内容...
"""
