#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码执行测试
测试代码执行功能的各种场景
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
from src.doc_agent.tools.code_execute import CodeExecuteTool


class CodeExecuteTest(TestBase):
    """代码执行测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.code_tool = CodeExecuteTool()
        logger.debug("初始化代码执行测试")

    def test_basic_code_execution(self):
        """测试基础代码执行"""
        logger.info("测试基础代码执行")

        code = "print('Hello, World!')\nprint(2 + 3)"

        try:
            result = self.code_tool.execute(code)
            logger.info("基础代码执行成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("Hello, World!", result)
            self.assertIn("5", result)

            logger.debug(f"输出: {result}")

        except Exception as e:
            logger.error(f"基础代码执行失败: {e}")
            self.fail(f"基础代码执行失败: {e}")

    def test_variable_assignment(self):
        """测试变量赋值"""
        logger.info("测试变量赋值")

        code = """
x = 10
y = 20
result = x + y
print(f"x + y = {result}")
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("变量赋值测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("x + y = 30", result)

        except Exception as e:
            logger.error(f"变量赋值测试失败: {e}")
            self.fail(f"变量赋值测试失败: {e}")

    def test_function_definition(self):
        """测试函数定义"""
        logger.info("测试函数定义")

        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(5)
print(f"fibonacci(5) = {result}")
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("函数定义测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("fibonacci(5) = 5", result)

        except Exception as e:
            logger.error(f"函数定义测试失败: {e}")
            self.fail(f"函数定义测试失败: {e}")

    def test_list_operations(self):
        """测试列表操作"""
        logger.info("测试列表操作")

        code = """
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]
person = {"name": "Alice", "age": 30}

print(f"Numbers: {numbers}")
print(f"Squares: {squares}")
print(f"Person: {person}")
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("列表操作测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("Numbers: [1, 2, 3, 4, 5]", result)
            self.assertIn("Squares: [1, 4, 9, 16, 25]", result)

        except Exception as e:
            logger.error(f"列表操作测试失败: {e}")
            self.fail(f"列表操作测试失败: {e}")

    def test_error_handling(self):
        """测试错误处理"""
        logger.info("测试错误处理")

        code = "print('Hello' + )"  # 语法错误

        try:
            result = self.code_tool.execute(code)
            logger.info("错误处理测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            self.assertIn("SyntaxError", result)

        except Exception as e:
            logger.error(f"错误处理测试失败: {e}")
            self.fail(f"错误处理测试失败: {e}")

    def test_infinite_loop_prevention(self):
        """测试无限循环防护"""
        logger.info("测试无限循环防护")

        code = """
while True:
    print(f"Line {i}")
    i += 1
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("无限循环防护测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

        except Exception as e:
            logger.error(f"无限循环防护测试失败: {e}")
            self.fail(f"无限循环防护测试失败: {e}")

    def test_import_statements(self):
        """测试导入语句"""
        logger.info("测试导入语句")

        code = """
import math
import random

print(f"Pi: {math.pi}")
print(f"Random number: {random.randint(1, 100)}")
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("导入语句测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("Pi: 3.141592653589793", result)

        except Exception as e:
            logger.error(f"导入语句测试失败: {e}")
            self.fail(f"导入语句测试失败: {e}")

    def test_file_operations(self):
        """测试文件操作"""
        logger.info("测试文件操作")

        code = """
import tempfile
import os

# 创建临时文件
with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
    f.write("Hello, World!")
    temp_file = f.name

# 读取文件
with open(temp_file, 'r') as f:
    content = f.read()

print(f"File content: {content}")

# 清理
os.unlink(temp_file)
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("文件操作测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("File content: Hello, World!", result)

        except Exception as e:
            logger.error(f"文件操作测试失败: {e}")
            self.fail(f"文件操作测试失败: {e}")

    def test_mathematical_calculations(self):
        """测试数学计算"""
        logger.info("测试数学计算")

        code = """
import math

radius = 5
area = math.pi * radius**2
circumference = 2 * math.pi * radius

print(f"Radius: {radius}")
print(f"Area: {area:.2f}")
print(f"Circumference: {circumference:.2f}")
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("数学计算测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("Radius: 5", result)
            self.assertIn("Area: 78.54", result)

        except Exception as e:
            logger.error(f"数学计算测试失败: {e}")
            self.fail(f"数学计算测试失败: {e}")

    def test_string_operations(self):
        """测试字符串操作"""
        logger.info("测试字符串操作")

        code = """
text = "Hello, World, Python, Programming"

print(f"Original: {text}")
print(f"Upper: {text.upper()}")
print(f"Lower: {text.lower()}")
print(f"Length: {len(text)}")
print(f"Words: {text.split(', ')}")
"""

        try:
            result = self.code_tool.execute(code)
            logger.info("字符串操作测试成功")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("Original: Hello, World, Python, Programming",
                          result)
            self.assertIn("Upper: HELLO, WORLD, PYTHON, PROGRAMMING", result)

        except Exception as e:
            logger.error(f"字符串操作测试失败: {e}")
            self.fail(f"字符串操作测试失败: {e}")

    def test_performance(self):
        """测试性能"""
        logger.info("测试性能")

        code = "print('Quick execution')"

        import time
        start_time = time.time()

        try:
            result = self.code_tool.execute(code)
            end_time = time.time()

            execution_time = end_time - start_time
            logger.info(f"代码执行时间: {execution_time:.3f} 秒")

            # 验证结果
            self.assertIsInstance(result, str)
            self.assertIn("Quick execution", result)

            # 性能基准测试
            self.assertLess(execution_time, 5.0)  # 应该在5秒内完成

        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            self.fail(f"性能测试失败: {e}")


def main():
    """主函数"""
    logger.info("代码执行测试")

    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(CodeExecuteTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if result.wasSuccessful():
        logger.info("所有代码执行测试通过")
    else:
        logger.error("代码执行测试失败")

    return result.wasSuccessful()


if __name__ == "__main__":
    main()
