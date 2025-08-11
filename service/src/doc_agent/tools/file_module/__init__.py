"""
文件处理模块 - 独立可用的文件上传、下载和解析功能

这个模块提供了完整的文件处理功能，包括：
- 文件上传和下载
- 多种文件格式的解析
- 文件转换功能

使用示例：
    from file_module import FileProcessor
    
    # 使用默认配置（连接到远程服务器）
    processor = FileProcessor()
    
    # 下载文件
    file_path = processor.download_file("file_token", "/tmp")
    
    # 解析文件
    content = processor.parse_file(file_path, "docx")
    
    # 上传文件
    file_token = processor.upload_file("/path/to/file.docx")
"""

import os
import sys

# 添加当前模块路径到Python路径，确保可以找到子模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入主要类
try:
    from .file_processor import FileProcessor
    from .file_utils import FileUtils
    from .parsers import (WordParser, ExcelParser, PowerPointParser,
                          TextParser, MarkdownParser, HtmlParser)
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from file_processor import FileProcessor
    from file_utils import FileUtils
    from parsers import (WordParser, ExcelParser, PowerPointParser, TextParser,
                         MarkdownParser, HtmlParser)

__version__ = "1.0.0"
__author__ = "Cyber RAG Team"

# 创建全局实例
file_processor = FileProcessor()

# 便捷函数
def filetoken_to_sources(file_token: str,
                         *,
                         title: str | None = None,
                         chunk_size: int = 2000,
                         overlap: int = 200) -> list:
    """便捷函数：将 file_token 转为 Sources 列表"""
    return file_processor.filetoken_to_sources(file_token,
                                               title=title,
                                               chunk_size=chunk_size,
                                               overlap=overlap)

def filetoken_to_outline(file_token: str) -> dict | None:
    """便捷函数：将 file_token 转为 outline 对象"""
    return file_processor.filetoken_to_outline(file_token)

def filetoken_to_text(file_token: str) -> str:
    """便捷函数：将 file_token 转为文本"""
    return file_processor.filetoken_to_text(file_token)

__all__ = [
    "FileProcessor", "WordParser", "ExcelParser", "PowerPointParser",
    "TextParser", "MarkdownParser", "HtmlParser", "FileUtils",
    "file_processor",
    "filetoken_to_sources",
    "filetoken_to_outline", 
    "filetoken_to_text"
]
