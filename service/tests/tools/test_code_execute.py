import subprocess
from unittest.mock import MagicMock, patch

from doc_agent.tools.code_execute import CodeExecuteTool


class TestCodeExecuteTool:
    """CodeExecuteTool测试类"""

    def test_execution_success(self):
        """测试成功执行代码"""
        # 配置mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "hello world"
        mock_process.stderr = ""

        with patch('subprocess.run', return_value=mock_process) as mock_run:
            # 实例化工具
            tool = CodeExecuteTool()

            # 执行测试代码
            result = tool.execute("print('hello world')")

            # 验证结果
            assert "hello world" in result
            assert mock_run.called

            # 验证subprocess.run的调用参数
            call_args = mock_run.call_args
            assert call_args[0][0][0] == 'python'  # 第一个参数是命令列表，第一个元素是'python'
            assert call_args[0][0][1].endswith('.py')  # 第二个元素是临时文件路径
            assert call_args[1]['capture_output'] is True
            assert call_args[1]['text'] is True
            assert call_args[1]['timeout'] == 5  # 默认超时时间

    def test_execution_with_error(self):
        """测试执行出错的情况"""
        # 配置mock模拟执行错误
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "NameError: name 'undefined_var' is not defined"

        with patch('subprocess.run', return_value=mock_process) as mock_run:
            # 实例化工具
            tool = CodeExecuteTool()

            # 执行有错误的代码
            result = tool.execute("print(undefined_var)")

            # 验证结果包含错误信息
            assert "NameError" in result
            assert "undefined_var" in result
            assert mock_run.called

    def test_execution_with_timeout(self):
        """测试执行超时的情况"""
        with patch('subprocess.run',
                   side_effect=subprocess.TimeoutExpired(['python', 'test.py'],
                                                         5)) as mock_run:
            # 实例化工具
            tool = CodeExecuteTool()

            # 执行会超时的代码
            result = tool.execute("import time; time.sleep(10)")

            # 验证超时处理
            assert "代码执行超时" in result
            assert mock_run.called

    def test_execution_with_general_exception(self):
        """测试一般异常情况"""
        with patch('subprocess.run',
                   side_effect=Exception("文件不存在")) as mock_run:
            # 实例化工具
            tool = CodeExecuteTool()

            # 执行会出错的代码
            result = tool.execute("print('test')")

            # 验证异常处理
            assert "执行出错" in result
            assert "文件不存在" in result
            assert mock_run.called

    def test_execution_with_custom_timeout(self):
        """测试自定义超时时间"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "custom timeout test"
        mock_process.stderr = ""

        with patch('subprocess.run', return_value=mock_process) as mock_run:
            # 实例化工具
            tool = CodeExecuteTool()

            # 使用自定义超时时间执行代码
            result = tool.execute("print('custom timeout test')", timeout=10)

            # 验证结果
            assert "custom timeout test" in result
            assert mock_run.called

            # 验证自定义超时时间被正确传递
            call_args = mock_run.call_args
            assert call_args[1]['timeout'] == 10

    def test_execution_with_both_stdout_and_stderr(self):
        """测试同时有stdout和stderr的情况"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "正常输出"
        mock_process.stderr = "警告信息"

        with patch('subprocess.run', return_value=mock_process) as mock_run:
            # 实例化工具
            tool = CodeExecuteTool()

            # 执行代码
            result = tool.execute(
                "print('正常输出'); import warnings; warnings.warn('警告信息')")

            # 验证结果包含stdout和stderr
            assert "正常输出" in result
            assert "警告信息" in result
            assert mock_run.called

    def test_tool_initialization(self):
        """测试工具初始化"""
        tool = CodeExecuteTool()
        assert tool is not None
        assert hasattr(tool, 'execute')
        assert callable(tool.execute)

    def test_empty_code_execution(self):
        """测试空代码执行"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""

        with patch('subprocess.run', return_value=mock_process) as mock_run:
            tool = CodeExecuteTool()
            result = tool.execute("")

            # 验证空代码也能正常处理
            assert result == ""
            assert mock_run.called
