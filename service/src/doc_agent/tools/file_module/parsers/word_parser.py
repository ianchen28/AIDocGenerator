"""
Word文档解析器 - 解析.docx文件内容
"""

import os
from typing import List

from docx import Document
from docx.document import Document as doctwo
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph


class WordParser:
    """
    Word文档解析器，支持.docx格式
    """

    def __init__(self):
        pass

    def iter_block_items(self, parent):
        """
        遍历文档中的段落和表格元素
        
        Args:
            parent: 父元素（通常是Document对象或Cell对象）
            
        Yields:
            段落或表格元素
        """
        if isinstance(parent, doctwo):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("不支持的父元素类型")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    def parse_docx(self, document):
        """
        解析Word文档内容
        
        Args:
            document: Document对象
            
        Returns:
            段落文本列表
        """
        paragraphs_text = []
        items = self.iter_block_items(document)

        for item in items:
            if isinstance(item, Paragraph):
                paragraphs_text.append(item.text)
            elif isinstance(item, Table):
                for row in item.rows:
                    try:
                        row_text = ' '.join(
                            [cell.text.strip() for cell in row.cells])
                        paragraphs_text.append(row_text)
                    except:
                        pass
        return paragraphs_text

    def merge_consecutive_elements(self, paragraphs_text, max_chars=4096):
        """
        合并连续的文本元素，确保每个合并后的元素不超过指定的字符数量
        
        Args:
            paragraphs_text: 段落文本列表
            max_chars: 最大字符数限制（默认4096）
            
        Returns:
            合并后的文本列表
        """
        if not paragraphs_text:
            return []

        merged_texts = []
        current_text = paragraphs_text[0]

        for i in range(1, len(paragraphs_text)):
            next_text = paragraphs_text[i]
            # 检查合并后是否超过字符限制
            if len(current_text) + len(
                    next_text) + 1 <= max_chars:  # +1 是为了考虑换行符
                current_text += '\n' + next_text
            else:
                merged_texts.append(current_text)
                current_text = next_text

        # 添加最后一个合并结果
        merged_texts.append(current_text)

        return merged_texts

    def to_uniformed_format(self, paragraphs):
        """
        转换为统一格式
        
        Args:
            paragraphs: 段落列表
            
        Returns:
            统一格式的结果列表
        """
        res_list = []
        for item in paragraphs:
            res_item = ['paragraph', item + '\n', [[0, 0, 0, 0]], [0], [0]]
            res_list.append(res_item)
        return res_list

    def parsing(self, file_path):
        """
        解析Word文档文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的内容列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取docx文件
        doc_infos = Document(file_path)

        # 解析内容
        contents = self.parse_docx(doc_infos)

        # 应用合并功能，确保每个元素不超过4096字符
        merged_contents = self.merge_consecutive_elements(contents,
                                                          max_chars=4096)

        # 再次检查并拆分任何超过4096字符的元素
        final_contents = []
        for content in merged_contents:
            if len(content) <= 4096:
                final_contents.append(content)
            else:
                # 如果仍有超过4096字符的元素，进一步拆分
                chunks = [
                    content[i:i + 4096] for i in range(0, len(content), 4096)
                ]
                final_contents.extend(chunks)

        res_dict = self.to_uniformed_format(final_contents)
        return res_dict
