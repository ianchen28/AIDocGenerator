#!/usr/bin/env python3
"""
Web搜索测试使用示例
展示如何在实际项目中使用web搜索可用性测试
"""

import asyncio
import sys
from pathlib import Path

# 添加根目录到Python路径
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# 导入测试器
from test_web_search_availability import WebSearchAvailabilityTester
from src.doc_agent.core.logger import logger


async def example_basic_test():
    """基本测试示例"""
    print("=== 基本测试示例 ===")

    # 创建测试器
    tester = WebSearchAvailabilityTester()

    # 运行所有测试
    report = await tester.run_all_tests()

    # 检查结果
    success_rate = report["summary"]["success_rate"]
    print(f"测试成功率: {success_rate:.1f}%")

    if success_rate >= 80:
        print("✅ 服务运行正常")
    else:
        print("❌ 服务存在问题，需要检查")

    return report


async def example_selective_test():
    """选择性测试示例"""
    print("\n=== 选择性测试示例 ===")

    tester = WebSearchAvailabilityTester()

    # 只运行特定的测试
    print("1. 测试配置初始化...")
    await tester.test_config_initialization()

    print("2. 测试API连接性...")
    await tester.test_api_connectivity()

    print("3. 测试响应结构...")
    await tester.test_response_structure()

    # 生成报告
    report = tester.generate_test_report()
    print(f"选择性测试成功率: {report['summary']['success_rate']:.1f}%")

    return report


async def example_custom_test():
    """自定义测试示例"""
    print("\n=== 自定义测试示例 ===")

    from src.doc_agent.tools.web_search import WebSearchTool

    # 创建自定义配置的搜索工具
    custom_config = {
        "count": 3,  # 只获取3个结果
        "timeout": 10,  # 10秒超时
        "retries": 2,  # 2次重试
        "fetch_full_content": False  # 不获取完整内容
    }

    web_search = WebSearchTool(config=custom_config)

    # 测试特定查询
    test_queries = ["Python异步编程", "机器学习算法", "深度学习框架"]

    for query in test_queries:
        print(f"\n测试查询: {query}")
        try:
            # 获取原始结果
            raw_results = await web_search.get_web_search(query)
            if raw_results:
                print(f"  ✅ 获取到 {len(raw_results)} 个结果")

                # 显示第一个结果的基本信息
                if raw_results:
                    first_result = raw_results[0]
                    title = first_result.get('docName', 'Unknown')
                    url = first_result.get('url', 'Unknown')
                    content_length = len(
                        first_result.get('materialContent', ''))
                    print(f"  第一个结果: {title}")
                    print(f"  URL: {url}")
                    print(f"  内容长度: {content_length} 字符")
            else:
                print(f"  ❌ 无结果")

        except Exception as e:
            print(f"  ❌ 查询失败: {e}")


async def example_monitoring_test():
    """监控测试示例"""
    print("\n=== 监控测试示例 ===")

    tester = WebSearchAvailabilityTester()

    # 模拟定期监控
    import time

    for i in range(3):  # 运行3次监控
        print(f"\n第 {i+1} 次监控检查...")

        # 只运行关键测试
        await tester.test_api_connectivity()
        await tester.test_performance()

        # 生成简单报告
        report = tester.generate_test_report()
        success_rate = report["summary"]["success_rate"]

        print(f"监控结果: {success_rate:.1f}% 通过")

        if success_rate < 100:
            print("⚠️  发现问题，需要关注")
        else:
            print("✅ 服务状态正常")

        # 等待一段时间再进行下一次监控
        if i < 2:  # 不是最后一次
            print("等待5秒后进行下一次检查...")
            await asyncio.sleep(5)


def example_offline_analysis():
    """离线分析示例"""
    print("\n=== 离线分析示例 ===")

    # 读取之前生成的测试报告
    import json

    try:
        with open("web_search_test_report.json", "r", encoding="utf-8") as f:
            report = json.load(f)

        print("分析测试报告:")
        summary = report["summary"]
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  通过测试: {summary['passed_tests']}")
        print(f"  失败测试: {summary['failed_tests']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")

        # 分析失败的测试
        failed_tests = [
            result for result in report["test_results"]
            if not result["success"]
        ]
        if failed_tests:
            print("\n失败的测试:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        else:
            print("\n所有测试都通过了！")

        # 分析建议
        if report["recommendations"]:
            print("\n建议:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")

    except FileNotFoundError:
        print("未找到测试报告文件，请先运行测试")


async def main():
    """主函数"""
    print("Web搜索测试使用示例")
    print("=" * 50)

    # 配置日志
    logger.add("logs/web_search_example.log",
               rotation="1 day",
               retention="7 days",
               level="INFO")

    try:
        # 运行各种示例
        await example_basic_test()
        await example_selective_test()
        await example_custom_test()
        await example_monitoring_test()
        example_offline_analysis()

        print("\n" + "=" * 50)
        print("所有示例运行完成")

    except Exception as e:
        print(f"示例运行过程中发生错误: {e}")
        logger.error(f"示例运行错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
