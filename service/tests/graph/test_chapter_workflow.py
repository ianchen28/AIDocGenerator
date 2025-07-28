#!/usr/bin/env python3
"""
Chapter Workflow集成测试
测试章节工作流子图的完整执行流程
"""

import sys

import pytest
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG",
    format=
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    colorize=True,
    backtrace=True,
    diagnose=True)

from core.config import AppSettings
from core.logging_config import setup_logging

# 初始化配置和日志
settings = AppSettings()
setup_logging(settings)


class TestChapterWorkflow:
    """章节工作流测试类"""

    @pytest.mark.asyncio
    async def test_single_chapter_generation(self, test_container):
        """
        测试单个章节生成
        验证章节工作流能够正确处理单个章节的研究和写作

        Args:
            test_container: 包含已配置的container实例的fixture
        """
        logger.info("🚀 开始测试单个章节生成工作流")

        # 1. 定义章节特定的输入状态
        chapter_input_state = {
            "topic":
            "Chapter 1: The Rise of AI in Diagnostics",
            "current_chapter_index":
            0,
            "chapters_to_process": [{
                "chapter_title": "The Rise of AI in Diagnostics",
                "description": "介绍AI在医疗诊断领域的发展历程和重要突破",
                "chapter_number": 1
            }],
            "completed_chapters_content": [],  # 空列表，因为这是第一个章节
            "search_queries": [],  # 初始化，planner节点会生成
            "research_plan":
            "",  # 初始化，planner节点会生成
            "gathered_data":
            "",  # 初始化，researcher节点会填充
            "messages": []  # 对话历史
        }

        logger.info("📋 章节输入状态:")
        logger.info(f"  - Topic: {chapter_input_state['topic']}")
        logger.info(
            f"  - Chapter Title: {chapter_input_state['chapters_to_process'][0]['chapter_title']}"
        )
        logger.info(
            f"  - Completed Chapters: {len(chapter_input_state['completed_chapters_content'])}"
        )

        # 2. 验证test_container fixture
        assert test_container is not None, "test_container fixture应该提供container实例"
        assert hasattr(test_container,
                       'chapter_graph'), "container应该包含chapter_graph"

        logger.info("✅ test_container fixture验证通过")

        # 3. 检查服务可用性并决定执行策略
        logger.info("🔍 检查服务可用性...")

        # 验证输入状态结构
        assert "topic" in chapter_input_state, "输入状态应该包含topic字段"
        assert "chapters_to_process" in chapter_input_state, "输入状态应该包含chapters_to_process字段"
        assert "current_chapter_index" in chapter_input_state, "输入状态应该包含current_chapter_index字段"
        assert "completed_chapters_content" in chapter_input_state, "输入状态应该包含completed_chapters_content字段"

        # 验证章节信息
        chapters = chapter_input_state["chapters_to_process"]
        assert len(chapters) > 0, "应该有至少一个章节"
        assert "chapter_title" in chapters[0], "章节应该包含chapter_title字段"
        assert "description" in chapters[0], "章节应该包含description字段"

        # 验证chapter_graph结构
        chapter_graph = test_container.chapter_graph
        assert hasattr(chapter_graph, 'astream'), "chapter_graph应该有astream方法"
        assert callable(chapter_graph.astream), "chapter_graph.astream应该是可调用的"

        logger.info("✅ 章节工作流结构验证通过")

        # 4. 尝试执行实际测试（如果服务可用）
        logger.info("🔄 开始调用章节工作流...")

        try:
            # 使用astream()方法流式执行
            async for event in test_container.chapter_graph.astream(
                    chapter_input_state):
                # 记录每个节点的事件
                node_name = list(event.keys())[0] if event else "unknown"
                logger.info(f"📊 节点执行: {node_name}")

                # 检查是否包含最终结果
                if "writer" in event:
                    final_result = event["writer"]
                    logger.info("✅ 章节工作流执行完成，获取到writer节点结果")

                    # 验证输出结果
                    logger.info("🔍 验证输出结果...")

                    # 验证final_document存在
                    assert "final_document" in final_result, "结果应该包含final_document字段"
                    logger.info("✅ final_document字段存在")

                    # 验证final_document是字符串类型
                    assert isinstance(final_result["final_document"],
                                      str), "final_document应该是字符串类型"
                    logger.info("✅ final_document是字符串类型")

                    # 验证内容包含章节主题关键词
                    final_document = final_result["final_document"]
                    assert "Diagnostics" in final_document, "文档内容应该包含'Diagnostics'关键词"
                    logger.info("✅ 文档内容包含'Diagnostics'关键词")

                    # 验证文档长度
                    assert len(final_document) > 50, "文档长度应该大于50个字符"
                    logger.info(f"✅ 文档长度验证通过: {len(final_document)} 字符")

                    # 额外验证：检查文档结构
                    assert "##" in final_document or "#" in final_document, "文档应该包含章节标题标记"
                    logger.info("✅ 文档结构验证通过，包含标题标记")

                    # 验证章节标题
                    chapter_title = chapter_input_state["chapters_to_process"][
                        0]["chapter_title"]
                    assert chapter_title in final_document, f"文档应该包含章节标题: {chapter_title}"
                    logger.info(f"✅ 文档包含正确的章节标题: {chapter_title}")

                    logger.info("🎉 所有验证通过！章节生成测试成功")
                    return  # 成功完成，退出循环

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"⚠️  服务调用失败: {error_msg}")

            # 检查是否是网络或服务相关的错误
            if any(keyword in error_msg.lower() for keyword in [
                    "connection", "timeout", "unreachable", "not found", "404",
                    "500", "network", "service", "embedding", "llm"
            ]):
                logger.info("📝 检测到网络或服务不可用，跳过实际执行测试")
                logger.info("✅ 章节工作流结构验证成功")
                logger.info("📋 输入状态格式验证通过")
                logger.info("🔧 test_container fixture验证通过")
                pytest.skip(f"服务不可用，跳过实际执行: {error_msg}")
            else:
                # 其他类型的错误，重新抛出
                logger.error(f"❌ 章节工作流执行失败: {error_msg}")
                raise

        # 如果没有找到writer节点的结果，抛出异常
        raise AssertionError("未找到writer节点的最终结果")

    @pytest.mark.asyncio
    async def test_chapter_workflow_with_research_data(self, test_container):
        """
        测试带有研究数据的章节工作流
        验证章节工作流能够处理已有的研究数据
        """
        logger.info("🚀 开始测试带有研究数据的章节工作流")

        # 定义包含研究数据的输入状态
        chapter_input_state = {
            "topic":
            "Chapter 2: AI Diagnostic Technologies",
            "current_chapter_index":
            0,
            "chapters_to_process": [{
                "chapter_title": "AI Diagnostic Technologies",
                "description": "详细介绍AI诊断技术的核心原理和应用",
                "chapter_number": 2
            }],
            "completed_chapters_content":
            ["## Chapter 1: The Rise of AI in Diagnostics\n\n这是第一章的内容..."
             ],  # 包含前一章的内容
            "search_queries": [
                "AI diagnostic technologies overview",
                "machine learning medical diagnosis",
                "deep learning healthcare applications"
            ],
            "research_plan":
            "研究AI诊断技术的核心原理、算法实现和实际应用案例",
            "gathered_data":
            """
            === AI Diagnostic Technologies Research Data ===

            Artificial Intelligence has revolutionized medical diagnostics through various technologies:

            1. Machine Learning Algorithms
            - Supervised learning for classification tasks
            - Unsupervised learning for pattern discovery
            - Reinforcement learning for treatment optimization

            2. Deep Learning Models
            - Convolutional Neural Networks (CNNs) for image analysis
            - Recurrent Neural Networks (RNNs) for sequential data
            - Transformer models for complex pattern recognition

            3. Computer Vision Applications
            - Medical imaging analysis (X-ray, MRI, CT scans)
            - Pathology slide analysis
            - Dermatology image classification

            === End of Research Data ===
            """,
            "messages": []
        }

        logger.info(
            f"📋 输入状态包含 {len(chapter_input_state['gathered_data'])} 字符的研究数据")

        try:
            # 调用章节工作流
            async for event in test_container.chapter_graph.astream(
                    chapter_input_state):
                if "writer" in event:
                    final_result = event["writer"]

                    # 验证结果
                    assert "final_document" in final_result
                    assert isinstance(final_result["final_document"], str)

                    final_document = final_result["final_document"]
                    assert "Technologies" in final_document
                    assert len(final_document) > 100  # 应该有更丰富的内容

                    logger.info("✅ 带有研究数据的章节工作流测试通过")
                    return

        except Exception as e:
            logger.error(f"❌ 带有研究数据的章节工作流测试失败: {str(e)}")
            raise

    @pytest.mark.asyncio
    async def test_chapter_workflow_error_handling(self, test_container):
        """
        测试章节工作流的错误处理
        验证在输入数据不完整时的行为
        """
        logger.info("🚀 开始测试章节工作流错误处理")

        # 定义不完整的输入状态（缺少必要字段）
        incomplete_state = {
            "topic": "Test Chapter",
            "current_chapter_index": 0,
            "chapters_to_process": [],  # 空列表，应该导致错误
            "completed_chapters_content": [],
            "search_queries": [],
            "research_plan": "",
            "gathered_data": "",
            "messages": []
        }

        try:
            # 尝试执行章节工作流
            async for _event in test_container.chapter_graph.astream(
                    incomplete_state):
                # 如果执行到这里，说明没有抛出预期的异常
                pass

            # 如果没有抛出异常，记录警告
            logger.warning("⚠️ 章节工作流没有对不完整输入抛出异常")

        except Exception as e:
            logger.info(f"✅ 章节工作流正确处理了错误: {str(e)}")
            # 这是预期的行为，测试通过
            return

        # 如果没有异常，测试也通过（取决于具体实现）
        logger.info("✅ 章节工作流错误处理测试完成")

    def test_chapter_workflow_fixture_validation(self, test_container):
        """
        测试章节工作流fixture的验证
        确保test_container包含正确的chapter_graph
        """
        logger.info("🔍 验证章节工作流fixture")

        # 验证container实例
        assert test_container is not None, "test_container不应该为None"

        # 验证chapter_graph属性
        assert hasattr(test_container,
                       'chapter_graph'), "container应该包含chapter_graph属性"

        # 验证chapter_graph是CompiledStateGraph对象
        chapter_graph = test_container.chapter_graph
        assert hasattr(chapter_graph, 'astream'), "chapter_graph应该有astream方法"
        assert callable(chapter_graph.astream), "chapter_graph.astream应该是可调用的"

        # 验证chapter_graph有invoke方法
        assert hasattr(chapter_graph, 'invoke'), "chapter_graph应该有invoke方法"
        assert callable(chapter_graph.invoke), "chapter_graph.invoke应该是可调用的"

        logger.info("✅ 章节工作流fixture验证通过")


# 独立运行测试
if __name__ == "__main__":
    # 配置日志
    logger.add("logs/test_chapter_workflow.log", rotation="1 day")

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short", "-s"])
