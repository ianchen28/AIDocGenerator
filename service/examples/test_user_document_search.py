#!/usr/bin/env python3
"""
测试用户文档范围搜索功能
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from doc_agent.core.config import settings
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.reranker import RerankerTool
from doc_agent.llm_clients.providers import EmbeddingClient
from doc_agent.core.logging_config import get_logger

logger = get_logger(__name__)


async def test_user_document_search():
    """测试用户文档范围搜索功能"""
    logger.info("🚀 开始测试用户文档范围搜索功能")

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

        # 2. 初始化重排序工具
        logger.info("🔄 初始化重排序工具...")
        reranker_config = settings.supported_models.get("reranker")
        if reranker_config:
            reranker_tool = RerankerTool(base_url=reranker_config.url,
                                         api_key=reranker_config.api_key)
            logger.info("✅ 重排序工具初始化成功")
        else:
            reranker_tool = None
            logger.warning("⚠️ 未找到重排序配置，将跳过重排序")

        # 3. 初始化Embedding客户端
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

        # 4. 测试参数
        test_query = "人工智能的发展趋势"
        test_file_tokens = ["test_doc_001", "test_doc_002"]  # 模拟用户上传的文档token

        logger.info(f"🔍 测试查询: {test_query}")
        logger.info(f"📄 测试文档tokens: {test_file_tokens}")

        # 5. 生成查询向量
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

        # 6. 执行用户文档范围搜索
        logger.info("🔍 执行用户文档范围搜索...")
        try:
            user_es_results = await es_search_tool.search_within_documents(
                query=test_query,
                query_vector=query_vector,
                file_tokens=test_file_tokens,
                top_k=10,
                config={'min_score': 0.3})

            logger.info(f"✅ 用户文档范围搜索完成，结果数量: {len(user_es_results)}")

            # 显示搜索结果
            for i, result in enumerate(user_es_results[:3], 1):  # 只显示前3个结果
                logger.info(f"结果 {i}:")
                logger.info(f"  - 文档ID: {result.doc_id}")
                logger.info(f"  - 文件Token: {result.file_token}")
                logger.info(f"  - 来源: {result.source}")
                logger.info(f"  - 分数: {result.score}")
                logger.info(f"  - 内容预览: {result.original_content[:100]}...")
                logger.info("")

        except Exception as e:
            logger.error(f"❌ 用户文档范围搜索失败: {str(e)}")
            return False

        # 7. 测试重排序功能
        if reranker_tool and user_es_results:
            logger.info("🔄 测试重排序功能...")
            try:
                # 转换为重排序工具需要的格式
                user_search_results = []
                for result in user_es_results:
                    user_search_results.append({
                        'content':
                        result.original_content or result.div_content,
                        'score':
                        result.score,
                        'metadata': {
                            'source': result.source,
                            'doc_id': result.doc_id,
                            'file_token': result.file_token,
                            'alias_name': result.alias_name
                        }
                    })

                # 执行重排序
                reranked_results = await reranker_tool.rerank(
                    query=test_query, documents=user_search_results, top_k=5)

                logger.info(f"✅ 重排序完成，结果数量: {len(reranked_results)}")

                # 显示重排序结果
                for i, result in enumerate(reranked_results[:3], 1):
                    logger.info(f"重排序结果 {i}:")
                    logger.info(f"  - 分数: {result['score']}")
                    logger.info(f"  - 内容预览: {result['content'][:100]}...")
                    logger.info("")

            except Exception as e:
                logger.error(f"❌ 重排序失败: {str(e)}")

        logger.info("🎉 用户文档范围搜索功能测试完成！")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("🧪 用户文档范围搜索功能测试")
    logger.info("=" * 50)

    success = await test_user_document_search()

    if success:
        logger.info("✅ 所有测试通过！")
    else:
        logger.error("❌ 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
