#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web搜索工具综合测试
测试Web搜索工具的各种功能和集成
"""

import sys
import os
import unittest
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import WebSearchTestCase, skip_if_no_web_search
from src.doc_agent.tools.web_search import WebSearchTool, get_web_search_tool, get_all_tools
from core.config import settings


class WebSearchComprehensiveTest(WebSearchTestCase):
    """Web搜索工具综合测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化 Web 搜索综合测试")

    @skip_if_no_web_search
    def test_web_search_tool_creation(self):
        """测试Web搜索工具创建"""
        logger.info("测试Web搜索工具创建")

        try:
            # 直接创建工具
            tool = WebSearchTool()
            logger.info(f"WebSearchTool 直接创建成功: {type(tool).__name__}")

            # 使用工厂函数创建
            factory_tool = get_web_search_tool()
            logger.info(
                f"get_web_search_tool 工厂函数创建成功: {type(factory_tool).__name__}")

        except Exception as e:
            logger.error(f"Web搜索工具创建失败: {str(e)}")
            self.fail(f"Web搜索工具创建失败: {str(e)}")

    @skip_if_no_web_search
    def test_basic_search_functionality(self):
        """测试基础搜索功能"""
        logger.info("测试基础搜索功能")

        tool = WebSearchTool()
        query = "人工智能最新发展"

        logger.info(f"搜索查询: {query}")

        try:
            result = tool.search(query)
            logger.info(f"搜索结果长度: {len(result)} 字符")
            logger.debug(f"结果预览: {result[:200]}...")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

        except Exception as e:
            logger.error(f"基础搜索测试失败: {str(e)}")
            self.fail(f"基础搜索测试失败: {str(e)}")

    @skip_if_no_web_search
    def test_advanced_search_with_filters(self):
        """测试带过滤条件的高级搜索"""
        logger.info("测试带过滤条件的搜索")

        tool = WebSearchTool()
        query = "机器学习算法"
        params = {
            "search_depth": "basic",
            "max_results": 5,
            "include_domains": ["arxiv.org", "papers.ssrn.com"],
            "exclude_domains": ["wikipedia.org"]
        }

        logger.info(f"高级搜索: {query}")
        logger.debug(f"参数: {params}")

        try:
            result = tool.search(query, **params)
            logger.info(f"结果长度: {len(result)} 字符")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

        except Exception as e:
            logger.error(f"高级搜索测试失败: {str(e)}")
            self.fail(f"高级搜索测试失败: {str(e)}")

    @skip_if_no_web_search
    def test_error_handling(self):
        """测试错误处理"""
        logger.info("测试错误处理")

        tool = WebSearchTool()

        # 测试空查询
        try:
            result = tool.search("")
            logger.info("空查询处理正常")
        except Exception as e:
            logger.warning(f"空查询处理异常: {str(e)}")

        # 测试特殊字符
        try:
            result = tool.search("!@#$%^&*()")
            logger.info("特殊字符处理正常")
        except Exception as e:
            logger.warning(f"特殊字符处理异常: {str(e)}")

        # 测试长查询
        long_query = "这是一个非常长的查询 " * 50
        try:
            result = tool.search(long_query)
            logger.info("长查询处理正常")
        except Exception as e:
            logger.warning(f"长查询处理异常: {str(e)}")

    @skip_if_no_web_search
    def test_factory_functions(self):
        """测试工厂函数"""
        logger.info("测试工厂函数")

        try:
            # 测试 get_web_search_tool
            tool = get_web_search_tool()
            logger.info("get_web_search_tool 创建成功")

            result = tool.search("测试查询")
            logger.info(f"工厂工具搜索结果: {len(result)} 字符")

            # 测试 get_all_tools
            all_tools = get_all_tools()
            logger.info(f"get_all_tools 获取成功，共 {len(all_tools)} 个工具")

            # 检查是否包含Web搜索工具
            web_tools = [
                tool for tool in all_tools if isinstance(tool, WebSearchTool)
            ]
            logger.info(f"Web搜索工具: {web_tools}")

            self.assertGreater(len(web_tools), 0)

        except Exception as e:
            logger.error(f"工厂函数测试失败: {str(e)}")
            self.fail(f"工厂函数测试失败: {str(e)}")

    @skip_if_no_web_search
    def test_configuration_integration(self):
        """测试配置集成"""
        logger.info("测试配置集成")

        # 检查Tavily配置
        tavily_config = settings.get_model_config("tavily")
        if tavily_config:
            logger.info("Tavily配置:")
            logger.info(
                f"  API Key: {'已设置' if tavily_config.api_key else '未设置'}")
            logger.info(f"  Search Depth: {tavily_config.search_depth}")
            logger.info(f"  Max Results: {tavily_config.max_results}")

        # 检查环境变量
        import os
        tavily_key = os.getenv("TAVILY_API_KEY")
        logger.info(f"  环境变量 TAVILY_API_KEY: {'已设置' if tavily_key else '未设置'}")

        # 验证配置
        self.assertIsNotNone(tavily_config)
        self.assertIsNotNone(tavily_config.api_key)

    @skip_if_no_web_search
    def test_performance(self):
        """测试性能"""
        logger.info("测试性能")

        tool = WebSearchTool()
        query = "深度学习技术"

        import time
        start_time = time.time()

        try:
            result = tool.search(query)
            end_time = time.time()
            response_time = end_time - start_time

            logger.info(f"搜索响应时间: {response_time:.2f} 秒")
            logger.info(f"结果长度: {len(result)} 字符")

            # 性能基准测试
            self.assertLess(response_time, 30.0)  # 30秒内应该完成
            self.assertGreater(len(result), 0)

        except Exception as e:
            logger.error(f"性能测试失败: {str(e)}")
            self.fail(f"性能测试失败: {str(e)}")

    @skip_if_no_web_search
    def test_agent_integration(self):
        """测试与Agent的集成"""
        logger.info("测试与Agent的集成")

        # 模拟Agent使用场景
        tool = WebSearchTool()
        research_topic = "量子计算在金融领域的应用"

        try:
            # 模拟Agent调用
            search_result = tool.search(research_topic)

            # 模拟Agent处理结果
            mock_agent_result = {
                "topic": research_topic,
                "gathered_data": search_result,
                "search_queries": [research_topic],
                "final_document": ""
            }

            logger.info("Agent集成测试通过")
            logger.debug(f"模拟结果: {len(mock_agent_result['gathered_data'])} 字符")

            # 验证结果
            self.assertIsInstance(mock_agent_result, dict)
            self.assertIn("gathered_data", mock_agent_result)
            self.assertGreater(len(mock_agent_result["gathered_data"]), 0)

        except Exception as e:
            logger.error(f"Agent集成测试失败: {str(e)}")
            self.fail(f"Agent集成测试失败: {str(e)}")


def main():
    """主函数"""
    logger.info("Web搜索工具综合测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(WebSearchComprehensiveTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有 Web 搜索测试通过")
    else:
        logger.error("Web 搜索测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
