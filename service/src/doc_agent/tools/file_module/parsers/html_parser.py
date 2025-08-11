"""
HTML文件解析器 - 解析.html文件内容
"""

import os
import re
from typing import List
from bs4 import BeautifulSoup

class HtmlParser:
    """
    HTML文件解析器，支持.html和.htm格式
    """
    
    def __init__(self):
        pass
    
    def parsing(self, file_path):
        """
        解析HTML文件内容
        
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
            
            # 解析HTML内容
            return self._parse_html_content(content)
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return self._parse_html_content(content)
            except Exception as e:
                raise Exception(f"无法读取HTML文件: {str(e)}")
        except Exception as e:
            raise Exception(f"解析HTML文件失败: {str(e)}")
    
    def _parse_html_content(self, content):
        """
        解析HTML内容
        
        Args:
            content: HTML文本内容
            
        Returns:
            解析后的内容列表
        """
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本内容
            text_content = soup.get_text()
            
            # 清理文本
            cleaned_text = self._clean_text(text_content)
            
            # 按段落分割
            paragraphs = self._split_into_paragraphs(cleaned_text)
            
            result = []
            for paragraph in paragraphs:
                if paragraph.strip():
                    # 检查内容长度
                    if len(paragraph) > 4096:
                        # 分割长内容
                        chunks = [paragraph[i:i+4096] for i in range(0, len(paragraph), 4096)]
                        for chunk in chunks:
                            result.append(['paragraph', chunk, [[0,0,0,0]], [0], [0]])
                    else:
                        result.append(['paragraph', paragraph, [[0,0,0,0]], [0], [0]])
            
            return result
            
        except Exception as e:
            raise Exception(f"解析HTML内容失败: {str(e)}")
    
    def _clean_text(self, text):
        """
        清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除空行
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # 移除行首行尾空白
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _split_into_paragraphs(self, text):
        """
        将文本分割成段落
        
        Args:
            text: 文本内容
            
        Returns:
            段落列表
        """
        # 按换行符分割段落
        paragraphs = text.split('\n')
        
        # 过滤空段落并清理
        return [p.strip() for p in paragraphs if p.strip()]
