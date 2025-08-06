#!/usr/bin/env python3
"""
网络搜索服务测试脚本
测试用户提供的网络搜索API配置
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional

import aiohttp
from loguru import logger


class WebSearchTester:
    """网络搜索服务测试器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化测试器
        
        Args:
            config: 配置字典，包含url和token
        """
        self.config = config
        self.url = config.get("url")
        self.token = config.get("token")

        # 设置日志
        logger.add("logs/web_search_test.log",
                   rotation="1 day",
                   retention="7 days",
                   level="INFO")

        logger.info("初始化网络搜索测试器")
        logger.info(f"测试URL: {self.url}")
        logger.info(
            f"Token: {self.token[:20]}..." if self.token else "Token: None")

    async def test_connectivity(self) -> bool:
        """测试网络连接性"""
        logger.info("=== 测试网络连接性 ===")

        try:
            timeout_obj = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(self.url) as response:
                    logger.info(f"连接状态码: {response.status}")
                    logger.info(f"响应头: {dict(response.headers)}")

                    if response.status == 200:
                        logger.info("✅ 网络连接成功")
                        return True
                    else:
                        logger.error(f"❌ 网络连接失败，状态码: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ 网络连接测试失败: {e}")
            return False

    async def test_api_authentication(self) -> bool:
        """测试API认证"""
        logger.info("=== 测试API认证 ===")

        if not self.token:
            logger.error("❌ Token未提供")
            return False

        headers = {"X-API-KEY-AUTH": f"Bearer {self.token}"}
        params = {"queryStr": "test", "count": 1}

        try:
            timeout_obj = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(self.url,
                                       headers=headers,
                                       params=params) as response:
                    logger.info(f"认证请求状态码: {response.status}")

                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(
                                f"API响应: {json.dumps(data, ensure_ascii=False, indent=2)}"
                            )

                            # 检查响应结构
                            if isinstance(data, dict):
                                if data.get('status') is True:
                                    logger.info("✅ API认证成功")
                                    return True
                                elif data.get('status') is False:
                                    error_msg = data.get('message', '未知错误')
                                    logger.error(f"❌ API返回错误: {error_msg}")
                                    return False
                                else:
                                    logger.info("✅ API响应正常（无明确状态字段）")
                                    return True
                            else:
                                logger.info("✅ API响应正常")
                                return True

                        except Exception as e:
                            logger.error(f"❌ 解析API响应失败: {e}")
                            return False
                    else:
                        logger.error(f"❌ API认证失败，状态码: {response.status}")
                        text = await response.text()
                        logger.error(f"错误响应: {text}")
                        return False

        except Exception as e:
            logger.error(f"❌ API认证测试失败: {e}")
            return False

    async def test_search_functionality(self, query: str = "水电站") -> bool:
        """测试搜索功能"""
        logger.info(f"=== 测试搜索功能: {query} ===")

        headers = {"X-API-KEY-AUTH": f"Bearer {self.token}"}
        params = {"queryStr": query, "count": 5}

        try:
            timeout_obj = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(self.url,
                                       headers=headers,
                                       params=params) as response:
                    logger.info(f"搜索请求状态码: {response.status}")

                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(
                                f"搜索响应: {json.dumps(data, ensure_ascii=False, indent=2)}"
                            )

                            # 分析搜索结果
                            if isinstance(data, dict):
                                if data.get('status') is True:
                                    results = data.get('data', [])
                                    logger.info(
                                        f"✅ 搜索成功，返回 {len(results)} 个结果")

                                    # 显示结果详情
                                    for i, result in enumerate(
                                            results[:3]):  # 只显示前3个
                                        logger.info(f"结果 {i+1}:")
                                        logger.info(
                                            f"  materialId: {result.get('materialId', 'N/A')}"
                                        )
                                        logger.info(
                                            f"  docName: {result.get('docName', 'N/A')}"
                                        )
                                        logger.info(
                                            f"  url: {result.get('url', 'N/A')}"
                                        )
                                        content_length = len(
                                            result.get('materialContent', ''))
                                        logger.info(
                                            f"  materialContent 长度: {content_length} 字符"
                                        )

                                        if content_length > 0:
                                            preview = result.get(
                                                'materialContent', '')[:200]
                                            logger.info(
                                                f"  内容预览: {preview}...")

                                    return True
                                else:
                                    error_msg = data.get('message', '未知错误')
                                    logger.error(f"❌ 搜索失败: {error_msg}")
                                    return False
                            else:
                                logger.error("❌ 搜索响应格式错误")
                                return False

                        except Exception as e:
                            logger.error(f"❌ 解析搜索响应失败: {e}")
                            return False
                    else:
                        logger.error(f"❌ 搜索请求失败，状态码: {response.status}")
                        text = await response.text()
                        logger.error(f"错误响应: {text}")
                        return False

        except Exception as e:
            logger.error(f"❌ 搜索功能测试失败: {e}")
            return False

    async def test_multiple_queries(self) -> bool:
        """测试多个查询"""
        logger.info("=== 测试多个查询 ===")

        test_queries = ["水电站建造", "水利工程", "水轮机", "发电机组"]

        success_count = 0
        total_count = len(test_queries)

        for query in test_queries:
            logger.info(f"测试查询: {query}")
            if await self.test_search_functionality(query):
                success_count += 1
            logger.info("-" * 50)

        success_rate = success_count / total_count * 100
        logger.info(
            f"查询测试完成: {success_count}/{total_count} 成功 ({success_rate:.1f}%)")

        return success_rate >= 75  # 75%成功率视为通过

    async def run_full_test(self) -> Dict[str, bool]:
        """运行完整测试"""
        logger.info("🚀 开始网络搜索服务完整测试")
        logger.info("=" * 60)

        results = {}

        # 1. 测试网络连接
        results['connectivity'] = await self.test_connectivity()

        # 2. 测试API认证
        results['authentication'] = await self.test_api_authentication()

        # 3. 测试搜索功能
        results['search_functionality'] = await self.test_search_functionality(
        )

        # 4. 测试多个查询
        results['multiple_queries'] = await self.test_multiple_queries()

        # 总结
        logger.info("=" * 60)
        logger.info("📊 测试结果总结:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")

        overall_success = all(results.values())
        logger.info(f"总体结果: {'✅ 所有测试通过' if overall_success else '❌ 部分测试失败'}")

        return results


async def main():
    """主函数"""
    # 用户提供的配置
    web_search_config = {
        "url":
        "http://10.215.149.74:9930/api/v1/llm-qa/api/chat/net",
        "token":
        "eyJhbGciOiJIUzI1NiJ9.eyJqd3RfbmFtZSI6Iueul-azleiBlOe9keaOpeWPo-a1i-ivlSIsImp3dF91c2VyX2lkIjoyMiwiand0X3VzZXJfbmFtZSI6ImFkbWluIiwiZXhwIjoyMDA1OTc2MjY2LCJpYXQiOjE3NDY3NzYyNjZ9.YLkrXAdx-wyVUwWveVCF2ddjqZrOrwOKxaF8fLOuc6E"
    }

    # 创建测试器
    tester = WebSearchTester(web_search_config)

    # 运行完整测试
    results = await tester.run_full_test()

    # 返回测试结果
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())

        # 根据测试结果设置退出码
        if all(results.values()):
            print("🎉 所有测试通过！网络搜索服务配置正确。")
            sys.exit(0)
        else:
            print("⚠️  部分测试失败，请检查配置和网络连接。")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        sys.exit(1)
