#!/usr/bin/env python3
"""
测试 Source metadata 的正确性
验证 ES 搜索结果和 Web 搜索结果的 source 字段是否正确设置
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.graph.common.parsers import parse_es_search_results, parse_web_search_results
from doc_agent.tools.es_service import ESSearchResult


def test_es_search_results():
    """测试 ES 搜索结果的 metadata.source 设置"""
    print("🔍 测试 ES 搜索结果的 metadata.source 设置")
    print("=" * 50)

    # 模拟 ES 搜索结果
    es_results = [
        ESSearchResult(
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
                "source": "old_value"  # 这个应该被 doc_from 覆盖
            },
            alias_name="personal_knowledge_base"),
        ESSearchResult(
            id="2",
            doc_id="doc2",
            index="standard_index_prod",
            domain_id="standard",
            doc_from="data_platform",
            file_token="",
            original_content="这是标准库的文档内容",
            div_content="",
            source="",
            score=0.8,
            metadata={
                "file_name": "标准文档.pdf",
                "source": "another_old_value"  # 这个应该被 doc_from 覆盖
            },
            alias_name="standard_index_prod"),
        ESSearchResult(
            id="3",
            doc_id="doc3",
            index="personal_knowledge_base",
            domain_id="documentUploadAnswer",
            doc_from="self",
            file_token="",
            original_content="这是没有 source 字段的文档内容",
            div_content="",
            source="",
            score=0.7,
            metadata={
                "file_name": "无source文档.pdf"
                # 没有 source 字段，应该使用 doc_from
            },
            alias_name="personal_knowledge_base")
    ]

    # 解析 ES 搜索结果
    sources = parse_es_search_results(es_results, "测试查询", 1)

    print(f"解析了 {len(sources)} 个 ES 源:")
    for i, source in enumerate(sources, 1):
        print(f"\n{i}. {source.title}")
        print(f"   doc_from: {source.doc_from}")
        print(f"   metadata.source: {source.metadata.get('source', '未设置')}")

        # 验证逻辑：所有 ES 搜索结果都应该使用 doc_from 作为 source
        if source.metadata.get('source') == source.doc_from:
            print(f"   ✅ 正确：source 值与 doc_from 一致 ({source.doc_from})")
        else:
            print(
                f"   ❌ 错误：source 值 '{source.metadata.get('source')}' 与 doc_from '{source.doc_from}' 不一致"
            )


def test_web_search_results():
    """测试 Web 搜索结果的 metadata.source 设置"""
    print("\n🔍 测试 Web 搜索结果的 metadata.source 设置")
    print("=" * 50)

    # 模拟 Web 搜索结果
    web_results = [{
        "materialId": "doc_1",
        "materialTitle": "Web 文档 1",
        "materialContent": "这是第一个 Web 文档的内容",
        "url": "https://example1.com",
        "siteName": "Example Site 1",
        "datePublished": "2024-01-01",
        "author": "作者1"
    }, {
        "materialId": "doc_2",
        "materialTitle": "Web 文档 2",
        "materialContent": "这是第二个 Web 文档的内容",
        "url": "https://example2.com",
        "siteName": "Example Site 2",
        "datePublished": "2024-01-02",
        "author": "作者2"
    }]

    # 解析 Web 搜索结果
    sources = parse_web_search_results(web_results, "测试查询", 100)

    print(f"解析了 {len(sources)} 个 Web 源:")
    for i, source in enumerate(sources, 1):
        print(f"\n{i}. {source.title}")
        print(f"   doc_from: {source.doc_from}")
        print(f"   metadata.source: {source.metadata.get('source', '未设置')}")

        # 验证逻辑
        if source.metadata.get('source') == 'web_search':
            print("   ✅ 正确：Web 搜索结果，source 为 'web_search'")
        else:
            print(f"   ❌ 错误：意外的 source 值 '{source.metadata.get('source')}'")


def main():
    """主函数"""
    print("🚀 开始测试 Source metadata 的正确性")
    print("=" * 60)

    try:
        test_es_search_results()
        test_web_search_results()

        print("\n" + "=" * 60)
        print("🎉 测试完成！")
        print("\n📋 总结:")
        print("- ES 搜索结果统一使用 doc_from 作为 source 值")
        print("- 个人知识库文档：source = 'self'")
        print("- 标准库文档：source = 'data_platform'")
        print("- Web 搜索结果：source = 'web_search'")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
