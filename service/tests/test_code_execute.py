import pytest
from test_base import TestBase
from src.doc_agent.tools.code_execute import CodeExecuteTool


class TestCodeExecuteTool(TestBase):
    """代码执行工具测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.tool = CodeExecuteTool()

    def test_basic_python_execution(self):
        """测试基本的Python代码执行"""
        code = "print('Hello, World!')\nprint(2 + 3)"
        result = self.tool.execute(code)

        assert "Hello, World!" in result
        assert "5" in result
        assert "代码执行超时" not in result
        assert "执行出错" not in result

    def test_variable_assignment_and_calculation(self):
        """测试变量赋值和计算"""
        code = """
x = 10
y = 20
result = x + y
print(f"x + y = {result}")
"""
        result = self.tool.execute(code)

        assert "x + y = 30" in result
        assert "代码执行超时" not in result
        assert "执行出错" not in result

    def test_function_definition_and_call(self):
        """测试函数定义和调用"""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(5)
print(f"fibonacci(5) = {result}")
"""
        result = self.tool.execute(code)

        assert "fibonacci(5) = 5" in result
        assert "代码执行超时" not in result
        assert "执行出错" not in result

    def test_list_and_dictionary_operations(self):
        """测试列表和字典操作"""
        code = """
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]
print(f"Numbers: {numbers}")
print(f"Squares: {squares}")

person = {"name": "Alice", "age": 30}
print(f"Person: {person}")
"""
        result = self.tool.execute(code)

        assert "Numbers: [1, 2, 3, 4, 5]" in result
        assert "Squares: [1, 4, 9, 16, 25]" in result
        assert "Person: {'name': 'Alice', 'age': 30}" in result

    def test_error_handling(self):
        """测试错误处理"""
        code = """
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
"""
        result = self.tool.execute(code)

        assert "Error: division by zero" in result
        assert "代码执行超时" not in result
        assert "执行出错" not in result

    def test_syntax_error(self):
        """测试语法错误处理"""
        code = "print('Hello' + )"  # 语法错误
        result = self.tool.execute(code)

        assert "SyntaxError" in result or "语法错误" in result

    def test_timeout_handling(self):
        """测试超时处理"""
        code = """
import time
time.sleep(10)  # 睡眠10秒
print("This should not be reached")
"""
        result = self.tool.execute(code, timeout=1)

        assert "代码执行超时" in result

    def test_large_output(self):
        """测试大量输出"""
        code = """
for i in range(1000):
    print(f"Line {i}")
"""
        result = self.tool.execute(code)

        assert "Line 0" in result
        assert "Line 999" in result
        # TODO: 后续应该限制输出长度

    def test_import_modules(self):
        """测试模块导入"""
        code = """
import math
import random

print(f"Pi: {math.pi}")
print(f"Random number: {random.randint(1, 100)}")
"""
        result = self.tool.execute(code)

        assert "Pi: 3.141592653589793" in result
        assert "Random number:" in result

    def test_file_operations(self):
        """测试文件操作（临时文件）"""
        code = """
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
    f.write("Hello from temp file")
    temp_path = f.name

with open(temp_path, 'r') as f:
    content = f.read()
    print(f"File content: {content}")

os.unlink(temp_path)  # 清理临时文件
"""
        result = self.tool.execute(code)

        assert "File content: Hello from temp file" in result

    def test_empty_code(self):
        """测试空代码"""
        result = self.tool.execute("")

        assert result == "" or "执行出错" not in result

    def test_whitespace_only_code(self):
        """测试只有空白字符的代码"""
        result = self.tool.execute("   \n\t\n   ")

        assert result == "" or "执行出错" not in result

    def test_complex_calculation(self):
        """测试复杂计算"""
        code = """
import math

def calculate_area(radius):
    return math.pi * radius ** 2

def calculate_circumference(radius):
    return 2 * math.pi * radius

radius = 5
area = calculate_area(radius)
circumference = calculate_circumference(radius)

print(f"Radius: {radius}")
print(f"Area: {area:.2f}")
print(f"Circumference: {circumference:.2f}")
"""
        result = self.tool.execute(code)

        assert "Radius: 5" in result
        assert "Area: 78.54" in result
        assert "Circumference: 31.42" in result

    def test_string_operations(self):
        """测试字符串操作"""
        code = """
text = "Hello, World!"
print(f"Original: {text}")
print(f"Upper: {text.upper()}")
print(f"Lower: {text.lower()}")
print(f"Length: {len(text)}")
print(f"Words: {text.split(', ')}")
"""
        result = self.tool.execute(code)

        assert "Original: Hello, World!" in result
        assert "Upper: HELLO, WORLD!" in result
        assert "Lower: hello, world!" in result
        assert "Length: 13" in result
        assert "Words: ['Hello', 'World!']" in result

    def test_custom_timeout(self):
        """测试自定义超时时间"""
        code = "print('Quick execution')"
        result = self.tool.execute(code, timeout=1)

        assert "Quick execution" in result
        assert "代码执行超时" not in result

    def test_infinite_loop_timeout(self):
        """测试无限循环超时"""
        code = """
while True:
    pass
"""
        result = self.tool.execute(code, timeout=1)

        assert "代码执行超时" in result

    # TODO: 安全性测试（需要更安全的沙箱环境）
    def test_security_concerns(self):
        """测试安全相关问题（标记为TODO）"""
        # 这些测试在基础版本中暂时跳过，等升级到安全沙箱后再实现
        pytest.skip("安全性测试需要更安全的沙箱环境")

        # TODO: 测试以下安全场景：
        # 1. 文件系统访问限制
        # 2. 网络访问限制
        # 3. 系统命令执行限制
        # 4. 内存使用限制
        # 5. CPU使用限制
        # 6. 输出长度限制


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
