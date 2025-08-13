#!/usr/bin/env python3
"""
测试大纲加载器功能
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.core.container import container
from doc_agent.graph.state import ResearchState


async def test_outline_loader():
    """测试大纲加载器功能"""

    # 测试用的file_token
    test_file_token = "a19bcc15e6098a030632aac19fd2780c"
    test_topic = "测试文档大纲"
    test_job_id = "test-outline-loader-001"
    test_session_id = "test-session-001"

    logger.info(f"🧪 开始测试大纲加载器功能")
    logger.info(f"📄 测试文件token: {test_file_token}")
    logger.info(f"📝 测试主题: {test_topic}")

    try:
        # 获取容器实例
        container_instance = container()

        # 获取大纲加载器图
        outline_loader_graph = container_instance.get_outline_loader_graph_runnable_for_job(
            test_job_id)

        # 创建初始状态
        initial_state = ResearchState(
            topic=test_topic,
            user_outline_file=test_file_token,
            job_id=test_job_id,
            session_id=test_session_id,
            style_guide_content="",
            requirements_content="",
            initial_sources=[],
            document_outline={},
            chapters_to_process=[],
            current_chapter_index=0,
            current_citation_index=1,
            completed_chapters=[],
            final_document="",
            sources=[],
            all_sources=[],
            cited_sources=[],
            cited_sources_in_chapter=[],
            messages=[],
            run_id=test_job_id,
        )

        logger.info("🚀 开始执行大纲加载器图...")

        # 执行图
        final_state = None
        async for event in outline_loader_graph.astream(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": test_session_id,
                        "job_id": test_job_id
                    }
                }):
            # 打印每个步骤的完成情况
            for key, value in event.items():
                logger.info(f"✅ 完成步骤: {key}")
                if key == "outline_loader" and "document_outline" in value:
                    final_state = value
                    outline = value["document_outline"]
                    logger.info(f"📋 生成的大纲标题: {outline.get('title', 'N/A')}")
                    logger.info(f"📋 章节数量: {len(outline.get('chapters', []))}")

                    # 打印大纲详情
                    logger.info("📋 大纲详情:")
                    for i, chapter in enumerate(outline.get('chapters', [])):
                        logger.info(
                            f"  第{i+1}章: {chapter.get('title', 'N/A')}")
                        for j, section in enumerate(chapter.get(
                                'sections', [])):
                            logger.info(
                                f"    {i+1}.{j+1} {section.get('title', 'N/A')}"
                            )

        if final_state:
            logger.success("✅ 大纲加载器测试成功完成！")

            # 保存结果到文件
            output_file = "test_outline_loader_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_state, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 结果已保存到: {output_file}")

            return True
        else:
            logger.error("❌ 大纲加载器测试失败：未获取到最终状态")
            return False

    except Exception as e:
        logger.error(f"❌ 大纲加载器测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("🎯 大纲加载器功能测试")
    logger.info("=" * 50)

    success = await test_outline_loader()

    logger.info("=" * 50)
    if success:
        logger.success("🎉 所有测试通过！")
    else:
        logger.error("💥 测试失败！")

    return 0 if success else 1


if __name__ == "__main__":
    # 激活conda环境
    import subprocess
    try:
        subprocess.run(["conda", "activate", "ai-doc"], shell=True, check=True)
        logger.info("✅ 已激活ai-doc conda环境")
    except subprocess.CalledProcessError:
        logger.warning("⚠️  无法激活conda环境，请手动激活")

    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
