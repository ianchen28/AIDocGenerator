# service/examples/run_full_workflow.py

import asyncio
import os
import pprint
import sys

from loguru import logger

# --- 路径设置 ---
# 确保脚本可以从根目录正确导入模块
# 这段代码会找到项目根目录 (AIDocGenerator) 并将其添加到 Python 路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
# service 目录的父目录就是项目根目录
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 导入核心组件 ---
# 必须在路径设置后导入
from service.core.config import settings
from service.core.container import container
from service.core.logging_config import setup_logging
from service.src.doc_agent.graph.state import ResearchState


# --- 主执行函数 ---
async def main():
    """
    主执行函数，用于运行完整的文档生成工作流并观察输出。
    """
    # 1. 配置日志
    # 我们在这里也配置一下日志，这样可以和应用运行时看到一样的输出
    setup_logging(settings)

    # 2. 定义输入状态
    # 你可以在这里修改 topic 来测试不同的生成主题
    topic = ("中国过去10年水电发展情况")

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

    logger.info("🚀 Starting Full End-to-End Workflow Test...")
    logger.info(f"   Topic: {topic}")
    print("-" * 80)

    # 3. 流式调用主图 (Main Orchestrator Graph)
    # astream() 方法会一步步地返回图中每个节点的输出
    final_result = None
    try:
        async for step_output in container.main_graph.astream(initial_state):
            # step_output 的格式是 { "node_name": {"state_key": value} }
            node_name = list(step_output.keys())[0]
            node_data = list(step_output.values())[0]

            logger.info(f"✅ Finished step: [ {node_name} ]")

            # 使用 pprint 美化输出，方便查看复杂的字典或列表
            pprint.pprint(node_data)
            print("-" * 80)

            final_result = node_data

    except Exception as e:
        logger.error(f"❌ An error occurred during the workflow execution: {e}",
                     exception=e)
        return

    # 4. 展示最终结果
    logger.success("\n\n🎉 WORKFLOW COMPLETED! 🎉")
    print("=" * 80)
    logger.info("Final Document:")
    print("=" * 80)

    # 从最终的状态中提取拼接好的 final_document
    final_document_content = final_result.get("final_document")
    if final_document_content:
        print(final_document_content)
    else:
        logger.warning(
            "No final document was generated. Check the logs for details.")
        logger.warning("Final state was:")
        pprint.pprint(final_result)


if __name__ == "__main__":
    # 使用 asyncio.run() 来执行我们的异步 main 函数
    asyncio.run(main())
