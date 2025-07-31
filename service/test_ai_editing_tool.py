#!/usr/bin/env python3
"""
AI 编辑工具单元测试
测试 AIEditingTool 类的核心功能
"""

import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# 添加项目路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.tools.ai_editing_tool import AIEditingTool
from src.doc_agent.common.prompt_selector import PromptSelector
from src.doc_agent.llm_clients.base import LLMClient


class TestAIEditingTool(unittest.TestCase):
    """AI 编辑工具测试类"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟的 LLM 客户端
        self.mock_llm_client = Mock(spec=LLMClient)
        self.mock_llm_client.invoke.return_value = "编辑后的文本"
        
        # 创建模拟的 Prompt 选择器
        self.mock_prompt_selector = Mock(spec=PromptSelector)
        self.mock_prompt_selector.get_prompt.return_value = "测试 prompt 模板 {text}"
        
        # 创建 AI 编辑工具实例
        self.tool = AIEditingTool(
            llm_client=self.mock_llm_client,
            prompt_selector=self.mock_prompt_selector
        )
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.tool)
        self.assertEqual(self.tool.valid_actions, ["polish", "expand", "summarize"])
        self.assertIsNotNone(self.tool.logger)
    
    def test_get_available_actions(self):
        """测试获取可用操作列表"""
        actions = self.tool.get_available_actions()
        self.assertEqual(actions, ["polish", "expand", "summarize"])
        # 确保返回的是副本，不是原始列表
        self.assertIsNot(actions, self.tool.valid_actions)
    
    def test_validate_action(self):
        """测试操作验证"""
        # 测试有效操作
        self.assertTrue(self.tool.validate_action("polish"))
        self.assertTrue(self.tool.validate_action("expand"))
        self.assertTrue(self.tool.validate_action("summarize"))
        
        # 测试无效操作
        self.assertFalse(self.tool.validate_action("invalid"))
        self.assertFalse(self.tool.validate_action(""))
        self.assertFalse(self.tool.validate_action(None))
    
    def test_run_valid_action(self):
        """测试有效操作的执行"""
        test_text = "这是一个测试文本"
        
        result = self.tool.run("polish", test_text)
        
        # 验证结果
        self.assertEqual(result, "编辑后的文本")
        
        # 验证 Prompt 选择器被正确调用
        self.mock_prompt_selector.get_prompt.assert_called_once_with(
            workflow_type="prompts",
            node_name="ai_editor",
            version="polish"
        )
        
        # 验证 LLM 客户端被正确调用
        self.mock_llm_client.invoke.assert_called_once()
        call_args = self.mock_llm_client.invoke.call_args[0][0]
        self.assertIn(test_text, call_args)
    
    def test_run_invalid_action(self):
        """测试无效操作的执行"""
        with self.assertRaises(ValueError) as context:
            self.tool.run("invalid_action", "测试文本")
        
        self.assertIn("无效的编辑操作", str(context.exception))
    
    def test_run_empty_text(self):
        """测试空文本的处理"""
        with self.assertRaises(ValueError) as context:
            self.tool.run("polish", "")
        
        self.assertIn("输入文本不能为空", str(context.exception))
    
    def test_run_none_text(self):
        """测试 None 文本的处理"""
        with self.assertRaises(ValueError) as context:
            self.tool.run("polish", None)
        
        self.assertIn("输入文本不能为空", str(context.exception))
    
    def test_run_prompt_selector_error(self):
        """测试 Prompt 选择器错误处理"""
        self.mock_prompt_selector.get_prompt.side_effect = Exception("Prompt 获取失败")
        
        with self.assertRaises(Exception) as context:
            self.tool.run("polish", "测试文本")
        
        self.assertIn("获取 prompt 模板失败", str(context.exception))
    
    def test_run_llm_client_error(self):
        """测试 LLM 客户端错误处理"""
        self.mock_llm_client.invoke.side_effect = Exception("LLM 调用失败")
        
        with self.assertRaises(Exception) as context:
            self.tool.run("polish", "测试文本")
        
        self.assertIn("LLM 调用失败", str(context.exception))
    
    def test_run_all_actions(self):
        """测试所有编辑操作"""
        test_text = "测试文本"
        
        for action in self.tool.valid_actions:
            with self.subTest(action=action):
                # 重置模拟对象
                self.mock_prompt_selector.reset_mock()
                self.mock_llm_client.reset_mock()
                
                result = self.tool.run(action, test_text)
                
                # 验证结果
                self.assertEqual(result, "编辑后的文本")
                
                # 验证 Prompt 选择器被正确调用
                self.mock_prompt_selector.get_prompt.assert_called_once_with(
                    workflow_type="prompts",
                    node_name="ai_editor",
                    version=action
                )


class TestAIEditingToolIntegration(unittest.TestCase):
    """AI 编辑工具集成测试"""
    
    @patch('src.doc_agent.llm_clients.get_llm_client')
    @patch('src.doc_agent.common.prompt_selector.PromptSelector')
    def test_integration_with_real_dependencies(self, mock_prompt_selector_class, mock_get_llm_client):
        """测试与真实依赖的集成"""
        # 设置模拟
        mock_llm_client = Mock()
        mock_llm_client.invoke.return_value = "集成测试结果"
        mock_get_llm_client.return_value = mock_llm_client
        
        mock_prompt_selector = Mock()
        mock_prompt_selector.get_prompt.return_value = "集成测试 prompt {text}"
        mock_prompt_selector_class.return_value = mock_prompt_selector
        
        # 创建工具实例
        tool = AIEditingTool(
            llm_client=mock_llm_client,
            prompt_selector=mock_prompt_selector
        )
        
        # 测试执行
        result = tool.run("polish", "集成测试文本")
        
        # 验证结果
        self.assertEqual(result, "集成测试结果")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2) 