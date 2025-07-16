#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试脚本
测试完整的文档生成图流程
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from core.env_loader import setup_environment

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir and str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 导入必要的模块
from core.container import container
from core.config import settings
import pprint


def export_results(final_state, topic):
    """导出结果到output文件夹"""
    # 创建output目录
    output_dir = Path(service_dir) / "output"
    output_dir.mkdir(exist_ok=True)

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 清理主题名称用于文件名
    safe_topic = "".join(c for c in topic
                         if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_topic = safe_topic.replace(' ', '_')[:50]  # 限制长度

    # 导出最终文档
    if "final_document" in final_state and final_state["final_document"]:
        doc_file = output_dir / f"{timestamp}_{safe_topic}_final_document.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(f"# {topic}\n\n")
            f.write(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(final_state["final_document"])
        print(f"📄 最终文档已导出: {doc_file}")

    # 导出完整状态（JSON格式）
    state_file = output_dir / f"{timestamp}_{safe_topic}_complete_state.json"
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(final_state, f, ensure_ascii=False, indent=2)
    print(f"📊 完整状态已导出: {state_file}")

    # 导出研究计划
    if "research_plan" in final_state and final_state["research_plan"]:
        plan_file = output_dir / f"{timestamp}_{safe_topic}_research_plan.md"
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(f"# 研究计划\n\n")
            f.write(f"主题: {topic}\n")
            f.write(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(final_state["research_plan"])
        print(f"📋 研究计划已导出: {plan_file}")

    # 导出收集的数据
    if "gathered_data" in final_state and final_state["gathered_data"]:
        data_file = output_dir / f"{timestamp}_{safe_topic}_gathered_data.md"
        with open(data_file, 'w', encoding='utf-8') as f:
            f.write(f"# 收集的研究数据\n\n")
            f.write(f"主题: {topic}\n")
            f.write(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(final_state["gathered_data"])
        print(f"📚 收集数据已导出: {data_file}")

    # 导出搜索查询
    if "search_queries" in final_state and final_state["search_queries"]:
        queries_file = output_dir / f"{timestamp}_{safe_topic}_search_queries.txt"
        with open(queries_file, 'w', encoding='utf-8') as f:
            f.write(f"# 搜索查询列表\n\n")
            f.write(f"主题: {topic}\n")
            f.write(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            for i, query in enumerate(final_state["search_queries"], 1):
                f.write(f"{i}. {query}\n")
        print(f"🔍 搜索查询已导出: {queries_file}")

    # 生成汇总报告
    summary_file = output_dir / f"{timestamp}_{safe_topic}_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# 文档生成汇总报告\n\n")
        f.write(f"**主题**: {topic}\n")
        f.write(
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 生成内容概览\n\n")

        if "research_plan" in final_state:
            f.write(f"- **研究计划**: {len(final_state['research_plan'])} 字符\n")
        if "search_queries" in final_state:
            f.write(f"- **搜索查询**: {len(final_state['search_queries'])} 个\n")
        if "gathered_data" in final_state:
            f.write(f"- **收集数据**: {len(final_state['gathered_data'])} 字符\n")
        if "final_document" in final_state:
            f.write(f"- **最终文档**: {len(final_state['final_document'])} 字符\n")

        f.write("\n## 文件列表\n\n")
        f.write("以下文件已生成:\n\n")
        for file_path in output_dir.glob(f"{timestamp}_{safe_topic}_*"):
            f.write(f"- `{file_path.name}`\n")

    print(f"📋 汇总报告已导出: {summary_file}")
    print(f"\n🎯 所有文件已导出到: {output_dir}")


async def test_end_to_end_graph():
    """端到端测试图流程"""
    print("🚀 开始端到端测试...")
    print("=" * 80)

    # 1. 定义初始输入
    initial_input = {
        "messages": [],
        "topic": "帮我写一份水电站的调研报告",
        "research_plan": "",
        "search_queries": [],
        "gathered_data": "",
        "final_document": ""
    }

    print("📝 初始主题:")
    print(f"   {initial_input['topic']}")
    print()

    try:
        # 2. 使用 stream() 方法执行图
        print("🔄 开始执行图流程...")
        print("=" * 80)

        step_count = 0
        final_state = None

        async for step in container.graph.astream(initial_input):
            step_count += 1
            print(f"\n{'='*20} 步骤 {step_count} {'='*20}")

            # 获取节点名称和输出
            node_name = list(step.keys())[0]
            node_output = list(step.values())[0]
            final_state = node_output  # 保存最终状态

            print(f"📋 节点: {node_name}")
            print(f"⏱️  状态: 完成")
            print()

            # 使用 pprint 格式化输出
            print("📊 节点输出:")
            pprint.pprint(node_output, width=120, depth=3)
            print()

            # 显示关键信息
            if node_name == "planner":
                if "research_plan" in node_output:
                    print("📋 研究计划:")
                    print(f"   {node_output['research_plan'][:200]}...")
                if "search_queries" in node_output:
                    print(f"🔍 搜索查询数量: {len(node_output['search_queries'])}")
                    for i, query in enumerate(
                            node_output['search_queries'][:3], 1):
                        print(f"   {i}. {query}")
                    if len(node_output['search_queries']) > 3:
                        print(
                            f"   ... 还有 {len(node_output['search_queries']) - 3} 个查询"
                        )

            elif node_name == "researcher":
                if "gathered_data" in node_output:
                    data_length = len(node_output['gathered_data'])
                    print(f"📚 收集数据长度: {data_length} 字符")
                    if data_length > 0:
                        print("📖 数据预览:")
                        preview = node_output['gathered_data'][:300]
                        print(f"   {preview}...")

            elif node_name == "writer":
                if "final_document" in node_output:
                    doc_length = len(node_output['final_document'])
                    print(f"📄 生成文档长度: {doc_length} 字符")
                    if doc_length > 0:
                        print("📝 文档预览:")
                        preview = node_output['final_document'][:500]
                        print(f"   {preview}...")

            print("-" * 80)

        # 3. 显示最终结果
        print("\n🎉 WORKFLOW COMPLETED!")
        print("=" * 80)

        # 获取最终状态
        if final_state and "final_document" in final_state:
            final_doc = final_state["final_document"]
            print("📄 最终文档:")
            print("=" * 80)
            print(final_doc)
            print("=" * 80)
        else:
            print("⚠️  未找到最终文档")

        # 显示统计信息
        print("\n📊 执行统计:")
        print(f"   总步骤数: {step_count}")
        if final_state:
            print(f"   最终文档长度: {len(final_state.get('final_document', ''))}")
            print(f"   收集数据长度: {len(final_state.get('gathered_data', ''))}")

        # 4. 导出结果
        if final_state:
            print("\n📤 开始导出结果...")
            print("=" * 80)
            export_results(final_state, initial_input['topic'])
            print("=" * 80)

        return True

    except Exception as e:
        print(f"❌ 图执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🧪 端到端图测试")
    print("=" * 80)

    # 运行异步测试
    success = asyncio.run(test_end_to_end_graph())

    if success:
        print("\n✅ 端到端测试完成!")
    else:
        print("\n❌ 端到端测试失败!")


if __name__ == "__main__":
    main()
