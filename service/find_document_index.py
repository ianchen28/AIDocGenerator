#!/usr/bin/env python3
"""
查找文档在哪个索引中
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService


async def find_document_index():
    """查找文档在哪个索引中"""

    test_file_token = "2dbceb750506dc2f2bdc3cf991adab4d"

    logger.info(f"🔍 查找文档索引，file_token: {test_file_token}")

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

        # 2. 在每个索引中搜索文档
        found_in_indices = []

        for index_info in indices:
            index_name = index_info['index']
            try:
                # 构建doc_id查询
                search_body = {
                    "size": 1,
                    "query": {
                        "term": {
                            "doc_id": test_file_token
                        }
                    }
                }

                response = await es_service._client.search(index=index_name,
                                                           body=search_body)
                hits = response['hits']['hits']

                if hits:
                    found_in_indices.append(index_name)
                    logger.info(f"✅ 在索引 {index_name} 中找到文档")

                    # 显示文档详情
                    hit = hits[0]
                    doc_data = hit['_source']
                    logger.info(f"  文档详情:")
                    logger.info(f"    ID: {hit['_id']}")
                    logger.info(f"    Doc ID: {doc_data.get('doc_id', 'N/A')}")
                    logger.info(
                        f"    File Token: {doc_data.get('file_token', 'N/A')}")
                    logger.info(
                        f"    File Name: {doc_data.get('file_name', 'N/A')}")
                    logger.info(
                        f"    Content (前100字符): {doc_data.get('content', '')[:100]}..."
                    )
                    logger.info("    ---")

            except Exception as e:
                logger.debug(f"❌ 搜索索引 {index_name} 失败: {e}")
                continue

        # 3. 总结结果
        logger.info("=" * 50)
        if found_in_indices:
            logger.success(f"🎉 找到文档！文档存在于以下 {len(found_in_indices)} 个索引中:")
            for idx, index_name in enumerate(found_in_indices, 1):
                logger.info(f"  {idx}. {index_name}")
        else:
            logger.error("❌ 未找到文档")

        return True

    except Exception as e:
        logger.error(f"❌ 查找失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("🎯 查找文档索引")
    logger.info("=" * 50)

    success = await find_document_index()

    logger.info("=" * 50)
    if success:
        logger.success("🎉 查找完成！")
    else:
        logger.error("💥 查找失败！")

    return 0 if success else 1


if __name__ == "__main__":
    # 激活conda环境
    import subprocess
    try:
        subprocess.run(["conda", "activate", "ai-doc"], shell=True, check=True)
        logger.info("✅ 已激活ai-doc conda环境")
    except subprocess.CalledProcessError:
        logger.warning("⚠️  无法激活conda环境，请手动激活")

    # 运行查找
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
