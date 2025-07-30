#!/usr/bin/env python3
"""
测试配置加载
"""

import os
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
service_dir = current_dir.parent
sys.path.insert(0, str(service_dir))

from core.config import settings


def test_config_loading():
    """测试配置加载"""

    logger.info("🧪 开始测试配置加载")

    # 测试搜索配置
    logger.info("📊 搜索配置:")
    logger.info(
        f"   max_search_rounds: {settings.search_config.max_search_rounds}")
    logger.info(f"   max_queries: {settings.search_config.max_queries}")
    logger.info(
        f"   max_results_per_query: {settings.search_config.max_results_per_query}"
    )

    # 测试文档生成配置
    logger.info("📄 文档生成配置:")
    if hasattr(settings, 'document_generation_config'):
        doc_config = settings.document_generation_config
        logger.info(
            f"   chapter_count: {doc_config.document_length.chapter_count}")
        logger.info(
            f"   chapter_target_words: {doc_config.document_length.chapter_target_words}"
        )
        logger.info(
            f"   total_target_words: {doc_config.document_length.total_target_words}"
        )
    else:
        logger.warning("⚠️  document_generation_config 不存在")

    # 测试YAML配置是否加载
    logger.info("📋 YAML配置检查:")
    if hasattr(settings, '_yaml_config') and settings._yaml_config:
        logger.info("✅ YAML配置已加载")
        if 'search_config' in settings._yaml_config:
            yaml_search = settings._yaml_config['search_config']
            logger.info(f"   YAML中的搜索配置: {yaml_search}")
        else:
            logger.warning("⚠️  YAML中没有search_config")
    else:
        logger.error("❌ YAML配置未加载")

    # 测试模型配置
    logger.info("🤖 模型配置:")
    if hasattr(settings, 'supported_models') and settings.supported_models:
        logger.info(f"✅ 已加载 {len(settings.supported_models)} 个模型")
        for model_name in list(settings.supported_models.keys())[:3]:  # 只显示前3个
            logger.info(f"   - {model_name}")
    else:
        logger.warning("⚠️  没有加载到模型配置")

    # 测试日志配置
    logger.info("📝 日志配置:")
    if hasattr(settings, 'logging_config'):
        log_config = settings.logging_config
        logger.info(f"   level: {log_config.level}")
        logger.info(f"   file_path: {log_config.file_path}")
    else:
        logger.warning("⚠️  logging_config 不存在")


def test_config_override():
    """测试配置覆盖"""

    logger.info("\n🧪 测试配置覆盖")

    # 尝试覆盖搜索配置
    original_rounds = settings.search_config.max_search_rounds
    original_queries = settings.search_config.max_queries
    original_results = settings.search_config.max_results_per_query

    logger.info(f"📊 原始配置:")
    logger.info(f"   max_search_rounds: {original_rounds}")
    logger.info(f"   max_queries: {original_queries}")
    logger.info(f"   max_results_per_query: {original_results}")

    # 尝试修改配置
    try:
        settings.search_config.max_search_rounds = 1
        settings.search_config.max_queries = 1
        settings.search_config.max_results_per_query = 3

        logger.info(f"📊 修改后配置:")
        logger.info(
            f"   max_search_rounds: {settings.search_config.max_search_rounds}"
        )
        logger.info(f"   max_queries: {settings.search_config.max_queries}")
        logger.info(
            f"   max_results_per_query: {settings.search_config.max_results_per_query}"
        )

        logger.success("✅ 配置覆盖成功")

    except Exception as e:
        logger.error(f"❌ 配置覆盖失败: {e}")

    # 恢复原始配置
    settings.search_config.max_search_rounds = original_rounds
    settings.search_config.max_queries = original_queries
    settings.search_config.max_results_per_query = original_results


def main():
    """主函数"""
    try:
        # 配置日志
        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="INFO")

        # 运行测试
        test_config_loading()
        test_config_override()

        logger.success("\n🎉 配置测试完成！")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()
