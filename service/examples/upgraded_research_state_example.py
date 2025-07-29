#!/usr/bin/env python3
"""
升级后的 ResearchState 使用示例
"""

import sys
from pathlib import Path

# 添加项目路径
current_file = Path(__file__)
service_dir = current_file.parent.parent
src_dir = service_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))


def demonstrate_upgraded_research_state():
    """演示升级后的 ResearchState 使用"""
    from src.doc_agent.schemas import Source

    print("🔬 升级后的 ResearchState 使用示例")
    print("=" * 60)

    # 1. 创建初始源
    print("\n1. 创建初始研究源:")
    initial_sources = [
        Source(id=1,
               source_type="webpage",
               title="水电站技术发展概述",
               url="https://www.example.com/overview",
               content="水电站技术发展经历了多个阶段，从传统的水轮机到现代的智能控制系统..."),
        Source(id=2,
               source_type="document",
               title="水电站设计规范 GB 50287-2016",
               content="本标准规定了水电站设计的基本要求，包括选址、结构设计、设备选型等方面...")
    ]

    for source in initial_sources:
        print(f"  [{source.id}] {source.title} ({source.source_type})")

    # 2. 创建章节级收集的源
    print("\n2. 创建章节级收集的源:")
    gathered_sources = [
        Source(id=3,
               source_type="webpage",
               title="水电站运行维护技术",
               url="https://www.example.com/maintenance",
               content="水电站运行维护是确保设备安全稳定运行的关键，包括日常检查、定期维护等..."),
        Source(id=4,
               source_type="es_result",
               title="水电站安全操作规程",
               url="https://internal.example.com/safety",
               content="为确保水电站安全运行，必须严格遵守安全操作规程，包括人员培训、设备检查等...")
    ]

    for source in gathered_sources:
        print(f"  [{source.id}] {source.title} ({source.source_type})")

    # 3. 创建引用源字典
    print("\n3. 创建引用源字典:")
    cited_sources = {}

    # 添加初始源
    for source in initial_sources:
        cited_sources[source.id] = source

    # 添加收集的源
    for source in gathered_sources:
        cited_sources[source.id] = source

    print(f"  引用源总数: {len(cited_sources)}")
    for source_id, source in cited_sources.items():
        print(f"    {source_id}: {source.title}")

    # 4. 模拟 ResearchState
    print("\n4. 模拟 ResearchState 结构:")
    research_state = {
        "topic":
        "水电站技术发展",
        "initial_sources":
        initial_sources,
        "document_outline": {
            "title":
            "水电站技术发展报告",
            "chapters": [{
                "title": "技术发展历程",
                "description": "概述水电站技术发展历史"
            }, {
                "title": "现状分析",
                "description": "分析当前水电站技术现状"
            }, {
                "title": "未来展望",
                "description": "展望水电站技术发展趋势"
            }]
        },
        "chapters_to_process": [{
            "chapter_title": "技术发展历程",
            "description": "概述水电站技术发展历史"
        }, {
            "chapter_title": "现状分析",
            "description": "分析当前水电站技术现状"
        }, {
            "chapter_title": "未来展望",
            "description": "展望水电站技术发展趋势"
        }],
        "current_chapter_index":
        0,
        "completed_chapters_content": [],
        "final_document":
        "",
        "research_plan":
        "研究水电站技术发展历程、现状和未来趋势",
        "search_queries": ["水电站技术", "发展历程", "安全规程", "维护技术"],
        "gathered_sources":
        gathered_sources,
        "sources":
        gathered_sources,  # 当前章节的源
        "cited_sources":
        cited_sources,
        "messages": []
    }

    print(f"  研究主题: {research_state['topic']}")
    print(f"  章节数量: {len(research_state['chapters_to_process'])}")
    print(f"  当前章节索引: {research_state['current_chapter_index']}")
    print(f"  搜索查询: {', '.join(research_state['search_queries'])}")

    # 5. 演示源管理功能
    print("\n5. 演示源管理功能:")

    def add_source_to_cited_sources(source: Source,
                                    cited_sources: dict) -> dict:
        """添加源到引用源字典"""
        cited_sources[source.id] = source
        return cited_sources

    def get_bibliography(cited_sources: dict) -> str:
        """生成参考文献"""
        bibliography = "参考文献:\n"
        for source_id in sorted(cited_sources.keys()):
            source = cited_sources[source_id]
            if source.url:
                bibliography += f"[{source_id}] {source.title} - {source.url}\n"
            else:
                bibliography += f"[{source_id}] {source.title} ({source.source_type})\n"
        return bibliography

    # 添加新源
    new_source = Source(id=5,
                        source_type="webpage",
                        title="水电站智能化技术",
                        url="https://www.example.com/smart-tech",
                        content="随着人工智能技术的发展，水电站智能化成为重要趋势...")

    cited_sources = add_source_to_cited_sources(new_source, cited_sources)
    print(f"  添加新源后，引用源总数: {len(cited_sources)}")

    # 生成参考文献
    bibliography = get_bibliography(cited_sources)
    print(f"\n  生成的参考文献:\n{bibliography}")

    print("\n✅ 升级后的 ResearchState 示例完成！")


def demonstrate_source_tracking():
    """演示源追踪功能"""
    from src.doc_agent.schemas import Source

    print("\n📊 源追踪功能演示")
    print("=" * 50)

    # 模拟研究过程中的源追踪
    research_sources = []
    cited_sources = {}

    # 模拟初始研究
    print("阶段1: 初始研究")
    initial_sources = [
        Source(id=1,
               source_type="webpage",
               title="概述",
               url="https://example.com/1",
               content="概述内容"),
        Source(id=2, source_type="document", title="规范", content="规范内容")
    ]

    for source in initial_sources:
        research_sources.append(source)
        cited_sources[source.id] = source

    print(f"  收集源: {len(research_sources)}")
    print(f"  引用源: {len(cited_sources)}")

    # 模拟章节研究
    print("\n阶段2: 章节研究")
    chapter_sources = [
        Source(id=3,
               source_type="webpage",
               title="技术细节",
               url="https://example.com/3",
               content="技术细节"),
        Source(id=4,
               source_type="es_result",
               title="案例分析",
               url="https://example.com/4",
               content="案例分析")
    ]

    for source in chapter_sources:
        research_sources.append(source)
        cited_sources[source.id] = source

    print(f"  收集源: {len(research_sources)}")
    print(f"  引用源: {len(cited_sources)}")

    # 模拟最终汇总
    print("\n阶段3: 最终汇总")
    print(f"  总收集源: {len(research_sources)}")
    print(f"  总引用源: {len(cited_sources)}")

    print("\n源类型统计:")
    source_types = {}
    for source in research_sources:
        if source.source_type not in source_types:
            source_types[source.source_type] = 0
        source_types[source.source_type] += 1

    for source_type, count in source_types.items():
        print(f"  {source_type}: {count} 个")

    print("\n✅ 源追踪功能演示完成！")


def main():
    """主函数"""
    print("🚀 升级后的 ResearchState 演示")
    print("=" * 70)

    # 演示升级后的 ResearchState
    demonstrate_upgraded_research_state()

    # 演示源追踪功能
    demonstrate_source_tracking()

    print("\n🎉 所有演示完成！")


if __name__ == "__main__":
    main()
