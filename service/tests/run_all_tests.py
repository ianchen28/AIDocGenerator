#!/usr/bin/env python3
"""
测试运行器
批量运行所有测试文件
"""

import sys
import os
import subprocess
import time
from pathlib import Path

from test_base import TestBase, setup_paths

# 设置测试环境
setup_paths()


def run_test_file(test_file: str) -> bool:
    """运行单个测试文件"""
    print(f"\n{'='*60}")
    print(f"🚀 运行测试: {test_file}")
    print(f"{'='*60}")

    try:
        # 使用subprocess运行测试文件
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if result.returncode == 0:
            print("✅ 测试通过")
            print(result.stdout)
            return True
        else:
            print("❌ 测试失败")
            print(result.stdout)
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("⏰ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 运行测试时出错: {str(e)}")
        return False


def run_all_tests():
    """运行所有测试文件"""
    print("🚀 开始运行所有测试...")

    # 获取所有测试文件
    tests_dir = Path(__file__).parent
    test_files = [
        "test_config.py",
        "test_all_llm_clients.py",
        "test_tools_factory.py",
        "test_es_unified.py",
        "test_es_comprehensive.py",
        "test_web_search_comprehensive.py",
        "test_code_execute.py",
        "test_planner_node.py",
    ]

    # 过滤掉不存在的文件
    existing_tests = []
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            existing_tests.append(test_file)
        else:
            print(f"⚠️  测试文件不存在: {test_file}")

    print(f"📋 找到 {len(existing_tests)} 个测试文件")

    # 运行测试
    results = {}
    start_time = time.time()

    for test_file in existing_tests:
        test_path = tests_dir / test_file
        success = run_test_file(str(test_path))
        results[test_file] = success

    end_time = time.time()
    total_time = end_time - start_time

    # 显示结果汇总
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")

    passed = 0
    for test_file, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_file}: {status}")
        if success:
            passed += 1

    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    print(f"总耗时: {total_time:.2f} 秒")

    if passed == len(results):
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")

    return passed == len(results)


def run_specific_test(test_name: str):
    """运行特定的测试文件"""
    tests_dir = Path(__file__).parent
    test_file = tests_dir / f"{test_name}.py"

    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False

    return run_test_file(str(test_file))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行特定测试
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        # 运行所有测试
        run_all_tests()
