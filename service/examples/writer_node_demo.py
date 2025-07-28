#!/usr/bin/env python3
"""
演示writer_node的文档生成功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent.parent  # service 目录
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.config import settings
from src.doc_agent.graph.nodes import writer_node
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.llm_clients.providers import InternalLLMClient


def test_writer_node():
    """测试writer_node的文档生成功能"""

    print("🚀 开始测试writer_node文档生成功能...")

    # 创建测试状态
    state = ResearchState()
    state["topic"] = "电力系统运行与维护"
    state["research_plan"] = """
研究计划：
1. 了解电力系统的基本概念和组成部分
2. 收集电力系统运行的相关标准和规范
3. 研究电力系统维护的最佳实践
4. 分析电力系统故障处理的方法
5. 总结电力系统安全运行的关键要素
"""
    state["gathered_data"] = """
=== 搜索查询 1: 电力系统运行 ===

知识库搜索结果:
搜索查询: 电力系统
找到 3 个相关文档:

1. 电力行业词汇 第9部分电网调度.pdf
   评分: 26.775
   原始内容: 电力系统过负荷 电力系统恢复状态 电力系统监视控制 电力系统紧急状态 电力系统经济调度控制 电力系统警戒状态 电力系统频率崩溃 电力系统频率调整 电力系统频率异常运行 电力系统日调度计划 电力系统实时负荷预测 电力系统同步相量测量 电力系统瓦解 电力系统稳定控制...

=== 搜索查询 2: 变电站设备维护 ===

知识库搜索结果:
搜索查询: 变电站
找到 3 个相关文档:

1. 城市电力网规划设计导则.pdf
   评分: 23.612
   原始内容: 变电站甲 变电站乙 变电站丙 图 B3a 电缆线路支接三个变电站(两侧电源, 两台变) 变电站甲 变电站乙 变电站丙 图 B3b 电缆线路支接三个变电站(两侧电源, 三台变) 变电站甲 变电站乙 图 B4 高压电缆线路链式接线...

=== 搜索查询 3: 输电线路故障处理 ===

知识库搜索结果:
搜索查询: 输电
找到 3 个相关文档:

1. 电力行业词汇 第7部分 输电系统.pdf
   评分: 25.814
   原始内容: *DL/T 1033.7-2006 直流高电压发生器 直流隔离开关 直流接地开关 直流绝缘子 直流石墨化 直流输电 直流输电潮流反转控制 直流输电电缆线路 直流输电功率控制 直流输电架空线路 直流输电接地 电极 直流输电接地极线路 直流输电接地极引线 直流输电控制...
"""

    # 创建LLM客户端
    llm_config = settings.supported_models.get("qwen_2_5_235b_a22b")
    if not llm_config:
        raise ValueError("❌ 没有找到qwen_2_5_235b_a22b配置，请检查配置文件")

    print(f"✅ 使用模型: {llm_config.model_id}")
    print(f"✅ API地址: {llm_config.url}")

    llm_client = InternalLLMClient(base_url=llm_config.url,
                                   api_key=llm_config.api_key,
                                   model_name=llm_config.model_id)

    print(f"📝 测试主题: {state['topic']}")
    print(f"📊 研究计划长度: {len(state['research_plan'])} 字符")
    print(f"📊 收集数据长度: {len(state['gathered_data'])} 字符")
    print("=" * 60)

    # 执行writer_node
    try:
        result = writer_node(state, llm_client)

        print("\n" + "=" * 60)
        print("📄 生成的文档:")
        print("=" * 60)

        final_document = result.get("final_document", "")
        print(f"文档长度: {len(final_document)} 字符")
        print("\n" + final_document)

        # 分析结果
        if "电力系统" in final_document and "变电站" in final_document:
            print("\n✅ 文档生成成功，内容相关且结构良好")
        elif "文档生成错误" in final_document:
            print("\n⚠️  文档生成过程中出现错误")
        else:
            print("\n❌ 文档生成可能存在问题")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    success = test_writer_node()

    if success:
        print("\n🎉 测试完成！")
    else:
        print("\n⚠️  测试失败！")


if __name__ == "__main__":
    main()
