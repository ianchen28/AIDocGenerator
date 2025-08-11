"""
文件工具类 - 提供文件名清理、路径标准化等通用功能
"""

import os
import platform
from pathlib import Path
from typing import Optional


class FileUtils:
    """
    文件工具类，提供各种文件处理相关的工具方法
    """

    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        清理文件名，移除Windows和Linux不允许的特殊字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除或替换不允许的字符
        invalid_chars = ['*', '?', '|', '\\', '/', ':', '"', '<', '>']
        for char in invalid_chars:
            filename = filename.replace(char, '')

        # 移除前后空格
        filename = filename.strip()

        # 如果文件名为空，使用默认名称
        if not filename:
            filename = "unnamed_file"

        return filename

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        标准化路径，确保使用正确的路径分隔符
        
        Args:
            path: 原始路径
            
        Returns:
            标准化后的路径
        """
        try:
            # 使用 pathlib 来处理路径
            path_obj = Path(path)
            # 转换为绝对路径并规范化
            normalized_path = str(path_obj.resolve())
            # 确保路径存在
            os.makedirs(normalized_path, exist_ok=True)
            return normalized_path
        except Exception as e:
            raise Exception(f"路径处理失败: {str(e)}")

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        获取文件扩展名
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件扩展名（小写，包含点号）
        """
        return os.path.splitext(file_path)[1].lower()

    @staticmethod
    def get_file_name(file_path: str) -> str:
        """
        获取文件名（不包含路径）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件名
        """
        return os.path.basename(file_path)

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        return os.path.getsize(file_path)

    @staticmethod
    def is_file_readable(file_path: str) -> bool:
        """
        检查文件是否可读
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否可读
        """
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)

    @staticmethod
    def create_temp_file(prefix: str = "temp_",
                         suffix: str = "",
                         directory: Optional[str] = None) -> str:
        """
        创建临时文件
        
        Args:
            prefix: 文件名前缀
            suffix: 文件名后缀
            directory: 临时文件目录（可选）
            
        Returns:
            临时文件路径
        """
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(prefix=prefix,
                                                suffix=suffix,
                                                dir=directory,
                                                delete=False)
        temp_file.close()
        return temp_file.name

    @staticmethod
    def ensure_directory_exists(directory_path: str) -> str:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            directory_path: 目录路径
            
        Returns:
            标准化后的目录路径
        """
        normalized_path = FileUtils.normalize_path(directory_path)
        os.makedirs(normalized_path, exist_ok=True)
        return normalized_path

    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """
        获取安全的文件名，确保长度不超过限制
        
        Args:
            filename: 原始文件名
            max_length: 最大长度限制
            
        Returns:
            安全的文件名
        """
        # 清理文件名
        safe_name = FileUtils.clean_filename(filename)

        # 如果文件名超过最大长度，进行截断
        if len(safe_name) > max_length:
            # 保留扩展名
            name, ext = os.path.splitext(safe_name)
            # 计算可用的名称长度
            available_length = max_length - len(ext)
            if available_length > 0:
                safe_name = name[:available_length] + ext
            else:
                # 如果扩展名太长，只保留扩展名
                safe_name = ext[:max_length]

        return safe_name

    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """
        获取文件的MIME类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            MIME类型
        """
        import mimetypes

        # 根据文件扩展名猜测MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type is None:
            # 如果无法猜测，返回通用二进制类型
            mime_type = "application/octet-stream"

        return mime_type

    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """
        判断是否为文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为文本文件
        """
        text_extensions = {
            '.txt', '.md', '.markdown', '.py', '.js', '.html', '.htm', '.css',
            '.json', '.xml', '.csv', '.log', '.ini', '.cfg', '.conf', '.sh',
            '.bat', '.ps1', '.sql', '.yaml', '.yml'
        }

        ext = FileUtils.get_file_extension(file_path)
        return ext in text_extensions

    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        获取文件的详细信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        stat_info = os.stat(file_path)

        return {
            'name': FileUtils.get_file_name(file_path),
            'path': file_path,
            'size': stat_info.st_size,
            'extension': FileUtils.get_file_extension(file_path),
            'mime_type': FileUtils.get_mime_type(file_path),
            'is_text': FileUtils.is_text_file(file_path),
            'created_time': stat_info.st_ctime,
            'modified_time': stat_info.st_mtime,
            'accessed_time': stat_info.st_atime,
            'is_readable': FileUtils.is_file_readable(file_path)
        }
