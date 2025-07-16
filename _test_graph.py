#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端图工作流测试脚本
运行完整的文档生成流程并显示每个步骤的输出
"""

import sys
import os
import pprint
from pathlib import Path

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent / "service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.env_loader import setup_environment
from service.core.container import Container


async def test_graph():
    """测试图流程"""
    print("🚀 开始端到端测试...")

    # 获取容器
    container = Container()

    # 创建初始状态
    initial_state = {
        "topic":
        "人工智能在中国电力行业的应用趋势和政策支持",
        "search_queries": [
            "人工智能 中国电力行业 应用趋势 政策支持", "电力AI 技术发展 行业报告", "深度学习 水电站 运维优化 研究进展",
            "AI+能源管理 省级电力公司 实施效果", "电力AI创业公司 技术突破 行业报告"
        ]
    }

    print(f"📋 初始状态: {initial_state}")

    # 流式执行图
    async for event in container.graph.astream(initial_state):
        node_name = list(event.keys())[0]
        node_output = event[node_name]

        print(f"\n🔍 节点: {node_name}")
        print(f"📊 输出类型: {type(node_output)}")

        if node_name == "planner":
            print(f"📝 搜索查询: {node_output.get('search_queries', [])}")
        elif node_name == "researcher":
            gathered_data = node_output.get('gathered_data', '')
            print(f"📚 收集数据长度: {len(gathered_data)} 字符")
            print(f"📖 数据预览: {gathered_data[:200]}...")
        elif node_name == "writer":
            final_document = node_output.get('final_document', '')
            print(f"📄 生成文档长度: {len(final_document)} 字符")
            print(f"📖 文档预览: {final_document[:200]}...")
            print("🛑 writer 节点执行完毕，流程应终止，停止遍历")
            break
        elif node_name == "supervisor_router":
            print(f"🎯 路由决策: {node_output}")
            print("🛑 supervisor_router 节点后停止执行")
            break

        print("-" * 50)


def main():
    """主函数"""
    print("🧪 端到端图工作流测试")
    print("=" * 80)

    import asyncio
    success = asyncio.run(test_graph())

    if success:
        print("\n✅ 端到端测试完成!")
    else:
        print("\n❌ 端到端测试失败!")


if __name__ == "__main__":
    main()
