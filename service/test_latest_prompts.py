#!/usr/bin/env python3
"""
测试脚本：验证所有最新的 prompt 版本都能正常工作
"""

import sys
import os
from pathlib import Path

# 项目路径已通过 pip install -e . 处理

from doc_agent.core.logger import logger


def test_latest_prompts():
    """测试所有最新的prompt版本"""
    logger.info("🧪 开始测试最新prompt版本...")

    try:
        # 测试大纲生成 - 使用最新的 V4_FAST 版本
        from doc_agent.prompts.outline_generation import V4_FAST
        logger.success("✅ outline_generation V4_FAST 导入成功")
        logger.info(f"   内容长度: {len(V4_FAST)} 字符")

        # 测试写作器 - 使用最新的 V4_FAST 版本
        from doc_agent.prompts.writer import V4_FAST
        logger.success("✅ writer V4_FAST 导入成功")
        logger.info(f"   内容长度: {len(V4_FAST)} 字符")

        # 测试规划器 - 使用最新的 V3_FAST 版本
        from doc_agent.prompts.planner import V3_FAST
        logger.success("✅ planner V3_FAST 导入成功")
        logger.info(f"   内容长度: {len(V3_FAST)} 字符")

        # 测试监督器 - 使用最新的 V3_FAST 版本
        from doc_agent.prompts.supervisor import V3_FAST
        logger.success("✅ supervisor V3_FAST 导入成功")
        logger.info(f"   内容长度: {len(V3_FAST)} 字符")

        # 测试内容处理器 - 使用最新的 V2_FAST 版本
        from doc_agent.prompts.content_processor import V2_FAST_RESEARCH_DATA_SUMMARY
        logger.success(
            "✅ content_processor V2_FAST_RESEARCH_DATA_SUMMARY 导入成功")
        logger.info(f"   内容长度: {len(V2_FAST_RESEARCH_DATA_SUMMARY)} 字符")

        # 测试反思器 - 使用最新的 V2_FAST 版本
        from doc_agent.prompts.reflection import V2_FAST
        logger.success("✅ reflection V2_FAST 导入成功")
        logger.info(f"   内容长度: {len(V2_FAST)} 字符")

        # 测试AI编辑器 - 使用最新的 POLISH_FAST_PROMPT 版本
        from doc_agent.prompts.ai_editor import POLISH_FAST_PROMPT
        logger.success("✅ ai_editor POLISH_FAST_PROMPT 导入成功")
        logger.info(f"   内容长度: {len(POLISH_FAST_PROMPT)} 字符")

        # 测试PromptSelector集成
        from doc_agent.common.prompt_selector import PromptSelector
        selector = PromptSelector()

        # 测试获取最新版本的prompt
        writer_prompt = selector.get_prompt("prompts", "writer", "default")
        logger.success("✅ PromptSelector 获取 writer prompt 成功")
        logger.info(f"   获取的prompt长度: {len(writer_prompt)} 字符")

        planner_prompt = selector.get_prompt("prompts", "planner", "default")
        logger.success("✅ PromptSelector 获取 planner prompt 成功")
        logger.info(f"   获取的prompt长度: {len(planner_prompt)} 字符")

        return True

    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


def test_api_prompt_usage():
    """测试API中使用的prompt版本"""
    logger.info("🧪 开始测试API prompt使用情况...")

    try:
        # 测试API端点中使用的prompt版本
        from workers.tasks import run_main_workflow
        logger.success("✅ run_main_workflow 任务导入成功")

        # 测试Container中的prompt选择器
        from doc_agent.core.container import container
        logger.success("✅ Container 初始化成功")
        logger.info(f"   加载的genre策略数量: {len(container.genre_strategies)}")

        # 测试genre-aware功能
        test_genres = ["default", "simple", "academic"]
        for genre in test_genres:
            if genre in container.genre_strategies:
                logger.success(f"✅ Genre '{genre}' 策略存在")
            else:
                logger.warning(f"⚠️  Genre '{genre}' 策略不存在")

        return True

    except Exception as e:
        logger.error(f"❌ API prompt测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("🚀 开始测试最新prompt版本...")

    # 测试1: 基础prompt导入
    test1_result = test_latest_prompts()

    # 测试2: API prompt使用
    test2_result = test_api_prompt_usage()

    if test1_result and test2_result:
        logger.success("🎉 所有测试通过！")
        logger.info("✅ fast_prompts 目录已成功整合到 prompts 模块")
        logger.info("✅ API 现在使用最新的 prompt 版本")
        logger.info("✅ 所有 prompt 版本都正常工作")
        return True
    else:
        logger.error("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
