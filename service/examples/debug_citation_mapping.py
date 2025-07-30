#!/usr/bin/env python3
"""
调试引用编号映射问题
"""
import re

def debug_citation_mapping():
    """调试引用编号映射"""
    
    # 模拟第1章的内容（包含引用）
    chapter1_content = """## 人工智能概述

人工智能是指由人类设计和构建的系统[2]。
这类模型在语言理解等任务中展现出表现[2]。
生成式人工智能作为重要分支[2]。
自然语言处理致力于理解与生成[2]。
上述技术呈现出高度融合的趋势[2]。
当前人工智能已进入新阶段[2]。
"""

    # 模拟第2章的内容（包含引用）  
    chapter2_content = """## 人工智能发展简史

达特茅斯会议设定了宏伟目标[2]。
这一成就验证了会议理念[2]。
美国政府大幅削减相关资助[2]。
"""

    print("🔍 调试引用编号映射问题")
    print("=" * 50)
    
    print(f"📝 第1章原始内容:")
    print(chapter1_content)
    print(f"📝 第2章原始内容:")
    print(chapter2_content)
    
    # 模拟全局ID映射
    global_cited_sources = {}
    max_global_id = 0
    all_chapters_content = []
    
    # 处理第1章
    print("\n🔄 处理第1章...")
    chapter1_citations = re.findall(r'\[(\d+)\]', chapter1_content)
    print(f"  📊 发现引用: {chapter1_citations}")
    
    # 模拟6个引用源（因为日志显示第1章引用了6个源）
    chapter1_sources = [
        {"id": 2, "title": f"源{i}", "content": f"内容{i}"} 
        for i in range(1, 7)  # 模拟6个源，但都用相同的章节ID=2
    ]
    
    chapter_to_global_id_map = {}
    for source in chapter1_sources:
        max_global_id += 1
        chapter_to_global_id_map[source["id"]] = max_global_id
        global_cited_sources[max_global_id] = source
        print(f"  📚 映射: 章节ID[{source['id']}] -> 全局ID[{max_global_id}]")
    
    # 更新第1章内容
    updated_chapter1_content = chapter1_content
    for chapter_id, global_id in chapter_to_global_id_map.items():
        updated_chapter1_content = updated_chapter1_content.replace(
            f"[{chapter_id}]", f"[{global_id}]")
    
    print(f"  ✅ 第1章更新后内容预览:")
    print(updated_chapter1_content[:200] + "...")
    all_chapters_content.append(updated_chapter1_content)
    
    # 处理第2章
    print("\n🔄 处理第2章...")
    chapter2_citations = re.findall(r'\[(\d+)\]', chapter2_content)
    print(f"  📊 发现引用: {chapter2_citations}")
    
    # 模拟3个引用源（因为日志显示第2章引用了3个源）
    chapter2_sources = [
        {"id": 2, "title": f"源{i}", "content": f"内容{i}"} 
        for i in range(7, 10)  # 模拟3个源，但都用相同的章节ID=2
    ]
    
    chapter_to_global_id_map = {}
    for source in chapter2_sources:
        max_global_id += 1
        chapter_to_global_id_map[source["id"]] = max_global_id
        global_cited_sources[max_global_id] = source
        print(f"  📚 映射: 章节ID[{source['id']}] -> 全局ID[{max_global_id}]")
    
    # 更新第2章内容
    updated_chapter2_content = chapter2_content
    for chapter_id, global_id in chapter_to_global_id_map.items():
        updated_chapter2_content = updated_chapter2_content.replace(
            f"[{chapter_id}]", f"[{global_id}]")
    
    print(f"  ✅ 第2章更新后内容预览:")
    print(updated_chapter2_content[:200] + "...")
    all_chapters_content.append(updated_chapter2_content)
    
    # 生成最终文档
    print("\n📄 最终文档分析:")
    final_content = "\n\n".join(all_chapters_content)
    
    # 统计最终文档中的引用
    final_citations = re.findall(r'\[(\d+)\]', final_content)
    unique_citations = sorted(set(int(c) for c in final_citations))
    
    print(f"  📊 最终文档中的引用编号: {unique_citations}")
    print(f"  📚 全局引用源数量: {len(global_cited_sources)}")
    print(f"  🔢 引用源编号范围: [1-{max_global_id}]")
    
    if len(unique_citations) < len(global_cited_sources):
        print(f"  ⚠️  问题发现: 文档中只有 {len(unique_citations)} 个引用，但有 {len(global_cited_sources)} 个引用源")
        missing_citations = set(range(1, len(global_cited_sources) + 1)) - set(unique_citations)
        print(f"  ❌ 缺失的引用编号: {sorted(missing_citations)}")

if __name__ == "__main__":
    debug_citation_mapping() 