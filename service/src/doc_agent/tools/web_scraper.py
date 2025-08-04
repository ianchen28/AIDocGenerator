# service/src/doc_agent/tools/web_scraper.py
"""
网页内容抓取工具
提供网页内容抓取、文本提取等功能
"""

import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


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

    async def fetch_metadata(self,
                             url: str,
                             timeout: int = 10) -> Optional[dict]:
        """
        获取网页元数据

        Args:
            url: 网页URL
            timeout: 超时时间（秒）

        Returns:
            包含元数据的字典，失败时返回None
        """
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    return self.extract_metadata_from_html(html, url)
        except Exception as e:
            self.logger.error(f"获取网页元数据失败 {url}: {e}")
            return None

    def extract_metadata_from_html(self, html: str, url: str) -> dict:
        """
        从HTML中提取元数据

        Args:
            html: HTML字符串
            url: 原始URL

        Returns:
            包含元数据的字典
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            metadata = {
                'url': url,
                'title': '',
                'description': '',
                'keywords': '',
                'author': '',
                'language': '',
                'charset': '',
                'content_length': len(html)
            }

            # 提取标题
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()

            # 提取meta标签信息
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                property = meta.get('property', '').lower()
                content = meta.get('content', '')

                if name == 'description' or property == 'og:description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif property == 'og:title':
                    metadata['title'] = content or metadata['title']

            # 提取语言信息
            html_tag = soup.find('html')
            if html_tag:
                metadata['language'] = html_tag.get('lang', '')

            # 提取字符集
            meta_charset = soup.find('meta', charset=True)
            if meta_charset:
                metadata['charset'] = meta_charset.get('charset', '')
            else:
                meta_content_type = soup.find(
                    'meta', attrs={'http-equiv': 'Content-Type'})
                if meta_content_type:
                    content_type = meta_content_type.get('content', '')
                    if 'charset=' in content_type:
                        metadata['charset'] = content_type.split(
                            'charset=')[-1]

            return metadata
        except Exception as e:
            self.logger.error(f"HTML元数据提取失败: {e}")
            return {'url': url, 'error': str(e)}

    async def fetch_with_metadata(self,
                                  url: str,
                                  timeout: int = 10) -> Optional[dict]:
        """
        获取网页内容和元数据

        Args:
            url: 网页URL
            timeout: 超时时间（秒）

        Returns:
            包含内容和元数据的字典，失败时返回None
        """
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()

                    return {
                        'url': url,
                        'content': self.extract_text_from_html(html),
                        'metadata': self.extract_metadata_from_html(html, url),
                        'raw_html': html,
                        'status_code': response.status,
                        'headers': dict(response.headers)
                    }
        except Exception as e:
            self.logger.error(f"获取网页内容和元数据失败 {url}: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """
        清理文本内容

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}"\'-]', '', text)

        # 清理引号
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)

        return text.strip()

    def extract_links(self, html: str, base_url: str) -> list[str]:
        """
        从HTML中提取链接

        Args:
            html: HTML字符串
            base_url: 基础URL

        Returns:
            链接列表
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []

            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    # 处理相对链接
                    if href.startswith('/'):
                        from urllib.parse import urljoin
                        href = urljoin(base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        from urllib.parse import urljoin
                        href = urljoin(base_url, href)

                    links.append(href)

            return list(set(links))  # 去重
        except Exception as e:
            self.logger.error(f"链接提取失败: {e}")
            return []

    def extract_images(self, html: str, base_url: str) -> list[dict]:
        """
        从HTML中提取图片信息

        Args:
            html: HTML字符串
            base_url: 基础URL

        Returns:
            图片信息列表
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            images = []

            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    # 处理相对链接
                    if src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    elif not src.startswith(('http://', 'https://')):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)

                    image_info = {
                        'src': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'width': img.get('width', ''),
                        'height': img.get('height', '')
                    }
                    images.append(image_info)

            return images
        except Exception as e:
            self.logger.error(f"图片提取失败: {e}")
            return []


# 创建默认实例
default_scraper = WebScraper()


async def fetch_url_content(url: str, timeout: int = 10) -> Optional[str]:
    """
    便捷函数：获取URL内容

    Args:
        url: 网页URL
        timeout: 超时时间（秒）

    Returns:
        网页文本内容
    """
    return await default_scraper.fetch_full_content(url, timeout)


async def fetch_url_with_metadata(url: str,
                                  timeout: int = 10) -> Optional[dict]:
    """
    便捷函数：获取URL内容和元数据

    Args:
        url: 网页URL
        timeout: 超时时间（秒）

    Returns:
        包含内容和元数据的字典
    """
    return await default_scraper.fetch_with_metadata(url, timeout)


if __name__ == "__main__":
    """
    网页抓取工具测试代码
    """
    import asyncio

    async def test_web_scraper():
        """测试网页抓取功能"""
        logger.info("=== 开始网页抓取测试 ===")

        # 创建网页抓取器
        scraper = WebScraper()

        # 测试URL
        test_urls = [
            "https://www.python.org", "https://docs.python.org/3/",
            "https://httpbin.org/html"
        ]

        for url in test_urls:
            logger.info(f"测试抓取: {url}")
            try:
                # 测试获取内容
                content = await scraper.fetch_full_content(url)
                if content:
                    logger.info(f"抓取成功，内容长度: {len(content)} 字符")
                    logger.info(f"内容预览: {content[:200]}...")
                else:
                    logger.warning("抓取失败，返回空内容")

                # 测试获取元数据
                metadata = await scraper.fetch_metadata(url)
                if metadata:
                    logger.info(f"元数据: {metadata}")
                else:
                    logger.warning("元数据获取失败")

                # 测试完整获取
                full_data = await scraper.fetch_with_metadata(url)
                if full_data:
                    logger.info(
                        f"完整数据获取成功，包含 {len(full_data.get('content', ''))} 字符内容"
                    )
                else:
                    logger.warning("完整数据获取失败")

            except Exception as e:
                logger.error(f"网页抓取测试失败: {e}")

            logger.info("-" * 30)

    # 运行测试
    asyncio.run(test_web_scraper())
