#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有测试的脚本
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))


def run_test_file(test_file: str, timeout: int = 300) -> dict:
    """运行单个测试文件"""
    logger.info(f"运行测试: {test_file}")

    try:
        # 使用 subprocess 运行测试文件
        result = subprocess.run([sys.executable, test_file],
                                capture_output=True,
                                text=True,
                                timeout=timeout)

        if result.returncode == 0:
            logger.info("测试通过")
            logger.debug(result.stdout)
            return {
                "status": "PASS",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            logger.error("测试失败")
            logger.error(result.stdout)
            logger.error(result.stderr)
            return {
                "status": "FAIL",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        logger.warning("测试超时")
        return {"status": "TIMEOUT", "stdout": "", "stderr": ""}
    except Exception as e:
        logger.error(f"运行测试时出错: {str(e)}")
        return {"status": "ERROR", "stdout": "", "stderr": str(e)}


def main():
    """主函数"""
    logger.info("开始运行所有测试...")

    # 测试文件列表
    test_files = [
        "test_base.py", "test_config.py", "test_all_llm_clients.py",
        "test_es_unified.py", "test_web_search_comprehensive.py",
        "test_reranker_tool.py", "test_search_rerank_simple.py",
        "test_search_rerank_integration.py", "test_reranker_validation.py",
        "test_reranker_client.py", "test_search_rerank_simple.py",
        "test_supervisor_router.py", "test_planner_node.py",
        "test_researcher_node.py", "test_code_execute.py"
    ]

    # 检查文件是否存在
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
        else:
            logger.warning(f"测试文件不存在: {test_file}")

    logger.info(f"找到 {len(existing_tests)} 个测试文件")

    # 运行测试
    results = {}
    total_time = 0

    for test_file in existing_tests:
        start_time = time.time()
        result = run_test_file(test_file)
        end_time = time.time()

        results[test_file] = result
        test_time = end_time - start_time
        total_time += test_time

        logger.info(f"{test_file}: {result['status']} ({test_time:.2f}s)")

    # 输出结果汇总
    logger.info("测试结果汇总")

    passed = 0
    for test_file, result in results.items():
        status = result["status"]
        logger.info(f"{test_file}: {status}")
        if status == "PASS":
            passed += 1

    logger.info(f"总计: {passed}/{len(results)} 个测试通过")
    logger.info(f"总耗时: {total_time:.2f} 秒")

    if passed == len(results):
        logger.info("所有测试通过！")
    else:
        logger.warning("部分测试失败")

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
