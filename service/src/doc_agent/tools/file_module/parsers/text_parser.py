"""
文本文件解析器 - 解析.txt文件内容
"""

import os
import chardet
from typing import List


class TextParser:
    """
    文本文件解析器，支持多种编码格式
    """

    def __init__(self):
        self.chunk_separator = '\n'  # 默认分隔符

    def parsing(self, txt_file):
        """
        解析文本文件内容
        
        Args:
            txt_file: 文本文件路径
            
        Returns:
            解析后的内容列表
        """
        if not os.path.exists(txt_file):
            raise FileNotFoundError(f"文件不存在: {txt_file}")

        # 使用chardet检测文件编码
        with open(txt_file, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        # 如果检测到的编码是 None 或者置信度太低，尝试使用 UTF-8
        if encoding is None or result['confidence'] < 0.6:
            try:
                # 尝试用 UTF-8 解码
                with open(txt_file, encoding='utf-8') as f:
                    f.read()
                encoding = 'utf-8'
            except UnicodeDecodeError:
                # 如果 UTF-8 解码失败，再尝试其他编码
                try:
                    with open(txt_file, encoding='gbk') as f:
                        f.read()
                    encoding = 'gbk'
                except UnicodeDecodeError:
                    raise Exception("无法检测文件编码，请检查文件编码格式")

        if encoding is None:
            raise Exception("无法检测文件编码")

        try:
            with open(txt_file, encoding=encoding) as f:
                txt_content = f.read()
        except Exception as e:
            raise Exception(f"读取文件时发生错误: {str(e)}")

        # 按分隔符分割内容
        chunks = txt_content.split(self.chunk_separator)
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        # 准备结果
        result_res = []

        for idx, content in enumerate(chunks):
            # 检查内容是否超过4096字符
            if len(content) > 4096:
                # 进一步分割大块内容
                sub_chunks = self._split_large_chunk(content)
                for sub_content in sub_chunks:
                    result_res.append(
                        ['paragraph', sub_content, [[0, 0, 0, 0]], [0], [0]])
            else:
                result_res.append(
                    ['paragraph', content, [[0, 0, 0, 0]], [0], [0]])

        return result_res

    def _split_large_chunk(self, content, max_length=4000):
        """
        将大块文本分割成更小的片段
        
        Args:
            content: 要分割的内容
            max_length: 每个片段的最大长度（默认: 4000）
            
        Returns:
            较小的内容片段列表
        """
        # 使用稍小的max_length确保不超过4096
        result = []

        # 如果内容有自然的句子分隔符，使用这些分隔符
        sentences = content.replace('. ', '.\n').replace('! ', '!\n').replace(
            '? ', '?\n').split('\n')

        current_chunk = ""
        for sentence in sentences:
            # 如果添加这个句子会超过max_length
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    result.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # 如果单个句子就超过max_length，强制分割
                    result.append(sentence[:max_length])
                    current_chunk = sentence[max_length:]
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # 添加最后一个块
        if current_chunk:
            result.append(current_chunk.strip())

        return result
