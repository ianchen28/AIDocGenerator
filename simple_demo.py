# demo.py
import streamlit as st
import asyncio
import logging
from service.core.container import container  # 导入你的核心容器
from service.src.doc_agent.graph.state import ResearchState  # 导入状态

# 设置日志
logger = logging.getLogger(__name__)

# --- Streamlit 页面配置 ---
st.set_page_config(page_title="智能文档生成 Demo", layout="wide")
st.title("🤖 智能文档生成系统 - 效果演示")

# --- 1. 用户输入 ---
topic = st.text_input("请输入您想生成的文档主题:", "以'人工智能在医疗领域的应用'为例，分析其现状、挑战与未来趋势")

# --- 2. Demo 模式配置 ---
is_demo_mode = st.checkbox("🚀 启用快速演示模式 (3-5分钟)", True)
if is_demo_mode:
    st.info("快速模式已启用：将减少研究深度、跳过自我修正、并生成较短的大纲。")

# --- 3. 启动按钮 ---
if st.button("开始生成文档", type="primary"):

    # --- 4. 准备图的输入 ---
    initial_state = ResearchState(
        topic=topic,
        # 其他初始状态...
        messages=[],
        initial_gathered_data="",
        document_outline={},
        chapters_to_process=[],
        current_chapter_index=0,
        completed_chapters_content=[],
        final_document="")

    # --- 5. 实时展示流程 ---
    st.markdown("---")
    st.subheader("实时生成流程追踪")

    # 创建用于显示状态和结果的占位符
    status_placeholder = st.empty()
    result_placeholder = st.empty()

    final_result = {}

    try:
        # 根据演示模式选择使用哪个图
        if is_demo_mode:
            logger.info("🚀 使用快速演示模式")
            graph_to_use = container.fast_main_graph
        else:
            logger.info("🚀 使用完整模式")
            graph_to_use = container.main_graph

        # 使用异步方法调用图
        async def run_graph():
            async for step_output in graph_to_use.astream(initial_state):
                node_name = list(step_output.keys())[0]
                node_data = list(step_output.values())[0]
                yield node_name, node_data

        # 在 Streamlit 中运行异步函数
        async def process_graph():
            async for node_name, node_data in run_graph():
                # 更新状态显示
                status_placeholder.info(f"🧠 正在执行: **{node_name}**...")

                # 可视化每个节点的输出（可选，但很酷）
                with st.expander(f"查看节点「{node_name}」的输出"):
                    st.json(node_data, expanded=False)

                # 模拟一点延迟，让用户能看清状态变化
                await asyncio.sleep(1)

                final_result.update(node_data)

        # 运行异步函数
        asyncio.run(process_graph())

    except Exception as e:
        st.error(f"生成过程中发生错误: {e}")
        st.stop()

    # --- 6. 展示最终结果 ---
    status_placeholder.success("🎉 文档生成完毕！")

    st.markdown("---")
    st.subheader("最终生成的文档")

    final_document_content = final_result.get("final_document", "未能生成最终文档。")
    st.markdown(final_document_content)
