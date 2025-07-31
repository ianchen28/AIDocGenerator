# service/src/doc_agent/tools/web_search.py
"""
网络搜索工具
基于外部搜索API和网页抓取功能
"""

import asyncio
import functools
import re
import time
from typing import Any, Optional

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


def timer(func=None, *, log_level="info"):
    """计算函数执行时间的装饰器"""

    def decorator(func):

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            log_func = getattr(logger, log_level)
            log_func(f"函数 {func.__name__} 执行耗时: {elapsed_time:.4f} 秒")
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            log_func = getattr(logger, log_level)
            log_func(f"异步函数 {func.__name__} 执行耗时: {elapsed_time:.4f} 秒")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    if func is None:
        return decorator
    return decorator(func)


class WebScraper:
    """网页内容抓取器"""

    def __init__(self):
        self.logger = logger.bind(name="web_scraper")

    async def fetch_full_content(self,
                                 url: str,
                                 timeout: int = 10) -> Optional[str]:
        """
        异步获取网页完整内容

        Args:
            url: 网页URL
            timeout: 超时时间（秒）

        Returns:
            网页的文本内容，失败时返回None
        """
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    return self.extract_text_from_html(html)
        except Exception as e:
            self.logger.error(f"获取网页内容失败 {url}: {e}")
            return None

    def extract_text_from_html(self, html: str) -> str:
        """
        从HTML中提取文本内容

        Args:
            html: HTML字符串

        Returns:
            提取的文本内容
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取文本
            text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines
                      for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text)

            return text
        except Exception as e:
            self.logger.error(f"HTML文本提取失败: {e}")
            return ""


class WebSearchConfig:
    """网络搜索配置"""

    def __init__(self, config: dict[str, Any] = None):
        # 默认配置
        default_config = {
            "url": "http://10.215.149.74:9930/api/v1/llm-qa/api/chat/net",
            "token":
            "eyJhbGciOiJIUzI1NiJ9.eyJqd3RfbmFtZSI6Iueul-azleiBlOe9keaOpeWPo-a1i-ivlSIsImp3dF91c2VyX2lkIjoyMiwiand0X3VzZXJfbmFtZSI6ImFkbWluIiwiZXhwIjoyMDA1OTc2MjY2LCJpYXQiOjE3NDY3NzYyNjZ9.YLkrXAdx-wyVUwWveVCF2ddjqZrOrwOKxaF8fLOuc6E",
            "count": 5,
            "timeout": 15,  # 从30秒减少到15秒
            "retries": 3,
            "delay": 1,
            "fetch_full_content": True
        }

        # 合并配置
        if config:
            default_config.update(config)

        self.url = default_config["url"]
        self.token = default_config["token"]
        self.count = default_config["count"]
        self.timeout = default_config["timeout"]
        self.retries = default_config["retries"]
        self.delay = default_config["delay"]
        self.fetch_full_content = default_config["fetch_full_content"]


class WebSearchTool:
    """
    网络搜索工具类
    支持异步搜索、网页抓取、重试机制
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 config: dict[str, Any] = None):
        """
        初始化网络搜索工具

        Args:
            api_key: API密钥（可选，用于兼容性）
            config: 配置字典
        """
        self.config = WebSearchConfig(config)
        self.web_scraper = WebScraper()
        self.logger = logger.bind(name="web_search")

        logger.info("初始化网络搜索工具")
        if api_key:
            logger.debug("API密钥已提供")
        else:
            logger.warning("未提供API密钥，将使用配置中的token")

    @timer(log_level="info")
    async def get_web_search(self,
                             query: str) -> Optional[list[dict[str, Any]]]:
        """
        异步请求外部搜索接口并返回结果

        Args:
            query: 查询参数

        Returns:
            如果请求成功，返回响应的数据；否则返回None
        """
        headers = {"X-API-KEY-AUTH": f"Bearer {self.config.token}"}
        params = {"queryStr": query, "count": self.config.count}

        # 创建aiohttp超时对象
        timeout_obj = aiohttp.ClientTimeout(total=self.config.timeout)

        async with aiohttp.ClientSession(timeout=timeout_obj) as session:
            for attempt in range(1, self.config.retries + 1):
                try:
                    async with session.get(self.config.url,
                                           headers=headers,
                                           params=params) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return data.get("data", [])
                except Exception as e:
                    self.logger.error(f"第 {attempt} 次请求失败: {e}")
                    if attempt < self.config.retries:
                        await asyncio.sleep(self.config.delay)
                    else:
                        self.logger.error("达到最大重试次数，请求失败")
                        return None

    async def get_web_docs(
            self,
            query: str,
            fetch_full_content: bool = None) -> list[dict[str, Any]]:
        """
        获取web搜索结果并格式化为文档格式

        Args:
            query: 查询参数
            fetch_full_content: 是否获取完整内容，None时使用配置中的设置

        Returns:
            格式化的文档列表
        """
        net_info = await self.get_web_search(query)
        if not net_info:
            return []

        # 确定是否获取完整内容
        should_fetch_full = fetch_full_content if fetch_full_content is not None else self.config.fetch_full_content

        # 处理每个搜索结果
        web_docs = []
        for index, web_page in enumerate(net_info):
            # 获取内容
            content = web_page.get('materialContent', '')

            # 如果需要获取完整内容且当前内容较短（少于200字符）
            if should_fetch_full and len(content) < 200 and web_page.get(
                    'url'):
                self.logger.info(f"获取完整内容: {web_page.get('url')}")
                try:
                    full_content = await self.web_scraper.fetch_full_content(
                        web_page.get('url'))
                    if full_content:
                        content = full_content
                        web_page['full_content_fetched'] = True
                    else:
                        web_page['full_content_fetched'] = False
                except Exception as e:
                    self.logger.warning(f"获取完整内容失败: {e}")
                    web_page['full_content_fetched'] = False
            else:
                web_page['full_content_fetched'] = False

            # 格式化文档
            web_page["file_name"] = web_page.get("docName", "")
            doc = {
                "doc_id": web_page.get("url", ""),
                "doc_type": "text",
                "domain_ids": ["web"],
                "meta_data": web_page,
                "text": content,
                "_id": web_page.get("materialId", ""),
                "rank": str(index + 1),
                "full_content_fetched": web_page.get('full_content_fetched',
                                                     False)
            }
            web_docs.append(doc)

        return web_docs

    async def get_full_content_for_url(self, url: str) -> Optional[str]:
        """
        获取指定URL的完整内容

        Args:
            url: 网页URL

        Returns:
            网页的完整文本内容
        """
        return await self.web_scraper.fetch_full_content(url)

    def search(self, query: str) -> str:
        """
        同步搜索接口（用于兼容性）

        Args:
            query: 搜索查询字符串

        Returns:
            str: 搜索结果的文本表示
        """
        logger.info(f"开始网络搜索，查询: '{query[:50]}...'")

        try:
            # 检查是否在异步环境中
            try:
                loop = asyncio.get_running_loop()
                # 在异步环境中，返回提示信息
                logger.warning("在异步环境中调用同步搜索方法，建议使用 search_async")
                return f"搜索查询: {query}\n注意: 在异步环境中请使用 search_async 方法"
            except RuntimeError:
                # 不在异步环境中，可以安全使用 run_until_complete
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    web_docs = loop.run_until_complete(
                        self.get_web_docs(query))
                finally:
                    loop.close()

            if not web_docs:
                return f"搜索失败或无结果: {query}"

            # 格式化结果
            result = f"Search results for: {query}\n\n"
            for i, doc in enumerate(web_docs[:3]):  # 只显示前3个结果
                meta = doc['meta_data']
                title = meta.get('docName', 'Unknown')
                url = doc['doc_id']
                content = doc['text'][:200] + "..." if len(
                    doc['text']) > 200 else doc['text']

                result += f"{i+1}. {title}\n"
                result += f"   URL: {url}\n"
                result += f"   内容长度: {len(doc['text'])} 字符\n"
                result += f"   是否获取完整内容: {doc.get('full_content_fetched', False)}\n"
                result += f"   内容预览: {content}\n\n"

            logger.info("网络搜索完成")
            return result

        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            return f"搜索失败: {str(e)}"

    async def search_async(self, query: str) -> str:
        """
        异步搜索接口

        Args:
            query: 搜索查询字符串

        Returns:
            str: 搜索结果的文本表示
        """
        logger.info(f"开始异步网络搜索，查询: '{query[:50]}...'")

        try:
            web_docs = await self.get_web_docs(query)

            if not web_docs:
                return f"搜索失败或无结果: {query}"

            # 格式化结果
            result = f"Search results for: {query}\n\n"
            for i, doc in enumerate(web_docs[:3]):  # 只显示前3个结果
                meta = doc['meta_data']
                title = meta.get('docName', 'Unknown')
                url = doc['doc_id']
                content = doc['text'][:200] + "..." if len(
                    doc['text']) > 200 else doc['text']

                result += f"{i+1}. {title}\n"
                result += f"   URL: {url}\n"
                result += f"   内容长度: {len(doc['text'])} 字符\n"
                result += f"   是否获取完整内容: {doc.get('full_content_fetched', False)}\n"
                result += f"   内容预览: {content}\n\n"

            logger.info("异步网络搜索完成")
            return result

        except Exception as e:
            logger.error(f"异步网络搜索失败: {str(e)}")
            return f"搜索失败: {str(e)}"
