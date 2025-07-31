# service/examples/test_decoupled_workflow_pro.py

import asyncio
import json
import os
import pprint
import sys
import uuid
from datetime import datetime

from loguru import logger

# --- 路径设置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 导入核心组件 ---
from service.core.config import settings
from service.core.logging_config import setup_logging

# --- 立即设置日志配置，避免后续初始化时的格式错误 ---
setup_logging(settings)

from service.core.container import container
from service.src.doc_agent.graph.state import ResearchState

# --- 模拟的上传文件内容 (保持不变) ---
STYLE_GUIDE_CONTENT = """
同志们，朋友们！今天我们汇聚一堂，核心议题是创新。创新是引领发展的第一动力，是建设现代化经济体系的战略支撑。我们必须把创新摆在国家发展全局的核心位置。
"""
REQUIREMENTS_CONTENT = """
- 报告必须首先定义什么是"可观测性"。
- 必须包含一个关于 OpenTelemetry 未来发展趋势的章节。
- 结论部分必须为不同规模的企业提供明确的技术选型建议。
"""


async def run_stage_one_outline_generation(
        initial_state: ResearchState) -> dict:
    # ... (此函数内容保持不变) ...
    logger.info("🚀🚀🚀 STAGE 1: Starting Outline Generation Workflow 🚀🚀🚀")
    outline_result = None
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
    return outline_result.get("document_outline")


async def run_stage_two_document_generation(
        initial_state: ResearchState) -> dict:
    # ... (此函数内容修改为返回最终状态) ...
    logger.info("🚀🚀🚀 STAGE 2: Starting Document Generation Workflow 🚀🚀🚀")
    final_result_state = None
    try:
        async for step_output in container.document_graph.astream(
                initial_state):
            node_name = list(step_output.keys())[0]
            logger.info(f"✅ [Stage 2] Finished step: [ {node_name} ]")
            final_result_state = list(step_output.values())[0]
    except Exception as e:
        logger.error(f"❌ [Stage 2] Error during document generation: {e}",
                     exception=e)
        return None
    logger.success("✅✅✅ STAGE 2: Document Generation Complete! ✅✅✅\n")
    return final_result_state


async def main():
    """
    主执行函数，串联两个独立的测试阶段，并保存所有产出。
    """
    # --- 1. 【新增】设置输出路径和日志 ---
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)

    log_file_path = os.path.join(output_dir,
                                 f"workflow_test_{run_timestamp}.log")

    # 添加额外的日志文件输出
    logger.add(log_file_path, level="DEBUG",
               serialize=True)  # 使用 serialize=True 可以让日志文件是 JSON 格式，便于机器分析

    # --- 1.5. 【新增】生成 run_id 并绑定到日志上下文 ---
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    logger.info(
        f"📝 All outputs for this run will be saved with timestamp: {run_timestamp}"
    )
    logger.info(f"🆔 Generated run_id: {run_id}")

    # 绑定 run_id 到日志上下文
    with logger.contextualize(run_id=run_id):
        logger.info("🚀 Starting decoupled workflow test with context tracking")

        # --- 2. 准备第一阶段的输入 (保持不变) ---
        topic = "以'可观测性'为核心，对比分析 Prometheus, Zabbix 和 OpenTelemetry 三种技术方案在现代云原生环境下的优缺点"
        stage_one_input_state = ResearchState(
            topic=topic,
            style_guide_content=STYLE_GUIDE_CONTENT,
            requirements_content=REQUIREMENTS_CONTENT,
            # ... 其他字段 ...
            initial_sources=[],
            document_outline={},
            chapters_to_process=[],
            current_chapter_index=0,
            completed_chapters=[],
            final_document="",
            messages=[],
            run_id=run_id,  # 【新增】添加 run_id 到状态
        )

        # --- 3. 执行第一阶段 (保持不变) ---
        generated_outline = await run_stage_one_outline_generation(
            stage_one_input_state)
        if not generated_outline:
            logger.error("Aborting test due to failure in Stage 1.")
            return

        logger.info("📋 Generated Outline for Stage 2:")
        pprint.pprint(generated_outline)
        print("-" * 80)

        # --- 4. 准备第二阶段的输入 (保持不变) ---
        stage_two_input_state = ResearchState(
            topic=topic,
            document_outline=generated_outline,
            style_guide_content=STYLE_GUIDE_CONTENT,
            # ... 其他字段 ...
            initial_sources=[],
            requirements_content="",
            chapters_to_process=[],
            current_chapter_index=0,
            completed_chapters=[],
            final_document="",
            messages=[],
            run_id=run_id,  # 【新增】添加 run_id 到状态
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
        state_file_path = os.path.join(output_dir,
                                       f"workflow_state_{run_timestamp}.json")
        try:
            with open(state_file_path, 'w', encoding='utf-8') as f:
                # Pydantic/TypedDict 不能直接 json.dump，需要先转为普通 dict
                # 我们简单地拷贝一下
                serializable_state = dict(final_state)
                json.dump(serializable_state, f, ensure_ascii=False, indent=4)
            logger.success(
                f"   - Full final state saved to: {state_file_path}")
        except Exception as e:
            logger.error(f"   - Failed to save state file: {e}")

        # 保存最终文档
        document_file_path = os.path.join(
            output_dir, f"final_document_{run_timestamp}.md")
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
        print(f"  - 📄 Document: {document_file_path}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
