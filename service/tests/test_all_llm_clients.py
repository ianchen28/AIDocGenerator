#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
所有LLM客户端测试
测试各种LLM客户端的创建和调用
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

from test_base import LLMTestCase, skip_if_no_llm
from core.config import settings


class AllLLMClientsTest(LLMTestCase):
    """所有LLM客户端测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        logger.debug("初始化 LLM 客户端测试")

    @skip_if_no_llm
    def test_config_loading(self):
        """测试配置加载"""
        logger.info("测试配置加载")

        try:
            # 获取所有支持的模型
            models = settings.get_available_models()
            logger.info(f"支持的模型数量: {len(models)}")

            # 显示模型配置
            for model_key, model_config in models.items():
                logger.info(f"模型: {model_key}")
                logger.info(f"    URL: {model_config.url}")
                logger.info(f"    Model ID: {model_config.model_id}")
                logger.info(f"    Description: {model_config.description}")
                logger.info("")

            # 验证配置
            self.assertIsInstance(models, dict)
            self.assertGreater(len(models), 0)

        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            self.fail(f"配置加载失败: {e}")

    @skip_if_no_llm
    def test_client_creation(self):
        """测试客户端创建"""
        logger.info("测试客户端创建")

        models = settings.get_available_models()
        success_count = 0
        total = len(models)

        for model_key in models.keys():
            try:
                from src.doc_agent.llm_clients import get_llm_client
                client = get_llm_client(model_key)

                logger.info(f"  {model_key} 客户端创建成功")
                logger.debug(f"     类型: {type(client).__name__}")
                success_count += 1

            except Exception as e:
                logger.error(f"  {model_key} 客户端创建失败: {e}")

        logger.info(f"客户端创建结果: {success_count}/{total} 成功")
        self.assertGreater(success_count, 0)

    @skip_if_no_llm
    def test_client_invocation(self):
        """测试客户端调用"""
        logger.info("测试客户端调用")

        models = settings.get_available_models()
        success_count = 0
        total = len(models)

        test_prompt = "请简单介绍一下人工智能"

        for model_key in models.keys():
            try:
                from src.doc_agent.llm_clients import get_llm_client
                client = get_llm_client(model_key)

                # 测试基本调用
                response = client.invoke(test_prompt)

                if response and len(str(response)) > 0:
                    logger.info(
                        f"  {model_key} invoke 返回: {str(response)[:60]}...")
                    success_count += 1
                else:
                    logger.error(f"  {model_key} invoke 返回内容异常")

            except Exception as e:
                logger.error(f"  {model_key} invoke 异常: {e}")

        logger.info(f"客户端调用结果: {success_count}/{total} 成功")
        self.assertGreater(success_count, 0)

    @skip_if_no_llm
    def test_moonshot_client_specifically(self):
        """专门测试Moonshot客户端"""
        logger.info("专门测试 Moonshot 客户端")

        try:
            from src.doc_agent.llm_clients import get_llm_client

            # 创建Moonshot客户端
            moonshot_client = get_llm_client("moonshot_k2_0711_preview")
            logger.info("  Moonshot 客户端创建成功")
            logger.debug(f"     类型: {type(moonshot_client).__name__}")

            # 测试基本调用
            test_prompt = "请用一句话介绍机器学习"
            response = moonshot_client.invoke(test_prompt)

            logger.info("  Moonshot 基本调用成功")
            logger.debug(f"     响应长度: {len(str(response))} 字符")
            logger.debug(f"     响应预览: {str(response)[:100]}...")

            # 测试带参数的调用
            response_with_params = moonshot_client.invoke(test_prompt,
                                                          temperature=0.7,
                                                          max_tokens=100)

            logger.info("  Moonshot 带参数调用成功")
            logger.debug(f"     响应: {str(response_with_params)[:50]}...")

            logger.info("  Moonshot 客户端测试全部通过")

        except Exception as e:
            logger.error(f"  Moonshot 客户端测试失败: {e}")
            self.fail(f"Moonshot 客户端测试失败: {e}")

    @skip_if_no_llm
    def test_client_error_handling(self):
        """测试客户端错误处理"""
        logger.info("测试客户端错误处理")

        try:
            from src.doc_agent.llm_clients import get_llm_client

            # 测试无效的模型键
            try:
                invalid_client = get_llm_client("invalid_model")
                logger.warning("无效模型键应该抛出异常")
            except Exception as e:
                logger.info(f"无效模型键正确处理: {e}")

            # 测试空提示词
            models = settings.get_available_models()
            if models:
                model_key = list(models.keys())[0]
                client = get_llm_client(model_key)

                try:
                    response = client.invoke("")
                    logger.info("空提示词处理正常")
                except Exception as e:
                    logger.warning(f"空提示词处理异常: {e}")

        except Exception as e:
            logger.error(f"错误处理测试失败: {e}")
            self.fail(f"错误处理测试失败: {e}")


def main():
    """主函数"""
    logger.info("LLM 客户端测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(AllLLMClientsTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有 LLM 客户端测试通过")
    else:
        logger.error("LLM 客户端测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
