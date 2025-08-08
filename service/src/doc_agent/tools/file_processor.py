"""
文件处理与来源抽取工具

提供以下能力：
1) 通过 file_token 下载文件（支持 http/https、本地路径、file://）
2) 提取可读文本（支持 text/html、text/plain、application/json 的基础处理）
3) 进行简单分段
4) 生成并返回 list[Source]
"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from doc_agent.core.logger import logger
from doc_agent.schemas import Outline, OutlineNode, Source


class FileProcessor:
    """文件处理工具类"""

    def __init__(self):
        self.logger = logger.bind(name="file_processor")

    def filetoken_to_text(self, file_token: str) -> str:
        """
        根据 file_token 获取纯文本内容。

        Args:
            file_token: URL、本地路径或 file:// 路径

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
                self.logger.error("未找到 outline-title 数据")
                return None

            title = title_item["content"]["title"]
            word_count = title_item["content"]["wordcount"]

            # 解析大纲节点
            outline_item = next(
                (item
                 for item in outline_data if item.get("type") == "outline"),
                None)
            if not outline_item:
                self.logger.error("未找到 outline 数据")
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

            self.logger.info(
                f"成功解析 outline，标题: {title}，章节数: {len(converted_chapters)}")
            return outline_dict

        except Exception as e:
            self.logger.error(f"解析 outline 失败: {e}")
            return None

    def text_to_sources(self,
                        text: str,
                        *,
                        title: str,
                        url: str | None = None,
                        source_type: str = "document",
                        chunk_size: int = 2000,
                        overlap: int = 200,
                        source_info: dict = None) -> list[Source]:
        """
        将给定文本切分并封装为 Source 列表。

        Args:
            text: 需要切分的完整文本
            title: 基础标题
            url: 可选的来源URL
            source_type: 来源类型，默认 document
            chunk_size: 分段大小
            overlap: 段间重叠

        Returns:
            list[Source]
        """
        if not text:
            return []
        chunks = self._split_text(text, chunk_size=chunk_size, overlap=overlap)
        self.logger.info(f"文本切分完成，共 {len(chunks)} 段")
        sources: list[Source] = []
        for idx, chunk in enumerate(chunks, start=1):
            sources.append(
                Source(
                    id=idx,
                    sourceType=source_type,
                    title=f"{title} - 切片 {idx}",
                    url=url,
                    content=chunk,
                ))
        # 应用 source_info 覆盖
        if source_info:
            for s in sources:
                for key, value in source_info.items():
                    setattr(s, key, value)

        # 回填 file_token 到 Source（如模型包含该字段）
        for s in sources:
            try:
                s.file_token = file_token  # type: ignore[attr-defined]
            except Exception:
                pass
        return sources

    def filetoken_to_sources(self,
                             file_token: str,
                             *,
                             title: str | None = None,
                             chunk_size: int = 2000,
                             overlap: int = 200,
                             source_info: dict = None) -> list[Source]:
        """
        将一个 file_token 转换为 list[Source]

        Args:
            file_token: 远端或本地文件标识（URL、本地绝对/相对路径、file://）
            title: 可选的来源标题；不提供则从URL/文件名推断
            chunk_size: 文本分段长度（按字符）
            overlap: 相邻分段重叠长度
            source_info: 可能的源信息，如 id、source_type、url、content 等
                    如果有对应字段则覆盖写入最终的 Source 中

        Returns:
            List[Source]
        """
        # 调用 filetoken_to_text 获取文本
        text = self.filetoken_to_text(file_token)

        # 推断标题
        inferred_title = title or self._infer_title(file_token)

        # 调用 text_to_sources 生成 Source 列表
        sources = self.text_to_sources(
            text,
            title=inferred_title,
            url=source_info.get("url"),
            source_type=source_info.get("source_type"),
            chunk_size=chunk_size,
            overlap=overlap,
            source_info=source_info)

        return sources

    # ========= 内部方法 =========
    def _load_text_from_token(self, file_token: str) -> tuple[str, dict]:
        """
        根据 file_token 下载/读取，并尽力提取纯文本。

        Returns:
            (text, meta)
        meta: {"title": str, "source_type": str, "url": Optional[str]}
        """
        try:
            if self._is_http_url(file_token):
                return self._load_text_from_http(file_token)
            return self._load_text_from_local(file_token)
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            return "", {}

    def _load_text_from_http(self, url: str) -> tuple[str, dict]:
        self.logger.info(f"通过HTTP下载: {url}")
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

    def filetoken_to_outline(self, file_token: str) -> Outline:
        """
        将给定 file_token 转换为 outline 对象
        """
        text = self.filetoken_to_text(file_token)
        return self.text_to_outline(text)

    def _load_text_from_local(self, token: str) -> tuple[str, dict]:
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

    def _html_to_text(self, raw: bytes) -> str:
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
                    overlap: int) -> list[str]:
        if chunk_size <= 0:
            return [text]
        chunks: list[str] = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + chunk_size, n)
            chunks.append(text[start:end])
            if end == n:
                break
            start = max(0, end - overlap)
        return chunks

    def _is_http_url(self, token: str) -> bool:
        t = token.lower()
        return t.startswith("http://") or t.startswith("https://")

    def _infer_title(self, token: str) -> str:
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


# 全局文件处理器实例
file_processor = FileProcessor()


def filetoken_to_sources(file_token: str,
                         *,
                         title: str | None = None,
                         chunk_size: int = 2000,
                         overlap: int = 200) -> list[Source]:
    """便捷函数：将 file_token 转为 Sources 列表"""
    return file_processor.filetoken_to_sources(file_token,
                                               title=title,
                                               chunk_size=chunk_size,
                                               overlap=overlap)


if __name__ == "__main__":
    file_token = "/Users/chenyuyang/git/AIDocGenerator/test_case/outline_from_fe.json"
    text = file_processor.filetoken_to_text(file_token)
    print(text)
    source_info = {
        "id": 1,
        "source_type": "document",
        "url": "https://www.baidu.com",
        "content": "test",
        "title": "test",
    }
    sources = file_processor.filetoken_to_sources(file_token,
                                                  source_info=source_info)
    print(sources)
    outline = file_processor.filetoken_to_outline(file_token)
    print(outline)
