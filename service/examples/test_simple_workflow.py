#!/usr/bin/env python3
"""
简化的工作流测试脚本
使用简单的任务测试整体流程，并将日志和结果分别保存到文件
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# --- 导入核心组件 ---
from doc_agent.core.config import settings
from doc_agent.core.container import container
from doc_agent.core.logging_config import setup_logging
from doc_agent.graph.state import ResearchState

# --- 创建输出目录 ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("output") / timestamp
output_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"📁 输出目录: {output_dir}")

# --- 配置日志 ---
log_file = output_dir / "workflow_test.log"

# 配置loguru输出到文件
logger.remove()  # 移除默认处理器
logger.add(
    log_file,
    format=
    "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}")


# --- 简化配置函数 ---
def setup_simple_config():
    """设置简化的配置"""
    # 配置已从YAML文件中读取，无需硬编码设置
    logger.info(
        f"✅ 搜索配置已加载: max_search_rounds={settings.search_config.max_search_rounds}"
    )
    logger.info(f"✅ 搜索配置已加载: max_queries={settings.search_config.max_queries}")
    logger.info(
        f"✅ 搜索配置已加载: max_results_per_query={settings.search_config.max_results_per_query}"
    )

    # 强制覆盖搜索配置以确保简化模式
    settings.search_config.max_search_rounds = 1
    settings.search_config.max_queries = 1
    settings.search_config.max_results_per_query = 3

    logger.info("🔧 强制设置简化搜索配置:")
    logger.info(
        f"   - max_search_rounds: {settings.search_config.max_search_rounds}")
    logger.info(f"   - max_queries: {settings.search_config.max_queries}")
    logger.info(
        f"   - max_results_per_query: {settings.search_config.max_results_per_query}"
    )

    # 修改文档生成配置 - 减少章节数
    if hasattr(settings, 'document_generation_config'):
        # 强制设置章节数量
        settings.document_generation_config.document_length.chapter_count = 3
        settings.document_generation_config.document_length.chapter_target_words = 500
        settings.document_generation_config.document_length.total_target_words = 1500

        logger.info("📄 文档生成配置:")
        logger.info(
            f"   - chapter_count: {settings.document_generation_config.document_length.chapter_count}"
        )
        logger.info(
            f"   - chapter_target_words: {settings.document_generation_config.document_length.chapter_target_words}"
        )
        logger.info(
            f"   - total_target_words: {settings.document_generation_config.document_length.total_target_words}"
        )
    else:
        logger.warning("⚠️  document_generation_config 不存在")

    # 设置使用简化的prompt版本
    logger.info("📝 Using simplified prompt versions:")
    logger.info("   - planner: v1_simple")
    logger.info("   - outline_generation: v1_simple")
    logger.info("   - writer: v2_simple_citations")
    logger.info("   - supervisor: v1_simple")
    logger.info("   - Max 1 search round (instead of 5)")


# --- 主执行函数 ---
async def main():
    """
    简化的主执行函数，用于测试完整的文档生成工作流
    """
    # 配置日志
    setup_logging(settings)

    # 设置简化配置
    setup_simple_config()

    # 使用简化的主题 - 故意选择可能需要多次搜索的主题
    topic = "人工智能的基本概念"
    genre = "simple"  # 使用简化的genre配置

    initial_state = ResearchState(
        topic=topic,
        # 使用新的Source-based字段
        initial_sources=[],
        gathered_sources=[],
        cited_sources={},
        cited_sources_in_chapter=[],
        # 其他字段使用默认初始值
        document_outline={},
        chapters_to_process=[],
        current_chapter_index=0,
        completed_chapters_content=[],
        final_document="",
        messages=[],
    )

    logger.info("🚀 Starting Simplified Workflow Test...")
    logger.info(f"   Topic: {topic}")
    logger.info(f"   Genre: {genre}")
    logger.info(f"   Log file: {log_file}")
    logger.info("   📝 Using simplified configuration:")
    logger.info("      - Max 2 search queries per research")
    logger.info("      - Max 3 results per query")
    logger.info("      - Max 3 chapters")
    logger.info("      - Max 1000 tokens per chapter")
    logger.info("      - Using simple prompt versions")
    print("-" * 80)

    # 记录工作流步骤
    workflow_steps = []
    final_result = None

    try:
        # 使用 genre-aware 的 graph
        graph = container.get_graph_runnable_for_job("test-job", genre)

        async for step_output in graph.astream(initial_state):
            # step_output 的格式是 { "node_name": {"state_key": value} }
            node_name = list(step_output.keys())[0]
            node_data = list(step_output.values())[0]

            logger.info(f"✅ Finished step: [ {node_name} ]")

            # 记录步骤信息
            step_info = {
                "node_name":
                node_name,
                "timestamp":
                datetime.now().isoformat(),
                "data_keys":
                list(node_data.keys()) if isinstance(node_data, dict) else str(
                    type(node_data))
            }

            # 添加特定步骤的详细信息
            if node_name == "initial_research":
                if "initial_sources" in node_data:
                    step_info["sources_count"] = len(
                        node_data["initial_sources"])
                    step_info["sources_preview"] = [
                        f"[{s.id}] {s.title[:50]}..."
                        for s in node_data["initial_sources"][:3]
                    ]

            elif node_name == "outline_generation":
                if "document_outline" in node_data:
                    outline = node_data["document_outline"]
                    step_info["chapters_count"] = len(
                        outline.get("chapters", []))
                    step_info["chapters"] = [
                        ch.get("chapter_title", "")
                        for ch in outline.get("chapters", [])
                    ]

            elif node_name == "reflector":
                if "search_queries" in node_data:
                    step_info["new_queries"] = node_data["search_queries"]
                    step_info["reflection_triggered"] = True

            elif "researcher" in node_name:
                if "gathered_sources" in node_data:
                    step_info["sources_count"] = len(
                        node_data["gathered_sources"])
                    step_info["sources_preview"] = [
                        f"[{s.id}] {s.title[:50]}..."
                        for s in node_data["gathered_sources"][:3]
                    ]

            elif "writer" in node_name:
                if "final_document" in node_data:
                    step_info["document_length"] = len(
                        node_data["final_document"])
                    step_info["document_preview"] = node_data[
                        "final_document"][:200] + "..."
                if "cited_sources_in_chapter" in node_data:
                    step_info["cited_sources_count"] = len(
                        node_data["cited_sources_in_chapter"])
                    # 添加引用源预览
                    if isinstance(node_data["cited_sources_in_chapter"], list):
                        step_info["cited_sources_preview"] = [
                            f"[{s.id}] {s.title[:30]}..."
                            for s in node_data["cited_sources_in_chapter"][:3]
                        ]

            elif node_name == "generate_bibliography":
                if "final_document" in node_data:
                    step_info["final_document_length"] = len(
                        node_data["final_document"])
                    # 检查是否包含参考文献
                    if "## 参考文献" in node_data["final_document"]:
                        step_info["bibliography_added"] = True
                        # 提取参考文献部分
                        doc = node_data["final_document"]
                        bib_start = doc.find("## 参考文献")
                        if bib_start != -1:
                            bibliography = doc[bib_start:]
                            step_info[
                                "bibliography_preview"] = bibliography[:300] + "..."
                            # 统计参考文献数量
                            import re
                            citations = re.findall(r'\[(\d+)\]', bibliography)
                            step_info["bibliography_count"] = len(
                                set(citations))

                # 添加全局引用源统计
                if "cited_sources" in node_data:
                    step_info["global_cited_sources_count"] = len(
                        node_data["cited_sources"])

            workflow_steps.append(step_info)
            final_result = node_data

    except Exception as e:
        logger.error(f"❌ An error occurred during the workflow execution: {e}",
                     exception=e)
        return

    # 保存工作流步骤信息
    steps_file = output_dir / "workflow_steps.json"
    with open(steps_file, 'w', encoding='utf-8') as f:
        json.dump(workflow_steps, f, ensure_ascii=False, indent=2)

    logger.info(f"📊 Workflow steps saved to: {steps_file}")

    # 保存最终结果
    if final_result and "final_document" in final_result:
        result_file = output_dir / "final_document.md"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(final_result["final_document"])

        logger.success(f"📄 Final document saved to: {result_file}")
        logger.success(
            f"📊 Document length: {len(final_result['final_document'])} characters"
        )

        # 检查是否包含参考文献
        if "## 参考文献" in final_result["final_document"]:
            logger.success(
                "✅ Bibliography successfully added to final document")
        else:
            logger.warning("⚠️  No bibliography found in final document")

        # 显示文档预览
        print("\n" + "=" * 80)
        print("📄 FINAL DOCUMENT PREVIEW")
        print("=" * 80)
        print(final_result["final_document"][:1000] + "...")
        print("=" * 80)

    else:
        logger.warning("No final document was generated.")
        if final_result:
            result_file = output_dir / "final_state.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(final_result,
                          f,
                          ensure_ascii=False,
                          indent=2,
                          default=str)
            logger.info(f"📊 Final state saved to: {result_file}")

    # 分析工作流执行情况
    print("\n📊 Workflow Analysis:")
    reflection_count = sum(1 for step in workflow_steps
                           if step.get("reflection_triggered", False))
    print(f"   🔄 Reflection triggered: {reflection_count} times")

    research_steps = [
        step for step in workflow_steps if "researcher" in step["node_name"]
    ]
    print(f"   🔍 Research steps: {len(research_steps)}")

    writer_steps = [
        step for step in workflow_steps if "writer" in step["node_name"]
    ]
    print(f"   ✍️  Writer steps: {len(writer_steps)}")

    # 分析引用系统
    if final_result and "final_document" in final_result:
        if "## 参考文献" in final_result["final_document"]:
            print("   📚 Bibliography: ✅ Added")

            # 统计参考文献数量和引用编号
            import re
            doc = final_result["final_document"]
            bib_start = doc.find("## 参考文献")
            if bib_start != -1:
                bibliography = doc[bib_start:]
                citations = re.findall(r'\[(\d+)\]', bibliography)
                unique_citations = sorted({int(c) for c in citations})
                print(f"   📖 Bibliography entries: {len(unique_citations)}")
                print(f"   🔢 Citation numbers: {unique_citations}")

                # 检查编号是否连续
                if unique_citations == list(range(1,
                                                  len(unique_citations) + 1)):
                    print("   ✅ Citation numbering: Consecutive")
                else:
                    print("   ❌ Citation numbering: Not consecutive")

            # 统计全文中的引用
            content_before_bib = doc[:bib_start] if bib_start != -1 else doc
            content_citations = re.findall(r'\[(\d+)\]', content_before_bib)
            unique_content_citations = sorted(
                {int(c)
                 for c in content_citations})
            print(f"   📝 In-text citations: {unique_content_citations}")

        else:
            print("   📚 Bibliography: ❌ Missing")

    # 统计全局引用源
    bibliography_steps = [
        step for step in workflow_steps
        if step["node_name"] == "generate_bibliography"
    ]
    if bibliography_steps:
        last_bib_step = bibliography_steps[-1]
        if "global_cited_sources_count" in last_bib_step:
            print(
                f"   🌐 Global sources tracked: {last_bib_step['global_cited_sources_count']}"
            )
        if "bibliography_count" in last_bib_step:
            print(
                f"   📋 Bibliography count: {last_bib_step['bibliography_count']}"
            )

    # 显示文件位置
    print("\n📁 Output files:")
    print(f"   📝 Log: {log_file}")
    print(f"   📊 Steps: {steps_file}")
    if final_result and "final_document" in final_result:
        print(f"   📄 Document: {result_file}")


if __name__ == "__main__":
    # 使用 asyncio.run() 来执行我们的异步 main 函数
    asyncio.run(main())
