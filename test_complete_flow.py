#!/usr/bin/env python3
"""
测试从 researcher 到 generation 的完整流程
特别关注 metadata.source 字段的传递
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.tools.es_service import ESSearchResult
from doc_agent.tools.reranker import RerankedSearchResult
from doc_agent.graph.common.parsers import parse_es_search_results
from doc_agent.schemas import Source


def test_complete_flow():
    """测试完整的数据流"""
    print("🔍 测试从 researcher 到 generation 的完整流程")
    print("=" * 60)
    
    # 1. 模拟 es_service.py 创建 ESSearchResult
    print("1️⃣ 模拟 es_service.py 创建 ESSearchResult")
    es_result = ESSearchResult(
        id="1",
        doc_id="doc1",
        index="personal_knowledge_base",
        domain_id="documentUploadAnswer",
        doc_from="self",
        file_token="",
        original_content="这是个人知识库的文档内容",
        div_content="",
        source="",
        score=0.9,
        metadata={
            "file_name": "个人文档.pdf",
            "source": "self"  # 这里正确设置了
        },
        alias_name="personal_knowledge_base"
    )
    print(f"   ✅ ESSearchResult 创建完成")
    print(f"   📄 metadata.source: {es_result.metadata.get('source')}")
    
    # 2. 模拟 reranker.py 创建 RerankedSearchResult
    print("\n2️⃣ 模拟 reranker.py 创建 RerankedSearchResult")
    reranked_result = RerankedSearchResult(
        id=es_result.id,
        doc_id=es_result.doc_id,
        index=es_result.index,
        domain_id=es_result.domain_id,
        doc_from=es_result.doc_from,
        original_content=es_result.original_content,
        div_content=es_result.div_content,
        source=es_result.source,
        score=es_result.score,
        rerank_score=es_result.score,
        metadata=es_result.metadata,
        alias_name=es_result.alias_name
    )
    print(f"   ✅ RerankedSearchResult 创建完成")
    print(f"   📄 doc_from: {reranked_result.doc_from}")
    print(f"   📄 metadata.source: {reranked_result.metadata.get('source')}")
    
    # 3. 模拟 parse_es_search_results 创建 Source
    print("\n3️⃣ 模拟 parse_es_search_results 创建 Source")
    sources = parse_es_search_results([reranked_result], "测试查询", 1)
    source = sources[0] if sources else None
    
    if source:
        print(f"   ✅ Source 创建完成")
        print(f"   📄 doc_from: {source.doc_from}")
        print(f"   📄 metadata.source: {source.metadata.get('source')}")
        
        # 4. 模拟 writer.py 中的引用标记
        print("\n4️⃣ 模拟 writer.py 中的引用标记")
        source.cited = True
        print(f"   ✅ 标记为已引用: {source.cited}")
        
        # 5. 模拟 generation.py 中的 batch_to_redis_fe
        print("\n5️⃣ 模拟 generation.py 中的 batch_to_redis_fe")
        answer_origins, webs = Source.batch_to_redis_fe([source])
        
        if answer_origins:
            origin = answer_origins[0]
            print(f"   ✅ answer_origins 转换完成")
            print(f"   📄 metadata: {origin.get('metadata')}")
            print(f"   📄 metadata.source: {origin.get('metadata', {}).get('source')}")
        else:
            print("   ❌ answer_origins 为空")
    else:
        print("   ❌ Source 创建失败")
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")


if __name__ == "__main__":
    test_complete_flow()
