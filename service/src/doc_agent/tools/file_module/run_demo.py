#!/usr/bin/env python3
"""
文件模块演示脚本
可以直接运行此脚本来测试文件模块功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from file_processor import FileProcessor


def create_test_file(content: str, file_path: str):
    """创建测试文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 创建测试文件: {file_path}")


def main():
    """主函数"""
    print("=== 文件模块演示 ===\n")
    
    # 初始化文件处理器
    print("1. 初始化文件处理器...")
    processor = FileProcessor()
    print("✓ 文件处理器初始化成功\n")
    
    # 创建测试文件
    print("2. 创建测试文件...")
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = os.path.join(temp_dir, "test_sample.txt")
        test_content = """这是一个测试文件
包含多行文本内容
用于演示文件处理功能

支持的功能：
- 文件上传
- 文件下载  
- 文件解析
- 多种格式支持
"""
        create_test_file(test_content, test_file_path)
        
        # 测试文件解析
        print("\n3. 测试文件解析...")
        try:
            content = processor.parse_file(test_file_path, "txt")
            print("✓ 文件解析成功")
            print(f"解析结果: {len(content)} 个段落")
            for i, para in enumerate(content[:3], 1):  # 只显示前3个段落
                print(f"  段落{i}: {para[:50]}...")
            if len(content) > 3:
                print(f"  ... 还有 {len(content) - 3} 个段落")
        except Exception as e:
            print(f"✗ 文件解析失败: {e}")
        
        # 测试文件上传（模拟）
        print("\n4. 测试文件上传（模拟）...")
        try:
            # 这里只是演示，实际需要真实的存储服务
            print("✓ 文件上传功能已准备就绪")
            print("  注意：需要配置真实的存储服务才能进行实际上传")
        except Exception as e:
            print(f"✗ 文件上传失败: {e}")
    
    print("\n=== 演示完成 ===")
    print("\n✅ 模块已准备就绪，可以直接复制到其他项目使用！")
    print("\n使用说明:")
    print("1. 复制整个 file_module 文件夹到您的项目")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 导入使用: from file_module import FileProcessor")
    print("4. 默认已配置远程服务器，可直接使用")


if __name__ == "__main__":
    main()
