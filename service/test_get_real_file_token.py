#!/usr/bin/env python3
"""
获取真实存在的 file_token 进行测试
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.tools.es_service import ESService


async def get_real_file_token():
    """获取一个真实存在的 file_token"""
    logger.info("开始获取真实存在的 file_token")
    
    # 从配置文件获取ES配置
    es_config = settings.elasticsearch_config
    es_hosts = es_config.hosts
    es_username = es_config.username
    es_password = es_config.password
    
    # 创建ES服务实例
    es_service = ESService(
        hosts=es_hosts,
        username=es_username,
        password=es_password
    )
    
    try:
        # 连接ES
        await es_service.connect()
        
        # 获取有效索引列表
        valid_indices = es_service.get_valid_indices()
        logger.info(f"有效索引列表: {valid_indices}")
        
        # 在 personal_knowledge_base 中搜索一些文档
        logger.info("在 personal_knowledge_base 中搜索文档...")
        results = await es_service.search(
            index="personal_knowledge_base",
            query="人工智能",
            top_k=5
        )
        
        if results:
            logger.info(f"找到 {len(results)} 个文档")
            for i, result in enumerate(results):
                logger.info(f"文档 {i+1}:")
                logger.info(f"  - ID: {result.id}")
                logger.info(f"  - doc_id: {result.doc_id}")
                logger.info(f"  - file_token: {result.file_token}")
                logger.info(f"  - 来源: {result.source}")
                logger.info(f"  - 分数: {result.score}")
                logger.info(f"  - 内容预览: {result.original_content[:100]}...")
                logger.info("---")
        else:
            logger.warning("没有找到任何文档")
            
        # 在 thesis_index_base 中搜索一些文档
        logger.info("在 thesis_index_base 中搜索文档...")
        results = await es_service.search(
            index="thesis_index_base",
            query="人工智能",
            top_k=5
        )
        
        if results:
            logger.info(f"找到 {len(results)} 个文档")
            for i, result in enumerate(results):
                logger.info(f"文档 {i+1}:")
                logger.info(f"  - ID: {result.id}")
                logger.info(f"  - doc_id: {result.doc_id}")
                logger.info(f"  - file_token: {result.file_token}")
                logger.info(f"  - 来源: {result.source}")
                logger.info(f"  - 分数: {result.score}")
                logger.info(f"  - 内容预览: {result.original_content[:100]}...")
                logger.info("---")
        else:
            logger.warning("没有找到任何文档")
    
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
    
    finally:
        # 关闭连接
        await es_service.close()
        logger.info("测试完成")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(get_real_file_token())
