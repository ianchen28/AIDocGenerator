#!/usr/bin/env python3
"""
测试运行脚本
从service根目录运行所有测试
"""

# 运行测试
if __name__ == "__main__":
    from tests.run_all_tests import run_all_tests
    run_all_tests()
