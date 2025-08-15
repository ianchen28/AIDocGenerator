#!/usr/bin/env python3
"""
测试 Source 类的 model_validator 是否会被意外触发
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.schemas import Source


def test_model_validator():
    """测试 model_validator 的行为"""
    print("🔍 测试 Source 类的 model_validator")
    print("=" * 50)
    
    # 测试1: 创建 Source 时传递 metadata
    print("1️⃣ 测试1: 创建 Source 时传递 metadata")
    source1 = Source(
        id=1,
        doc_id="doc1",
        doc_from="self",
        domain_id="documentUploadAnswer",
        index="personal_knowledge_base",
        source_type="es_result",
        title="测试文档",
        content="测试内容",
        metadata={
            "file_name": "测试文档.pdf",
            "source": "self"
        }
    )
    print(f"   ✅ Source 创建完成")
    print(f"   📄 metadata.source: {source1.metadata.get('source')}")
    
    # 测试2: 创建 Source 时不传递 metadata
    print("\n2️⃣ 测试2: 创建 Source 时不传递 metadata")
    source2 = Source(
        id=2,
        doc_id="doc2",
        doc_from="data_platform",
        domain_id="standard",
        index="standard_index_prod",
        source_type="es_result",
        title="测试文档2",
        content="测试内容2"
    )
    print(f"   ✅ Source 创建完成")
    print(f"   📄 metadata.source: {source2.metadata.get('source')}")
    
    # 测试3: 创建 Source 时传递空的 metadata
    print("\n3️⃣ 测试3: 创建 Source 时传递空的 metadata")
    source3 = Source(
        id=3,
        doc_id="doc3",
        doc_from="self",
        domain_id="documentUploadAnswer",
        index="personal_knowledge_base",
        source_type="es_result",
        title="测试文档3",
        content="测试内容3",
        metadata={}
    )
    print(f"   ✅ Source 创建完成")
    print(f"   📄 metadata.source: {source3.metadata.get('source')}")
    
    # 测试4: 创建 Source 时传递 None 的 metadata
    print("\n4️⃣ 测试4: 创建 Source 时传递 None 的 metadata")
    try:
        source4 = Source(
            id=4,
            doc_id="doc4",
            doc_from="self",
            domain_id="documentUploadAnswer",
            index="personal_knowledge_base",
            source_type="es_result",
            title="测试文档4",
            content="测试内容4",
            metadata=None
        )
        print(f"   ✅ Source 创建完成")
        print(f"   📄 metadata.source: {source4.metadata.get('source')}")
    except Exception as e:
        print(f"   ❌ Source 创建失败: {e}")
    
    # 测试5: 测试 model_dump 是否会影响 metadata
    print("\n5️⃣ 测试5: 测试 model_dump 是否会影响 metadata")
    source_dict = source1.model_dump()
    print(f"   📄 model_dump 后的 metadata.source: {source_dict.get('metadata', {}).get('source')}")
    
    # 测试6: 测试 model_dump(by_alias=True) 是否会影响 metadata
    print("\n6️⃣ 测试6: 测试 model_dump(by_alias=True) 是否会影响 metadata")
    source_dict_alias = source1.model_dump(by_alias=True)
    print(f"   📄 model_dump(by_alias=True) 后的 metadata.source: {source_dict_alias.get('metadata', {}).get('source')}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")


if __name__ == "__main__":
    test_model_validator()
