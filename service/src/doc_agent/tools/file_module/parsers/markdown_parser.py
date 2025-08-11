"""
Markdown文件解析器 - 解析.md文件内容
"""

import os
import re
from typing import List


class MarkdownParser:
    """
    Markdown文件解析器，支持.md和.markdown格式
    """

    def __init__(self):
        pass

    def parsing(self, file_path):
        """
        解析Markdown文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的内容列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析Markdown内容
            return self._parse_markdown_content(content)

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return self._parse_markdown_content(content)
            except Exception as e:
                raise Exception(f"无法读取Markdown文件: {str(e)}")
        except Exception as e:
            raise Exception(f"解析Markdown文件失败: {str(e)}")

    def _parse_markdown_content(self, content):
        """
        解析Markdown内容
        
        Args:
            content: Markdown文本内容
            
        Returns:
            解析后的内容列表
        """
        # 按段落分割内容
        paragraphs = self._split_into_paragraphs(content)
        result = []

        for paragraph in paragraphs:
            if paragraph.strip():
                # 清理Markdown语法
                cleaned_text = self._clean_markdown_syntax(paragraph)

                # 检查内容长度
                if len(cleaned_text) > 4096:
                    # 分割长内容
                    chunks = [
                        cleaned_text[i:i + 4096]
                        for i in range(0, len(cleaned_text), 4096)
                    ]
                    for chunk in chunks:
                        result.append(
                            ['paragraph', chunk, [[0, 0, 0, 0]], [0], [0]])
                else:
                    result.append(
                        ['paragraph', cleaned_text, [[0, 0, 0, 0]], [0], [0]])

        return result

    def _split_into_paragraphs(self, content):
        """
        将内容分割成段落
        
        Args:
            content: 原始内容
            
        Returns:
            段落列表
        """
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _clean_markdown_syntax(self, text):
        """
        清理Markdown语法标记
        
        Args:
            text: 包含Markdown语法的文本
            
        Returns:
            清理后的文本
        """
        # 移除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text)

        # 移除粗体和斜体标记
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 粗体
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # 斜体
        text = re.sub(r'__(.*?)__', r'\1', text)  # 粗体
        text = re.sub(r'_(.*?)_', r'\1', text)  # 斜体

        # 移除代码标记
        text = re.sub(r'`(.*?)`', r'\1', text)  # 行内代码
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)  # 代码块

        # 移除链接标记
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # 移除图片标记
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

        # 移除列表标记
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)

        # 移除引用标记
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # 移除水平分割线
        text = re.sub(r'^[\s]*[-*_]{3,}[\s]*$', '', text, flags=re.MULTILINE)

        # 清理多余的空行和空格
        text = re.sub(r'\n\s*\n', '\n', text)
        text = text.strip()

        return text
