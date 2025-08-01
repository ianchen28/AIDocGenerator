#!/usr/bin/env python3
"""
测试 reflection_node 功能
"""

from unittest.mock import Mock, patch

from loguru import logger

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.graph.chapter_workflow.nodes import (
    _parse_reflection_response,
    reflection_node,
)
from doc_agent.llm_clients.base import LLMClient


def test_parse_reflection_response_json():
    """测试解析 JSON 格式的 reflection 响应"""
    logger.info("🧪 测试解析 JSON 格式的 reflection 响应...")

    try:
        # 测试标准的 JSON 响应
        json_response = '''
        {
            "new_queries": [
                "人工智能在医疗领域的应用案例",
                "机器学习算法在诊断中的准确性",
                "AI辅助医疗的未来发展趋势"
            ],
            "reasoning": "基于现有数据，发现需要更具体的应用案例和未来趋势信息"
        }
        '''

        queries = _parse_reflection_response(json_response)
        assert len(queries) == 3
        assert "人工智能在医疗领域的应用案例" in queries
        assert "机器学习算法在诊断中的准确性" in queries
        assert "AI辅助医疗的未来发展趋势" in queries

        logger.success("✅ JSON 格式解析测试成功")

    except Exception as e:
        logger.error(f"❌ JSON 格式解析测试失败: {e}")
        return False

    return True


def test_parse_reflection_response_text():
    """测试解析文本格式的 reflection 响应"""
    logger.info("🧪 测试解析文本格式的 reflection 响应...")

    try:
        # 测试带编号的文本响应
        text_response = '''
        基于分析，我建议以下新的搜索查询：
        
        1. 人工智能在医疗诊断中的实际应用案例
        2. 机器学习算法在医学影像识别中的准确性研究
        3. AI辅助医疗系统的未来发展趋势和挑战
        '''

        queries = _parse_reflection_response(text_response)
        assert len(queries) == 3
        assert "人工智能在医疗诊断中的实际应用案例" in queries
        assert "机器学习算法在医学影像识别中的准确性研究" in queries
        assert "AI辅助医疗系统的未来发展趋势和挑战" in queries

        logger.success("✅ 文本格式解析测试成功")

    except Exception as e:
        logger.error(f"❌ 文本格式解析测试失败: {e}")
        return False

    return True


def test_parse_reflection_response_bullet_points():
    """测试解析带项目符号的 reflection 响应"""
    logger.info("🧪 测试解析带项目符号的 reflection 响应...")

    try:
        # 测试带项目符号的响应
        bullet_response = '''
        建议的新查询：
        
        • 深度学习在医学影像分析中的应用
        • 人工智能辅助诊断的准确性和可靠性
        • AI医疗系统的伦理问题和监管挑战
        '''

        queries = _parse_reflection_response(bullet_response)
        assert len(queries) == 3
        assert "深度学习在医学影像分析中的应用" in queries
        assert "人工智能辅助诊断的准确性和可靠性" in queries
        assert "AI医疗系统的伦理问题和监管挑战" in queries

        logger.success("✅ 项目符号格式解析测试成功")

    except Exception as e:
        logger.error(f"❌ 项目符号格式解析测试失败: {e}")
        return False

    return True


def test_parse_reflection_response_quotes():
    """测试解析带引号的 reflection 响应"""
    logger.info("🧪 测试解析带引号的 reflection 响应...")

    try:
        # 测试带引号的响应
        quote_response = '''
        新的搜索查询：
        
        "人工智能在医疗领域的实际应用"
        "机器学习在医学诊断中的准确性"
        "AI辅助医疗的未来发展"
        '''

        queries = _parse_reflection_response(quote_response)
        assert len(queries) == 3
        assert "人工智能在医疗领域的实际应用" in queries
        assert "机器学习在医学诊断中的准确性" in queries
        assert "AI辅助医疗的未来发展" in queries

        logger.success("✅ 引号格式解析测试成功")

    except Exception as e:
        logger.error(f"❌ 引号格式解析测试失败: {e}")
        return False

    return True


def test_parse_reflection_response_invalid():
    """测试解析无效的 reflection 响应"""
    logger.info("🧪 测试解析无效的 reflection 响应...")

    try:
        # 测试空响应
        empty_response = ""
        queries = _parse_reflection_response(empty_response)
        assert len(queries) == 0

        # 测试只有标题的响应
        title_response = "新的搜索查询：\n\n# 标题\n\n## 子标题"
        queries = _parse_reflection_response(title_response)
        assert len(queries) == 0

        # 测试只有数字的响应
        number_response = "1. 2. 3. 4. 5."
        queries = _parse_reflection_response(number_response)
        assert len(queries) == 0

        logger.success("✅ 无效响应解析测试成功")

    except Exception as e:
        logger.error(f"❌ 无效响应解析测试失败: {e}")
        return False

    return True


@patch('doc_agent.graph.chapter_workflow.nodes.settings')
async def test_reflection_node_basic(mock_settings):
    """测试 reflection_node 的基本功能"""
    logger.info("🧪 测试 reflection_node 的基本功能...")

    try:
        # 模拟设置
        mock_settings.get_agent_component_config.return_value = Mock(
            temperature=0.7, max_tokens=2000, extra_params={})

        # 模拟 LLM 客户端
        mock_llm_client = Mock(spec=LLMClient)
        mock_llm_client.invoke.return_value = '''
        {
            "new_queries": [
                "人工智能在医疗诊断中的最新应用",
                "机器学习算法在医学影像分析中的准确性",
                "AI辅助医疗系统的未来发展趋势"
            ],
            "reasoning": "基于现有数据，需要更具体的应用案例和未来趋势信息"
        }
        '''

        # 模拟 PromptSelector
        mock_prompt_selector = Mock(spec=PromptSelector)
        mock_prompt_selector.get_prompt.return_value = """
        你是一个专业的研究专家和查询优化师。
        
        **文档主题:** {topic}
        **当前章节信息:**
        - 章节标题: {chapter_title}
        - 章节描述: {chapter_description}
        
        **原始搜索查询:**
        {original_queries}
        
        **已收集的数据摘要:**
        {gathered_data_summary}
        
        请生成新的搜索查询。
        """

        # 准备测试状态
        test_state = {
            "topic":
            "人工智能在医疗领域的应用",
            "search_queries": ["人工智能医疗应用", "AI诊断技术", "机器学习医疗"],
            "gathered_data":
            "人工智能在医疗领域有广泛应用，包括医学影像分析、疾病诊断、药物发现等。深度学习算法在医学影像识别方面取得了显著进展，准确率已经达到或超过人类专家水平。这些技术在临床实践中已经显示出巨大的潜力，特别是在早期疾病检测和精准医疗方面。",
            "current_chapter_index":
            0,
            "chapters_to_process": [{
                "chapter_title": "人工智能在医疗诊断中的应用",
                "description": "探讨AI技术在医疗诊断中的具体应用和效果"
            }]
        }

        # 调用 reflection_node
        result = await reflection_node(state=test_state,
                                       llm_client=mock_llm_client,
                                       prompt_selector=mock_prompt_selector,
                                       genre="default")

        # 验证结果
        assert "search_queries" in result
        assert len(result["search_queries"]) == 3
        assert "人工智能在医疗诊断中的最新应用" in result["search_queries"]

        # 验证 LLM 被调用
        mock_llm_client.invoke.assert_called_once()

        logger.success("✅ Reflection node 基本功能测试成功")

    except Exception as e:
        logger.error(f"❌ Reflection node 基本功能测试失败: {e}")
        return False

    return True


@patch('doc_agent.graph.chapter_workflow.nodes.settings')
async def test_reflection_node_insufficient_data(mock_settings):
    """测试 reflection_node 在数据不足时的情况"""
    logger.info("🧪 测试 reflection_node 在数据不足时的情况...")

    try:
        # 模拟设置
        mock_settings.get_agent_component_config.return_value = Mock(
            temperature=0.7, max_tokens=2000, extra_params={})

        # 模拟 LLM 客户端
        mock_llm_client = Mock(spec=LLMClient)

        # 模拟 PromptSelector
        mock_prompt_selector = Mock(spec=PromptSelector)

        # 准备测试状态（数据不足）
        test_state = {
            "topic":
            "人工智能在医疗领域的应用",
            "search_queries": ["人工智能医疗应用", "AI诊断技术"],
            "gathered_data":
            "数据很少",  # 数据不足
            "current_chapter_index":
            0,
            "chapters_to_process": [{
                "chapter_title": "人工智能在医疗诊断中的应用",
                "description": "探讨AI技术在医疗诊断中的具体应用和效果"
            }]
        }

        # 调用 reflection_node
        result = await reflection_node(state=test_state,
                                       llm_client=mock_llm_client,
                                       prompt_selector=mock_prompt_selector,
                                       genre="default")

        # 验证结果（应该返回原始查询）
        assert "search_queries" in result
        assert result["search_queries"] == test_state["search_queries"]

        # 验证 LLM 没有被调用（因为数据不足）
        mock_llm_client.invoke.assert_not_called()

        logger.success("✅ Reflection node 数据不足测试成功")

    except Exception as e:
        logger.error(f"❌ Reflection node 数据不足测试失败: {e}")
        return False

    return True


@patch('doc_agent.graph.chapter_workflow.nodes.settings')
async def test_reflection_node_no_queries(mock_settings):
    """测试 reflection_node 在没有原始查询时的情况"""
    logger.info("🧪 测试 reflection_node 在没有原始查询时的情况...")

    try:
        # 模拟设置
        mock_settings.get_agent_component_config.return_value = Mock(
            temperature=0.7, max_tokens=2000, extra_params={})

        # 模拟 LLM 客户端
        mock_llm_client = Mock(spec=LLMClient)

        # 模拟 PromptSelector
        mock_prompt_selector = Mock(spec=PromptSelector)

        # 准备测试状态（没有原始查询）
        test_state = {
            "topic":
            "人工智能在医疗领域的应用",
            "search_queries": [],  # 没有原始查询
            "gathered_data":
            "人工智能在医疗领域有广泛应用，包括医学影像分析、疾病诊断、药物发现等。",
            "current_chapter_index":
            0,
            "chapters_to_process": [{
                "chapter_title": "人工智能在医疗诊断中的应用",
                "description": "探讨AI技术在医疗诊断中的具体应用和效果"
            }]
        }

        # 调用 reflection_node
        result = await reflection_node(state=test_state,
                                       llm_client=mock_llm_client,
                                       prompt_selector=mock_prompt_selector,
                                       genre="default")

        # 验证结果（应该返回空列表）
        assert "search_queries" in result
        assert result["search_queries"] == []

        # 验证 LLM 没有被调用
        mock_llm_client.invoke.assert_not_called()

        logger.success("✅ Reflection node 无原始查询测试成功")

    except Exception as e:
        logger.error(f"❌ Reflection node 无原始查询测试失败: {e}")
        return False

    return True


if __name__ == "__main__":
    import asyncio

    # 运行所有测试
    tests = [
        test_parse_reflection_response_json,
        test_parse_reflection_response_text,
        test_parse_reflection_response_bullet_points,
        test_parse_reflection_response_quotes, test_reflection_node_basic,
        test_reflection_node_insufficient_data, test_reflection_node_no_queries
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = asyncio.run(test())
            else:
                result = test()

            if result:
                passed += 1
            print("\n" + "=" * 50 + "\n")
        except Exception as e:
            logger.error(f"❌ 测试 {test.__name__} 异常: {e}")
            print("\n" + "=" * 50 + "\n")

    logger.success(f"🎉 测试完成！通过: {passed}/{total}")

    if passed == total:
        logger.success("✅ 所有测试通过！")
    else:
        logger.error(f"❌ {total - passed} 个测试失败")
