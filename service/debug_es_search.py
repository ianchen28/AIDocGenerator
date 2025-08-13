#!/usr/bin/env python3
"""
调试ES搜索功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService


async def debug_es_search():
    """调试ES搜索功能"""

    test_file_token = "2dbceb750506dc2f2bdc3cf991adab4d"

    logger.info(f"🔍 调试ES搜索，file_token: {test_file_token}")

    try:
        # 使用配置文件中的ES配置
        es_config = settings.elasticsearch_config
        logger.info(f"📊 使用ES配置: {es_config.hosts}")

        # 直接使用ES服务
        es_service = ESService(hosts=es_config.hosts,
                               username=es_config.username,
                               password=es_config.password,
                               timeout=es_config.timeout)

        # 连接ES
        await es_service.connect()

        # 1. 先检查所有索引
        logger.info("📊 检查所有索引...")
        indices = await es_service.get_indices()
        logger.info(f"找到 {len(indices)} 个索引")

        # 2. 在全索引中搜索 - 使用修改后的search_by_file_token方法
        test_indices = ["*"]

        for index_name in test_indices:
            logger.info(f"🔍 在索引 {index_name} 中搜索...")

            try:
                results = await es_service.search_by_file_token(
                    index=index_name, file_token=test_file_token, top_k=10)

                logger.info(f"📊 索引 {index_name} 返回 {len(results)} 个结果")

                if results:
                    logger.info(f"✅ 在索引 {index_name} 中找到文档！")
                    for i, result in enumerate(results[:3]):
                        logger.info(f"  结果 {i+1}:")
                        logger.info(f"    ID: {result.id}")
                        logger.info(f"    Doc ID: {result.doc_id}")
                        logger.info(f"    File Token: {result.file_token}")
                        logger.info(f"    Source: {result.source}")
                        logger.info(
                            f"    Content (前100字符): {result.original_content[:100]}..."
                        )
                        logger.info("    ---")
                    break
                else:
                    logger.info(f"❌ 索引 {index_name} 中未找到文档")

            except Exception as e:
                logger.error(f"❌ 搜索索引 {index_name} 失败: {e}")

        # 3. 尝试直接使用doc_id字段查询
        logger.info("🔍 尝试直接使用doc_id字段查询...")
        for index_name in test_indices:
            try:
                # 构建doc_id查询
                search_body = {
                    "size": 20,  # 设置更大的size
                    "query": {
                        "term": {
                            "doc_id": test_file_token
                        }
                    }
                }

                response = await es_service._client.search(index=index_name,
                                                           body=search_body)
                hits = response['hits']['hits']

                logger.info(f"📊 索引 {index_name} doc_id查询返回 {len(hits)} 个结果")

                if hits:
                    logger.info(f"✅ 在索引 {index_name} 中找到doc_id匹配文档！")
                    for hit in hits[:3]:
                        doc_data = hit['_source']
                        logger.info(f"  文档:")
                        logger.info(f"    ID: {hit['_id']}")
                        logger.info(
                            f"    Doc ID: {doc_data.get('doc_id', 'N/A')}")
                        logger.info(
                            f"    File Token: {doc_data.get('file_token', 'N/A')}"
                        )
                        logger.info(
                            f"    Source: {doc_data.get('file_name', 'N/A')}")
                        logger.info("    ---")
                    break

            except Exception as e:
                logger.error(f"❌ doc_id查询索引 {index_name} 失败: {e}")

        # 4. 尝试搜索部分doc_id
        logger.info("🔍 尝试搜索部分doc_id...")
        partial_doc_id = test_file_token[:16]

        for index_name in test_indices:
            try:
                search_body = {
                    "size": 20,
                    "query": {
                        "wildcard": {
                            "doc_id": f"*{partial_doc_id}*"
                        }
                    }
                }

                response = await es_service._client.search(index=index_name,
                                                           body=search_body)
                hits = response['hits']['hits']

                logger.info(f"📊 索引 {index_name} 部分doc_id搜索返回 {len(hits)} 个结果")

                if hits:
                    logger.info(f"✅ 在索引 {index_name} 中找到部分doc_id匹配文档！")
                    for hit in hits[:3]:
                        doc_data = hit['_source']
                        logger.info(f"  文档:")
                        logger.info(f"    ID: {hit['_id']}")
                        logger.info(
                            f"    Doc ID: {doc_data.get('doc_id', 'N/A')}")
                        logger.info(
                            f"    File Token: {doc_data.get('file_token', 'N/A')}"
                        )
                        logger.info(
                            f"    Source: {doc_data.get('file_name', 'N/A')}")
                        logger.info("    ---")
                    break

            except Exception as e:
                logger.error(f"❌ 部分doc_id搜索索引 {index_name} 失败: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ 调试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("🎯 ES搜索调试")
    logger.info("=" * 50)

    success = await debug_es_search()

    logger.info("=" * 50)
    if success:
        logger.success("🎉 调试完成！")
    else:
        logger.error("💥 调试失败！")

    return 0 if success else 1


if __name__ == "__main__":
    # 激活conda环境
    import subprocess
    try:
        subprocess.run(["conda", "activate", "ai-doc"], shell=True, check=True)
        logger.info("✅ 已激活ai-doc conda环境")
    except subprocess.CalledProcessError:
        logger.warning("⚠️  无法激活conda环境，请手动激活")

    # 运行调试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
