#!/usr/bin/env python3
"""
测试ES搜索的原始返回结果，查看所有字段
"""

import asyncio
import json
import sys
import os
from pprint import pprint

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from doc_agent.core.config import settings
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.llm_clients.providers import EmbeddingClient
from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)


async def test_es_raw_response():
    """测试ES搜索的原始返回结果"""
    logger.info("🚀 开始测试ES搜索原始返回结果")

    try:
        # 1. 初始化ES搜索工具
        logger.info("📡 初始化ES搜索工具...")
        es_config = settings.elasticsearch_config
        es_hosts = es_config.hosts
        es_username = es_config.username
        es_password = es_config.password

        es_search_tool = ESSearchTool(hosts=es_hosts,
                                      username=es_username,
                                      password=es_password)
        logger.info("✅ ES搜索工具初始化成功")

        # 2. 初始化Embedding客户端
        logger.info("🧠 初始化Embedding客户端...")
        embedding_config = settings.supported_models.get("gte_qwen")
        if embedding_config:
            embedding_client = EmbeddingClient(
                base_url=embedding_config.url,
                api_key=embedding_config.api_key)
            logger.info("✅ Embedding客户端初始化成功")
        else:
            embedding_client = None
            logger.warning("⚠️ 未找到Embedding配置，将使用文本搜索")

        # 3. 测试参数
        test_query = "水电站"

        logger.info(f"🔍 测试查询: {test_query}")

        # 4. 生成查询向量
        query_vector = None
        if embedding_client:
            try:
                logger.info("🧠 生成查询向量...")
                embedding_response = embedding_client.invoke(test_query)
                embedding_data = json.loads(embedding_response)

                if isinstance(embedding_data, list):
                    if len(embedding_data) > 0 and isinstance(
                            embedding_data[0], list):
                        query_vector = embedding_data[0]
                    else:
                        query_vector = embedding_data
                elif isinstance(embedding_data,
                                dict) and 'data' in embedding_data:
                    query_vector = embedding_data['data']

                logger.info(
                    f"✅ 查询向量生成成功，维度: {len(query_vector) if query_vector else 0}"
                )
            except Exception as e:
                logger.error(f"❌ 查询向量生成失败: {str(e)}")
                query_vector = None

        # 5. 执行ES搜索并获取原始结果
        logger.info("🔍 执行ES搜索...")
        try:
            # 直接调用ES服务获取原始结果
            await es_search_tool._ensure_initialized()

            # 获取原始ES响应
            if es_search_tool._indices_list:
                index_to_use = es_search_tool._current_index or es_search_tool._indices_list[
                    0]
                logger.info(f"🔍 使用索引: {index_to_use}")

                # 构建搜索查询
                search_body = es_search_tool._es_service._build_search_body(
                    test_query, query_vector, None, 3)
                logger.info(
                    f"🔍 搜索查询体: {json.dumps(search_body, indent=2, ensure_ascii=False)}"
                )

                # 执行原始搜索
                raw_response = await es_search_tool._es_service._client.search(
                    index=index_to_use, body=search_body)

                logger.info(f"✅ 原始ES响应获取成功")
                logger.info(f"📊 原始响应结构: {list(raw_response.keys())}")

                # 分析原始响应
                hits = raw_response.get('hits', {})
                total_hits = hits.get('total', {})
                logger.info(f"📊 总命中数: {total_hits}")

                # 分析前3个原始结果
                for i, hit in enumerate(hits.get('hits', [])[:3], 1):
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
                        'domainId', 'domain_id', 'domain', 'DomainId',
                        'domainId', 'domainName'
                    ]
                    file_variants = [
                        'fileFrom', 'file_from', 'fileFrom', 'FileFrom',
                        'source_type', 'file_source'
                    ]

                    for variant in domain_variants:
                        if variant in source:
                            logger.info(
                                f"  ✅ 找到 domain 变体 '{variant}': {source[variant]}"
                            )

                    for variant in file_variants:
                        if variant in source:
                            logger.info(
                                f"  ✅ 找到 file 变体 '{variant}': {source[variant]}"
                            )

                    # 显示所有字段的详细信息
                    logger.info(f"\n📄 所有字段详细信息:")
                    for key, value in source.items():
                        if isinstance(value, str) and len(value) > 100:
                            display_value = value[:100] + "..."
                        else:
                            display_value = value
                        logger.info(f"  * {key}: {display_value}")

                # 现在也测试ESSearchResult处理后的结果进行对比
                logger.info(f"\n{'='*80}")
                logger.info(f"对比：ESSearchResult处理后的结果")
                logger.info(f"{'='*80}")

                es_results = await es_search_tool.search(
                    query=test_query,
                    query_vector=query_vector,
                    top_k=3,
                    use_multiple_indices=True,
                    config={'min_score': 0.1})

                for i, result in enumerate(es_results, 1):
                    logger.info(f"\n处理后的结果 {i}:")
                    logger.info(f"  - ID: {result.id}")
                    logger.info(f"  - 文档ID: {result.doc_id}")
                    logger.info(f"  - 文件Token: {result.file_token}")
                    logger.info(f"  - 来源: {result.source}")
                    logger.info(f"  - 分数: {result.score}")
                    logger.info(f"  - 别名: {result.alias_name}")
                    logger.info(
                        f"  - 元数据字段数: {len(result.metadata) if result.metadata else 0}"
                    )
                    if result.metadata:
                        logger.info(
                            f"  - 元数据字段: {list(result.metadata.keys())}")
            else:
                logger.warning("⚠️ 没有可用的索引")
                return False

            logger.info(f"✅ ES搜索完成，结果数量: {len(es_results)}")

            if not es_results:
                logger.warning("⚠️ 没有找到搜索结果，尝试降低分数阈值...")
                # 尝试不设置分数阈值
                es_results = await es_search_tool.search(
                    query=test_query,
                    query_vector=query_vector,
                    top_k=3,
                    use_multiple_indices=True)
                logger.info(f"✅ 重新搜索完成，结果数量: {len(es_results)}")

            # 6. 分析每个结果的字段
            for i, result in enumerate(es_results, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"结果 {i}:")
                logger.info(f"{'='*60}")

                # 基本信息
                logger.info(f"📋 基本信息:")
                logger.info(f"  - ID: {result.id}")
                logger.info(f"  - 文档ID: {result.doc_id}")
                logger.info(f"  - 文件Token: {result.file_token}")
                logger.info(f"  - 来源: {result.source}")
                logger.info(f"  - 分数: {result.score}")
                logger.info(f"  - 别名: {result.alias_name}")

                # 内容信息
                logger.info(f"📄 内容信息:")
                logger.info(f"  - 原始内容长度: {len(result.original_content)}")
                logger.info(f"  - 切分内容长度: {len(result.div_content)}")
                logger.info(f"  - 原始内容预览: {result.original_content[:200]}...")

                # 元数据信息
                logger.info(f"🔍 元数据信息:")
                if result.metadata:
                    logger.info(f"  - 元数据字段数量: {len(result.metadata)}")
                    logger.info(f"  - 元数据字段列表:")
                    for key, value in result.metadata.items():
                        # 限制长值的显示
                        if isinstance(value, str) and len(value) > 100:
                            display_value = value[:100] + "..."
                        else:
                            display_value = value
                        logger.info(f"    * {key}: {display_value}")

                    # 特别检查domainId和fileFrom字段
                    logger.info(f"🔎 特殊字段检查:")
                    if 'domainId' in result.metadata:
                        logger.info(
                            f"  ✅ 找到 domainId: {result.metadata['domainId']}")
                    else:
                        logger.info(f"  ❌ 未找到 domainId")

                    if 'fileFrom' in result.metadata:
                        logger.info(
                            f"  ✅ 找到 fileFrom: {result.metadata['fileFrom']}")
                    else:
                        logger.info(f"  ❌ 未找到 fileFrom")

                    # 检查所有可能的字段名变体
                    domain_id_variants = [
                        'domainId', 'domain_id', 'domain', 'domainId',
                        'DomainId'
                    ]
                    file_from_variants = [
                        'fileFrom', 'file_from', 'fileFrom', 'FileFrom',
                        'source_type'
                    ]

                    for variant in domain_id_variants:
                        if variant in result.metadata:
                            logger.info(
                                f"  ✅ 找到 domainId 变体 '{variant}': {result.metadata[variant]}"
                            )

                    for variant in file_from_variants:
                        if variant in result.metadata:
                            logger.info(
                                f"  ✅ 找到 fileFrom 变体 '{variant}': {result.metadata[variant]}"
                            )
                else:
                    logger.info(f"  - 无元数据")

                logger.info(f"{'='*60}")

            # 7. 总结分析
            logger.info(f"\n📊 字段分析总结:")
            if es_results:
                # 收集所有元数据字段
                all_metadata_fields = set()
                for result in es_results:
                    if result.metadata:
                        all_metadata_fields.update(result.metadata.keys())

                logger.info(f"  - 发现的总元数据字段数: {len(all_metadata_fields)}")
                logger.info(
                    f"  - 所有元数据字段: {sorted(list(all_metadata_fields))}")

                # 检查是否有类似domainId和fileFrom的字段
                domain_related_fields = [
                    f for f in all_metadata_fields if 'domain' in f.lower()
                ]
                file_related_fields = [
                    f for f in all_metadata_fields
                    if 'file' in f.lower() or 'from' in f.lower()
                ]

                if domain_related_fields:
                    logger.info(f"  - 可能的domain相关字段: {domain_related_fields}")
                else:
                    logger.info(f"  - 未发现domain相关字段")

                if file_related_fields:
                    logger.info(f"  - 可能的file相关字段: {file_related_fields}")
                else:
                    logger.info(f"  - 未发现file相关字段")
            else:
                logger.warning("  - 没有搜索结果，无法分析字段")

        except Exception as e:
            logger.error(f"❌ ES搜索失败: {str(e)}")
            return False

        logger.info("🎉 ES搜索原始返回结果分析完成！")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧪 ES搜索原始返回结果分析")
    logger.info("=" * 60)

    success = await test_es_raw_response()

    if success:
        logger.info("✅ 分析完成！")
    else:
        logger.error("❌ 分析失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
