#!/usr/bin/env python3
"""
简单的ES原始响应测试
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService
from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)


async def test_es_raw_simple():
    """简单的ES原始响应测试"""
    logger.info("🚀 开始简单ES原始响应测试")

    try:
        # 1. 初始化ES服务
        logger.info("📡 初始化ES服务...")
        es_config = settings.elasticsearch_config
        es_hosts = es_config.hosts
        es_username = es_config.username
        es_password = es_config.password

        es_service = ESService(hosts=es_hosts,
                               username=es_username,
                               password=es_password)

        # 2. 连接ES
        await es_service.connect()
        logger.info("✅ ES连接成功")

        # 3. 获取索引列表
        indices = await es_service.get_indices()
        logger.info(f"📊 可用索引数量: {len(indices)}")

        if not indices:
            logger.warning("⚠️ 没有可用索引")
            return False

        # 4. 选择一个有数据的索引进行测试
        test_index = None
        for idx in indices:
            if isinstance(idx, dict) and 'index' in idx:
                index_name = idx['index']
                # 跳过系统索引
                if not index_name.startswith(
                        '.') and 'monitoring' not in index_name:
                    test_index = index_name
                    break

        if not test_index:
            test_index = indices[0]['index'] if isinstance(
                indices[0], dict) and 'index' in indices[0] else str(
                    indices[0])

        logger.info(f"🔍 使用测试索引: {test_index}")

        # 5. 构建简单搜索查询
        search_body = {
            "size": 2,
            "query": {
                "multi_match": {
                    "query": "人工智能",
                    "fields": ["content", "title", "text"]
                }
            }
        }

        logger.info(
            f"🔍 搜索查询体: {json.dumps(search_body, indent=2, ensure_ascii=False)}"
        )

        # 6. 执行原始搜索
        raw_response = await es_service._client.search(index=test_index,
                                                       body=search_body)

        logger.info("✅ 原始ES响应获取成功")
        logger.info(f"📊 原始响应结构: {list(raw_response.keys())}")

        # 7. 分析原始响应
        hits = raw_response.get('hits', {})
        total_hits = hits.get('total', {})
        logger.info(f"📊 总命中数: {total_hits}")

        # 8. 分析前2个原始结果
        for i, hit in enumerate(hits.get('hits', [])[:2], 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"原始结果 {i}:")
            logger.info(f"{'='*80}")

            # 显示完整的原始hit结构
            logger.info(f"📋 完整原始hit结构:")
            logger.info(json.dumps(hit, indent=2, ensure_ascii=False))

            # 分析_source字段
            source = hit.get('_source', {})
            logger.info(f"\n🔍 _source字段分析:")
            logger.info(f"  - _source字段数量: {len(source)}")
            logger.info(f"  - _source字段列表: {list(source.keys())}")

            # 检查是否有domainId和fileFrom
            logger.info(f"\n🔎 特殊字段检查:")
            if 'domainId' in source:
                logger.info(f"  ✅ 找到 domainId: {source['domainId']}")
            else:
                logger.info(f"  ❌ 未找到 domainId")

            if 'fileFrom' in source:
                logger.info(f"  ✅ 找到 fileFrom: {source['fileFrom']}")
            else:
                logger.info(f"  ❌ 未找到 fileFrom")

            # 检查所有可能的字段变体
            domain_variants = [
                'domainId', 'domain_id', 'domain', 'DomainId', 'domainId',
                'domainName'
            ]
            file_variants = [
                'fileFrom', 'file_from', 'fileFrom', 'FileFrom', 'source_type',
                'file_source'
            ]

            for variant in domain_variants:
                if variant in source:
                    logger.info(
                        f"  ✅ 找到 domain 变体 '{variant}': {source[variant]}")

            for variant in file_variants:
                if variant in source:
                    logger.info(
                        f"  ✅ 找到 file 变体 '{variant}': {source[variant]}")

            # 显示所有字段的详细信息
            logger.info(f"\n📄 所有字段详细信息:")
            for key, value in source.items():
                if isinstance(value, str) and len(value) > 100:
                    display_value = value[:100] + "..."
                else:
                    display_value = value
                logger.info(f"  * {key}: {display_value}")

        logger.info("🎉 简单ES原始响应测试完成！")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧪 简单ES原始响应测试")
    logger.info("=" * 60)

    success = await test_es_raw_simple()

    if success:
        logger.info("✅ 测试完成！")
    else:
        logger.error("❌ 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
