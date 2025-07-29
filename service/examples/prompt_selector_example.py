#!/usr/bin/env python3
"""
PromptSelector 使用示例
"""

import sys
import os
from pathlib import Path

# Add service directory to Python path
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# Change to service directory for imports
os.chdir(service_dir)

from src.doc_agent.common.prompt_selector import PromptSelector, get_prompt
from loguru import logger


def basic_usage_example():
    """基本使用示例"""
    logger.info("📝 基本使用示例")

    # 创建 PromptSelector 实例
    selector = PromptSelector()

    # 获取不同类型的prompt
    prompts = {
        "标准写作器": selector.get_prompt("prompts", "writer", "default"),
        "快速写作器": selector.get_prompt("fast_prompts", "writer", "default"),
        "标准规划器": selector.get_prompt("prompts", "planner", "default"),
        "快速规划器": selector.get_prompt("fast_prompts", "planner", "default"),
        "内容处理器": selector.get_prompt("prompts", "content_processor",
                                     "default"),
    }

    # 显示结果
    for name, prompt in prompts.items():
        logger.success(f"✅ {name}")
        logger.info(f"   长度: {len(prompt)} 字符")
        logger.info(f"   开头: {prompt[:50]}...")


def convenience_function_example():
    """便捷函数使用示例"""
    logger.info("📝 便捷函数使用示例")

    # 使用便捷函数直接获取prompt
    writer_prompt = get_prompt("prompts", "writer", "default")
    fast_writer_prompt = get_prompt("fast_prompts", "writer", "default")

    logger.success("✅ 使用便捷函数获取prompt")
    logger.info(f"   标准写作器: {len(writer_prompt)} 字符")
    logger.info(f"   快速写作器: {len(fast_writer_prompt)} 字符")


def utility_methods_example():
    """工具方法使用示例"""
    logger.info("📝 工具方法使用示例")

    selector = PromptSelector()

    # 列出可用工作流
    workflows = selector.list_available_workflows()
    logger.info(f"📋 可用工作流: {workflows}")

    # 列出可用节点
    for workflow in workflows:
        nodes = selector.list_available_nodes(workflow)
        logger.info(f"📋 {workflow} 可用节点: {nodes}")

    # 验证prompt存在性
    test_cases = [
        ("prompts", "writer", "default"),
        ("fast_prompts", "writer", "default"),
        ("prompts", "content_processor", "default"),
    ]

    for workflow, node, version in test_cases:
        is_valid = selector.validate_prompt(workflow, node, version)
        status = "✅ 有效" if is_valid else "❌ 无效"
        logger.info(f"🔍 {workflow}.{node}.{version}: {status}")


def error_handling_example():
    """错误处理示例"""
    logger.info("📝 错误处理示例")

    selector = PromptSelector()

    # 测试不存在的模块
    try:
        selector.get_prompt("nonexistent", "writer", "default")
        logger.error("❌ 应该抛出错误")
    except ImportError:
        logger.success("✅ 正确处理了不存在的模块")

    # 测试不存在的节点
    try:
        selector.get_prompt("prompts", "nonexistent", "default")
        logger.error("❌ 应该抛出错误")
    except ImportError:
        logger.success("✅ 正确处理了不存在的节点")

    # 测试不存在的版本（应该使用fallback）
    try:
        selector.get_prompt("prompts", "writer", "nonexistent_version")
        logger.success("✅ 正确处理了不存在的版本（使用fallback）")
    except Exception as e:
        logger.error(f"❌ 处理不存在的版本时出错: {e}")


def batch_processing_example():
    """批量处理示例"""
    logger.info("📝 批量处理示例")

    selector = PromptSelector()

    # 获取所有可用的prompt
    workflows = selector.list_available_workflows()
    all_prompts = {}

    for workflow in workflows:
        nodes = selector.list_available_nodes(workflow)
        for node in nodes:
            try:
                prompt = selector.get_prompt(workflow, node, "default")
                all_prompts[f"{workflow}.{node}"] = {
                    "length":
                    len(prompt),
                    "content":
                    prompt[:100] + "..." if len(prompt) > 100 else prompt
                }
                logger.success(f"✅ 成功获取 {workflow}.{node}.default")
            except Exception as e:
                logger.error(f"❌ 获取 {workflow}.{node}.default 失败: {e}")

    # 显示统计信息
    logger.info(f"📊 总共获取了 {len(all_prompts)} 个prompt")
    for name, info in all_prompts.items():
        logger.info(f"   {name}: {info['length']} 字符")


def prompt_content_analysis():
    """Prompt内容分析示例"""
    logger.info("📝 Prompt内容分析示例")

    selector = PromptSelector()

    # 分析不同类型的prompt
    prompt_types = [
        ("标准写作器", "prompts", "writer"),
        ("快速写作器", "fast_prompts", "writer"),
        ("标准规划器", "prompts", "planner"),
        ("快速规划器", "fast_prompts", "planner"),
    ]

    for name, workflow, node in prompt_types:
        try:
            prompt = selector.get_prompt(workflow, node, "default")

            # 分析内容
            analysis = {
                "长度": len(prompt),
                "包含'角色'": "角色" in prompt,
                "包含'专业'": "专业" in prompt,
                "包含'研究员'": "研究员" in prompt,
                "包含'文档'": "文档" in prompt,
                "包含'章节'": "章节" in prompt,
            }

            logger.success(f"✅ {name} 分析结果:")
            for key, value in analysis.items():
                logger.info(f"   {key}: {value}")

        except Exception as e:
            logger.error(f"❌ 分析 {name} 失败: {e}")


if __name__ == "__main__":
    # 配置logger
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")

    # 运行所有示例
    basic_usage_example()
    print("\n" + "=" * 50 + "\n")

    convenience_function_example()
    print("\n" + "=" * 50 + "\n")

    utility_methods_example()
    print("\n" + "=" * 50 + "\n")

    error_handling_example()
    print("\n" + "=" * 50 + "\n")

    batch_processing_example()
    print("\n" + "=" * 50 + "\n")

    prompt_content_analysis()

    logger.success("🎉 所有示例运行完成！")
