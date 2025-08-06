#!/usr/bin/env python3
"""
网络搜索服务使用示例
演示如何在AI文档生成系统中使用网络搜索功能
"""

import asyncio
import sys
from typing import List, Dict, Any

from loguru import logger

# 添加项目路径
sys.path.append("../src")

from doc_agent.tools.web_search import WebSearchTool


async def example_basic_search():
    """基本搜索示例"""
    logger.info("=== 基本搜索示例 ===")
    
    # 创建网络搜索工具实例
    web_search = WebSearchTool()
    
    # 执行搜索
    query = "水电站建造过程中可能出现的问题"
    logger.info(f"搜索查询: {query}")
    
    try:
        # 获取搜索结果
        docs = await web_search.get_web_docs(query)
        
        if docs:
            logger.info(f"找到 {len(docs)} 个相关文档")
            
            # 显示搜索结果
            for i, doc in enumerate(docs[:3]):  # 只显示前3个
                logger.info(f"\n文档 {i+1}:")
                logger.info(f"  标题: {doc.get('meta_data', {}).get('docName', 'Unknown')}")
                logger.info(f"  URL: {doc.get('url', 'N/A')}")
                logger.info(f"  内容长度: {len(doc.get('text', ''))} 字符")
                
                # 显示内容摘要
                content = doc.get('text', '')
                summary = content[:300] + "..." if len(content) > 300 else content
                logger.info(f"  内容摘要: {summary}")
        else:
            logger.warning("未找到相关文档")
            
    except Exception as e:
        logger.error(f"搜索失败: {e}")


async def example_async_search():
    """异步搜索示例"""
    logger.info("=== 异步搜索示例 ===")
    
    web_search = WebSearchTool()
    
    # 多个查询
    queries = [
        "水电站施工安全",
        "水利工程质量控制",
        "水轮机维护保养"
    ]
    
    for query in queries:
        logger.info(f"\n搜索: {query}")
        try:
            result = await web_search.search_async(query)
            logger.info(f"搜索结果: {len(result)} 个文档")
        except Exception as e:
            logger.error(f"搜索失败: {e}")


async def example_integration_with_doc_generation():
    """与文档生成系统集成的示例"""
    logger.info("=== 文档生成集成示例 ===")
    
    web_search = WebSearchTool()
    
    # 模拟文档生成流程
    topic = "水电站建造过程中可能出现的问题与解决方案"
    
    logger.info(f"开始生成文档: {topic}")
    
    # 1. 收集相关信息
    logger.info("1. 收集相关信息...")
    search_queries = [
        "水电站建造问题",
        "水利工程施工难点",
        "水电站质量控制",
        "水电站安全施工"
    ]
    
    all_docs = []
    for query in search_queries:
        try:
            docs = await web_search.get_web_docs(query)
            all_docs.extend(docs)
            logger.info(f"  从 '{query}' 收集到 {len(docs)} 个文档")
        except Exception as e:
            logger.error(f"  搜索 '{query}' 失败: {e}")
    
    # 2. 分析收集到的信息
    logger.info(f"2. 分析收集到的信息...")
    logger.info(f"   总共收集到 {len(all_docs)} 个文档")
    
    # 3. 提取关键信息
    logger.info("3. 提取关键信息...")
    key_topics = set()
    for doc in all_docs:
        content = doc.get('text', '')
        # 简单的关键词提取（实际应用中可以使用更复杂的NLP技术）
        if '问题' in content or '困难' in content or '风险' in content:
            key_topics.add('施工问题')
        if '安全' in content or '防护' in content:
            key_topics.add('安全措施')
        if '质量' in content or '标准' in content:
            key_topics.add('质量控制')
    
    logger.info(f"   识别到关键主题: {list(key_topics)}")
    
    # 4. 生成文档大纲
    logger.info("4. 生成文档大纲...")
    outline = [
        "水电站建造过程中可能出现的问题与解决方案",
        "  1. 施工准备阶段的问题",
        "  2. 施工过程中的技术难点",
        "  3. 质量控制与安全管理",
        "  4. 常见问题的解决方案"
    ]
    
    for item in outline:
        logger.info(f"   {item}")
    
    logger.info("文档生成流程完成！")


async def main():
    """主函数"""
    logger.info("🚀 网络搜索服务使用示例")
    logger.info("=" * 60)
    
    # 设置日志
    logger.add("logs/web_search_example.log", 
              rotation="1 day", 
              retention="7 days",
              level="INFO")
    
    try:
        # 运行示例
        await example_basic_search()
        await example_async_search()
        await example_integration_with_doc_generation()
        
        logger.info("\n✅ 所有示例运行完成！")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 