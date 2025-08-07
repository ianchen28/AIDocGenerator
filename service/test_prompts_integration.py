#!/usr/bin/env python3
"""
测试脚本：验证fast_prompts整合到prompts模块是否成功
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "src"))

from doc_agent.core.logger import logger


def test_prompts_import():
    """测试所有prompts模块的导入"""
    logger.info("🧪 开始测试prompts模块导入...")

    try:
        # 测试outline_generation
        from doc_agent.prompts.outline_generation import V4_FAST
        logger.success("✅ outline_generation V4_FAST 导入成功")

        # 测试writer
        from doc_agent.prompts.writer import V4_FAST
        logger.success("✅ writer V4_FAST 导入成功")

        # 测试planner
        from doc_agent.prompts.planner import V3_FAST
        logger.success("✅ planner V3_FAST 导入成功")

        # 测试supervisor
        from doc_agent.prompts.supervisor import V3_FAST
        logger.success("✅ supervisor V3_FAST 导入成功")

        # 测试content_processor
        from doc_agent.prompts.content_processor import V2_FAST_RESEARCH_DATA_SUMMARY
        logger.success("✅ content_processor V2_FAST 导入成功")

        return True

    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        return False


def test_prompt_selector():
    """测试PromptSelector是否正常工作"""
    logger.info("🧪 开始测试PromptSelector...")

    try:
        from doc_agent.common.prompt_selector import PromptSelector

        selector = PromptSelector()

        # 测试获取可用工作流
        workflows = selector.get_available_workflows()
        logger.info(f"📋 可用工作流: {workflows}")

        # 测试获取可用节点
        nodes = selector.list_available_nodes("prompts")
        logger.info(f"📋 prompts可用节点: {nodes}")

        logger.success("✅ PromptSelector 测试成功")
        return True

    except Exception as e:
        logger.error(f"❌ PromptSelector测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("🚀 开始prompts整合测试...")

    tests = [
        ("Prompts模块导入", test_prompts_import),
        ("PromptSelector测试", test_prompt_selector),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 运行测试: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ 测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))

    # 输出测试结果
    logger.info(f"\n{'='*50}")
    logger.info("📊 测试结果汇总:")
    logger.info(f"{'='*50}")

    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        logger.success("🎉 所有测试通过！Prompts整合成功！")
    else:
        logger.error("💥 部分测试失败，请检查问题")

    return all_passed


if __name__ == "__main__":
    main()
