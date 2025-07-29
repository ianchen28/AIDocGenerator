#!/usr/bin/env python3
"""
Genre-aware PromptSelector 使用示例

这个示例展示了如何使用新的 genre-aware PromptSelector 功能
来根据不同的文档类型选择相应的 prompt 版本。
"""

import sys
import os
from pathlib import Path

# 添加 service 目录到 Python 路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 切换到 service 目录
os.chdir(service_dir)

from loguru import logger
from src.doc_agent.common.prompt_selector import PromptSelector


def demonstrate_genre_aware_prompt_selector():
    """演示 genre-aware PromptSelector 的使用"""
    logger.info("🎭 演示 Genre-aware PromptSelector 功能")

    # 创建 PromptSelector 实例
    selector = PromptSelector()

    # 1. 列出所有可用的 genres
    logger.info("📋 可用的 genres:")
    genres = selector.list_available_genres()
    for genre in genres:
        genre_info = selector.get_genre_info(genre)
        logger.info(
            f"  - {genre}: {genre_info['name']} - {genre_info['description']}")

    print("\n" + "=" * 60 + "\n")

    # 2. 演示不同 genre 的 prompt 版本选择
    logger.info("🔍 不同 genre 的 prompt 版本选择:")

    test_cases = [("default", "writer"), ("work_report", "writer"),
                  ("speech_draft", "writer"), ("default", "planner"),
                  ("work_report", "planner"), ("speech_draft", "planner")]

    for genre, node in test_cases:
        try:
            # 获取该 genre 和节点的 prompt 版本
            genre_info = selector.get_genre_info(genre)
            prompt_versions = genre_info['prompt_versions']
            version = prompt_versions.get(node, "未配置")

            logger.info(f"  {genre}.{node} -> 版本: {version}")

            # 尝试获取实际的 prompt
            try:
                prompt = selector.get_prompt("prompts", node, genre)
                prompt_preview = prompt[:100] + "..." if len(
                    prompt) > 100 else prompt
                logger.debug(f"    Prompt 预览: {prompt_preview}")
            except Exception as e:
                logger.warning(f"    获取 prompt 失败: {e}")

        except Exception as e:
            logger.error(f"  处理 {genre}.{node} 时出错: {e}")

    print("\n" + "=" * 60 + "\n")

    # 3. 演示自定义 genre 策略
    logger.info("🎨 演示自定义 genre 策略:")

    custom_strategies = {
        "academic_paper": {
            "name": "学术论文",
            "description": "生成严谨的学术论文，注重逻辑性和引用规范",
            "prompt_versions": {
                "writer": "v1_default",
                "planner": "v1_default",
                "supervisor": "v1_metadata_based",
                "outline_generation": "v1_default"
            }
        },
        "creative_story": {
            "name": "创意故事",
            "description": "生成富有想象力和感染力的创意故事",
            "prompt_versions": {
                "writer": "v1_default",
                "planner": "v1_default",
                "supervisor": "v1_metadata_based",
                "outline_generation": "v1_default"
            }
        }
    }

    custom_selector = PromptSelector(custom_strategies)
    logger.info(f"  自定义 genres: {custom_selector.list_available_genres()}")

    # 测试自定义 genre
    try:
        prompt = custom_selector.get_prompt("prompts", "writer",
                                            "academic_paper")
        logger.info("  ✅ 成功获取学术论文 genre 的 writer prompt")
    except Exception as e:
        logger.error(f"  ❌ 获取学术论文 prompt 失败: {e}")

    print("\n" + "=" * 60 + "\n")

    # 4. 演示错误处理
    logger.info("⚠️  演示错误处理:")

    # 测试无效 genre
    try:
        selector.get_prompt("prompts", "writer", "invalid_genre")
        logger.error("  ❌ 应该抛出异常但没有")
    except ValueError as e:
        logger.info(f"  ✅ 正确捕获无效 genre 错误: {e}")

    # 测试无效节点
    try:
        selector.get_prompt("prompts", "invalid_node", "default")
        logger.error("  ❌ 应该抛出异常但没有")
    except ValueError as e:
        logger.info(f"  ✅ 正确捕获无效节点错误: {e}")

    print("\n" + "=" * 60 + "\n")

    # 5. 演示便捷函数
    logger.info("🚀 演示便捷函数:")

    from src.doc_agent.common.prompt_selector import get_prompt

    try:
        prompt = get_prompt("prompts", "writer", "work_report")
        logger.info("  ✅ 使用便捷函数成功获取工作报告的 writer prompt")
    except Exception as e:
        logger.error(f"  ❌ 便捷函数调用失败: {e}")

    logger.success("🎉 Genre-aware PromptSelector 演示完成！")


def demonstrate_genre_specific_features():
    """演示 genre 特定功能"""
    logger.info("🎯 演示 Genre 特定功能")

    selector = PromptSelector()

    # 1. 获取特定 genre 的可用节点
    for genre in ["default", "work_report", "speech_draft"]:
        try:
            nodes = selector.list_available_nodes_for_genre(genre)
            logger.info(f"  {genre} 的可用节点: {nodes}")
        except Exception as e:
            logger.error(f"  获取 {genre} 节点失败: {e}")

    print("\n" + "=" * 60 + "\n")

    # 2. 验证 prompt 是否存在
    test_cases = [("prompts", "writer", "default"),
                  ("prompts", "writer", "work_report"),
                  ("prompts", "writer", "speech_draft"),
                  ("prompts", "writer", "invalid_genre")]

    logger.info("🔍 Prompt 验证结果:")
    for workflow_type, node, genre in test_cases:
        is_valid = selector.validate_prompt(workflow_type, node, genre)
        status = "✅ 有效" if is_valid else "❌ 无效"
        logger.info(f"  {workflow_type}.{node} ({genre}): {status}")


if __name__ == "__main__":
    # 运行演示
    demonstrate_genre_aware_prompt_selector()
    print("\n" + "=" * 80 + "\n")
    demonstrate_genre_specific_features()
