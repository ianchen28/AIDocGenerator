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

                        # 检查API响应状态
                        if isinstance(data, dict):
                            # 如果API返回错误状态，记录错误信息并返回None
                            if data.get('status') is False:
                                error_msg = data.get('message', '未知错误')
                                error_code = data.get('code', '未知错误码')
                                self.logger.error(
                                    f"API返回错误: {error_msg} (错误码: {error_code})"
                                )
                                return None

                            # 如果API返回成功状态，返回数据
                            if data.get('status') is True:
                                return data.get("data", [])

                            # 如果没有明确的状态字段，尝试直接获取data
                            if "data" in data:
                                return data.get("data", [])

                        # 如果响应格式不符合预期，记录警告
                        self.logger.warning(f"API响应格式异常: {data}")
                        return data.get("data", []) if isinstance(
                            data, dict) else []

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
            fetch_full_content: bool = True) -> list[dict[str, Any]]:
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

        # 处理每个搜索结果
        web_docs = []
        for index, web_page in enumerate(net_info):
            # 获取内容
            content = web_page.get('materialContent', '')

            # 如果需要获取完整内容且当前内容较短（少于200字符）
            if fetch_full_content and len(content) < 200 and web_page.get(
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
                "url": web_page.get("url", ""),
                "doc_id": web_page.get("file_name", ""),
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

    async def search_async(self,
                           query: str,
                           fetch_full_content: bool = True) -> str:
        """
        异步搜索接口

        Args:
            query: 搜索查询字符串

        Returns:
            str: 搜索结果的文本表示
        """
        logger.info(f"开始异步网络搜索，查询: '{query[:50]}...'")

        try:
            web_docs = await self.get_web_docs(query, fetch_full_content)

            if not web_docs:
                return f"搜索失败或无结果: {query}"

            # 格式化结果
            result = f"Search results for: {query}\n\n"
            for i, doc in enumerate(web_docs):
                meta = doc['meta_data']
                title = meta.get('docName', 'Unknown')
                url = doc['url']
                content = doc['text'][:200] + "..." if len(
                    doc['text']) > 200 else doc['text']

                result += f"{i+1}. {title}\n"
                result += f"   URL: {url}\n"
                result += f"   内容长度: {len(doc['text'])} 字符\n"
                result += f"   是否获取完整内容: {doc.get('full_content_fetched', False)}\n"
                result += f"   内容预览: {content}\n\n"

            logger.info("异步网络搜索完成")
            return web_docs, result

        except Exception as e:
            logger.error(f"异步网络搜索失败: {str(e)}")
            return f"搜索失败: {str(e)}"


if __name__ == "__main__":
    """
    网络搜索工具测试代码
    测试同步和异步搜索功能
    """
    import asyncio

    from loguru import logger

    # 配置日志
    logger.add("logs/web_search_test.log",
               rotation="1 day",
               retention="7 days")

    async def test_async_search():
        """测试异步搜索功能"""
        logger.info("=== 开始异步搜索测试 ===")

        # 创建搜索工具实例
        web_search = WebSearchTool()

        # 测试查询
        test_queries = ["Python 异步编程", "人工智能发展", "机器学习算法"]

        for query in test_queries:
            logger.info(f"测试查询: {query}")
            try:
                # 测试异步搜索
                result = await web_search.search_async(query)
                logger.info(f"异步搜索结果:\n{result}")

                # 测试获取文档
                web_docs = await web_search.get_web_docs(query)
                logger.info(f"获取到 {len(web_docs)} 个文档")

                # 显示文档详情
                for i, doc in enumerate(web_docs[:2]):  # 只显示前2个
                    logger.info(f"文档 {i+1}:")
                    logger.info(f"  ID: {doc.get('_id', 'N/A')}")
                    logger.info(f"  URL: {doc.get('doc_id', 'N/A')}")
                    logger.info(
                        f"  标题: {doc.get('meta_data', {}).get('docName', 'N/A')}"
                    )
                    logger.info(f"  内容长度: {len(doc.get('text', ''))} 字符")
                    logger.info(
                        f"  是否获取完整内容: {doc.get('full_content_fetched', False)}"
                    )

            except Exception as e:
                logger.error(f"异步搜索测试失败: {e}")

            logger.info("-" * 50)

    def test_sync_search():
        """测试同步搜索功能"""
        logger.info("=== 开始同步搜索测试 ===")

        # 创建搜索工具实例
        web_search = WebSearchTool()

        # 测试查询
        test_query = "Python 编程教程"
        logger.info(f"测试查询: {test_query}")

        try:
            # 测试同步搜索
            result = web_search.search(test_query)
            logger.info(f"同步搜索结果:\n{result}")

        except Exception as e:
            logger.error(f"同步搜索测试失败: {e}")

        logger.info("-" * 50)

    async def test_web_scraper():
        """测试网页抓取功能"""
        logger.info("=== 开始网页抓取测试 ===")

        # 创建网页抓取器
        scraper = WebScraper()

        # 测试URL
        test_urls = ["https://www.python.org", "https://docs.python.org/3/"]

        for url in test_urls:
            logger.info(f"测试抓取: {url}")
            try:
                content = await scraper.fetch_full_content(url)
                if content:
                    logger.info(f"抓取成功，内容长度: {len(content)} 字符")
                    logger.info(f"内容预览: {content[:200]}...")
                else:
                    logger.warning("抓取失败，返回空内容")
            except Exception as e:
                logger.error(f"网页抓取测试失败: {e}")

            logger.info("-" * 30)

    async def test_config():
        """测试配置功能"""
        logger.info("=== 开始配置测试 ===")

        # 测试默认配置
        default_config = WebSearchConfig()
        logger.info(f"默认配置:")
        logger.info(f"  URL: {default_config.url}")
        logger.info(f"  Count: {default_config.count}")
        logger.info(f"  Timeout: {default_config.timeout}")
        logger.info(f"  Retries: {default_config.retries}")
        logger.info(f"  Delay: {default_config.delay}")
        logger.info(
            f"  Fetch Full Content: {default_config.fetch_full_content}")

        # 测试自定义配置
        custom_config = WebSearchConfig({
            "count": 3,
            "timeout": 10,
            "retries": 2,
            "delay": 0.5
        })
        logger.info(f"自定义配置:")
        logger.info(f"  Count: {custom_config.count}")
        logger.info(f"  Timeout: {custom_config.timeout}")
        logger.info(f"  Retries: {custom_config.retries}")
        logger.info(f"  Delay: {custom_config.delay}")

        logger.info("-" * 50)

    async def test_detailed_search():
        """详细测试搜索功能，包含请求详情"""
        logger.info("=== 开始详细搜索测试 ===")

        # 创建搜索工具实例
        web_search = WebSearchTool()

        # 测试查询
        test_query = "Python 编程"
        logger.info(f"测试查询: {test_query}")

        try:
            # 直接测试 get_web_search 方法
            logger.info("1. 测试 get_web_search 方法")
            raw_results = await web_search.get_web_search(test_query)

            if raw_results is None:
                logger.error("get_web_search 返回 None，可能的原因:")
                logger.error("  - API 服务不可用")
                logger.error("  - 网络连接问题")
                logger.error("  - Token 无效或过期")
                logger.error("  - URL 配置错误")
                return

            logger.info(f"原始搜索结果数量: {len(raw_results)}")

            # 显示原始结果详情
            for i, result in enumerate(raw_results[:2]):
                logger.info(f"原始结果 {i+1}:")
                logger.info(f"  materialId: {result.get('materialId', 'N/A')}")
                logger.info(f"  docName: {result.get('docName', 'N/A')}")
                logger.info(f"  url: {result.get('url', 'N/A')}")
                logger.info(
                    f"  materialContent 长度: {len(result.get('materialContent', ''))}"
                )
                logger.info(f"  完整内容: {result}")

            # 测试 get_web_docs 方法
            logger.info("2. 测试 get_web_docs 方法")
            web_docs = await web_search.get_web_docs(test_query)
            logger.info(f"格式化文档数量: {len(web_docs)}")

            # 显示格式化文档详情
            for i, doc in enumerate(web_docs[:2]):
                logger.info(f"格式化文档 {i+1}:")
                logger.info(f"  doc_id: {doc.get('doc_id', 'N/A')}")
                logger.info(f"  _id: {doc.get('_id', 'N/A')}")
                logger.info(f"  rank: {doc.get('rank', 'N/A')}")
                logger.info(f"  text 长度: {len(doc.get('text', ''))}")
                logger.info(
                    f"  full_content_fetched: {doc.get('full_content_fetched', False)}"
                )
                logger.info(f"  meta_data: {doc.get('meta_data', {})}")

        except Exception as e:
            logger.error(f"详细搜索测试失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

        logger.info("-" * 50)

    async def test_network_connectivity():
        """测试网络连接性"""
        logger.info("=== 开始网络连接测试 ===")

        import aiohttp

        # 测试配置
        config = WebSearchConfig()
        test_url = config.url
        headers = {"X-API-KEY-AUTH": f"Bearer {config.token}"}
        params = {"queryStr": "test", "count": 1}

        logger.info(f"测试URL: {test_url}")
        logger.info(f"请求头: {headers}")
        logger.info(f"请求参数: {params}")

        try:
            timeout_obj = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(test_url,
                                       headers=headers,
                                       params=params) as response:
                    logger.info(f"响应状态码: {response.status}")
                    logger.info(f"响应头: {dict(response.headers)}")

                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"响应数据: {data}")
                        except Exception as e:
                            logger.error(f"解析响应JSON失败: {e}")
                            text = await response.text()
                            logger.info(f"响应文本: {text[:500]}...")
                    else:
                        logger.error(f"HTTP错误: {response.status}")
                        text = await response.text()
                        logger.error(f"错误响应: {text}")

        except Exception as e:
            logger.error(f"网络连接测试失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

        logger.info("-" * 50)

    async def test_api_diagnosis():
        """API诊断测试"""
        logger.info("=== 开始API诊断测试 ===")

        import aiohttp

        # 测试配置
        config = WebSearchConfig()
        test_url = config.url
        headers = {"X-API-KEY-AUTH": f"Bearer {config.token}"}

        # 测试不同的查询参数
        test_cases = [
            {
                "queryStr": "Python",
                "count": 1
            },
            {
                "queryStr": "人工智能",
                "count": 2
            },
            {
                "queryStr": "机器学习",
                "count": 3
            },
            {
                "queryStr": "深度学习",
                "count": 5
            },
        ]

        logger.info(f"API端点: {test_url}")
        logger.info(f"认证Token: {config.token[:20]}...")
        logger.info(f"请求头: {headers}")

        for i, params in enumerate(test_cases, 1):
            logger.info(f"\n测试用例 {i}: {params}")

            try:
                timeout_obj = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(
                        timeout=timeout_obj) as session:
                    async with session.get(test_url,
                                           headers=headers,
                                           params=params) as response:
                        logger.info(f"  响应状态码: {response.status}")
                        logger.info(f"  响应头: {dict(response.headers)}")

                        if response.status == 200:
                            try:
                                data = await response.json()
                                logger.info(f"  响应数据: {data}")

                                # 分析响应
                                if isinstance(data, dict):
                                    status = data.get('status')
                                    message = data.get('message', '')
                                    code = data.get('code', '')

                                    if status is False:
                                        logger.error(
                                            f"  ❌ API错误: {message} (错误码: {code})"
                                        )

                                        # 根据错误码提供建议
                                        if code == -8000040:
                                            logger.error("  💡 建议解决方案:")
                                            logger.error(
                                                "    1. 检查网络检索服务是否正常运行")
                                            logger.error("    2. 确认API权限和配额")
                                            logger.error("    3. 联系API服务提供商")
                                            logger.error("    4. 检查查询参数格式是否正确")
                                    elif status is True:
                                        logger.info(
                                            f"  ✅ API成功: 找到 {len(data.get('data', []))} 个结果"
                                        )
                                    else:
                                        logger.warning(
                                            f"  ⚠️   API状态不明确: {status}")
                                else:
                                    logger.warning(
                                        f"  ⚠️  响应格式异常: {type(data)}")

                            except Exception as e:
                                logger.error(f"  ❌ 解析响应失败: {e}")
                                text = await response.text()
                                logger.info(f"  原始响应: {text[:500]}...")
                        else:
                            logger.error(f"  ❌ HTTP错误: {response.status}")
                            text = await response.text()
                            logger.error(f"  错误响应: {text}")

            except Exception as e:
                logger.error(f"  ❌ 请求失败: {e}")

        logger.info("-" * 50)

    async def test_alternative_queries():
        """测试替代查询方式"""
        logger.info("=== 开始替代查询测试 ===")

        # 创建搜索工具实例
        web_search = WebSearchTool()

        # 测试不同的查询格式
        test_queries = [
            "Python编程", "AI技术", "机器学习算法", "深度学习框架", "自然语言处理", "计算机视觉", "数据科学",
            "算法设计"
        ]

        for query in test_queries:
            logger.info(f"测试查询: '{query}'")
            try:
                result = await web_search.get_web_search(query)
                if result:
                    logger.info(f"  ✅ 成功获取 {len(result)} 个结果")
                else:
                    logger.warning(f"  ⚠️  无结果")
            except Exception as e:
                logger.error(f"  ❌ 查询失败: {e}")

        logger.info("-" * 50)

    async def main():
        """主测试函数"""
        logger.info("开始网络搜索工具测试")

        try:
            # 测试配置
            await test_config()

            # 测试网络连接
            await test_network_connectivity()

            # API诊断测试
            await test_api_diagnosis()

            # 替代查询测试
            await test_alternative_queries()

            # 测试网页抓取
            await test_web_scraper()

            # 详细搜索测试
            await test_detailed_search()

            # 测试异步搜索
            await test_async_search()

            # 测试同步搜索
            test_sync_search()

            logger.info("所有测试完成")

        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

    # 运行测试
    if __name__ == "__main__":
        asyncio.run(main())
