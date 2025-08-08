# service/examples/test_decoupled_workflow_pro.py

import asyncio
import json
import pprint
import sys
import uuid
from datetime import datetime
from pathlib import Path

from doc_agent.core.logger import logger
# --- 导入核心组件 ---
from doc_agent.core.config import settings
from doc_agent.core.logging_config import setup_logging

# --- 立即设置日志配置，避免后续初始化时的格式错误 ---
setup_logging(settings)

from doc_agent.core.container import get_container
from doc_agent.graph.state import ResearchState

# --- 模拟的上传文件内容 (保持不变) ---
STYLE_GUIDE_CONTENT = """
同志们，朋友们！今天我们汇聚一堂，核心议题是创新。创新是引领发展的第一动力，是建设现代化经济体系的战略支撑。我们必须把创新摆在国家发展全局的核心位置。
"""
REQUIREMENTS_CONTENT = """
- 报告必须要引用白鹤滩水电站的相关经验作为例子。
- 必须包含一个关于中国水电站未来发展趋势的章节。
- 结论部分必须为不同规模的水电站提 供明确的技术选型建议。
"""


async def run_stage_one_outline_generation(
        initial_state: ResearchState) -> dict:
    """执行第一阶段：大纲生成工作流"""
    logger.info("🚀🚀🚀 STAGE 1: Starting Outline Generation Workflow 🚀🚀🚀")
    outline_result = None
    container = get_container()
    try:
        async for step_output in container.outline_graph.astream(
                initial_state):
            node_name = list(step_output.keys())[0]
            logger.info(f"✅ [Stage 1] Finished step: [ {node_name} ]")
            outline_result = list(step_output.values())[0]
    except Exception as e:
        logger.error(f"❌ [Stage 1] Error during outline generation: {e}",
                     exception=e)
        return None

    logger.success("✅✅✅ STAGE 1: Outline Generation Complete! ✅✅✅\n")

    # 检查结果是否有效
    if outline_result is None:
        logger.error("❌ [Stage 1] outline_result is None")
        return None

    document_outline = outline_result.get("document_outline")
    if document_outline is None:
        logger.error("❌ [Stage 1] document_outline is None in outline_result")
        logger.debug(
            f"📄 outline_result keys: {list(outline_result.keys()) if outline_result else 'None'}"
        )
        return None

    logger.info(f"✅ [Stage 1] Successfully extracted document_outline")
    return document_outline


async def run_stage_two_document_generation(
        initial_state: ResearchState) -> dict:
    logger.info("🚀🚀🚀 STAGE 2: Starting Document Generation Workflow 🚀🚀🚀")
    final_result_state = None
    container = get_container()
    try:
        async_stream = container.document_graph.astream(initial_state)
        async for step_output in async_stream:
            node_name = list(step_output.keys())[0]
            logger.info(f"✅ [Stage 2] Finished step: [ {node_name} ]")
            step_result = list(step_output.values())[0]

            # 检查步骤结果是否有效
            if step_result is not None:
                final_result_state = step_result
                logger.debug(f"📊 步骤 {node_name} 返回有效结果")
            else:
                logger.warning(f"⚠️  步骤 {node_name} 返回 None")

    except Exception as e:
        logger.error(f"❌ [Stage 2] Error during document generation: {e}",
                     exception=e)
        return None

    # 如果最终状态为None，尝试使用初始状态
    if final_result_state is None:
        logger.warning("⚠️  最终状态为None，使用初始状态")
        final_result_state = initial_state

    logger.success("✅✅✅ STAGE 2: Document Generation Complete! ✅✅✅\n")
    return final_result_state


async def main():
    """
    主执行函数，串联两个独立的测试阶段，并保存所有产出。
    """
    # --- 1. 【新增】设置输出路径和日志 ---
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    log_file_path = output_dir / f"workflow_test_{run_timestamp}.log"

    # 配置日志同时输出到文件和控制台
    # 移除默认处理器
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level="INFO",
        colorize=True)

    # 添加文件输出
    logger.add(
        log_file_path,
        format=
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days")

    # --- 1.5. 【新增】生成 run_id 并绑定到日志上下文 ---
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    logger.info(
        f"📝 All outputs for this run will be saved with timestamp: {run_timestamp}"
    )
    logger.info(f"🆔 Generated run_id: {run_id}")

    # 绑定 run_id 到日志上下文
    with logger.contextualize(run_id=run_id):
        logger.info("🚀 Starting decoupled workflow test with context tracking")

        # --- 2. 准备第一阶段的输入 (修正：添加所有必需字段) ---
        topic = "调研一下水电站建造过程中可能出现的问题和解决方案"
        stage_one_input_state = ResearchState(
            # 日志追踪 ID
            run_id=run_id,

            # 研究主题
            topic=topic,

            # 文档样式和需求指南
            style_guide_content=STYLE_GUIDE_CONTENT,
            requirements_content=REQUIREMENTS_CONTENT,

            # 第一层: 上层研究的初始研究结果
            initial_sources=[],

            # 文档结构
            document_outline={},

            # 章节处理
            chapters_to_process=[],
            current_chapter_index=0,

            # 上下文积累 - 保持连贯性
            completed_chapters=[],

            # 最终输出
            final_document="",

            # 章节级研究状态
            research_plan="",
            search_queries=[],
            gathered_sources=[],

            # 源追踪
            sources=[],
            all_sources=[],
            current_citation_index=1,

            # 全局引用源追踪 - 用于最终参考文献
            cited_sources=[],
            cited_sources_in_chapter=[],

            # 对话历史
            messages=[],
        )

        # --- 3. 执行第一阶段 (保持不变) ---
        generated_outline = await run_stage_one_outline_generation(
            stage_one_input_state)
        if not generated_outline:
            logger.error("❌ Aborting test due to failure in Stage 1.")
            return

        logger.info("📋 Generated Outline for Stage 2:")
        pprint.pprint(generated_outline)
        print("-" * 80)

        # --- 3.5. 【新增】验证大纲结构 ---
        logger.info("🔍 Validating generated outline structure...")
        if generated_outline and isinstance(generated_outline, dict):
            chapters = generated_outline.get('chapters', [])
            logger.info(f"📊 Outline contains {len(chapters)} chapters")

            for i, chapter in enumerate(chapters):
                chapter_title = chapter.get('chapter_title', f'Chapter {i+1}')
                sub_sections = chapter.get('sub_sections', [])
                logger.info(
                    f"  📖 Chapter {i+1}: {chapter_title} ({len(sub_sections)} sub-sections)"
                )

                for j, sub_section in enumerate(sub_sections):
                    sub_title = sub_section.get('section_title',
                                                f'Sub-section {j+1}')
                    key_points = sub_section.get('key_points', [])
                    logger.info(
                        f"    📝 {i+1}.{j+1}: {sub_title} ({len(key_points)} key points)"
                    )
        else:
            logger.warning("⚠️  Generated outline is invalid or empty")

        # --- 4. 准备第二阶段的输入 (修正：添加所有必需字段) ---
        stage_two_input_state = ResearchState(
            # 日志追踪 ID
            run_id=run_id,

            # 研究主题
            topic=topic,

            # 文档样式和需求指南
            style_guide_content=STYLE_GUIDE_CONTENT,
            requirements_content="",

            # 第一层: 上层研究的初始研究结果
            initial_sources=[],

            # 文档结构
            document_outline=generated_outline,

            # 章节处理
            chapters_to_process=[],
            current_chapter_index=0,

            # 上下文积累 - 保持连贯性
            completed_chapters=[],

            # 最终输出
            final_document="",

            # 章节级研究状态
            research_plan="",
            search_queries=[],
            gathered_sources=[],

            # 源追踪
            sources=[],
            all_sources=[],
            current_citation_index=1,

            # 全局引用源追踪 - 用于最终参考文献
            cited_sources=[],
            cited_sources_in_chapter=[],

            # 对话历史
            messages=[],
        )

        # --- 5. 执行第二阶段 ---
        final_state = await run_stage_two_document_generation(
            stage_two_input_state)

        if not final_state:
            logger.error("Aborting test due to failure in Stage 2.")
            return

        # --- 6. 【新增】保存所有产出文件 ---
        logger.info("💾 Saving all workflow outputs...")

        # 保存最终状态
        state_file_path = output_dir / f"workflow_state_{run_timestamp}.json"
        try:
            with open(state_file_path, 'w', encoding='utf-8') as f:
                serializable_state = dict(final_state)
                json.dump(serializable_state, f, ensure_ascii=False, indent=4)
            logger.success(
                f"   - Full final state saved to: {state_file_path}")
        except Exception as e:
            logger.error(f"   - Failed to save state file: {e}")

        # 保存大纲文件
        outline_file_path = output_dir / f"generated_outline_{run_timestamp}.json"
        try:
            with open(outline_file_path, 'w', encoding='utf-8') as f:
                json.dump(generated_outline, f, ensure_ascii=False, indent=4)
            logger.success(
                f"   - Generated outline saved to: {outline_file_path}")
        except Exception as e:
            logger.error(f"   - Failed to save outline file: {e}")

        # 保存最终文档
        document_file_path = output_dir / f"final_document_{run_timestamp}.md"
        final_document_content = final_state.get("final_document", "")
        try:
            with open(document_file_path, 'w', encoding='utf-8') as f:
                f.write(final_document_content)
            logger.success(
                f"   - Final document saved to: {document_file_path}")
        except Exception as e:
            logger.error(f"   - Failed to save document file: {e}")

        # --- 7. 打印最终总结 ---
        print("\n\n" + "=" * 80)
        logger.success("🎉 End-to-End Test with Output Saving COMPLETED! 🎉")
        print("=" * 80)
        print("📁 Output files:")
        print(f"  - 📝 Log: {log_file_path}")
        print(f"  - 📊 State: {state_file_path}")
        print(f"  - 📋 Outline: {outline_file_path}")
        print(f"  - 📄 Document: {document_file_path}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
