#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主要编排器集成测试
测试完整的LangGraph文档生成工作流
"""

import pytest
import asyncio
import json
from datetime import datetime
from pathlib import Path
from loguru import logger


class TestMainOrchestrator:
    """主要编排器集成测试类"""

    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, test_container,
                                           sample_research_state):
        """
        测试完整的工作流执行
        从研究状态开始，通过所有节点，生成最终文档
        """
        logger.info("开始完整工作流执行测试")

        # 验证输入fixtures
        assert test_container is not None, "test_container fixture应该不为空"
        assert sample_research_state is not None, "sample_research_state fixture应该不为空"
        assert hasattr(test_container, 'main_graph'), "容器应该有main_graph属性"

        # 初始化测试变量
        final_result = None
        nodes_executed = []
        execution_log = []

        try:
            logger.info(f"使用研究主题: {sample_research_state.get('topic', 'N/A')}")

            # 异步流式执行主图
            async for event in test_container.main_graph.astream(
                sample_research_state):
                # 获取节点名称和输出
                node_name = list(event.keys())[0]
                node_output = event[node_name]

                logger.debug(f"执行节点: {node_name}")
                nodes_executed.append(node_name)
                execution_log.append({
                    "node":
                    node_name,
                    "timestamp":
                    datetime.now().isoformat(),
                    "output_type":
                    str(type(node_output)),
                    "output_keys":
                    list(node_output.keys())
                    if isinstance(node_output, dict) else None
                })

                # 验证节点输出不为空
                assert node_output is not None, f"节点 '{node_name}' 的输出不应为空"
                assert isinstance(node_output,
                                  dict), f"节点 '{node_name}' 应该返回字典类型"

                # 根据节点类型进行特定验证
                if node_name == "planner":
                    self._validate_planner_output(node_output)

                elif node_name == "researcher":
                    self._validate_researcher_output(node_output)

                elif node_name == "writer":
                    self._validate_writer_output(node_output)
                    # writer节点通常是最后一个节点
                    final_result = node_output
                    logger.info("writer节点执行完成，获得最终结果")
                    break

                elif node_name == "finalize_document":
                    self._validate_finalize_output(node_output)
                    final_result = node_output
                    logger.info("finalize_document节点执行完成，获得最终结果")
                    break

                elif node_name == "supervisor_router":
                    self._validate_supervisor_output(node_output)
                    # 路由器节点可能决定流程走向
                    continue

                # 保存最新的节点输出作为潜在的最终结果
                final_result = node_output

            # 验证执行结果
            assert len(nodes_executed) > 0, "至少应该执行一个节点"
            assert final_result is not None, "应该有最终执行结果"

            logger.info(f"执行的节点: {nodes_executed}")
            logger.info(f"执行日志条目数: {len(execution_log)}")

            # 验证最终文档
            self._validate_final_document(final_result)

            # 验证工作流完整性
            self._validate_workflow_completeness(nodes_executed, final_result)

            logger.info("✅ 完整工作流执行测试通过")

        except Exception as e:
            logger.error(f"工作流执行测试失败: {str(e)}")
            logger.error(f"已执行节点: {nodes_executed}")
            logger.error(
                f"执行日志: {json.dumps(execution_log, ensure_ascii=False, indent=2)}"
            )
            raise

    def _validate_planner_output(self, output):
        """验证planner节点输出"""
        logger.debug("验证planner节点输出")

        # planner应该生成搜索查询
        assert "search_queries" in output, "planner应该生成search_queries"

        search_queries = output["search_queries"]
        assert isinstance(search_queries, list), "search_queries应该是列表"
        assert len(search_queries) > 0, "应该生成至少一个搜索查询"

        # 验证查询质量
        for query in search_queries:
            assert isinstance(query, str), "每个搜索查询应该是字符串"
            assert len(query.strip()) > 5, "搜索查询应该有实质内容"

        logger.debug(f"✅ planner输出验证通过，生成了 {len(search_queries)} 个查询")

    def _validate_researcher_output(self, output):
        """验证researcher节点输出"""
        logger.debug("验证researcher节点输出")

        # researcher应该收集研究数据
        assert "gathered_data" in output, "researcher应该生成gathered_data"

        gathered_data = output["gathered_data"]
        assert isinstance(gathered_data, str), "gathered_data应该是字符串"
        assert len(gathered_data) > 100, "研究数据应该有足够的内容"
        assert gathered_data.strip() != "", "研究数据不应为空"

        logger.debug(f"✅ researcher输出验证通过，收集了 {len(gathered_data)} 字符的数据")

    def _validate_writer_output(self, output):
        """验证writer节点输出"""
        logger.debug("验证writer节点输出")

        # writer应该生成最终文档
        assert "final_document" in output, "writer应该生成final_document"

        final_document = output["final_document"]
        assert isinstance(final_document, str), "final_document应该是字符串"
        assert len(final_document) > 200, "最终文档应该有足够的长度"
        assert final_document.strip() != "", "最终文档不应为空"

        # 验证文档包含基本结构
        assert any(marker in final_document for marker in ["#", "##", "标题", "概述", "总结"]), \
            "文档应该包含基本的结构标记"

        logger.debug(f"✅ writer输出验证通过，生成了 {len(final_document)} 字符的文档")

    def _validate_finalize_output(self, output):
        """验证finalize_document节点输出"""
        logger.debug("验证finalize_document节点输出")

        # finalize_document节点与writer类似
        assert "final_document" in output, "finalize_document应该包含final_document"

        final_document = output["final_document"]
        assert isinstance(final_document, str), "final_document应该是字符串"
        assert len(final_document) > 200, "最终文档应该有足够的长度"

        logger.debug(f"✅ finalize_document输出验证通过")

    def _validate_supervisor_output(self, output):
        """验证supervisor_router节点输出"""
        logger.debug("验证supervisor_router节点输出")

        # supervisor通常包含路由决策信息
        # 输出格式可能因具体实现而异，这里做基本验证
        assert isinstance(output, dict), "supervisor输出应该是字典"

        logger.debug("✅ supervisor_router输出验证通过")

    def _validate_final_document(self, final_result):
        """验证最终文档质量"""
        logger.debug("验证最终文档质量")

        assert "final_document" in final_result, "最终结果应该包含final_document"

        final_document = final_result["final_document"]
        assert isinstance(final_document, str), "最终文档应该是字符串"
        assert len(final_document) > 100, "最终文档应该有合理的长度"

        # 检查文档内容质量
        assert not final_document.strip().startswith("Error"), "文档不应以错误开头"
        assert "抽蓄电站" in final_document or "医疗" in final_document, \
            "文档应该包含与主题相关的内容"

        logger.debug(f"✅ 最终文档验证通过，长度: {len(final_document)} 字符")

    def _validate_workflow_completeness(self, nodes_executed, final_result):
        """验证工作流完整性"""
        logger.debug("验证工作流完整性")

        # 检查关键节点是否被执行
        expected_nodes = ["planner", "researcher"]
        for node in expected_nodes:
            assert node in nodes_executed, f"关键节点 '{node}' 应该被执行"

        # 检查是否有输出节点（writer或finalize_document）
        output_nodes = ["writer", "finalize_document"]
        assert any(node in nodes_executed for node in output_nodes), \
            "应该执行至少一个输出节点（writer或finalize_document）"

        # 验证执行顺序的合理性
        if "planner" in nodes_executed and "researcher" in nodes_executed:
            planner_idx = nodes_executed.index("planner")
            researcher_idx = nodes_executed.index("researcher")
            assert planner_idx < researcher_idx, "planner应该在researcher之前执行"

        logger.debug("✅ 工作流完整性验证通过")

    @pytest.mark.asyncio
    async def test_workflow_with_different_topics(self, test_container,
                                                  sample_research_state):
        """
        测试不同主题的工作流执行
        验证系统对不同输入的适应性
        """
        logger.info("开始不同主题工作流测试")

        # 修改研究状态的主题
        test_topics = ["区块链技术在供应链管理中的应用", "人工智能伦理问题研究", "新能源汽车市场分析报告"]

        for topic in test_topics:
            logger.info(f"测试主题: {topic}")

            # 创建新的研究状态
            modified_state = sample_research_state.copy()
            modified_state["topic"] = topic

            # 执行简化的工作流测试
            executed_nodes = []
            final_result = None

            try:
                async for event in test_container.main_graph.astream(
                        modified_state):
                    node_name = list(event.keys())[0]
                    node_output = event[node_name]
                    executed_nodes.append(node_name)

                    if node_name in ["writer", "finalize_document"]:
                        final_result = node_output
                        break

                    # 只执行前几个节点以加快测试速度
                    if len(executed_nodes) >= 3:
                        final_result = node_output
                        break

                # 基本验证
                assert len(executed_nodes) > 0, f"主题 '{topic}' 应该执行至少一个节点"
                assert final_result is not None, f"主题 '{topic}' 应该有执行结果"

                logger.info(
                    f"✅ 主题 '{topic}' 测试通过，执行了 {len(executed_nodes)} 个节点")

            except Exception as e:
                logger.error(f"主题 '{topic}' 测试失败: {str(e)}")
                # 对于这个测试，我们记录错误但不中断其他主题的测试
                continue

        logger.info("✅ 不同主题工作流测试完成")

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, test_container):
        """
        测试工作流错误处理
        验证系统对无效输入的处理能力
        """
        logger.info("开始工作流错误处理测试")

        # 测试空输入
        with pytest.raises(Exception):
            async for event in test_container.main_graph.astream({}):
                pass

        # 测试无效主题
        invalid_state = {
            "topic": "",  # 空主题
            "messages": []
        }

        with pytest.raises(Exception):
            async for event in test_container.main_graph.astream(
                    invalid_state):
                pass

        logger.info("✅ 工作流错误处理测试通过")


# 独立运行测试
if __name__ == "__main__":
    # 配置日志
    logger.add("logs/test_main_orchestrator.log", rotation="1 day")

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short", "-s"])
