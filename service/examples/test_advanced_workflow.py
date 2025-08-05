# service/examples/test_advanced_workflow.py

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger

from doc_agent.core.config import settings

# --- 导入核心组件 ---
from doc_agent.core.container import container
from doc_agent.core.logging_config import setup_logging
from doc_agent.graph.state import ResearchState
from doc_agent.workers.tasks import (
    get_redis_client,  # 我们需要 Redis 客户端来模拟 Worker 的行为
)

# --- 创建输出目录 ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("output") / f"advanced_{timestamp}"
output_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"📁 输出目录: {output_dir}")

# --- 配置日志 ---
log_file = output_dir / "advanced_workflow_test.log"

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
    """设置简化的配置以加快测试速度"""
    logger.info("🔧 Setting up simplified configuration for faster testing...")

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
        settings.document_generation_config.document_length.chapter_count = 2
        settings.document_generation_config.document_length.chapter_target_words = 300
        settings.document_generation_config.document_length.total_target_words = 600

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

    # 设置 Agent 组件配置以控制搜索行为
    if hasattr(settings, '_yaml_config') and settings._yaml_config:
        agent_config = settings._yaml_config.get('agent_config', {})
        # 确保搜索配置被正确设置
        if 'search_config' not in agent_config:
            agent_config['search_config'] = {}
        agent_config['search_config'].update({
            'max_search_rounds': 1,
            'max_queries': 1,
            'max_results_per_query': 3
        })
        settings._yaml_config['agent_config'] = agent_config
        logger.info("✅ Agent 配置已更新")

    logger.info("📝 Using simplified prompt versions for faster processing")


def create_fast_test_config():
    """创建一个专门用于快速测试的配置"""
    return {
        "search_config": {
            "max_search_rounds": 1,
            "max_queries": 1,
            "max_results_per_query": 3
        },
        "document_generation_config": {
            "document_length": {
                "chapter_count": 2,
                "chapter_target_words": 300,
                "total_target_words": 600
            }
        },
        "agent_config": {
            "task_planner": {
                "temperature": 0.3,
                "max_tokens": 1000
            },
            "document_writer": {
                "temperature": 0.5,
                "max_tokens": 1500
            }
        }
    }


def verify_config():
    """验证配置是否正确加载（不再强制覆盖，只读取 config.yaml）"""
    logger.info("🔍 验证当前配置（从 config.yaml 加载）:")
    logger.info(
        f"   - search_config.max_search_rounds: {settings.search_config.max_search_rounds}"
    )
    logger.info(
        f"   - search_config.max_queries: {settings.search_config.max_queries}"
    )
    logger.info(
        f"   - search_config.max_results_per_query: {settings.search_config.max_results_per_query}"
    )

    # 获取文档配置（使用快速模式）
    doc_config = settings.get_document_config(fast_mode=True)
    logger.info("   - 快速模式配置:")
    logger.info(
        f"     * chapter_count: {doc_config.get('chapter_count', 'N/A')}")
    logger.info(
        f"     * total_target_words: {doc_config.get('total_target_words', 'N/A')}"
    )
    logger.info(
        f"     * chapter_target_words: {doc_config.get('chapter_target_words', 'N/A')}"
    )
    logger.info(f"     * rerank_size: {doc_config.get('rerank_size', 'N/A')}")

    if hasattr(settings, 'document_generation_config'):
        logger.info(
            f"   - fast_test_mode.enabled: {settings.document_generation_config.fast_test_mode.enabled}"
        )
        logger.info(
            f"   - fast_test_mode.chapter_count: {settings.document_generation_config.fast_test_mode.chapter_count}"
        )

    logger.info("✅ 配置验证完成，所有配置都来自 config.yaml")


# --- 模拟的上传文件内容 ---

# 1. 风格范例 (模仿一段慷慨激昂的讲话稿)
STYLE_GUIDE_CONTENT = """
同志们，朋友们！
今天，我们站在这里，不是为了回顾过去的辉煌，而是为了展望未来的无限可能！我们面临的不是挑战，而是机遇；我们看到的不是困难，而是通往成功的阶梯！
我们的目标是什么？是创新！是突破！是用科技的力量，点燃未来的火炬，照亮前行的道路！让我们携手并进，共创辉煌！
"""

# 2. 需求指令 (明确要求大纲必须包含的内容)
REQUIREMENTS_CONTENT = """
- 报告必须首先定义什么是“可观测性”，并与传统监控进行明确对比。
- 必须详细分析 Prometheus 的拉取模型 (pull-based model) 的优缺点。
- 必须包含一个关于 OpenTelemetry 未来发展趋势的章节。
- 结论部分必须为不同规模的企业提供明确的技术选型建议。
"""


# 3. (可选) 内容参考
# 在这个测试中，我们让 Agent 自行研究，所以内容文件为空
async def setup_test_context_in_redis(context_id: str):
    """
    模拟 process_files_task Worker 的行为，将风格和需求内容存入 Redis。
    """
    logger.info(f"🔧 Simulating file processing for context_id: {context_id}")
    redis_client = await get_redis_client()
    context_key = f"context:{context_id}"

    # 使用 aio-redis 的 pipeline 来批量操作
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.hset(context_key, "style_guide_content", STYLE_GUIDE_CONTENT)
        pipe.hset(context_key, "requirements_content", REQUIREMENTS_CONTENT)
        pipe.hset(context_key, "status", "READY")
        await pipe.execute()

    logger.success(
        f"✅ Mock context created in Redis for context_id: {context_id}")
    await redis_client.aclose()


async def load_context_for_state(context_id: str) -> dict:
    """
    模拟 run_main_workflow 任务开始时的行为，从 Redis 加载上下文内容。
    """
    logger.info(f"📥 Loading context from Redis for context_id: {context_id}")
    redis_client = await get_redis_client()
    context_key = f"context:{context_id}"

    context_data = await redis_client.hgetall(context_key)

    # 因为设置了 decode_responses=True，返回的已经是字符串
    style_content = context_data.get('style_guide_content', '')
    requirements_content = context_data.get('requirements_content', '')

    logger.success("✅ Context loaded successfully.")
    await redis_client.aclose()

    return {
        "style_guide_content": style_content,
        "requirements_content": requirements_content
    }


async def main():
    """
    主执行函数，运行包含多类型输入的完整工作流。
    """
    setup_logging(settings)

    # 验证配置（从 config.yaml 加载）
    verify_config()

    # --- 1. 模拟上下文创建 ---
    # 生成一个唯一的 context_id 用于本次测试
    test_context_id = f"ctx-{uuid.uuid4().hex}"
    await setup_test_context_in_redis(test_context_id)

    # --- 2. 准备初始状态 ---
    # 使用原来的复杂主题以测试多类型输入功能
    topic = "以'可观测性'为核心，对比分析 Prometheus, Zabbix 和 OpenTelemetry 三种技术方案在现代云原生环境下的优缺点"

    # 模拟 Worker 从 Redis 加载上下文
    context_from_redis = await load_context_for_state(test_context_id)

    # 添加调试信息
    logger.info("🔍 从 Redis 加载的上下文数据:")
    logger.info(
        f"   - style_guide_content 长度: {len(context_from_redis['style_guide_content'])}"
    )
    logger.info(
        f"   - requirements_content 长度: {len(context_from_redis['requirements_content'])}"
    )
    logger.info(
        f"   - requirements_content 内容: {context_from_redis['requirements_content'][:100]}..."
    )

    initial_state = ResearchState(
        topic=topic,
        context_id=test_context_id,
        # 将从 Redis 加载的内容注入到初始状态中
        style_guide_content=context_from_redis["style_guide_content"],
        requirements_content=context_from_redis["requirements_content"],
        # 其他字段使用默认值
        initial_sources=[],
        document_outline={},
        chapters_to_process=[],
        current_chapter_index=0,
        current_citation_index=0,  # 添加引用索引初始化
        completed_chapters=[],
        final_document="",
        messages=[],
    )

    # 验证初始状态
    logger.info("🔍 初始状态验证:")
    logger.info(
        f"   - requirements_content 在状态中: {'requirements_content' in initial_state}"
    )
    logger.info(
        f"   - requirements_content 值: {initial_state.get('requirements_content', 'NOT_FOUND')}"
    )
    logger.info(
        f"   - requirements_content 长度: {len(initial_state.get('requirements_content', ''))}"
    )

    logger.info("🚀 Starting Advanced Workflow Test with multi-type inputs...")
    logger.info(f"   Topic: {topic}")
    logger.info(f"   Context ID: {test_context_id}")
    logger.info(f"   Log file: {log_file}")
    logger.info("   📝 Using simplified configuration for faster testing:")
    logger.info("      - Max 1 search round")
    logger.info("      - Max 1 query per research")
    logger.info("      - Max 3 results per query")
    logger.info("      - Max 2 chapters")
    logger.info("      - Max 300 words per chapter")
    print("-" * 80)

    # --- 3. 流式调用主图 ---
    # 记录工作流步骤
    workflow_steps = []
    final_result = None

    try:
        async for step_output in container.main_graph.astream(initial_state):
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
            elif "researcher" in node_name:
                if "gathered_sources" in node_data:
                    step_info["sources_count"] = len(
                        node_data["gathered_sources"])
                    step_info["sources_preview"] = [
                        f"[{s.id}] {s.title[:50]}..."
                        for s in node_data["gathered_sources"][:3]
                    ]
            elif "writer" in node_name or node_name == "chapter_processing":
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
                    if "## 参考文献" in node_data["final_document"]:
                        step_info["bibliography_added"] = True

            workflow_steps.append(step_info)
            final_result = node_data

    except Exception as e:
        logger.error(f"❌ An error occurred during the workflow execution: {e}",
                     exception=e)
        return

    # 保存工作流步骤信息
    steps_file = output_dir / "advanced_workflow_steps.json"
    with open(steps_file, 'w', encoding='utf-8') as f:
        json.dump(workflow_steps, f, ensure_ascii=False, indent=2)
    logger.info(f"📊 Workflow steps saved to: {steps_file}")

    # --- 4. 展示最终结果 ---
    logger.success("\n\n🎉 WORKFLOW COMPLETED! 🎉")
    print("=" * 80)
    logger.info("Final Document:")
    print("=" * 80)

    final_document_content = final_result.get("final_document")
    if final_document_content:
        # 保存最终文档
        result_file = output_dir / "final_document.md"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(final_document_content)

        logger.success(f"📄 Final document saved to: {result_file}")
        logger.success(
            f"📊 Document length: {len(final_document_content)} characters")

        # 检查是否包含参考文献
        if "## 参考文献" in final_document_content:
            logger.success(
                "✅ Bibliography successfully added to final document")
        else:
            logger.warning("⚠️  No bibliography found in final document")

        # 显示文档预览
        print(final_document_content[:1000] + "...")
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
    print("\n📊 Advanced Workflow Analysis:")
    research_steps = [
        step for step in workflow_steps if "researcher" in step["node_name"]
    ]
    print(f"   🔍 Research steps: {len(research_steps)}")

    writer_steps = [
        step for step in workflow_steps if "writer" in step["node_name"]
        or step["node_name"] == "chapter_processing"
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
        else:
            print("   📚 Bibliography: ❌ Missing")

    # 显示文件位置
    print("\n📁 Output files:")
    print(f"   📝 Log: {log_file}")
    print(f"   📊 Steps: {steps_file}")
    if final_result and "final_document" in final_result:
        print(f"   📄 Document: {result_file}")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
