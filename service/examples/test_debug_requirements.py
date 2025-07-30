# service/examples/test_debug_requirements.py

import sys
import os
import asyncio
from loguru import logger

# --- 路径设置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 导入核心组件 ---
from service.core.container import container
from service.src.doc_agent.graph.state import ResearchState
from service.core.logging_config import setup_logging
from service.core.config import settings
from service.workers.tasks import get_redis_client

# --- 测试需求文档内容 ---
REQUIREMENTS_CONTENT = """
--- Requirement from requirements.txt ---
- 报告必须首先定义什么是"可观测性"，并与传统监控进行明确对比。
- 必须详细分析 Prometheus 的拉取模型 (pull-based model) 的优缺点。
- 必须包含一个关于 OpenTelemetry 未来发展趋势的章节。
- 结论部分必须为不同规模的企业提供明确的技术选型建议。
"""

async def test_requirements_debug():
    """测试需求文档传递问题"""
    setup_logging(settings)
    
    logger.info("🔍 开始调试需求文档问题...")
    
    # 1. 测试 ResearchState 创建
    test_state = ResearchState(
        topic="测试主题",
        requirements_content=REQUIREMENTS_CONTENT,
        initial_sources=[],
        initial_gathered_data="这是一些测试研究数据，用于验证需求文档功能。",
        document_outline={},
        chapters_to_process=[],
        current_chapter_index=0,
        completed_chapters=[],
        final_document="",
        messages=[],
    )
    
    logger.info(f"✅ ResearchState 创建成功")
    logger.info(f"   - requirements_content 在状态中: {'requirements_content' in test_state}")
    logger.info(f"   - requirements_content 值: {test_state.get('requirements_content', 'NOT_FOUND')}")
    logger.info(f"   - requirements_content 长度: {len(test_state.get('requirements_content', ''))}")
    
    # 2. 测试 outline_generation_node 调用
    try:
        from service.src.doc_agent.graph.main_orchestrator.nodes import outline_generation_node
        from service.src.doc_agent.llm_clients import get_llm_client
        from service.src.doc_agent.common.prompt_selector import PromptSelector
        
        llm_client = get_llm_client("qwen_2_5_235b_a22b")
        prompt_selector = PromptSelector()
        
        logger.info("🔍 调用 outline_generation_node...")
        result = outline_generation_node(test_state, llm_client, prompt_selector)
        
        logger.info(f"✅ outline_generation_node 调用成功")
        logger.info(f"   - 结果类型: {type(result)}")
        logger.info(f"   - 结果键: {list(result.keys())}")
        
    except Exception as e:
        logger.error(f"❌ outline_generation_node 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_requirements_debug()) 