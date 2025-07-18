#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速端到端图工作流测试脚本
优化版本，减少耗时，快速验证功能
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent / "service"
src_dir = service_dir / "src"
for p in [str(service_dir), str(src_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 设置环境变量
from core.env_loader import setup_environment

setup_environment()

from core.container import Container


def setup_output_dir():
    """设置输出目录"""
    logger.debug("设置快速测试输出目录")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # 创建带时间戳的子目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"fast_test_{timestamp}"
    session_dir.mkdir(exist_ok=True)

    logger.debug(f"快速测试输出目录已设置: {session_dir}")
    return session_dir


def save_document(session_dir: Path, document: str, topic: str):
    """保存生成的文档"""
    logger.debug(f"保存快速测试文档，主题: {topic}")
    # 清理文件名中的特殊字符
    safe_topic = "".join(c for c in topic
                         if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_topic = safe_topic.replace(' ', '_')[:30]  # 限制长度

    doc_file = session_dir / f"{safe_topic}.md"
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(document)
    logger.info(f"文档已保存到: {doc_file}")


async def test_graph_fast():
    """快速测试图流程"""
    logger.info("开始快速端到端测试")

    # 设置输出目录
    session_dir = setup_output_dir()
    logger.info(f"输出目录: {session_dir}")

    def log(message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        logger.info(log_entry)

    # 获取容器和配置
    logger.debug("初始化容器和配置")
    container = Container()
    from core.config import settings

    # 获取快速模式配置
    doc_config = settings.get_document_config(fast_mode=True)
    logger.debug(f"快速模式配置: {doc_config}")
    log(f"⚙️  快速模式配置: 总字数={doc_config['total_target_words']}, 章节字数={doc_config['chapter_target_words']}"
        )
    log(f"🔍 ES检索配置: 向量召回={doc_config['vector_recall_size']}, 混合召回={doc_config['hybrid_recall_size']}, 重排={doc_config['rerank_size']}"
        )

    try:
        # 创建简化的初始状态 - 使用电力系统主题，减少搜索查询数量
        initial_state = {
            "topic": "智能电网技术在电力系统中的应用",
            "search_queries": ["智能电网 电力系统 技术应用", "AI 电力调度 优化算法"]
        }

        topic = initial_state["topic"]
        logger.debug(f"快速测试初始状态: {initial_state}")
        log(f"📋 快速测试主题: {topic}")

        # 流式执行图
        logger.info("开始流式执行图")
        async for event in container.main_graph.astream(initial_state):
            node_name = list(event.keys())[0]
            node_output = event[node_name]

            logger.debug(f"执行节点: {node_name}")
            log(f"🔍 执行节点: {node_name}")

            if node_name == "planner":
                search_queries = node_output.get('search_queries', [])
                logger.debug(f"生成的搜索查询: {search_queries}")
                log(f"📝 生成 {len(search_queries)} 个搜索查询")

            elif node_name == "researcher":
                gathered_data = node_output.get('gathered_data', '')
                logger.debug(f"收集数据长度: {len(gathered_data)} 字符")
                log(f"📚 收集数据: {len(gathered_data)} 字符")

            elif node_name == "writer":
                final_document = node_output.get('final_document', '')
                logger.debug(f"生成文档长度: {len(final_document)} 字符")
                log(f"📄 生成文档: {len(final_document)} 字符")
                log("🛑 writer 节点完成，停止执行")
                break

            elif node_name == "supervisor_router":
                decision = node_output.get('decision', '')
                logger.debug(f"路由决策: {decision}")
                log(f"🎯 路由决策: {decision}")
                log("🛑 supervisor_router 节点完成，停止执行")
                break

            elif node_name == "finalize_document":
                final_document = node_output.get('final_document', '')
                logger.debug(f"最终文档长度: {len(final_document)} 字符")
                log(f"📄 最终文档: {len(final_document)} 字符")
                log("🛑 finalize_document 节点完成，流程结束")
                break

        # 保存最终文档
        if final_document and topic:
            save_document(session_dir, final_document, topic)

        log("\n✅ 快速测试完成!")
        logger.info("快速端到端测试完成")
        return True

    except Exception as e:
        error_msg = f"\n❌ 快速测试失败: {str(e)}"
        logger.error(f"快速端到端测试失败: {str(e)}")
        log(error_msg)
        return False

    finally:
        # 清理资源
        logger.info("清理快速测试资源")
        log("🧹 清理资源...")
        try:
            await container.cleanup()
            logger.info("资源清理完成")
            log("✅ 资源清理完成")
        except Exception as e:
            logger.error(f"资源清理时出错: {str(e)}")
            log(f"⚠️  资源清理时出错: {str(e)}")


def main():
    """主函数"""
    logger.info("快速端到端图工作流测试")
    print("🧪 快速端到端图工作流测试")
    print("=" * 60)
    print("⚡ 优化配置:")
    print("  - 减少搜索查询数量")
    print("  - 简化测试主题")
    print("  - 精简日志输出")
    print("=" * 60)

    import asyncio
    success = asyncio.run(test_graph_fast())

    if success:
        logger.info("快速测试完成")
        print("\n✅ 快速测试完成!")
    else:
        logger.error("快速测试失败")
        print("\n❌ 快速测试失败!")


if __name__ == "__main__":
    main()
