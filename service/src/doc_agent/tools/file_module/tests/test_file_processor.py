"""
文件处理器测试
"""

import unittest
import os
import tempfile
from unittest.mock import Mock, patch

# 添加模块路径
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_module import FileProcessor, FileUtils


class TestFileProcessor(unittest.TestCase):
    """文件处理器测试类"""

    def setUp(self):
        """测试前准备"""
        self.processor = FileProcessor(
            storage_base_url="http://test-storage.com",
            app="test_app",
            app_secret="test_secret",
            tenant_id="test_tenant")

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.processor.storage_base_url,
                         "http://test-storage.com")
        self.assertEqual(self.processor.tenant_config['app'], "test_app")
        self.assertEqual(self.processor.tenant_config['app_secret'],
                         "test_secret")
        self.assertEqual(self.processor.tenant_id, "test_tenant")

    def test_check_download_url(self):
        """测试URL检查功能"""
        # 测试标准URL
        url = self.processor.check_download_url("http://test.com")
        self.assertEqual(url, "http://test.com/api/v1/sys-storage/download")

        # 测试带参数的URL
        url = self.processor.check_download_url(
            "http://test.com/api/sys-storage/download?f8s=123")
        self.assertEqual(url, "http://test.com/api/sys-storage/download")

        # 测试已包含下载路径的URL
        url = self.processor.check_download_url(
            "http://test.com/api/sys-storage/download")
        self.assertEqual(url, "http://test.com/api/sys-storage/download")

    def test_calculate_rfc2104_hmac(self):
        """测试HMAC计算"""
        data = "test_data"
        secret = "test_secret"
        hmac_result = self.processor.calculate_rfc2104_hmac(data, secret)
        self.assertIsInstance(hmac_result, str)
        self.assertGreater(len(hmac_result), 0)

    def test_build_sort_param(self):
        """测试参数排序"""
        params = {'b': '2', 'a': '1', 'c': '3'}
        result = self.processor.build_sort_param(params)
        self.assertEqual(result, "a=1&b=2&c=3")

    def test_sign(self):
        """测试签名生成"""
        params = {'test': 'value'}
        sign_result = self.processor.sign(params)

        # 检查返回的字典包含必要的键
        required_keys = ['sign', 'ts', 'ttl', 'uid', 'appId', 'test']
        for key in required_keys:
            self.assertIn(key, sign_result)

        # 检查签名值不为空
        self.assertIsInstance(sign_result['sign'], str)
        self.assertGreater(len(sign_result['sign']), 0)

    def test_build_url_with_sign(self):
        """测试带签名的URL构建"""
        base_url = "http://test.com/api/download"
        params = {'f8s': 'test_token'}
        url = self.processor.build_url_with_sign(base_url, params)

        # 检查URL包含必要的参数
        self.assertIn('sign=', url)
        self.assertIn('f8s=test_token', url)
        self.assertIn('ts=', url)
        self.assertIn('ttl=', url)

    def test_get_supported_formats(self):
        """测试支持的文件格式"""
        formats = self.processor.get_supported_formats()
        expected_formats = [
            "docx", "xlsx", "csv", "pptx", "txt", "md", "markdown", "html",
            "doc"
        ]

        for format_type in expected_formats:
            self.assertIn(format_type, formats)

    @patch('requests.get')
    def test_download_file_success(self, mock_get):
        """测试文件下载成功"""
        # 模拟成功的HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test file content"
        mock_response.headers._store = {
            'content-disposition': [None, 'filename="test.txt"']
        }
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = self.processor.download_file("test_token", tmpdir)
            self.assertTrue(os.path.exists(file_path))

    @patch('requests.get')
    def test_download_file_failure(self, mock_get):
        """测试文件下载失败"""
        # 模拟失败的HTTP响应
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(Exception):
                self.processor.download_file("invalid_token", tmpdir)

    def test_upload_file_not_implemented(self):
        """测试上传功能未实现"""
        with self.assertRaises(NotImplementedError):
            self.processor.upload_file("/path/to/file.txt")

    def test_parse_file_invalid_path(self):
        """测试解析不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.processor.parse_file("/nonexistent/file.txt", "txt")

    def test_parse_file_unsupported_format(self):
        """测试解析不支持的文件格式"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test content")
            temp_file = f.name

        try:
            with self.assertRaises(ValueError):
                self.processor.parse_file(temp_file, "xyz")
        finally:
            os.unlink(temp_file)


class TestFileUtils(unittest.TestCase):
    """文件工具类测试"""

    def test_clean_filename(self):
        """测试文件名清理"""
        # 测试包含特殊字符的文件名
        dirty_name = "file*name?.txt"
        clean_name = FileUtils.clean_filename(dirty_name)
        self.assertEqual(clean_name, "filename.txt")

        # 测试空文件名
        empty_name = ""
        clean_name = FileUtils.clean_filename(empty_name)
        self.assertEqual(clean_name, "unnamed_file")

    def test_get_file_extension(self):
        """测试文件扩展名获取"""
        # 测试正常文件路径
        extension = FileUtils.get_file_extension("/path/to/file.txt")
        self.assertEqual(extension, ".txt")

        # 测试无扩展名文件
        extension = FileUtils.get_file_extension("/path/to/file")
        self.assertEqual(extension, "")

        # 测试大写扩展名
        extension = FileUtils.get_file_extension("/path/to/file.TXT")
        self.assertEqual(extension, ".txt")

    def test_get_file_name(self):
        """测试文件名获取"""
        # 测试正常文件路径
        filename = FileUtils.get_file_name("/path/to/file.txt")
        self.assertEqual(filename, "file.txt")

        # 测试只有文件名的路径
        filename = FileUtils.get_file_name("file.txt")
        self.assertEqual(filename, "file.txt")

    def test_is_text_file(self):
        """测试文本文件判断"""
        # 测试文本文件
        self.assertTrue(FileUtils.is_text_file("/path/to/file.txt"))
        self.assertTrue(FileUtils.is_text_file("/path/to/file.md"))
        self.assertTrue(FileUtils.is_text_file("/path/to/file.py"))

        # 测试非文本文件
        self.assertFalse(FileUtils.is_text_file("/path/to/file.docx"))
        self.assertFalse(FileUtils.is_text_file("/path/to/file.xlsx"))

    def test_get_mime_type(self):
        """测试MIME类型获取"""
        # 测试文本文件
        mime_type = FileUtils.get_mime_type("/path/to/file.txt")
        self.assertEqual(mime_type, "text/plain")

        # 测试未知类型
        mime_type = FileUtils.get_mime_type("/path/to/file.xyz")
        self.assertEqual(mime_type, "application/octet-stream")


if __name__ == '__main__':
    unittest.main()
