#!/usr/bin/env python3
"""
使用真实存在的 doc_id 测试 search_within_documents 函数
"""

import asyncio
import os
import sys
from typing import Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.tools.es_search import ESSearchTool


async def test_search_within_documents_real():
    """使用真实存在的 doc_id 测试 search_within_documents 函数"""
    logger.info("开始使用真实 doc_id 测试 search_within_documents 函数")

    # 测试参数 - 使用从之前测试中获取的真实 doc_id
    query = "人工智能"
    # 使用从 personal_knowledge_base 中获取的真实 doc_id
    file_tokens = ["3e1e5b97fd91f53140b7a6588ad9a502"]  # 这个 doc_id 是真实存在的
    top_k = 10

    # 从配置文件获取ES配置
    from doc_agent.core.config import settings

    es_config = settings.elasticsearch_config
    es_hosts = es_config.hosts
    es_username = es_config.username
    es_password = es_config.password

    logger.info(f"ES配置 - hosts: {es_hosts}, username: {es_username}")
    logger.info(
        f"测试参数 - query: {query}, file_tokens: {file_tokens}, top_k: {top_k}")

    # 创建ES搜索工具实例
    es_search_tool = ESSearchTool(hosts=es_hosts,
                                  username=es_username,
                                  password=es_password)

    try:
        # 确保初始化
        await es_search_tool._ensure_initialized()

        # 检查ES服务状态
        logger.info("检查ES服务状态...")
        await es_search_tool._es_service._ensure_connected()

        # 获取有效索引列表
        valid_indices = es_search_tool._es_service.get_valid_indices()
        logger.info(f"有效索引列表: {valid_indices}")

        # 测试目标函数
        logger.info("测试: 调用 search_within_documents 函数")
        results = await es_search_tool.search_within_documents(
            query=query, file_tokens=file_tokens, top_k=top_k)

        logger.info(f"search_within_documents 返回结果数量: {len(results)}")

        if results:
            logger.info("搜索结果详情:")
            for i, result in enumerate(results):
                logger.info(f"结果{i+1}:")
                logger.info(f"  - ID: {result.id}")
                logger.info(f"  - 索引: {result.index}")
                logger.info(f"  - doc_id: {result.doc_id}")
                logger.info(f"  - domain_id: {result.domain_id}")
                logger.info(f"  - doc_from: {result.doc_from}")
                logger.info(f"  - 来源: {result.source}")
                logger.info(f"  - 分数: {result.score}")
                logger.info(f"  - 内容长度: {len(result.original_content)}")
                logger.info(f"  - 内容预览: {result.original_content[:100]}...")
        else:
            logger.warning("没有找到任何搜索结果")

            # 进一步诊断
            logger.info("进一步诊断:")

            # 检查是否有任何文档包含这个doc_id
            logger.info("检查是否有任何文档包含这个doc_id...")
            for index in valid_indices[:3]:
                try:
                    # 使用 doc_id 进行搜索
                    search_body = {
                        "size": 5,
                        "query": {
                            "term": {
                                "doc_id": file_tokens[0]
                            }
                        }
                    }

                    response = await es_search_tool._es_service._client.search(
                        index=index, body=search_body)

                    hits = response.get('hits', {}).get('hits', [])
                    logger.info(f"索引 {index} 中doc_id搜索结果: {len(hits)}")
                    if hits:
                        for hit in hits:
                            doc_data = hit['_source']
                            logger.info(
                                f"  - doc_id: {doc_data.get('doc_id')}, file_token: {doc_data.get('file_token')}"
                            )
                except Exception as e:
                    logger.error(f"检查索引 {index} 失败: {e}")

            # 检查是否有任何文档包含查询词
            logger.info("检查是否有任何文档包含查询词...")
            for index in valid_indices[:3]:
                try:
                    content_results = await es_search_tool._es_service.search(
                        index=index, query=query, top_k=5)
                    logger.info(f"索引 {index} 中内容搜索结果: {len(content_results)}")
                    if content_results:
                        for result in content_results:
                            logger.info(
                                f"  - doc_id: {result.doc_id}, score: {result.score}"
                            )
                except Exception as e:
                    logger.error(f"检查索引 {index} 内容失败: {e}")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

    finally:
        # 关闭连接
        await es_search_tool._es_service.close()
        logger.info("测试完成")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_search_within_documents_real())
