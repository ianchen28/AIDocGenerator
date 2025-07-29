#!/usr/bin/env python3
"""
Source 模型使用示例
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


def demonstrate_source_usage():
    """演示 Source 模型的使用"""
    from src.doc_agent.schemas import Source

    print("🔍 Source 模型使用示例")
    print("=" * 50)

    # 1. 创建不同类型的源
    print("\n1. 创建不同类型的源:")

    # 网页源
    webpage_source = Source(
        id=1,
        source_type="webpage",
        title="水电站技术发展现状",
        url="https://www.example.com/hydropower-tech",
        content="水电站技术在过去几十年中取得了显著进展，包括涡轮机效率提升、自动化控制系统改进等...")

    # 文档源
    document_source = Source(id=2,
                             source_type="document",
                             title="水电站设计规范 GB 50287-2016",
                             content="本标准规定了水电站设计的基本要求，包括选址、结构设计、设备选型等方面...")

    # ES 搜索结果源
    es_source = Source(id=3,
                       source_type="es_result",
                       title="水电站运行维护手册",
                       url="https://internal.example.com/manual",
                       content="水电站运行维护手册详细说明了日常维护流程、故障处理方法和安全操作规程...")

    sources = [webpage_source, document_source, es_source]

    # 2. 显示源信息
    print("\n2. 源信息展示:")
    for source in sources:
        print(f"\n  源 #{source.id}: {source.title}")
        print(f"    类型: {source.source_type}")
        print(f"    URL: {source.url or '无'}")
        print(f"    内容长度: {len(source.content)} 字符")
        print(f"    内容预览: {source.content[:50]}...")

    # 3. 按类型分组
    print("\n3. 按类型分组:")
    source_types = {}
    for source in sources:
        if source.source_type not in source_types:
            source_types[source.source_type] = []
        source_types[source.source_type].append(source)

    for source_type, type_sources in source_types.items():
        print(f"\n  {source_type.upper()} 类型 ({len(type_sources)} 个):")
        for source in type_sources:
            print(f"    - {source.id}: {source.title}")

    # 4. 生成引用格式
    print("\n4. 引用格式:")
    for source in sources:
        if source.url:
            print(f"  [{source.id}] {source.title} - {source.url}")
        else:
            print(f"  [{source.id}] {source.title} ({source.source_type})")

    # 5. JSON 序列化示例
    print("\n5. JSON 序列化示例:")
    for source in sources:
        json_data = source.model_dump()
        print(f"  源 #{source.id} JSON:")
        print(f"    {json_data}")

    print("\n✅ Source 模型使用示例完成！")


def demonstrate_research_state_integration():
    """演示 ResearchState 中的 sources 集成"""
    from src.doc_agent.schemas import Source

    print("\n🔬 ResearchState 集成示例")
    print("=" * 50)

    # 模拟研究状态中的源
    research_sources = [
        Source(id=1,
               source_type="webpage",
               title="水电站技术发展趋势",
               url="https://www.example.com/trends",
               content="近年来，水电站技术呈现出数字化、智能化的发展趋势..."),
        Source(id=2,
               source_type="document",
               title="水电站安全操作规程",
               content="为确保水电站安全运行，必须严格遵守以下操作规程..."),
        Source(id=3,
               source_type="es_result",
               title="水电站环境影响评估报告",
               url="https://internal.example.com/eia-report",
               content="本报告详细分析了水电站建设对周边环境的影响...")
    ]

    # 模拟研究状态
    research_state = {
        "topic": "水电站技术发展",
        "sources": research_sources,
        "gathered_data": "基于收集的多个信息源，水电站技术发展呈现以下特点...",
        "search_queries": ["水电站技术", "发展趋势", "安全规程"]
    }

    print(f"研究主题: {research_state['topic']}")
    print(f"搜索查询: {', '.join(research_state['search_queries'])}")
    print(f"收集的源数量: {len(research_state['sources'])}")
    print(f"收集的数据: {research_state['gathered_data'][:50]}...")

    print("\n源追踪信息:")
    for source in research_state['sources']:
        print(f"  [{source.id}] {source.title} ({source.source_type})")
        if source.url:
            print(f"      URL: {source.url}")

    print("\n✅ ResearchState 集成示例完成！")


def main():
    """主函数"""
    print("🚀 Source 模型演示")
    print("=" * 60)

    # 演示基本使用
    demonstrate_source_usage()

    # 演示研究状态集成
    demonstrate_research_state_integration()

    print("\n🎉 所有演示完成！")


if __name__ == "__main__":
    main()
