"""
独立的Web搜索模块
可以移植到其他项目中使用

功能：
1. 异步调用外部搜索API
2. 支持重试机制
3. 生成文本嵌入向量
4. 格式化搜索结果
5. 网页全文抓取
"""

import aiohttp
import asyncio
import json
import os
import sys
from typing import List, Dict, Any, Optional
from doc_agent.core.logger import logger
import time
import functools
from bs4 import BeautifulSoup
import re


# 配置日志
def setup_logger():
    """设置日志配置"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level="INFO",
        colorize=True)

    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)

    # 添加文件输出
    logger.add(
        "logs/web_search.log",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        format=
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="INFO")


def get_logger(name: str):
    """获取命名的logger实例"""
    return logger.bind(name=name)


def timer(func=None, *, log_level="info", logger_name=None):
    """计算函数执行时间的装饰器"""

    def decorator(func):

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_logger = get_logger(logger_name) if logger_name else logger
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            log_func = getattr(current_logger, log_level)
            log_func(f"函数 {func.__name__} 执行耗时: {elapsed_time:.4f} 秒")
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_logger = get_logger(logger_name) if logger_name else logger
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            log_func = getattr(current_logger, log_level)
            log_func(f"异步函数 {func.__name__} 执行耗时: {elapsed_time:.4f} 秒")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    if func is None:
        return decorator
    return decorator(func)


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """加载配置文件"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return {}
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


class WebScraper:
    """网页抓取器"""

    def __init__(self):
        self.logger = get_logger("web_scraper")
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def fetch_full_content(self,
                                 url: str,
                                 timeout: int = 10) -> Optional[str]:
        """
        获取网页的完整内容
        
        Args:
            url: 网页URL
            timeout: 超时时间
            
        Returns:
            网页的完整文本内容，失败时返回None
        """
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj,
                                             headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.extract_text_from_html(html)
                    else:
                        self.logger.warning(
                            f"HTTP状态码: {response.status} for URL: {url}")
                        return None
        except Exception as e:
            self.logger.error(f"抓取网页失败 {url}: {e}")
            return None

    def extract_text_from_html(self, html: str) -> str:
        """
        从HTML中提取纯文本内容
        
        Args:
            html: HTML内容
            
        Returns:
            提取的纯文本内容
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

            return text.strip()
        except Exception as e:
            self.logger.error(f"HTML解析失败: {e}")
            return ""


class WebSearchConfig:
    """Web搜索配置类"""

    def __init__(self,
                 config: Dict[str, Any] = None,
                 config_path: str = "config.json"):
        # 加载配置文件
        file_config = load_config(config_path)

        if config is None:
            # 从配置文件获取web_search_params
            web_search_params = file_config.get('web_search_params', {})
            embedding_config = file_config.get('embedding', {})

            # 默认配置，可以通过环境变量覆盖
            config = {
                "url":
                os.getenv(
                    "WEB_SEARCH_URL",
                    web_search_params.get("url",
                                          "http://localhost:8080/api/search")),
                "token":
                os.getenv("WEB_SEARCH_TOKEN",
                          web_search_params.get("token", "")),
                "count":
                int(os.getenv("WEB_SEARCH_COUNT", "10")),
                "timeout":
                int(os.getenv("WEB_SEARCH_TIMEOUT", "3")),
                "retries":
                int(os.getenv("WEB_SEARCH_RETRIES", "5")),
                "delay":
                int(os.getenv("WEB_SEARCH_DELAY", "2")),
                "embedding_url":
                os.getenv(
                    "EMBEDDING_URL",
                    embedding_config.get("gte_qwen_url",
                                         "http://localhost:8081/embeddings")),
                "fetch_full_content":
                os.getenv("FETCH_FULL_CONTENT", "false").lower() == "true"
            }

        self.url = config["url"]
        self.token = config["token"]
        self.count = config["count"]
        self.timeout = config["timeout"]
        self.retries = config["retries"]
        self.delay = config["delay"]
        self.embedding_url = config.get("embedding_url",
                                        "http://localhost:8081/embeddings")
        self.fetch_full_content = config.get("fetch_full_content", False)


class EmbeddingService:
    """文本嵌入服务"""

    def __init__(self, embedding_url: str = None):
        self.embedding_url = embedding_url or os.getenv(
            "EMBEDDING_URL", "http://localhost:8081/embeddings")
        self.logger = get_logger("embedding")

    @timer(log_level="info", logger_name="embedding")
    async def get_embeddings(self,
                             input_texts: List[str],
                             max_retries: int = 3,
                             timeout: int = 10) -> List[List[float]]:
        """
        从API获取文本嵌入向量
        
        Args:
            input_texts: 需要生成嵌入向量的文本列表
            max_retries: 最大重试次数
            timeout: 请求超时时间(秒)
            
        Returns:
            嵌入向量结果列表
        """
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        # 限制每个文本长度不超过4096
        truncated_texts = [text[:4096] for text in input_texts]

        # 分批处理，每批8个
        batch_size = 8
        batches = [
            truncated_texts[i:i + batch_size]
            for i in range(0, len(truncated_texts), batch_size)
        ]

        all_embeddings = []

        async with aiohttp.ClientSession() as session:
            for batch in batches:
                data = {"inputs": batch}

                for attempt in range(max_retries + 1):
                    try:
                        async with session.post(self.embedding_url,
                                                json=data,
                                                headers=headers,
                                                timeout=timeout) as response:
                            response.raise_for_status()
                            batch_embeddings = await response.json()
                            all_embeddings.extend(batch_embeddings)
                            self.logger.info(f"成功获取嵌入向量 (批次大小: {len(batch)})")
                            break
                    except Exception as error:
                        if attempt < max_retries:
                            await asyncio.sleep(1)
                            continue
                        self.logger.error(f"请求失败，已重试{max_retries}次: {error}")
                        raise

        return all_embeddings


class WebSearchService:
    """Web搜索服务"""

    def __init__(self,
                 config: WebSearchConfig = None,
                 embedding_service: EmbeddingService = None,
                 web_scraper: WebScraper = None,
                 config_path: str = "config.json"):
        self.config = config or WebSearchConfig(config_path=config_path)
        self.embedding_service = embedding_service or EmbeddingService(
            self.config.embedding_url)
        self.web_scraper = web_scraper or WebScraper()
        self.logger = get_logger("web_search")

    async def get_web_search(self,
                             query: str) -> Optional[List[Dict[str, Any]]]:
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
                    self.logger.error(f"第 {attempt} 次请求失败: {e}", exc_info=True)
                    if attempt < self.config.retries:
                        await asyncio.sleep(self.config.delay)
                    else:
                        self.logger.error("达到最大重试次数，请求失败。")
                        return None

    async def get_web_docs(
            self,
            query: str,
            fetch_full_content: bool = None) -> List[Dict[str, Any]]:
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

            # 如果需要获取完整内容且当前内容较短
            if should_fetch_full and len(content) < 500 and web_page.get(
                    'url'):
                self.logger.info(f"获取完整内容: {web_page.get('url')}")
                full_content = await self.web_scraper.fetch_full_content(
                    web_page.get('url'))
                if full_content:
                    content = full_content
                    web_page['full_content_fetched'] = True
                else:
                    web_page['full_content_fetched'] = False

            # 提取内容用于嵌入向量生成
            contents = [content]

            # 获取嵌入向量
            try:
                contents_vector = await self.embedding_service.get_embeddings(
                    contents)
                vec = contents_vector[0] if contents_vector else []
            except Exception as e:
                self.logger.error(f"获取嵌入向量失败: {e}")
                vec = []

            # 格式化文档
            web_page["file_name"] = web_page.get("docName", "")
            doc = {
                "doc_id": web_page.get("url", ""),
                "doc_type": "text",
                "domain_ids": ["web"],
                "meta_data": web_page,
                "context_vector": vec,
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


# 使用示例
async def main():
    """使用示例"""
    # 设置日志
    setup_logger()

    # 创建web搜索服务（会自动加载config.json）
    web_search_service = WebSearchService()

    # 执行搜索
    query = "水轮机"
    print(f"正在搜索: {query}")

    # 获取搜索结果（包含完整内容）
    result = await web_search_service.get_web_docs(query,
                                                   fetch_full_content=True)

    if result:
        print(f"搜索到 {len(result)} 个结果:")
        for i, doc in enumerate(result[:3]):  # 只显示前3个结果
            print(f"{i+1}. {doc['meta_data'].get('docName', 'Unknown')}")
            print(f"   URL: {doc['doc_id']}")
            print(f"   内容长度: {len(doc['text'])} 字符")
            print(f"   是否获取完整内容: {doc.get('full_content_fetched', False)}")
            print(f"   内容预览: {doc['text'][:200]}...")
            print()
    else:
        print("搜索失败或无结果")


def create_standalone_config():
    """创建独立的配置文件"""
    config = {
        "web_search_params": {
            "url":
            "http://10.215.149.74:9930/api/v1/llm-qa/api/chat/net",
            "token":
            "eyJhbGciOiJIUzI1NiJ9.eyJqd3RfbmFtZSI6Iueul-azleiBlOe9keaOpeWPo-a1i-ivlSIsImp3dF91c2VyX2lkIjoyMiwiand0X3VzZXJfbmFtZSI6ImFkbWluIiwiZXhwIjoyMDA1OTc2MjY2LCJpYXQiOjE3NDY3NzYyNjZ9.YLkrXAdx-wyVUwWveVCF2ddjqZrOrwOKxaF8fLOuc6E"
        },
        "embedding": {
            "gte_qwen_url": "http://10.215.58.199:13037/embed",
            "gte_qwen_url_offline": "http://10.215.58.199:13037/embed"
        }
    }

    with open("standalone_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    print("已创建独立配置文件: standalone_config.json")


if __name__ == "__main__":
    # 如果配置文件不存在，创建一个独立的配置文件
    if not os.path.exists("config.json"):
        create_standalone_config()
        print("请检查并修改 standalone_config.json 中的配置信息")

    # 运行示例
    asyncio.run(main())
