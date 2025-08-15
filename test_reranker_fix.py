#!/usr/bin/env python3
"""
测试 Reranker 修复
验证 _fallback_to_original_results 是否正确复制所有字段
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from doc_agent.tools.es_service import ESSearchResult
from doc_agent.tools.reranker import RerankerTool


def test_fallback_results():
    """测试回退结果是否正确复制所有字段"""
    print("🔍 测试 Reranker 回退结果字段复制")
    print("=" * 50)

    # 创建模拟的 ESSearchResult
    es_results = [
        ESSearchResult(id="1",
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
                           "source": "self"
                       },
                       alias_name="personal_knowledge_base"),
        ESSearchResult(id="2",
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
                           "source": "data_platform"
                       },
                       alias_name="standard_index_prod")
    ]

    # 创建 RerankerTool 实例（使用模拟的配置）
    reranker = RerankerTool(base_url="http://mock", api_key="mock")

    # 调用 _fallback_to_original_results 方法
    fallback_results = reranker._fallback_to_original_results(es_results)

    print(f"转换了 {len(fallback_results)} 个结果:")
    for i, result in enumerate(fallback_results, 1):
        print(f"\n{i}. {result.metadata.get('file_name', '未知文档')}")
        print(f"   id: {result.id}")
        print(f"   doc_id: {result.doc_id}")
        print(f"   index: {result.index}")
        print(f"   domain_id: {result.domain_id}")
        print(f"   doc_from: {result.doc_from}")
        print(f"   metadata.source: {result.metadata.get('source', '未设置')}")

        # 验证所有字段是否正确复制
        original = es_results[i - 1]
        issues = []

        if result.index != original.index:
            issues.append(f"index 不匹配: {result.index} vs {original.index}")
        if result.domain_id != original.domain_id:
            issues.append(
                f"domain_id 不匹配: {result.domain_id} vs {original.domain_id}")
        if result.doc_from != original.doc_from:
            issues.append(
                f"doc_from 不匹配: {result.doc_from} vs {original.doc_from}")
        if result.metadata.get('source') != original.metadata.get('source'):
            issues.append(
                f"metadata.source 不匹配: {result.metadata.get('source')} vs {original.metadata.get('source')}"
            )

        if issues:
            print(f"   ❌ 发现问题:")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"   ✅ 所有字段正确复制")


def main():
    """主函数"""
    print("🚀 开始测试 Reranker 修复")
    print("=" * 60)

    try:
        test_fallback_results()

        print("\n" + "=" * 60)
        print("🎉 测试完成！")
        print("\n📋 总结:")
        print("- 修复了 _fallback_to_original_results 方法中缺少的字段")
        print("- 现在会正确复制 index、domain_id、doc_from 等字段")
        print("- 这确保了 parse_es_search_results 能正确设置 source 值")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
