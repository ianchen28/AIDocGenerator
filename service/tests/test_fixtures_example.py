#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixtures使用示例测试
演示如何使用conftest.py中定义的各种fixtures
"""

import pytest
from loguru import logger


class TestFixturesExample:
    """展示fixtures使用的示例测试类"""

    def test_container_fixture(self, test_container):
        """测试container fixture"""
        logger.info("测试Container fixture")

        # 验证container存在
        assert test_container is not None

        # 验证container有必要的属性
        assert hasattr(test_container, 'llm_client')
        assert hasattr(test_container, 'main_graph')

        logger.info("✅ Container fixture测试通过")

    def test_research_state_fixture(self, sample_research_state):
        """测试研究状态fixture"""
        logger.info("测试ResearchState fixture")

        # 验证必要字段存在
        assert "topic" in sample_research_state
        assert "initial_gathered_data" in sample_research_state
        assert "document_outline" in sample_research_state
        assert "messages" in sample_research_state

        # 验证数据类型
        assert isinstance(sample_research_state["topic"], str)
        assert isinstance(sample_research_state["messages"], list)
        assert isinstance(sample_research_state["document_outline"], dict)

        # 验证具体内容
        assert sample_research_state["topic"] == "人工智能在医疗诊断中的应用"
        assert len(sample_research_state["initial_gathered_data"]) > 100

        logger.info("✅ ResearchState fixture测试通过")

    def test_outline_fixture(self, sample_outline):
        """测试大纲fixture"""
        logger.info("测试Outline fixture")

        # 验证大纲结构
        assert "title" in sample_outline
        assert "nodes" in sample_outline

        # 验证节点结构
        assert isinstance(sample_outline["nodes"], list)
        assert len(sample_outline["nodes"]) > 0

        # 验证第一个节点的结构
        first_node = sample_outline["nodes"][0]
        assert "id" in first_node
        assert "title" in first_node
        assert "content_summary" in first_node
        assert "children" in first_node

        logger.info("✅ Outline fixture测试通过")

    def test_job_data_fixture(self, sample_job_data):
        """测试作业数据fixture"""
        logger.info("测试Job Data fixture")

        # 验证作业数据结构
        required_fields = ["job_id", "task_prompt", "status", "created_at"]
        for field in required_fields:
            assert field in sample_job_data

        # 验证ID格式
        assert sample_job_data["job_id"].startswith("job-")
        assert sample_job_data["status"] == "CREATED"

        logger.info("✅ Job Data fixture测试通过")

    def test_context_data_fixture(self, sample_context_data):
        """测试上下文数据fixture"""
        logger.info("测试Context Data fixture")

        # 验证上下文数据结构
        assert "context_id" in sample_context_data
        assert "files" in sample_context_data
        assert "status" in sample_context_data

        # 验证文件列表
        files = sample_context_data["files"]
        assert isinstance(files, list)
        assert len(files) > 0

        # 验证文件结构
        first_file = files[0]
        file_fields = ["file_id", "file_name", "storage_url"]
        for field in file_fields:
            assert field in first_file

        logger.info("✅ Context Data fixture测试通过")

    def test_redis_data_fixture(self, mock_redis_data):
        """测试Redis数据fixture"""
        logger.info("测试Redis Data fixture")

        # 验证Redis数据结构
        assert isinstance(mock_redis_data, dict)

        # 验证作业键存在
        job_key = "job:job-test123456"
        assert job_key in mock_redis_data

        # 验证大纲键存在
        outline_key = "job:job-test123456:outline"
        assert outline_key in mock_redis_data

        # 验证文档键存在
        document_key = "job:job-test123456:document"
        assert document_key in mock_redis_data

        logger.info("✅ Redis Data fixture测试通过")

    def test_api_requests_fixture(self, sample_api_requests):
        """测试API请求数据fixture"""
        logger.info("测试API Requests fixture")

        # 验证API请求结构
        expected_requests = ["create_context", "create_job", "update_outline"]
        for request_type in expected_requests:
            assert request_type in sample_api_requests

        # 验证create_context请求
        create_context = sample_api_requests["create_context"]
        assert "files" in create_context
        assert isinstance(create_context["files"], list)

        # 验证create_job请求
        create_job = sample_api_requests["create_job"]
        assert "task_prompt" in create_job
        assert "context_id" in create_job

        # 验证update_outline请求
        update_outline = sample_api_requests["update_outline"]
        assert "outline" in update_outline
        assert "title" in update_outline["outline"]
        assert "nodes" in update_outline["outline"]

        logger.info("✅ API Requests fixture测试通过")

    def test_combined_fixtures_usage(self, sample_research_state,
                                     sample_outline, mock_redis_data):
        """测试组合使用多个fixtures"""
        logger.info("测试组合使用多个fixtures")

        # 模拟一个完整的测试场景
        topic = sample_research_state["topic"]
        outline_title = sample_outline["title"]
        redis_job_data = mock_redis_data["job:job-test123456"]

        # 验证数据一致性和完整性
        assert isinstance(topic, str)
        assert isinstance(outline_title, str)
        assert isinstance(redis_job_data, dict)

        # 验证可以正常处理这些数据
        combined_data = {
            "research_topic": topic,
            "outline_title": outline_title,
            "job_status": redis_job_data.get("status", "unknown")
        }

        assert combined_data["research_topic"] != ""
        assert combined_data["outline_title"] != ""
        assert combined_data["job_status"] != ""

        logger.info("✅ 组合fixtures使用测试通过")


# 单独运行测试
if __name__ == "__main__":
    # 配置日志
    logger.add("logs/test_fixtures_example.log", rotation="1 day")

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
