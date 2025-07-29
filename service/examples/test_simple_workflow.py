#!/usr/bin/env python3
"""
简化的工作流测试脚本
使用简单的任务测试整体流程，并将日志和结果分别保存到文件
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# --- 路径设置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 导入核心组件 ---
from service.core.config import settings
from service.core.container import container
from service.core.logging_config import setup_logging
from service.src.doc_agent.graph.state import ResearchState

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

    # 修改大纲生成配置 - 减少章节数
    if hasattr(settings, 'outline_generation_config'):
        settings.outline_generation_config.max_chapters = 3  # 最多3个章节
        settings.outline_generation_config.max_chapter_length = 500  # 每章最多500字

    # 修改写作配置 - 减少内容长度
    if hasattr(settings, 'document_writer_config'):
        settings.document_writer_config.max_tokens = 1000  # 减少token数量
        settings.document_writer_config.temperature = 0.7

    # 设置使用简化的prompt版本
    logger.info("📝 Using simplified prompt versions:")
    logger.info("   - planner: v1_simple")
    logger.info("   - outline_generation: v1_simple")
    logger.info("   - writer: v2_simple_citations")
    logger.info("   - supervisor: v1_simple")
    logger.info("   - Max 2 search rounds (instead of 5)")


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
    topic = "量子计算的基本原理"
    genre = "simple"  # 使用简化的genre配置

    initial_state = ResearchState(
        topic=topic,
        # 其他字段使用默认初始值
        initial_gathered_data="",
        document_outline={},
        chapters_to_process=[],
        current_chapter_index=0,
        completed_chapters=[],
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
    print(f"\n📊 Workflow Analysis:")
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

    if final_result and "final_document" in final_result:
        if "## 参考文献" in final_result["final_document"]:
            print(f"   📚 Bibliography: ✅ Added")
        else:
            print(f"   📚 Bibliography: ❌ Missing")

    # 显示文件位置
    print(f"\n📁 Output files:")
    print(f"   📝 Log: {log_file}")
    print(f"   📊 Steps: {steps_file}")
    if final_result and "final_document" in final_result:
        print(f"   📄 Document: {result_file}")


if __name__ == "__main__":
    # 使用 asyncio.run() 来执行我们的异步 main 函数
    asyncio.run(main())
