"""
文件处理器 - 整合上传、下载和解析功能的主类
"""

import os
import sys
import re
import platform
from pathlib import Path
import unicodedata
import traceback
import requests
from urllib.parse import quote, unquote
import hmac
import hashlib
import base64
import time
import logging
import json
import mimetypes
import tempfile
import shutil
from typing import Dict, List, Optional, Union, Tuple

import httpx
from bs4 import BeautifulSoup

# 使用相对导入，支持独立运行
try:
    from .file_utils import FileUtils
    from .parsers import (WordParser, ExcelParser, PowerPointParser,
                          TextParser, MarkdownParser, HtmlParser)
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from file_utils import FileUtils
    from parsers import (WordParser, ExcelParser, PowerPointParser, TextParser,
                         MarkdownParser, HtmlParser)

# 尝试导入Source类
try:
    from doc_agent.schemas import Source
except ImportError:
    # 如果导入失败，定义一个简单的Source类
    class Source:

        def __init__(self, id: int, sourceType: str, title: str, url: str,
                     content: str):
            self.id = id
            self.sourceType = sourceType
            self.title = title
            self.url = url
            self.content = content


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileProcessor:
    """
    文件处理器 - 提供完整的文件上传、下载和解析功能
    """

    def __init__(self,
                 storage_base_url: str = "http://ai.test.hcece.net",
                 app: str = "hdec",
                 app_secret: str = "hdec_secret",
                 tenant_id: str = "100023",
                 file_transform_url: Optional[str] = None):
        """
        初始化文件处理器
        
        Args:
            storage_base_url: 存储服务的基础URL
            app: 应用标识
            app_secret: 应用密钥
            tenant_id: 租户ID
            file_transform_url: 文件转换服务URL（可选）
        """
        self.storage_base_url = storage_base_url.rstrip('/')
        self.tenant_config = {
            'app': app,
            'app_secret': app_secret,
            'tenant_id': tenant_id
        }
        self.tenant_id = tenant_id
        self.file_transform_url = file_transform_url

        # 初始化解析器
        self.word_parser = WordParser()
        self.excel_parser = ExcelParser()
        self.powerpoint_parser = PowerPointParser()
        self.text_parser = TextParser()
        self.markdown_parser = MarkdownParser()
        self.html_parser = HtmlParser()

        # 初始化工具类
        self.file_utils = FileUtils()

        logger.info(
            f"FileProcessor initialized with storage_base_url: {storage_base_url}"
        )

    def check_download_url(self, input_url: str) -> str:
        """
        检查并标准化下载URL格式
        
        Args:
            input_url: 输入的URL
            
        Returns:
            标准化后的下载URL
        """
        if not input_url:
            raise ValueError("文件下载服务地址缺失")

        # 去掉问号后面的参数
        if 'api/sys-storage/download?f8s=' in input_url:
            question_mark_index = input_url.find('?')
            if question_mark_index != -1:
                return input_url[:question_mark_index]

        # 确保URL格式一致，移除可能的尾部斜杠
        base_url = input_url.rstrip('/')

        # 检查URL是否已经包含下载路径
        if '/api/sys-storage/download' in base_url:
            return base_url
        else:
            # 统一返回下载URL格式：http://{ip}:{port}/api/v1/sys-storage/download
            return f"{base_url}/api/v1/sys-storage/download"

    def calculate_rfc2104_hmac(self, data: str, secret_key: str) -> str:
        """生成HMAC签名"""
        try:
            hmac_obj = hmac.new(secret_key.encode(), data.encode(),
                                hashlib.sha1)
            return base64.b64encode(hmac_obj.digest()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to generate HMAC: {str(e)}")

    def build_sort_param(self, single_value_map: Dict) -> str:
        """构建排序后的参数字符串"""
        sorted_params = sorted(single_value_map.items())
        param_strings = [f"{key}={value}" for key, value in sorted_params]
        return "&".join(param_strings)

    def sign(self, params: Optional[Dict] = None) -> Dict:
        """
        生成API请求的签名认证
        
        Args:
            params: 需要签名的附加参数字典
            
        Returns:
            包含签名和所有参数的字典
        """
        params = params or {}
        app = self.tenant_config.get('app')
        app_secret = self.tenant_config.get('app_secret')

        # 生成当前时间戳(毫秒)
        ts = int(time.time() * 1000)

        # 设置签名有效期(秒)
        ttl = 180

        # 创建签名参数对象
        signing_map = {
            'ts': str(ts),
            'ttl': str(ttl),
            'uid': f"{self.tenant_id}:{app}",
            'appId': app,
            **params
        }

        # 将参数按键名排序并拼接成字符串
        signing_flat_words = self.build_sort_param(signing_map)

        # 使用HMAC-SHA1算法和密钥生成签名
        sign_value = self.calculate_rfc2104_hmac(signing_flat_words,
                                                 app_secret)

        # 返回签名和所有参数
        return {'sign': sign_value, **signing_map}

    def build_url_with_sign(self,
                            base_url: str,
                            params: Optional[Dict] = None) -> str:
        """
        使用签名构建完整的URL
        
        Args:
            base_url: 基础URL
            params: 需要签名的附加参数
            
        Returns:
            包含签名的完整URL
        """
        sign_result = self.sign(params)
        sign_value = quote(sign_result.pop('sign'))

        # 构建URL查询参数
        query_params = "&".join([f"{k}={v}" for k, v in sign_result.items()])

        # 返回完整URL
        return f"{base_url}?sign={sign_value}&{query_params}"

    def download_file(self, file_token: str, tmpdir: str) -> str:
        """
        根据文件token下载文件
        
        Args:
            file_token: 文件的token
            tmpdir: 临时目录路径
            
        Returns:
            下载文件的本地路径
        """
        try:
            params = {'f8s': file_token}
            url = self.build_url_with_sign(
                self.check_download_url(self.storage_base_url), params)
            logger.info(f"Downloading file from: {url}")

            response = requests.get(url, timeout=120)

            if response.status_code == 200:
                try:
                    file_name = response.headers._store['content-disposition'][
                        1].split('=')[1]
                    decoded_file_name = unquote(file_name)[-50:]
                    cleaned_file_name = self.file_utils.clean_filename(
                        decoded_file_name)

                    normalized_tmpdir = self.file_utils.normalize_path(tmpdir)
                    tmppath = os.path.join(normalized_tmpdir,
                                           cleaned_file_name)

                    os.makedirs(os.path.dirname(tmppath), exist_ok=True)

                    with open(tmppath, 'wb') as file:
                        file.write(response.content)
                        file.flush()
                        os.fsync(file.fileno())

                    logger.info(f"File downloaded successfully: {tmppath}")
                    return tmppath
                except Exception as e:
                    raise Exception(f"文件处理失败: {str(e)}")
            else:
                raise Exception(f"文件下载失败，状态码：{response.status_code}")
        except Exception as e:
            logger.error(f"Download file error: {traceback.format_exc()}")
            raise

    def generate_download_url(self, file_token: str) -> str:
        """
        生成文件下载URL
        
        Args:
            file_token: 文件的token
            
        Returns:
            带签名的下载URL
        """
        params = {'f8s': file_token}
        url = self.build_url_with_sign(
            self.check_download_url(self.storage_base_url), params)
        return url

    def upload_file(self, file_path: str) -> str:
        """
        上传文件到存储服务
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            文件的token
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # 构建上传URL
            upload_url = f"{self.storage_base_url}/api/v1/sys-storage/upload"

            # 准备上传参数
            file_name = os.path.basename(file_path)
            files = {
                'file': (file_name, file_content, 'application/octet-stream')
            }

            # 生成签名参数
            sign_params = self.sign()

            # 发送上传请求
            response = requests.post(upload_url,
                                     files=files,
                                     params=sign_params,
                                     timeout=120)

            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'fileToken' in result['data']:
                    file_token = result['data']['fileToken']
                    logger.info(f"文件上传成功，Token: {file_token}")
                    return file_token
                else:
                    raise Exception(f"上传响应格式错误: {result}")
            else:
                raise Exception(
                    f"上传失败，状态码: {response.status_code}, 响应: {response.text}")

        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            raise Exception(f"文件上传失败: {str(e)}")

    def parse_file(self, file_path: str, file_type: str) -> List:
        """
        解析文件内容
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 (docx, xlsx, pptx, txt, md, html, doc)
            
        Returns:
            解析后的内容列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_type = file_type.lower()

        try:
            if file_type == "docx":
                return self.word_parser.parsing(file_path)
            elif file_type in ["xlsx", "csv"]:
                return self.excel_parser.parsing(file_path)
            elif file_type == "pptx":
                return self.powerpoint_parser.parsing(file_path)
            elif file_type == "txt":
                return self.text_parser.parsing(file_path)
            elif file_type in ["md", "markdown"]:
                return self.markdown_parser.parsing(file_path)
            elif file_type == "html":
                return self.html_parser.parsing(file_path)
            elif file_type == "json":
                return self._parse_json_file(file_path)
            elif file_type == "doc":
                # 对于doc文件，需要先转换为docx
                if self.file_transform_url:
                    docx_path = self._convert_doc_to_docx(file_path)
                    return self.word_parser.parsing(docx_path)
                else:
                    raise ValueError("doc文件转换需要配置file_transform_url")
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
        except Exception as e:
            logger.error(f"Parse file error: {str(e)}")
            raise

    def _parse_json_file(self, file_path: str) -> List:
        """
        解析JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的内容列表
        """
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # 将JSON转换为字符串
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)

            # 检查内容长度
            if len(json_str) > 4096:
                # 分割长内容
                chunks = [
                    json_str[i:i + 4096]
                    for i in range(0, len(json_str), 4096)
                ]
                result = []
                for chunk in chunks:
                    result.append(
                        ['paragraph', chunk, [[0, 0, 0, 0]], [0], [0]])
                return result
            else:
                return [['paragraph', json_str, [[0, 0, 0, 0]], [0], [0]]]

        except Exception as e:
            raise Exception(f"解析JSON文件失败: {str(e)}")

    def _convert_doc_to_docx(self, file_path: str) -> str:
        """
        将doc文件转换为docx格式
        
        Args:
            file_path: doc文件路径
            
        Returns:
            转换后的docx文件路径
        """
        # 这里需要实现doc到docx的转换逻辑
        # 可以使用外部转换服务或本地转换工具
        raise NotImplementedError("doc到docx转换功能需要实现")

    def download_and_parse(self,
                           file_token: str,
                           file_type: str,
                           tmpdir: str = "/tmp") -> List:
        """
        下载文件并解析内容
        
        Args:
            file_token: 文件token
            file_type: 文件类型
            tmpdir: 临时目录
            
        Returns:
            解析后的内容列表
        """
        file_path = self.download_file(file_token, tmpdir)
        try:
            return self.parse_file(file_path, file_type)
        finally:
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"临时文件已删除: {file_path}")

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式列表
        
        Returns:
            支持的文件格式列表
        """
        return [
            "docx", "xlsx", "csv", "pptx", "txt", "md", "markdown", "html",
            "json", "doc"
        ]

    # ==================== 文本处理和Source生成方法 ====================

    def filetoken_to_text(self, file_token: str) -> str:
        """
        根据 file_token 获取纯文本内容。

        Args:
            file_token: URL、本地路径、file:// 路径或storage token

        Returns:
            提取到的纯文本字符串；失败时返回空字符串
        """
        text, _ = self._load_text_from_token(file_token)
        return text

    def text_to_outline(self, text: str) -> dict | None:
        """
        将给定文本尝试解析为 outline 字典对象
        
        Args:
            text: JSON 格式的 outline 数据
            
        Returns:
            outline 字典对象，解析失败时返回 None
        """
        try:
            outline_data = json.loads(text)

            # 解析标题和字数信息
            title_item = next((item for item in outline_data
                               if item.get("type") == "outline-title"), None)
            if not title_item:
                logger.error("未找到 outline-title 数据")
                return None

            title = title_item["content"]["title"]
            word_count = title_item["content"]["wordcount"]

            # 解析大纲节点
            outline_item = next(
                (item
                 for item in outline_data if item.get("type") == "outline"),
                None)
            if not outline_item:
                logger.error("未找到 outline 数据")
                return None

            chapters = outline_item["content"]

            # 转换章节格式，将 children 映射为 sections
            converted_chapters = []
            for chapter in chapters:
                converted_chapter = chapter.copy()
                # 将 children 映射为 sections，保持兼容性
                if "children" in converted_chapter:
                    converted_chapter["sections"] = converted_chapter.pop(
                        "children")
                converted_chapters.append(converted_chapter)

            # 转换为字典格式，保留原始数据结构
            outline_dict = {
                "title": title,
                "word_count": word_count,
                "chapters": converted_chapters  # 使用转换后的章节结构
            }

            logger.info(
                f"成功解析 outline，标题: {title}，章节数: {len(converted_chapters)}")
            return outline_dict

        except Exception as e:
            logger.error(f"解析 outline 失败: {e}")
            return None

    def filetoken_to_outline(self, file_token: str) -> dict | None:
        """
        将给定 file_token 转换为 outline 对象
        """
        if self._is_storage_token(file_token):
            # 对于storage token，直接解析JSON
            try:
                text = self.filetoken_to_text(file_token)
                outline_data = json.loads(text)

                # 检查是否是直接的outline格式
                if isinstance(
                        outline_data, dict
                ) and "title" in outline_data and "chapters" in outline_data:
                    # 直接返回outline数据
                    word_count = outline_data.get("word_count", 0)
                    return {
                        "title": outline_data["title"],
                        "word_count": word_count,
                        "chapters": outline_data["chapters"]
                    }
                else:
                    # 尝试使用原有的text_to_outline方法
                    return self.text_to_outline(text)
            except Exception as e:
                logger.error(f"解析storage token outline失败: {e}")
                return None
        else:
            # 对于其他类型的token，使用原有方法
            text = self.filetoken_to_text(file_token)
            return self.text_to_outline(text)

    def text_to_sources(self,
                        text: str,
                        *,
                        title: str,
                        url: str | None = None,
                        source_type: str = "document",
                        chunk_size: int = 2000,
                        overlap: int = 200,
                        source_info: dict = None) -> List[Source]:
        """
        将给定文本切分并封装为 Source 列表。

        Args:
            text: 需要切分的完整文本
            title: 基础标题
            url: 可选的来源URL
            source_type: 来源类型，默认 document
            chunk_size: 分段大小
            overlap: 段间重叠
            source_info: 可选的源信息覆盖

        Returns:
            List[Source]
        """
        if not text:
            return []
        chunks = self._split_text(text, chunk_size=chunk_size, overlap=overlap)
        logger.info(f"文本切分完成，共 {len(chunks)} 段")
        sources: List[Source] = []
        for idx, chunk in enumerate(chunks, start=1):
            source = Source(
                id=idx,
                sourceType=source_type,
                title=f"{title} - 切片 {idx}",
                url=url,
                content=chunk,
            )
            # 应用 source_info 覆盖
            if source_info:
                for key, value in source_info.items():
                    if hasattr(source, key):
                        setattr(source, key, value)
            sources.append(source)
        return sources

    def filetoken_to_sources(self,
                             file_token: str,
                             *,
                             title: str | None = None,
                             chunk_size: int = 2000,
                             overlap: int = 200,
                             source_info: dict = None) -> List[Source]:
        """
        将给定 file_token 转换为 Sources 列表

        Args:
            file_token: 文件token
            title: 可选的标题
            chunk_size: 分段大小
            overlap: 段间重叠
            source_info: 可选的源信息覆盖

        Returns:
            List[Source]
        """
        text, meta = self._load_text_from_token(file_token)
        if not text:
            return []

        # 使用元数据中的标题，如果没有则使用传入的标题
        final_title = title or meta.get("title", "未命名文档")
        url = meta.get("url")

        return self.text_to_sources(text,
                                    title=final_title,
                                    url=url,
                                    source_type=meta.get(
                                        "source_type", "document"),
                                    chunk_size=chunk_size,
                                    overlap=overlap,
                                    source_info=source_info)

    def _load_text_from_token(self, file_token: str) -> Tuple[str, dict]:
        """
        根据 file_token 下载/读取，并尽力提取纯文本。

        Returns:
            (text, meta)
        meta: {"title": str, "source_type": str, "url": Optional[str]}
        """
        try:
            if self._is_http_url(file_token):
                return self._load_text_from_http(file_token)
            elif self._is_storage_token(file_token):
                return self._load_text_from_storage(file_token)
            return self._load_text_from_local(file_token)
        except Exception as e:
            logger.error(f"加载文件失败: {e}")
            return "", {}

    def _load_text_from_http(self, url: str) -> Tuple[str, dict]:
        """从HTTP URL加载文本"""
        logger.info(f"通过HTTP下载: {url}")
        with httpx.Client(timeout=30) as client:
            resp = client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            raw = resp.content

        if "text/html" in content_type:
            text = self._html_to_text(raw)
        elif "application/json" in content_type or url.lower().endswith(
                ".json"):
            try:
                text = json.dumps(resp.json(), ensure_ascii=False, indent=2)
            except Exception:
                text = raw.decode("utf-8", errors="ignore")
        else:
            # 默认按文本尝试
            try:
                text = raw.decode("utf-8")
            except Exception:
                text = raw.decode("utf-8", errors="ignore")

        meta = {
            "title": self._infer_title(url),
            "source_type": "document",
            "url": url,
        }
        return text, meta

    def _load_text_from_local(self, token: str) -> Tuple[str, dict]:
        """从本地文件加载文本"""
        # 支持 file:// 与普通路径
        path_str = token[7:] if token.startswith("file://") else token
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"本地文件不存在: {path}")

        raw = path.read_bytes()
        guess, _ = mimetypes.guess_type(path.name)

        if guess and "html" in guess:
            text = self._html_to_text(raw)
        elif guess and ("json" in guess or path.suffix.lower() == ".json"):
            try:
                text = json.dumps(json.loads(
                    raw.decode("utf-8", errors="ignore")),
                                  ensure_ascii=False,
                                  indent=2)
            except Exception:
                text = raw.decode("utf-8", errors="ignore")
        else:
            # 默认当作文本
            try:
                text = raw.decode("utf-8")
            except Exception:
                text = raw.decode("utf-8", errors="ignore")

        meta = {
            "title": path.stem,
            "source_type": "document",
            "url": None,
        }
        return text, meta

    def _load_text_from_storage(self, file_token: str) -> Tuple[str, dict]:
        """
        从远程storage下载文件并提取文本
        
        Args:
            file_token: storage文件token
            
        Returns:
            (text, meta)
        """
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()

            try:
                # 首先下载文件以获取文件名
                file_path = self.download_file(file_token, temp_dir)
                file_name = os.path.basename(file_path)

                # 根据文件扩展名确定文件类型
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext in ['.json']:
                    file_type = "json"
                elif file_ext in ['.md', '.markdown']:
                    file_type = "md"
                elif file_ext in ['.txt']:
                    file_type = "txt"
                elif file_ext in ['.docx', '.doc']:
                    file_type = "word"
                elif file_ext in ['.xlsx', '.xls']:
                    file_type = "excel"
                elif file_ext in ['.pptx', '.ppt']:
                    file_type = "powerpoint"
                elif file_ext in ['.html', '.htm']:
                    file_type = "html"
                else:
                    # 默认按文本处理
                    file_type = "txt"

                # 下载并解析文件
                parsed_content = self.download_and_parse(
                    file_token, file_type, temp_dir)

                if not parsed_content:
                    raise Exception("文件内容为空")

                # 提取文本内容
                if file_type == "json":
                    # JSON文件通常只有一个内容块
                    text = parsed_content[0][1] if parsed_content else ""
                else:
                    # 其他文件类型，合并所有内容块
                    text = "\n\n".join(
                        [content[1] for content in parsed_content])

                meta = {
                    "title": f"storage_file_{file_token[:8]}",
                    "source_type": "document",
                    "url": None,
                }

                logger.info(f"成功从storage加载文件: {file_token} (类型: {file_type})")
                return text, meta

            finally:
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")

        except Exception as e:
            logger.error(f"从storage加载文件失败: {e}")
            raise

    def _is_http_url(self, token: str) -> bool:
        """判断是否为HTTP URL"""
        t = token.lower()
        return t.startswith("http://") or t.startswith("https://")

    def _is_storage_token(self, token: str) -> bool:
        """
        判断是否为storage token（32位十六进制字符串）
        """
        # 检查是否为32位十六进制字符串
        return bool(re.match(r'^[a-f0-9]{32}$', token.lower()))

    def _html_to_text(self, raw: bytes) -> str:
        """将HTML转换为纯文本"""
        soup = BeautifulSoup(raw, "lxml")
        # 移除script/style
        for tag in soup(["script", "style"]):
            tag.extract()
        text = soup.get_text("\n")
        # 规范化空白
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join([ln for ln in lines if ln])
        return text

    def _split_text(self, text: str, *, chunk_size: int,
                    overlap: int) -> List[str]:
        """将文本分割成块"""
        if chunk_size <= 0:
            return [text]
        chunks: List[str] = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + chunk_size, n)
            chunks.append(text[start:end])
            if end == n:
                break
            start = max(0, end - overlap)
        return chunks

    def _infer_title(self, token: str) -> str:
        """推断标题"""
        if self._is_http_url(token):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(token)
                name = Path(parsed.path).name or parsed.netloc
                return name or "未命名来源"
            except Exception:
                return "未命名来源"
        # 本地
        return Path(token[7:] if token.startswith("file://") else token
                    ).name or "未命名来源"
