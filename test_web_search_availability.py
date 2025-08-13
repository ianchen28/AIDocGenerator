#!/usr/bin/env python3
"""
Web搜索服务可用性测试脚本
测试 web_search.py 服务的可用性和返回值字段
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加service目录到Python路径
service_path = Path(__file__).parent / "service"
sys.path.insert(0, str(service_path))

try:
    from src.doc_agent.tools.web_search import WebSearchTool, WebSearchConfig
    from src.doc_agent.core.logger import logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


class WebSearchAvailabilityTester:
    """Web搜索服务可用性测试器"""

    def __init__(self):
        self.logger = logger.bind(name="web_search_tester")
        self.test_results = []

    def log_test_result(self,
                        test_name: str,
                        success: bool,
                        details: str = "",
                        data: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "details": details,
            "data": data
        }
        self.test_results.append(result)

        status = "✅ 通过" if success else "❌ 失败"
        self.logger.info(f"{status} - {test_name}: {details}")

    async def test_config_initialization(self):
        """测试配置初始化"""
        self.logger.info("=== 测试配置初始化 ===")

        try:
            # 测试默认配置
            config = WebSearchConfig()
            self.logger.info(f"默认配置:")
            self.logger.info(f"  URL: {config.url}")
            self.logger.info(f"  Count: {config.count}")
            self.logger.info(f"  Timeout: {config.timeout}")
            self.logger.info(f"  Retries: {config.retries}")
            self.logger.info(f"  Delay: {config.delay}")
            self.logger.info(
                f"  Fetch Full Content: {config.fetch_full_content}")

            # 验证必要字段
            required_fields = [
                "url", "token", "count", "timeout", "retries", "delay"
            ]
            missing_fields = []

            for field in required_fields:
                if not hasattr(config, field) or getattr(config,
                                                         field) is None:
                    missing_fields.append(field)

            if missing_fields:
                self.log_test_result("配置初始化", False,
                                     f"缺少必要字段: {missing_fields}")
                return False
            else:
                self.log_test_result("配置初始化", True, "所有必要字段都存在")
                return True

        except Exception as e:
            self.log_test_result("配置初始化", False, f"配置初始化失败: {e}")
            return False

    async def test_web_search_tool_initialization(self):
        """测试WebSearchTool初始化"""
        self.logger.info("=== 测试WebSearchTool初始化 ===")

        try:
            # 测试默认初始化
            web_search = WebSearchTool()
            self.logger.info("WebSearchTool默认初始化成功")

            # 测试自定义配置初始化
            custom_config = {"count": 3, "timeout": 10, "retries": 2}
            web_search_custom = WebSearchTool(config=custom_config)
            self.logger.info("WebSearchTool自定义配置初始化成功")

            # 验证实例属性
            required_attrs = ["config", "web_scraper", "logger"]
            missing_attrs = []

            for attr in required_attrs:
                if not hasattr(web_search, attr):
                    missing_attrs.append(attr)

            if missing_attrs:
                self.log_test_result("WebSearchTool初始化", False,
                                     f"缺少必要属性: {missing_attrs}")
                return False
            else:
                self.log_test_result("WebSearchTool初始化", True, "所有必要属性都存在")
                return True

        except Exception as e:
            self.log_test_result("WebSearchTool初始化", False,
                                 f"WebSearchTool初始化失败: {e}")
            return False

    async def test_api_connectivity(self):
        """测试API连接性"""
        self.logger.info("=== 测试API连接性 ===")

        try:
            web_search = WebSearchTool()

            # 测试简单查询
            test_query = "Python编程"
            self.logger.info(f"测试查询: {test_query}")

            # 测试get_web_search方法
            raw_results = await web_search.get_web_search(test_query)

            if raw_results is None:
                self.log_test_result("API连接性", False, "API返回None，可能服务不可用")
                return False

            self.logger.info(f"API连接成功，返回 {len(raw_results)} 个结果")
            self.log_test_result("API连接性", True,
                                 f"成功获取 {len(raw_results)} 个结果")
            return True

        except Exception as e:
            self.log_test_result("API连接性", False, f"API连接失败: {e}")
            return False

    async def test_response_structure(self):
        """测试响应结构"""
        self.logger.info("=== 测试响应结构 ===")

        try:
            web_search = WebSearchTool()
            test_query = "人工智能"

            # 获取原始响应
            raw_results = await web_search.get_web_search(test_query)

            if not raw_results:
                self.log_test_result("响应结构", False, "无响应数据")
                return False

            # 分析第一个结果的字段结构
            first_result = raw_results[0]
            self.logger.info(f"第一个结果字段: {list(first_result.keys())}")

            # 检查必要字段
            required_fields = [
                "materialId", "docName", "url", "materialContent"
            ]
            missing_fields = []

            for field in required_fields:
                if field not in first_result:
                    missing_fields.append(field)

            if missing_fields:
                self.log_test_result("响应结构", False,
                                     f"缺少必要字段: {missing_fields}")
                return False

            # 验证字段类型
            field_types = {
                "materialId": (str, int),
                "docName": str,
                "url": str,
                "materialContent": str
            }

            type_errors = []
            for field, expected_type in field_types.items():
                if field in first_result:
                    value = first_result[field]
                    if not isinstance(value, expected_type):
                        type_errors.append(
                            f"{field}: 期望 {expected_type}, 实际 {type(value)}")

            if type_errors:
                self.log_test_result("响应结构", False, f"字段类型错误: {type_errors}")
                return False

            self.log_test_result("响应结构", True, "响应结构正确")
            return True

        except Exception as e:
            self.log_test_result("响应结构", False, f"响应结构测试失败: {e}")
            return False

    async def test_web_docs_formatting(self):
        """测试web_docs格式化"""
        self.logger.info("=== 测试web_docs格式化 ===")

        try:
            web_search = WebSearchTool()
            test_query = "机器学习"

            # 获取格式化的web_docs
            web_docs = await web_search.get_web_docs(test_query)

            if not web_docs:
                self.log_test_result("web_docs格式化", False, "无格式化文档")
                return False

            self.logger.info(f"获取到 {len(web_docs)} 个格式化文档")

            # 检查第一个文档的结构
            first_doc = web_docs[0]
            self.logger.info(f"文档字段: {list(first_doc.keys())}")

            # 检查必要字段
            required_fields = [
                "url", "doc_id", "doc_type", "domain_ids", "meta_data", "text",
                "_id", "rank"
            ]
            missing_fields = []

            for field in required_fields:
                if field not in first_doc:
                    missing_fields.append(field)

            if missing_fields:
                self.log_test_result("web_docs格式化", False,
                                     f"缺少必要字段: {missing_fields}")
                return False

            # 验证字段值
            if first_doc["doc_type"] != "text":
                self.log_test_result("web_docs格式化", False, "doc_type应该为'text'")
                return False

            if "web" not in first_doc["domain_ids"]:
                self.log_test_result("web_docs格式化", False,
                                     "domain_ids应该包含'web'")
                return False

            if not first_doc["text"]:
                self.log_test_result("web_docs格式化", False, "text字段不能为空")
                return False

            self.log_test_result("web_docs格式化", True, "文档格式化正确")
            return True

        except Exception as e:
            self.log_test_result("web_docs格式化", False, f"web_docs格式化测试失败: {e}")
            return False

    async def test_content_quality(self):
        """测试内容质量"""
        self.logger.info("=== 测试内容质量 ===")

        try:
            web_search = WebSearchTool()
            test_query = "深度学习"

            # 获取web_docs
            web_docs = await web_search.get_web_docs(test_query)

            if not web_docs:
                self.log_test_result("内容质量", False, "无文档内容")
                return False

            # 分析内容质量
            content_lengths = []
            titles = []

            for doc in web_docs:
                content_length = len(doc["text"])
                content_lengths.append(content_length)

                title = doc["meta_data"].get("docName", "")
                titles.append(title)

                self.logger.info(f"文档: {title}")
                self.logger.info(f"  内容长度: {content_length} 字符")
                self.logger.info(f"  URL: {doc['url']}")
                self.logger.info(
                    f"  是否获取完整内容: {doc.get('full_content_fetched', False)}")

            # 计算统计信息
            avg_length = sum(content_lengths) / len(content_lengths)
            min_length = min(content_lengths)
            max_length = max(content_lengths)

            self.logger.info(f"内容长度统计:")
            self.logger.info(f"  平均长度: {avg_length:.0f} 字符")
            self.logger.info(f"  最小长度: {min_length} 字符")
            self.logger.info(f"  最大长度: {max_length} 字符")

            # 评估内容质量
            quality_score = 0
            quality_issues = []

            if avg_length > 100:
                quality_score += 1
            else:
                quality_issues.append("平均内容长度过短")

            if min_length > 50:
                quality_score += 1
            else:
                quality_issues.append("存在过短内容")

            if len(set(titles)) > 1:
                quality_score += 1
            else:
                quality_issues.append("标题重复")

            if quality_score >= 2:
                self.log_test_result("内容质量", True,
                                     f"内容质量良好 (得分: {quality_score}/3)")
            else:
                self.log_test_result("内容质量", False,
                                     f"内容质量问题: {quality_issues}")

            return quality_score >= 2

        except Exception as e:
            self.log_test_result("内容质量", False, f"内容质量测试失败: {e}")
            return False

    async def test_error_handling(self):
        """测试错误处理"""
        self.logger.info("=== 测试错误处理 ===")

        try:
            web_search = WebSearchTool()

            # 测试空查询
            empty_result = await web_search.get_web_search("")
            if empty_result is None:
                self.log_test_result("错误处理-空查询", True, "正确处理空查询")
            else:
                self.log_test_result("错误处理-空查询", False, "空查询应该返回None")

            # 测试特殊字符查询
            special_query = "!@#$%^&*()"
            special_result = await web_search.get_web_search(special_query)
            # 特殊字符查询可能返回结果或None，都是可接受的
            self.log_test_result("错误处理-特殊字符", True, "特殊字符查询处理正常")

            return True

        except Exception as e:
            self.log_test_result("错误处理", False, f"错误处理测试失败: {e}")
            return False

    async def test_performance(self):
        """测试性能"""
        self.logger.info("=== 测试性能 ===")

        try:
            web_search = WebSearchTool()
            test_query = "Python编程"

            # 测试响应时间
            start_time = time.time()
            results = await web_search.get_web_search(test_query)
            end_time = time.time()

            response_time = end_time - start_time
            self.logger.info(f"响应时间: {response_time:.2f} 秒")

            if response_time < 10:  # 10秒内响应
                self.log_test_result("性能测试", True,
                                     f"响应时间: {response_time:.2f}秒")
                return True
            else:
                self.log_test_result("性能测试", False,
                                     f"响应时间过长: {response_time:.2f}秒")
                return False

        except Exception as e:
            self.log_test_result("性能测试", False, f"性能测试失败: {e}")
            return False

    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results
                           if result["success"])
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests":
                total_tests,
                "passed_tests":
                passed_tests,
                "failed_tests":
                failed_tests,
                "success_rate":
                (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "timestamp":
                time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "test_results": self.test_results,
            "recommendations": []
        }

        # 生成建议
        if failed_tests > 0:
            report["recommendations"].append("存在失败的测试，请检查相关功能")

        if passed_tests == total_tests:
            report["recommendations"].append("所有测试通过，服务运行正常")

        return report

    def save_test_report(self,
                         report: Dict[str, Any],
                         filename: str = "web_search_test_report.json"):
        """保存测试报告"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"测试报告已保存到: {filename}")
        except Exception as e:
            self.logger.error(f"保存测试报告失败: {e}")

    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始Web搜索服务可用性测试")

        # 运行各项测试
        await self.test_config_initialization()
        await self.test_web_search_tool_initialization()
        await self.test_api_connectivity()
        await self.test_response_structure()
        await self.test_web_docs_formatting()
        await self.test_content_quality()
        await self.test_error_handling()
        await self.test_performance()

        # 生成报告
        report = self.generate_test_report()

        # 打印摘要
        summary = report["summary"]
        self.logger.info("=" * 50)
        self.logger.info("测试摘要:")
        self.logger.info(f"  总测试数: {summary['total_tests']}")
        self.logger.info(f"  通过测试: {summary['passed_tests']}")
        self.logger.info(f"  失败测试: {summary['failed_tests']}")
        self.logger.info(f"  成功率: {summary['success_rate']:.1f}%")
        self.logger.info("=" * 50)

        # 保存报告
        self.save_test_report(report)

        return report


async def main():
    """主函数"""
    # 配置日志
    logger.add("logs/web_search_availability_test.log",
               rotation="1 day",
               retention="7 days",
               level="INFO")

    # 创建测试器并运行测试
    tester = WebSearchAvailabilityTester()
    report = await tester.run_all_tests()

    # 返回测试结果
    success_rate = report["summary"]["success_rate"]
    if success_rate >= 80:
        print(f"✅ 测试完成，成功率: {success_rate:.1f}%")
        return 0
    else:
        print(f"❌ 测试完成，成功率: {success_rate:.1f}%，存在问题")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        sys.exit(1)
