#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基础类
提供统一的测试基础设施
"""

import os
import sys
import unittest
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.config import settings


class TestEnvironment:
    """测试环境检查"""

    def __init__(self):
        self.es_available = self._check_es_service()
        self.llm_available = self._check_llm_service()
        self.web_search_available = self._check_web_search_service()

    def _check_es_service(self) -> bool:
        """检查ES服务是否可用"""
        try:
            es_config = settings.elasticsearch_config
            if es_config and es_config.hosts:
                logger.debug("ES 服务配置可用")
                return True
            else:
                logger.warning("ES 服务配置不完整")
                return False
        except Exception as e:
            logger.error(f"ES 服务检查失败: {e}")
            return False

    def _check_llm_service(self) -> bool:
        """检查LLM服务是否可用"""
        try:
            # 检查是否有可用的LLM配置
            available_models = settings.get_available_models()
            if available_models:
                logger.debug("LLM 服务配置可用")
                return True
            else:
                logger.warning("LLM 服务配置不完整")
                return False
        except Exception as e:
            logger.error(f"LLM 服务检查失败: {e}")
            return False

    def _check_web_search_service(self) -> bool:
        """检查Web搜索服务是否可用"""
        try:
            tavily_config = settings.get_model_config("tavily")
            if tavily_config and tavily_config.api_key:
                logger.debug("WebSearch 服务配置可用")
                return True
            else:
                logger.warning("WebSearch 服务配置不完整")
                return False
        except Exception as e:
            logger.error(f"WebSearch 服务检查失败: {e}")
            return False


class TestBase(unittest.TestCase):
    """测试基类"""

    @classmethod
    def setUpClass(cls):
        """类级别的测试前准备"""
        super().setUpClass()
        cls.env = TestEnvironment()

        logger.info("测试环境检查:")
        logger.info(f"  ES 服务: {'✅' if cls.env.es_available else '❌'}")
        logger.info(f"  LLM 服务: {'✅' if cls.env.llm_available else '❌'}")
        logger.info(
            f"  WebSearch 服务: {'✅' if cls.env.web_search_available else '❌'}")


class LLMTestCase(TestBase):
    """LLM相关测试基类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化 LLM 测试")


class ESTestCase(TestBase):
    """ES相关测试基类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化 ES 测试")


class WebSearchTestCase(TestBase):
    """Web搜索相关测试基类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化 Web 搜索测试")


class NodeTestCase(TestBase):
    """节点相关测试基类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化节点测试")

    def get_llm_client(self, model_key: str):
        """获取LLM客户端"""
        try:
            from src.doc_agent.llm_clients import get_llm_client
            return get_llm_client(model_key)
        except Exception as e:
            logger.error(f"获取LLM客户端失败: {e}")
            return None


# 装饰器函数
def skip_if_no_llm(func):
    """如果没有LLM服务则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not self.env.llm_available:
            logger.warning(f"跳过测试 {func.__name__}: LLM服务不可用")
            return
        return func(self, *args, **kwargs)

    return wrapper


def skip_if_no_es(func):
    """如果没有ES服务则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not self.env.es_available:
            logger.warning(f"跳过测试 {func.__name__}: ES服务不可用")
            return
        return func(self, *args, **kwargs)

    return wrapper


def skip_if_no_web_search(func):
    """如果没有Web搜索服务则跳过测试"""

    def wrapper(self, *args, **kwargs):
        if not self.env.web_search_available:
            logger.warning(f"跳过测试 {func.__name__}: Web搜索服务不可用")
            return
        return func(self, *args, **kwargs)

    return wrapper


def skip_if_no_reranker(func):
    """如果没有重排序服务则跳过测试"""

    def wrapper(self, *args, **kwargs):
        try:
            reranker_config = settings.get_model_config("reranker")
            if not reranker_config or not reranker_config.api_key:
                logger.warning(f"跳过测试 {func.__name__}: 重排序服务不可用")
                return
        except Exception:
            logger.warning(f"跳过测试 {func.__name__}: 重排序服务不可用")
            return
        return func(self, *args, **kwargs)

    return wrapper


# 工具函数
def setup_paths():
    """设置Python路径"""
    current_file = Path(__file__)
    service_dir = current_file.parent.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))


def load_env_vars():
    """加载环境变量"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.debug("环境变量加载成功")
    except ImportError:
        logger.warning("dotenv未安装，跳过环境变量加载")
    except Exception as e:
        logger.error(f"环境变量加载失败: {e}")


# 初始化
setup_paths()
load_env_vars()
