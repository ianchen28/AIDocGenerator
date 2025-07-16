#!/usr/bin/env python3
"""
测试 supervisor_router 的 exact prompt
"""

import sys
import os

# 添加 service 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'service'))

from service.core.env_loader import setup_environment
from service.src.doc_agent.llm_clients import get_llm_client


def test_supervisor_prompt():
    """测试 supervisor_router 的 exact prompt"""
    print("🔍 开始测试 supervisor_router 的 exact prompt...")

    # 设置环境
    setup_environment()

    # 创建客户端
    llm_client = get_llm_client("qwen_2_5_235b_a22b")

    # 模拟 supervisor_router 的 prompt
    topic = "人工智能在中国电力行业的应用趋势和政策支持"
    gathered_data = "=== 搜索查询 1: 人工智能 电力行业 应用趋势 中国 ===\n\n知识库搜索结果:\n搜索查询: 人工智能 电力行业 应用趋势 中国\n找到 75 个相关文档:\n\n1. [standard_index_base] 智慧城市 人工智能技术应用场景分类指南\n   评分: 1.595\n   原始内容: *7.6 智慧能源 人工智能技术在智慧能源领域的应用主要是为能源全周期供应链提供智能化服务, 包括生产、服务和管理的智能化等,应用场景分类及描述见表 13 。 *表 13 智慧能源应用场景分类及描述" + "这是一个很长的研究资料内容。" * 2000  # 模拟长数据

    prompt = f"""**角色：** 你是一位研究主管，需要判断下方资料是否足够撰写完整文档。

**主题：**「{topic}」

**已收集的研究资料：**
{gathered_data}

**评判标准（宽松版）：**
- 如果资料包含3条或以上详细检索结果，每条都有具体内容，且总字数超过500字，则视为"充足"
- 如果只有1-2条检索，或内容过于简单（只有定义），则视为"不充足"

**重要提示：**
- 只要资料内容丰富、有多个方面、有具体信息，就应该返回FINISH
- 不要过于苛刻，资料不需要完美无缺
- 重点看是否有足够的内容来写文档

**你的决策：**
请根据上述标准判断，当前资料能否用于撰写文档？只能回答一个单词：
- "FINISH" = 资料充足，可以写文档
- "CONTINUE" = 资料不足，需要更多研究

请直接输出：FINISH 或 CONTINUE"""

    print(f"📋 Prompt 信息:")
    print(f"   Topic: {topic}")
    print(f"   Gathered data 长度: {len(gathered_data)} 字符")
    print(f"   Total prompt 长度: {len(prompt)} 字符")
    print(f"   Prompt 预览: {prompt[:200]}...")

    # 测试不同的 max_tokens 值
    max_tokens_values = [10, 100, 1000]

    for max_tokens in max_tokens_values:
        print(f"\n🧪 测试 max_tokens={max_tokens}:")
        try:
            response = llm_client.invoke(prompt,
                                         temperature=0,
                                         max_tokens=max_tokens)
            print(f"✅ 成功: {response}")
        except Exception as e:
            print(f"❌ 失败: {e}")
            # 如果是 400 错误，尝试减少 prompt 长度
            if "400" in str(e):
                print("💡 尝试减少 prompt 长度...")
                shorter_prompt = prompt[:5000] + "\n\n请直接输出：FINISH 或 CONTINUE"
                try:
                    response = llm_client.invoke(shorter_prompt,
                                                 temperature=0,
                                                 max_tokens=max_tokens)
                    print(f"✅ 短 prompt 成功: {response}")
                except Exception as e2:
                    print(f"❌ 短 prompt 也失败: {e2}")


if __name__ == "__main__":
    test_supervisor_prompt()
