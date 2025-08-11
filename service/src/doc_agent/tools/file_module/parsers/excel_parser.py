"""
Excel文件解析器 - 解析.xlsx和.csv文件内容
"""

import os
import pandas as pd
from typing import List


class ExcelParser:
    """
    Excel文件解析器，支持.xlsx和.csv格式
    """

    def __init__(self):
        pass

    def parsing(self, file_path):
        """
        解析Excel文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的内容列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == '.csv':
                return self._parse_csv(file_path)
            elif file_extension == '.xlsx':
                return self._parse_xlsx(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
        except Exception as e:
            raise Exception(f"解析Excel文件失败: {str(e)}")

    def _parse_csv(self, file_path):
        """
        解析CSV文件
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            解析后的内容列表
        """
        try:
            # 尝试不同的编码方式读取CSV
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise Exception("无法读取CSV文件，请检查文件编码")

            return self._process_dataframe(df)

        except Exception as e:
            raise Exception(f"解析CSV文件失败: {str(e)}")

    def _parse_xlsx(self, file_path):
        """
        解析XLSX文件
        
        Args:
            file_path: XLSX文件路径
            
        Returns:
            解析后的内容列表
        """
        try:
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            all_content = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_content = self._process_dataframe(df, sheet_name)
                all_content.extend(sheet_content)

            return all_content

        except Exception as e:
            raise Exception(f"解析XLSX文件失败: {str(e)}")

    def _process_dataframe(self, df, sheet_name=None):
        """
        处理DataFrame数据
        
        Args:
            df: pandas DataFrame对象
            sheet_name: 工作表名称（可选）
            
        Returns:
            处理后的内容列表
        """
        result = []

        # 处理表头
        if not df.empty:
            header_text = " | ".join([str(col) for col in df.columns])
            if sheet_name:
                header_text = f"[{sheet_name}] {header_text}"
            result.append(['paragraph', header_text, [[0, 0, 0, 0]], [0], [0]])

        # 处理数据行
        for index, row in df.iterrows():
            row_text = " | ".join([str(cell) for cell in row.values])

            # 检查内容长度
            if len(row_text) > 4096:
                # 分割长内容
                chunks = [
                    row_text[i:i + 4096]
                    for i in range(0, len(row_text), 4096)
                ]
                for chunk in chunks:
                    result.append(
                        ['paragraph', chunk, [[0, 0, 0, 0]], [0], [0]])
            else:
                result.append(
                    ['paragraph', row_text, [[0, 0, 0, 0]], [0], [0]])

        return result
