"""
基本使用示例 - 演示文件模块的基本功能
"""

import os
import sys

# 添加模块路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_module import FileProcessor, WordParser, TextParser, FileUtils


def basic_usage_example():
    """基本使用示例"""
    print("=== 文件模块基本使用示例 ===\n")

    # 1. 初始化文件处理器
    print("1. 初始化文件处理器...")
    processor = FileProcessor(
        storage_base_url="http://your-storage-service.com",
        app="your_app",
        app_secret="your_secret",
        tenant_id="your_tenant")
    print("✓ 文件处理器初始化完成\n")

    # 2. 获取支持的文件格式
    print("2. 获取支持的文件格式...")
    supported_formats = processor.get_supported_formats()
    print(f"支持的文件格式: {', '.join(supported_formats)}\n")

    # 3. 使用工具函数
    print("3. 使用文件工具函数...")

    # 清理文件名
    dirty_filename = "file*name?.txt"
    clean_filename = FileUtils.clean_filename(dirty_filename)
    print(f"文件名清理: '{dirty_filename}' -> '{clean_filename}'")

    # 标准化路径
    path = "./temp/dir"
    normalized_path = FileUtils.normalize_path(path)
    print(f"路径标准化: '{path}' -> '{normalized_path}'")

    # 获取文件扩展名
    file_path = "/path/to/document.docx"
    extension = FileUtils.get_file_extension(file_path)
    print(f"文件扩展名: '{file_path}' -> '{extension}'")

    print("✓ 工具函数使用完成\n")


def parser_example():
    """解析器使用示例"""
    print("=== 解析器使用示例 ===\n")

    # 创建示例文件
    create_sample_files()

    # 1. Word文档解析
    print("1. Word文档解析...")
    try:
        word_parser = WordParser()
        # 注意：这里需要有一个实际的.docx文件
        # content = word_parser.parsing("sample.docx")
        print("✓ Word解析器初始化完成")
    except Exception as e:
        print(f"✗ Word解析器错误: {e}")

    # 2. 文本文件解析
    print("2. 文本文件解析...")
    try:
        text_parser = TextParser()
        # 注意：这里需要有一个实际的.txt文件
        # content = text_parser.parsing("sample.txt")
        print("✓ 文本解析器初始化完成")
    except Exception as e:
        print(f"✗ 文本解析器错误: {e}")

    print("✓ 解析器示例完成\n")


def create_sample_files():
    """创建示例文件"""
    # 创建示例文本文件
    sample_text = """这是一个示例文本文件。

包含多个段落的内容。

用于演示文本解析功能。

支持中文和英文内容。
This is English content.
"""

    try:
        with open("sample.txt", "w", encoding="utf-8") as f:
            f.write(sample_text)
        print("✓ 创建示例文本文件: sample.txt")
    except Exception as e:
        print(f"✗ 创建示例文件失败: {e}")


def download_example():
    """下载功能示例"""
    print("=== 下载功能示例 ===\n")

    processor = FileProcessor(
        storage_base_url="http://your-storage-service.com",
        app="your_app",
        app_secret="your_secret",
        tenant_id="your_tenant")

    # 生成下载URL
    print("1. 生成下载URL...")
    try:
        file_token = "example_token"
        download_url = processor.generate_download_url(file_token)
        print(f"下载URL: {download_url}")
        print("✓ URL生成完成")
    except Exception as e:
        print(f"✗ URL生成失败: {e}")

    print("✓ 下载功能示例完成\n")


def main():
    """主函数"""
    print("文件模块示例程序\n")

    # 运行基本使用示例
    basic_usage_example()

    # 运行解析器示例
    parser_example()

    # 运行下载示例
    download_example()

    print("=== 示例程序完成 ===")
    print("\n注意事项:")
    print("1. 请根据实际情况配置存储服务参数")
    print("2. 确保有实际的文件用于解析测试")
    print("3. 查看README.md了解更多使用方法")


if __name__ == "__main__":
    main()
