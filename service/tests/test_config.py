#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置测试
测试配置加载和验证功能
"""

import sys
import os
import unittest
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from test_base import TestBase
from core.config import settings


class ConfigTest(TestBase):
    """配置测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化配置测试")

    def test_basic_config(self):
        """测试基本配置"""
        logger.info("基本配置测试")

        try:
            # 检查基本配置
            logger.info(f"Redis URL: {settings.redis_url}")
            logger.info(
                f"OpenAI API Key: {'已设置' if settings.openai.api_key else '未设置'}"
            )

            # 检查支持的模型
            models = settings.supported_models
            logger.info(f"支持的模型数量: {len(models)}")

            # 显示部分模型信息
            for i, (model_key, model_config) in enumerate(models.items()):
                if i >= 3:  # 只显示前3个
                    break
                logger.info(f"  {model_key}: {model_config.name}")

            logger.info("基本配置加载成功")

        except Exception as e:
            logger.error(f"基本配置测试失败: {e}")
            self.fail(f"基本配置测试失败: {e}")

    def test_elasticsearch_config(self):
        """测试Elasticsearch配置"""
        logger.info("Elasticsearch 配置测试")

        try:
            es_config = settings.elasticsearch_config
            logger.info(f"Hosts: {es_config.hosts}")
            logger.info(f"Username: {es_config.username}")
            logger.info(f"Index Prefix: {es_config.index_prefix}")

            # 验证配置
            self.assertIsNotNone(es_config.hosts)
            self.assertIsNotNone(es_config.username)
            logger.info("Elasticsearch 配置验证成功")

        except Exception as e:
            logger.error(f"Elasticsearch 配置测试失败: {e}")
            self.fail(f"Elasticsearch 配置测试失败: {e}")

    def test_tavily_config(self):
        """测试Tavily配置"""
        logger.info("Tavily 配置测试")

        tavily_config = settings.get_model_config("tavily")
        if not tavily_config:
            logger.warning("Tavily 配置未找到")
            self.skipTest("Tavily 配置未找到")

        try:
            logger.info(
                f"API Key: {'已设置' if tavily_config.api_key else '未设置'}")
            logger.info(f"Search Depth: {tavily_config.search_depth}")
            logger.info(f"Max Results: {tavily_config.max_results}")

            # 验证配置
            self.assertIsNotNone(tavily_config.api_key)
            logger.info("Tavily 配置验证成功")

        except Exception as e:
            logger.error(f"Tavily 配置测试失败: {e}")
            self.fail(f"Tavily 配置测试失败: {e}")

    def test_agent_config(self):
        """测试Agent配置"""
        logger.info("Agent 配置测试")

        try:
            agent_config = settings.agent_config
            logger.info(f"Task Planner: {agent_config.task_planner.name}")
            logger.info(f"Composer: {agent_config.composer.name}")
            logger.info(f"Validator: {agent_config.validator.name}")

            # 验证配置
            self.assertIsNotNone(agent_config.task_planner)
            self.assertIsNotNone(agent_config.composer)
            self.assertIsNotNone(agent_config.validator)
            logger.info("Agent 配置验证成功")

        except Exception as e:
            logger.error(f"Agent 配置测试失败: {e}")
            self.fail(f"Agent 配置测试失败: {e}")

    def test_model_config_retrieval(self):
        """测试模型配置获取"""
        logger.info("模型配置获取测试")

        try:
            # 测试获取各种模型配置
            test_models = [
                "moonshot_k2_0711_preview", "qwen_2_5_235b_a22b", "tavily"
            ]

            for model_key in test_models:
                try:
                    model_config = settings.get_model_config(model_key)
                    if model_config:
                        logger.info(f"  {model_key} 配置获取成功:")
                        logger.info(f"  - Name: {model_config.name}")
                        logger.info(f"  - URL: {model_config.url}")
                        logger.info(f"  - Type: {model_config.type}")
                    else:
                        logger.warning(f"  {model_key} 配置未找到")

                except Exception as e:
                    logger.warning(f"  {model_key} 配置获取失败: {e}")

            logger.info("模型配置获取测试完成")

        except Exception as e:
            logger.error(f"模型配置获取测试失败: {e}")
            self.fail(f"模型配置获取测试失败: {e}")

    def test_agent_component_config(self):
        """测试Agent组件配置"""
        logger.info("Agent 组件配置测试")

        try:
            agent_config = settings.agent_config
            components = ["task_planner", "composer", "validator"]

            for component in components:
                try:
                    component_config = getattr(agent_config, component)
                    logger.info(f"  {component} 组件配置获取成功:")
                    logger.info(
                        f"  - Temperature: {component_config.temperature}")
                    logger.info(
                        f"  - Max Tokens: {component_config.max_tokens}")
                    logger.info(f"  - Timeout: {component_config.timeout}")

                except Exception as e:
                    logger.warning(f"  {component} 组件配置未找到")

            logger.info("Agent 组件配置测试完成")

        except Exception as e:
            logger.error(f"Agent 组件配置测试失败: {e}")
            self.fail(f"Agent 组件配置测试失败: {e}")

    def test_llm_model_config(self):
        """测试LLM模型配置"""
        logger.info("LLM 模型配置测试")

        try:
            # 测试Moonshot配置
            moonshot_config = settings.get_model_config(
                "moonshot_k2_0711_preview")
            if moonshot_config:
                logger.info("Moonshot 模型配置:")
                logger.info(f"  - Name: {moonshot_config.name}")
                logger.info(f"  - URL: {moonshot_config.url}")
                logger.info(f"  - Model ID: {moonshot_config.model_id}")
                logger.info(f"  - Description: {moonshot_config.description}")
            else:
                logger.warning("Moonshot 模型配置未找到")

            # 测试Qwen配置
            qwen_config = settings.get_model_config("qwen_2_5_235b_a22b")
            if qwen_config:
                logger.info("Qwen 模型配置:")
                logger.info(f"  - Name: {qwen_config.name}")
                logger.info(f"  - URL: {qwen_config.url}")
                logger.info(f"  - Model ID: {qwen_config.model_id}")
            else:
                logger.warning("Qwen 模型配置未找到")

            logger.info("LLM 模型配置测试完成")

        except Exception as e:
            logger.error(f"LLM 模型配置测试失败: {e}")
            self.fail(f"LLM 模型配置测试失败: {e}")

    def test_es_detailed_config(self):
        """测试ES详细配置"""
        logger.info("ES 详细配置测试")

        try:
            es_config = settings.elasticsearch_config
            logger.info("ES 详细配置:")
            logger.info(f"  - Hosts: {es_config.hosts}")
            logger.info(f"  - Username: {es_config.username}")
            logger.info(
                f"  - Password: {'已设置' if es_config.password else '未设置'}")
            logger.info(f"  - Index Prefix: {es_config.index_prefix}")
            logger.info(f"  - Timeout: {es_config.timeout}")

            # 验证详细配置
            self.assertIsNotNone(es_config.hosts)
            self.assertIsNotNone(es_config.username)
            self.assertIsNotNone(es_config.password)
            self.assertIsNotNone(es_config.index_prefix)
            logger.info("ES 详细配置验证成功")

        except Exception as e:
            logger.error(f"ES 详细配置测试失败: {e}")
            self.fail(f"ES 详细配置测试失败: {e}")

    def test_websearch_config(self):
        """测试WebSearch配置"""
        logger.info("WebSearch 配置测试")

        tavily_config = settings.get_model_config("tavily")
        if not tavily_config:
            logger.warning("Tavily 配置未找到")
            self.skipTest("Tavily 配置未找到")

        try:
            logger.info("Tavily 详细配置:")
            logger.info(
                f"  - API Key: {'已设置' if tavily_config.api_key else '未设置'}")
            logger.info(f"  - Search Depth: {tavily_config.search_depth}")
            logger.info(f"  - Max Results: {tavily_config.max_results}")
            # print(f"  - Include Answer: {tavily_config.include_answer}")  # 字段不存在，注释掉
            # print(f"  - Include Raw Content: {tavily_config.include_raw_content}")  # 字段不存在，注释掉

            # 验证配置
            self.assertIsNotNone(tavily_config.api_key)
            self.assertIsNotNone(tavily_config.search_depth)
            self.assertIsNotNone(tavily_config.max_results)
            logger.info("WebSearch 配置验证成功")

        except Exception as e:
            logger.error(f"WebSearch 配置测试失败: {e}")
            self.fail(f"WebSearch 配置测试失败: {e}")

    def test_config_validation(self):
        """测试配置验证"""
        logger.info("配置验证测试")

        try:
            # 验证各种配置项
            config_items = [
                ("Redis URL", settings.redis_url),
                ("ES Hosts", settings.elasticsearch_config.hosts),
                ("ES Username", settings.elasticsearch_config.username),
            ]

            # 检查Tavily配置
            tavily_config = settings.get_model_config("tavily")
            if tavily_config:
                config_items.append(("Tavily API Key", tavily_config.api_key))

            for name, value in config_items:
                if value:
                    logger.info(f"  {name}: 已配置")
                else:
                    logger.error(f"  {name}: 未配置")

            logger.info("配置验证完成")

        except Exception as e:
            logger.error(f"配置验证测试失败: {e}")
            self.fail(f"配置验证测试失败: {e}")


def main():
    """主函数"""
    logger.info("配置测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ConfigTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有配置测试通过")
    else:
        logger.error("配置测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
