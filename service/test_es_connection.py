#!/usr/bin/env python3
"""
测试ES连接和索引状态
"""

import asyncio
import sys
from typing import Any

from doc_agent.core.logger import logger

# 添加项目路径
sys.path.append("src")

from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService


async def test_es_connection():
    """测试ES连接"""
    logger.info("=== 测试ES连接和索引状态 ===")

    # 获取ES配置
    es_config = settings.elasticsearch_config
    logger.info(f"ES配置:")
    logger.info(f"  Hosts: {es_config.hosts}")
    logger.info(f"  Username: {es_config.username}")
    logger.info(
        f"  Password: {'*' * len(es_config.password) if es_config.password else 'None'}"
    )
    logger.info(f"  Index Prefix: {es_config.index_prefix}")
    logger.info(f"  Timeout: {es_config.timeout}")

    # 创建ES服务实例
    es_service = ESService(hosts=es_config.hosts,
                           username=es_config.username,
                           password=es_config.password,
                           timeout=es_config.timeout)

    try:
        # 测试连接
        logger.info("🔗 测试ES连接...")
        if await es_service.connect():
            logger.success("✅ ES连接成功")

            # 获取所有索引
            logger.info("📋 获取所有索引...")
            indices = await es_service.get_indices()
            logger.info(f"找到 {len(indices)} 个索引:")

            for idx in indices:
                index_name = idx.get('index', '')
                docs_count = idx.get('docs.count', '0')
                size = idx.get('store.size', '0')
                logger.info(f"  - {index_name}: {docs_count} 文档, 大小: {size}")

            # 检查是否有知识库相关索引
            knowledge_indices = []
            for idx in indices:
                index_name = idx.get('index', '')
                docs_count = idx.get('docs.count', '0')

                # 查找包含知识库关键词的索引
                if any(keyword in index_name.lower()
                       for keyword in ['knowledge', 'base', 'index', 'doc']):
                    if docs_count and docs_count != '0' and docs_count != 'None':
                        knowledge_indices.append({
                            'name':
                            index_name,
                            'docs_count':
                            int(docs_count) if docs_count != 'None' else 0
                        })

            if knowledge_indices:
                logger.success(f"✅ 找到 {len(knowledge_indices)} 个知识库索引:")
                for idx in knowledge_indices:
                    logger.info(f"  - {idx['name']} ({idx['docs_count']} 文档)")
            else:
                logger.warning("⚠️  没有找到知识库索引")
                logger.info(
                    "💡 建议创建包含 'knowledge', 'base', 'index', 'doc' 关键词的索引")

            # 测试搜索功能
            if knowledge_indices:
                test_index = knowledge_indices[0]['name']
                logger.info(f"🔍 测试搜索功能，使用索引: {test_index}")

                # 获取索引映射
                mapping = await es_service.get_index_mapping(test_index)
                if mapping:
                    logger.info("✅ 成功获取索引映射")
                    properties = mapping.get('properties', {})
                    if 'context_vector' in properties:
                        logger.info("✅ 找到向量字段 'context_vector'")
                        vector_config = properties['context_vector']
                        if 'dims' in vector_config:
                            logger.info(f"✅ 向量维度: {vector_config['dims']}")
                        else:
                            logger.warning("⚠️  向量配置中未找到dims字段")
                    else:
                        logger.warning("⚠️  索引中未找到向量字段")
                else:
                    logger.warning("⚠️  无法获取索引映射")

                # 测试文本搜索
                logger.info("🔍 测试文本搜索...")
                try:
                    results = await es_service.search(index=test_index,
                                                      query="测试查询",
                                                      top_k=5)
                    logger.success(f"✅ 文本搜索成功，返回 {len(results)} 个结果")
                except Exception as e:
                    logger.error(f"❌ 文本搜索失败: {str(e)}")

        else:
            logger.error("❌ ES连接失败")

    except Exception as e:
        logger.error(f"❌ ES测试失败: {str(e)}")

    finally:
        # 关闭连接
        await es_service.close()
        logger.info("🔒 ES连接已关闭")


async def main():
    """主函数"""
    logger.info("🚀 开始ES连接测试")
    await test_es_connection()
    logger.info("✅ ES连接测试完成")


if __name__ == "__main__":
    asyncio.run(main())
