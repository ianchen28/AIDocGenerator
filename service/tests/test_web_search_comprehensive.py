#!/usr/bin/env python3
"""
综合Web搜索测试文件
包含WebSearchTool、Tavily搜索等所有Web搜索相关测试
"""

import asyncio
import logging

from test_base import setup_paths

# 设置测试环境
setup_paths()

from src.doc_agent.tools.web_search import WebSearchTool
from src.doc_agent.tools import get_web_search_tool, get_all_tools
from core.config import settings

# 配置日志
logger = logging.getLogger(__name__)


class ComprehensiveWebSearchTest:
    """综合Web搜索测试类"""

    def __init__(self):
        self.web_search_tool = None
        self.tavily_config = settings.tavily_config

    def setup(self):
        """初始化测试环境"""
        print("🔧 初始化Web搜索测试环境...")

        # 创建Web搜索工具
        self.web_search_tool = WebSearchTool()

        print("✅ 测试环境初始化完成")

    def test_web_search_tool_creation(self):
        """测试Web搜索工具创建"""
        print("\n=== 测试Web搜索工具创建 ===")

        try:
            # 测试直接创建
            tool = WebSearchTool()
            print("✅ WebSearchTool 直接创建成功")
            print(f"工具类型: {type(tool).__name__}")

            # 测试工厂函数
            factory_tool = get_web_search_tool()
            print("✅ get_web_search_tool 工厂函数创建成功")
            print(f"工厂工具类型: {type(factory_tool).__name__}")

            return True

        except Exception as e:
            print(f"❌ Web搜索工具创建失败: {str(e)}")
            return False

    def test_basic_search(self):
        """测试基础搜索功能"""
        print("\n=== 测试基础搜索功能 ===")

        try:
            # 测试基本搜索
            test_queries = ["人工智能最新发展", "Python编程教程", "机器学习算法", "深度学习技术"]

            for query in test_queries:
                print(f"\n📝 搜索查询: {query}")
                print("-" * 50)

                try:
                    result = self.web_search_tool.search(query)
                    print(f"搜索结果长度: {len(result)} 字符")
                    print(f"结果预览: {result[:300]}...")
                    print("✅ 搜索成功")

                except Exception as e:
                    print(f"❌ 搜索失败: {str(e)}")

            return True

        except Exception as e:
            print(f"❌ 基础搜索测试失败: {str(e)}")
            return False

    def test_search_with_filters(self):
        """测试带过滤条件的搜索"""
        print("\n=== 测试带过滤条件的搜索 ===")

        try:
            # 测试不同的搜索参数
            search_params = [{
                "query": "Python教程",
                "max_results": 3
            }, {
                "query": "机器学习",
                "search_depth": "basic"
            }, {
                "query":
                "深度学习",
                "include_domains": ["github.com", "stackoverflow.com"]
            }]

            for params in search_params:
                query = params["query"]
                print(f"\n📝 高级搜索: {query}")
                print(f"参数: {params}")

                try:
                    result = self.web_search_tool.search(query)
                    print(f"结果长度: {len(result)} 字符")
                    print("✅ 高级搜索成功")

                except Exception as e:
                    print(f"❌ 高级搜索失败: {str(e)}")

            return True

        except Exception as e:
            print(f"❌ 过滤搜索测试失败: {str(e)}")
            return False

    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")

        try:
            # 测试空查询
            result = self.web_search_tool.search("")
            print("空查询处理正常")

            # 测试特殊字符
            result = self.web_search_tool.search("!@#$%^&*()")
            print("特殊字符处理正常")

            # 测试长查询
            long_query = "这是一个非常长的搜索查询" * 10
            result = self.web_search_tool.search(long_query)
            print("长查询处理正常")

            return True

        except Exception as e:
            print(f"❌ 错误处理测试失败: {str(e)}")
            return False

    def test_factory_functions(self):
        """测试工厂函数"""
        print("\n=== 测试工厂函数 ===")

        try:
            # 测试get_web_search_tool
            web_tool = get_web_search_tool()
            print("✅ get_web_search_tool 创建成功")

            # 测试搜索
            result = web_tool.search("工厂函数测试")
            print(f"工厂工具搜索结果: {len(result)} 字符")

            # 测试get_all_tools
            all_tools = get_all_tools()
            print(f"✅ get_all_tools 获取成功，共 {len(all_tools)} 个工具")

            # 检查是否包含Web搜索工具
            web_tools = [
                name for name in all_tools.keys()
                if 'web' in name.lower() or 'search' in name.lower()
            ]
            if web_tools:
                print(f"Web搜索工具: {web_tools}")
            else:
                print("⚠️  未在get_all_tools中找到Web搜索工具")

            return True

        except Exception as e:
            print(f"❌ 工厂函数测试失败: {str(e)}")
            return False

    def test_config_integration(self):
        """测试配置集成"""
        print("\n=== 测试配置集成 ===")

        try:
            # 检查Tavily配置
            print("📋 Tavily配置:")
            print(
                f"  API Key: {'已设置' if self.tavily_config.api_key else '未设置'}")
            print(f"  Search Depth: {self.tavily_config.search_depth}")
            print(f"  Max Results: {self.tavily_config.max_results}")

            # 检查环境变量
            import os
            tavily_key = os.getenv('TAVILY_API_KEY')
            print(f"  环境变量 TAVILY_API_KEY: {'已设置' if tavily_key else '未设置'}")

            return True

        except Exception as e:
            print(f"❌ 配置集成测试失败: {str(e)}")
            return False

    def test_performance(self):
        """测试性能"""
        print("\n=== 测试性能 ===")

        try:
            import time

            # 测试搜索响应时间
            test_query = "Python编程"

            start_time = time.time()
            result = self.web_search_tool.search(test_query)
            end_time = time.time()

            response_time = end_time - start_time
            print(f"搜索响应时间: {response_time:.2f} 秒")
            print(f"结果长度: {len(result)} 字符")

            if response_time < 10:  # 10秒内响应
                print("✅ 性能测试通过")
                return True
            else:
                print("⚠️  响应时间较长，可能需要优化")
                return False

        except Exception as e:
            print(f"❌ 性能测试失败: {str(e)}")
            return False

    def test_integration_with_agent(self):
        """测试与Agent的集成"""
        print("\n=== 测试与Agent的集成 ===")

        try:
            # 模拟Agent使用场景
            def mock_agent_node(state, search_tool):
                """模拟Agent节点"""
                query = state.get("search_query", "默认查询")
                results = search_tool.search(query)
                return {"gathered_data": results}

            # 测试模拟场景
            mock_state = {"search_query": "人工智能发展"}
            result = mock_agent_node(mock_state, self.web_search_tool)

            print("✅ Agent集成测试通过")
            print(f"模拟结果: {len(result['gathered_data'])} 字符")

            return True

        except Exception as e:
            print(f"❌ Agent集成测试失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始综合Web搜索测试...")

        try:
            self.setup()

            test_results = []

            # 运行各项测试
            test_results.append(("工具创建", self.test_web_search_tool_creation()))
            test_results.append(("基础搜索", self.test_basic_search()))
            test_results.append(("过滤搜索", self.test_search_with_filters()))
            test_results.append(("错误处理", self.test_error_handling()))
            test_results.append(("工厂函数", self.test_factory_functions()))
            test_results.append(("配置集成", self.test_config_integration()))
            test_results.append(("性能测试", self.test_performance()))
            test_results.append(
                ("Agent集成", self.test_integration_with_agent()))

            # 显示测试结果
            print("\n" + "=" * 50)
            print("📊 测试结果汇总:")
            print("=" * 50)

            passed = 0
            for test_name, result in test_results:
                status = "✅ 通过" if result else "❌ 失败"
                print(f"{test_name}: {status}")
                if result:
                    passed += 1

            print(f"\n总计: {passed}/{len(test_results)} 项测试通过")

            if passed == len(test_results):
                print("🎉 所有测试通过！")
            else:
                print("⚠️  部分测试失败，请检查配置和网络连接")

        except Exception as e:
            print(f"❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主测试函数"""
    tester = ComprehensiveWebSearchTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
