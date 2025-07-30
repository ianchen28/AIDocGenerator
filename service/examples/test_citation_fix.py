#!/usr/bin/env python3
"""
测试引用编号修复功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.schemas import Source


def test_chapter_processing_logic():
    """测试章节处理中的引用编号逻辑"""
    print("🧪 测试章节处理中的引用编号逻辑...")

    # 模拟第一章的引用源
    chapter1_sources = [
        Source(id=1,
               source_type='webpage',
               title='人工智能基础',
               url='http://example.com/1',
               content='内容1'),
        Source(id=2,
               source_type='es_result',
               title='机器学习概述',
               url='',
               content='内容2')
    ]

    # 模拟第二章的引用源（注意：ID又从1开始，这是问题所在）
    chapter2_sources = [
        Source(id=1,
               source_type='webpage',
               title='深度学习应用',
               url='http://example.com/3',
               content='内容3'),
        Source(id=2,
               source_type='webpage',
               title='AI发展趋势',
               url='http://example.com/4',
               content='内容4')
    ]

    # 模拟章节内容（包含引用）
    chapter1_content = "## 第一章\n\n这是关于人工智能的介绍[1]，包括机器学习的概念[2]。"
    chapter2_content = "## 第二章\n\n这里讨论深度学习[1]和AI的未来发展[2]。"

    print(f"📝 第一章原始内容: {chapter1_content}")
    print(f"📝 第二章原始内容: {chapter2_content}")
    print(f"📚 第一章引用源: {[(s.id, s.title) for s in chapter1_sources]}")
    print(f"📚 第二章引用源: {[(s.id, s.title) for s in chapter2_sources]}")

    # 模拟全局引用源处理逻辑
    global_cited_sources = {}
    max_global_id = 0
    all_chapters_content = []

    # 处理第一章
    print("\n🔄 处理第一章...")
    chapter_to_global_id_map = {}

    for source in chapter1_sources:
        # 检查是否已存在相同内容的源
        existing_global_id = None
        for global_id, existing_source in global_cited_sources.items():
            if (existing_source.title == source.title
                    and existing_source.url == source.url):
                existing_global_id = global_id
                break

        if existing_global_id:
            chapter_to_global_id_map[source.id] = existing_global_id
            print(
                f"  📚 复用已存在的引用源: 章节ID[{source.id}] -> 全局ID[{existing_global_id}] {source.title}"
            )
        else:
            max_global_id += 1
            new_source = source.model_copy()
            new_source.id = max_global_id
            global_cited_sources[max_global_id] = new_source
            chapter_to_global_id_map[source.id] = max_global_id
            print(
                f"  📚 添加新引用源到全局: 章节ID[{source.id}] -> 全局ID[{max_global_id}] {source.title}"
            )

    # 更新第一章内容中的引用编号
    updated_chapter1_content = chapter1_content
    for chapter_id, global_id in chapter_to_global_id_map.items():
        updated_chapter1_content = updated_chapter1_content.replace(
            f"[{chapter_id}]", f"[{global_id}]")

    all_chapters_content.append(updated_chapter1_content)
    print(f"  ✅ 第一章更新后内容: {updated_chapter1_content}")

    # 处理第二章
    print("\n🔄 处理第二章...")
    chapter_to_global_id_map = {}

    for source in chapter2_sources:
        # 检查是否已存在相同内容的源
        existing_global_id = None
        for global_id, existing_source in global_cited_sources.items():
            if (existing_source.title == source.title
                    and existing_source.url == source.url):
                existing_global_id = global_id
                break

        if existing_global_id:
            chapter_to_global_id_map[source.id] = existing_global_id
            print(
                f"  📚 复用已存在的引用源: 章节ID[{source.id}] -> 全局ID[{existing_global_id}] {source.title}"
            )
        else:
            max_global_id += 1
            new_source = source.model_copy()
            new_source.id = max_global_id
            global_cited_sources[max_global_id] = new_source
            chapter_to_global_id_map[source.id] = max_global_id
            print(
                f"  📚 添加新引用源到全局: 章节ID[{source.id}] -> 全局ID[{max_global_id}] {source.title}"
            )

    # 更新第二章内容中的引用编号
    updated_chapter2_content = chapter2_content
    for chapter_id, global_id in chapter_to_global_id_map.items():
        updated_chapter2_content = updated_chapter2_content.replace(
            f"[{chapter_id}]", f"[{global_id}]")

    all_chapters_content.append(updated_chapter2_content)
    print(f"  ✅ 第二章更新后内容: {updated_chapter2_content}")

    # 生成最终文档
    print("\n📄 生成最终文档...")
    final_document = "\n\n".join(all_chapters_content)

    # 生成参考文献
    bibliography_section = "\n\n## 参考文献\n\n"
    sorted_sources = sorted(global_cited_sources.items(), key=lambda x: x[0])

    for global_number, (source_id, source) in enumerate(sorted_sources, 1):
        reference_entry = f"[{global_number}] {source.title}"
        if source.url and source.url.strip():
            reference_entry += f" ({source.url})"
        if source.source_type:
            reference_entry += f" [{source.source_type}]"
        bibliography_section += reference_entry + "\n"

    final_document_with_bibliography = final_document + bibliography_section

    print("📄 最终文档:")
    print("=" * 60)
    print(final_document_with_bibliography)
    print("=" * 60)

    print(f"\n📊 统计信息:")
    print(f"  🔢 全局引用源总数: {len(global_cited_sources)}")
    print(f"  📝 章节数量: {len(all_chapters_content)}")
    print(f"  📏 最终文档长度: {len(final_document_with_bibliography)} 字符")

    # 验证引用编号是否连续
    print(f"\n✅ 验证结果:")
    expected_ids = list(range(1, len(global_cited_sources) + 1))
    actual_ids = sorted(global_cited_sources.keys())
    if expected_ids == actual_ids:
        print(f"  ✅ 引用编号连续: {actual_ids}")
    else:
        print(f"  ❌ 引用编号不连续: 期望 {expected_ids}, 实际 {actual_ids}")

    # 检查每章节的引用编号是否正确
    for i, content in enumerate(all_chapters_content, 1):
        import re
        citations = re.findall(r'\[(\d+)\]', content)
        print(f"  📖 第{i}章引用编号: {citations}")


if __name__ == "__main__":
    test_chapter_processing_logic()
