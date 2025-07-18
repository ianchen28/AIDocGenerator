#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端图工作流测试脚本
运行完整的文档生成流程并显示每个步骤的输出
"""

import sys
import os
import pprint
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 设置日志级别为DEBUG
os.environ['LOGGING_LEVEL'] = 'DEBUG'

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

# 重新配置日志级别为DEBUG（确保在环境设置后生效）
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG",
    format=
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    colorize=True)

from core.container import Container


def setup_output_dir():
    """设置输出目录"""
    logger.debug("设置输出目录")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # 创建带时间戳的子目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"test_session_{timestamp}"
    session_dir.mkdir(exist_ok=True)

    logger.debug(f"输出目录已设置: {session_dir}")
    return session_dir


def save_log(session_dir: Path, content: str, filename: str):
    """保存日志内容到文件"""
    log_file = session_dir / filename
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"日志已保存到: {log_file}")


def save_document(session_dir: Path, document: str, topic: str):
    """保存生成的文档"""
    logger.debug(f"保存文档，主题: {topic}")
    # 清理文件名中的特殊字符
    safe_topic = "".join(c for c in topic
                         if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_topic = safe_topic.replace(' ', '_')[:50]  # 限制长度

    doc_file = session_dir / f"{safe_topic}.md"
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(document)
    logger.info(f"文档已保存到: {doc_file}")


async def test_graph():
    """测试图流程"""
    logger.info("开始端到端测试")

    # 设置输出目录
    session_dir = setup_output_dir()
    logger.info(f"输出目录: {session_dir}")

    # 初始化日志内容
    log_content = []
    final_document = None
    topic = None

    def log(message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        logger.info(log_entry)
        log_content.append(log_entry)

    # 获取容器
    logger.debug("初始化容器")
    container = Container()

    try:
        # 创建初始状态
        initial_state = {"topic": "抽蓄电站可行性研究报告", "search_queries": []}

        topic = initial_state["topic"]
        logger.debug(
            f"初始状态: {json.dumps(initial_state, ensure_ascii=False, indent=2)}")
        log(f"📋 初始状态: {json.dumps(initial_state, ensure_ascii=False, indent=2)}"
            )

        # 流式执行图
        logger.info("开始流式执行图")
        async for event in container.main_graph.astream(initial_state):
            node_name = list(event.keys())[0]
            node_output = event[node_name]

            logger.debug(f"执行节点: {node_name}")
            logger.debug(f"节点输出类型: {type(node_output)}")
            log(f"\n🔍 节点: {node_name}")
            log(f"📊 输出类型: {type(node_output)}")

            if node_name == "planner":
                search_queries = node_output.get('search_queries', [])
                logger.debug(
                    f"搜索查询: {json.dumps(search_queries, ensure_ascii=False, indent=2)}"
                )
                log(f"📝 搜索查询: {json.dumps(search_queries, ensure_ascii=False, indent=2)}"
                    )

            elif node_name == "researcher":
                gathered_data = node_output.get('gathered_data', '')
                logger.debug(f"收集数据长度: {len(gathered_data)} 字符")
                logger.debug(f"数据预览: {gathered_data[:200]}...")
                log(f"📚 收集数据长度: {len(gathered_data)} 字符")
                log(f"📖 数据预览: {gathered_data[:200]}...")

                # 保存详细的研究数据
                research_file = session_dir / "research_data.txt"
                with open(research_file, 'w', encoding='utf-8') as f:
                    f.write(gathered_data)
                logger.info(f"研究数据已保存到: {research_file}")
                log(f"💾 研究数据已保存到: {research_file}")

            elif node_name == "writer":
                final_document = node_output.get('final_document', '')
                logger.debug(f"生成文档长度: {len(final_document)} 字符")
                logger.debug(f"文档预览: {final_document[:200]}...")
                log(f"📄 生成文档长度: {len(final_document)} 字符")
                log(f"📖 文档预览: {final_document[:200]}...")
                log("🛑 writer 节点执行完毕，流程应终止，停止遍历")
                break

            elif node_name == "supervisor_router":
                logger.debug(
                    f"路由决策: {json.dumps(node_output, ensure_ascii=False, indent=2)}"
                )
                log(f"🎯 路由决策: {json.dumps(node_output, ensure_ascii=False, indent=2)}"
                    )
                log("🛑 supervisor_router 节点后停止执行")
                break

            elif node_name == "finalize_document":
                final_document = node_output.get('final_document', '')
                logger.debug(f"最终文档生成完成，长度: {len(final_document)} 字符")
                logger.debug(f"文档预览: {final_document[:200]}...")
                log(f"📄 最终文档生成完成，长度: {len(final_document)} 字符")
                log(f"📖 文档预览: {final_document[:200]}...")
                log("🛑 finalize_document 节点执行完毕，流程完成")
                break

            log("-" * 50)

        # 保存最终文档
        if final_document and topic:
            save_document(session_dir, final_document, topic)

        # 保存完整日志
        log_text = "\n".join(log_content)
        save_log(session_dir, log_text, "test_log.txt")

        # 保存测试摘要
        summary = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "session_dir": str(session_dir),
            "document_length": len(final_document) if final_document else 0,
            "log_entries": len(log_content)
        }
        summary_file = session_dir / "test_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"测试摘要已保存到: {summary_file}")
        log(f"📊 测试摘要已保存到: {summary_file}")

        log("\n✅ 端到端测试完成!")
        logger.info("端到端测试完成")
        return True

    except Exception as e:
        error_msg = f"\n❌ 端到端测试失败: {str(e)}"
        logger.error(f"端到端测试失败: {str(e)}")
        log(error_msg)

        # 保存错误日志
        error_log = "\n".join(log_content) + f"\n\n错误信息: {str(e)}"
        save_log(session_dir, error_log, "error_log.txt")

        return False

    finally:
        # 清理资源
        logger.info("清理资源")
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
    logger.info("端到端图工作流测试")
    print("🧪 端到端图工作流测试")
    print("=" * 80)

    import asyncio
    success = asyncio.run(test_graph())

    if success:
        logger.info("端到端测试完成")
        print("\n✅ 端到端测试完成!")
    else:
        logger.error("端到端测试失败")
        print("\n❌ 端到端测试失败!")


if __name__ == "__main__":
    main()
