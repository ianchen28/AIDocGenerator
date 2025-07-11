#!/usr/bin/env python3
"""
测试基类
提供通用的路径设置和初始化功能，确保所有测试文件都能独立运行
"""

import sys
import os
import logging
import asyncio
import atexit
from pathlib import Path


# 先设置路径，再导入环境变量加载器
def setup_paths():
    """设置Python路径"""
    # 获取当前文件所在目录
    current_dir = Path(__file__).parent

    # 添加service目录到Python路径
    service_dir = current_dir.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    # 添加项目根目录到Python路径
    project_root = service_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# 设置路径
setup_paths()

# 导入环境变量加载器（会自动加载.env文件）
from core.env_loader import load_env_file


class TestBase:
    """测试基类，提供通用的测试功能"""

    @staticmethod
    def setup_test_environment():
        """设置测试环境，确保模块路径正确"""
        # 获取当前文件所在目录
        current_file = Path(__file__)
        tests_dir = current_file.parent
        service_dir = tests_dir.parent

        # 添加service目录到Python路径
        if str(service_dir) not in sys.path:
            sys.path.insert(0, str(service_dir))

        # 添加项目根目录到Python路径（用于访问外部模块）
        project_root = service_dir.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        return service_dir, project_root

    @staticmethod
    def print_test_header(test_name: str):
        """打印测试标题"""
        print("\n" + "=" * 60)
        print(f"🚀 开始运行测试: {test_name}")
        print("=" * 60)

    @staticmethod
    def print_test_footer(test_name: str, passed: int, total: int):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print(f"📊 {test_name} 测试结果")
        print("=" * 60)
        print(f"通过: {passed}/{total}")

        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败")
        print("=" * 60)

    @staticmethod
    async def cleanup_all_es_tools():
        """清理所有ES工具"""
        try:
            # 尝试导入并清理所有ES工具
            from src.doc_agent.tools import close_all_es_tools
            await close_all_es_tools()
        except ImportError:
            # 如果导入失败，说明没有ES工具模块，忽略
            pass
        except Exception as e:
            # 在退出时，静默处理错误
            pass

    @staticmethod
    def register_exit_handlers():
        """注册退出时的清理处理器"""

        def cleanup_on_exit():
            """程序退出时的清理函数"""
            try:
                # 检查是否已经有事件循环
                try:
                    loop = asyncio.get_running_loop()
                    # 如果有运行中的循环，创建任务
                    if loop.is_running():
                        return  # 避免在运行中的循环中创建新循环
                except RuntimeError:
                    pass  # 没有运行中的循环

                # 尝试运行异步清理
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(TestBase.cleanup_all_es_tools())
                loop.close()
            except Exception as e:
                # 在退出时，静默处理错误，避免影响程序退出
                pass

        # 注册退出处理器（只在非关闭状态下注册）
        try:
            atexit.register(cleanup_on_exit)
        except Exception:
            # 如果注册失败（比如在关闭过程中），忽略错误
            pass


def setup_paths():
    """设置路径的便捷函数"""
    return TestBase.setup_test_environment()


# 自动设置环境（当模块被导入时）
if __name__ != "__main__":
    setup_paths()
    # 注册退出处理器（安全注册）
    import threading
    if threading.current_thread() is threading.main_thread():
        try:
            TestBase.register_exit_handlers()
        except Exception:
            # 如果注册失败，忽略错误
            pass
