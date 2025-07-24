#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API端点测试
测试创建上下文和作业的API端点，以及大纲交互端点
"""

import pytest
import asyncio
import httpx
from loguru import logger
from service.api.main import app


class TestAPIEndpoints:
    """API端点测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return httpx.AsyncClient(app=app, base_url="http://test")

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查端点"""
        logger.info("测试健康检查端点")

        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "运行中"

        # 测试API健康检查
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_create_context(self, client):
        """测试创建上下文端点"""
        logger.info("测试创建上下文端点")

        # 准备测试数据
        test_data = {
            "files": [{
                "file_id": "test-file-123",
                "file_name": "test_document.pdf",
                "storage_url": "s3://bucket/test_document.pdf"
            }]
        }

        # 发送POST请求
        response = await client.post("/api/v1/contexts", json=test_data)

        # 验证响应
        assert response.status_code == 202  # HTTP_202_ACCEPTED
        data = response.json()

        assert "context_id" in data
        assert data["context_id"].startswith("ctx-")
        assert data["status"] == "PENDING"

        logger.info(f"创建上下文成功: {data['context_id']}")

    @pytest.mark.asyncio
    async def test_create_job_without_context(self, client):
        """测试创建作业端点（不关联上下文）"""
        logger.info("测试创建作业端点（不关联上下文）")

        # 准备测试数据
        test_data = {"task_prompt": "写一篇关于人工智能发展趋势的报告"}

        # 发送POST请求
        response = await client.post("/api/v1/jobs", json=test_data)

        # 验证响应
        assert response.status_code == 201  # HTTP_201_CREATED
        data = response.json()

        assert "job_id" in data
        assert data["job_id"].startswith("job-")
        assert data["status"] == "CREATED"
        assert "created_at" in data

        logger.info(f"创建作业成功: {data['job_id']}")
        return data["job_id"]  # 返回job_id供后续测试使用

    @pytest.mark.asyncio
    async def test_create_job_with_context(self, client):
        """测试创建作业端点（关联上下文）"""
        logger.info("测试创建作业端点（关联上下文）")

        # 准备测试数据
        test_data = {
            "context_id": "ctx-test123",
            "task_prompt": "基于上传的文档，生成一份分析报告"
        }

        # 发送POST请求
        response = await client.post("/api/v1/jobs", json=test_data)

        # 验证响应
        assert response.status_code == 201  # HTTP_201_CREATED
        data = response.json()

        assert "job_id" in data
        assert data["job_id"].startswith("job-")
        assert data["status"] == "CREATED"
        assert "created_at" in data

        logger.info(f"创建关联上下文的作业成功: {data['job_id']}")

    @pytest.mark.asyncio
    async def test_outline_workflow(self, client):
        """测试完整的大纲工作流"""
        logger.info("测试完整的大纲工作流")

        # 1. 先创建一个作业
        job_data = {"task_prompt": "写一篇关于机器学习基础知识的教程"}

        job_response = await client.post("/api/v1/jobs", json=job_data)
        assert job_response.status_code == 201
        job_id = job_response.json()["job_id"]
        logger.info(f"创建作业成功: {job_id}")

        # 2. 触发大纲生成
        outline_trigger_response = await client.post(
            f"/api/v1/jobs/{job_id}/outline")
        assert outline_trigger_response.status_code == 202

        trigger_data = outline_trigger_response.json()
        assert trigger_data["job_id"] == job_id
        assert trigger_data["outline_status"] == "GENERATING"
        logger.info("大纲生成已触发")

        # 3. 等待大纲生成完成（在实际应用中可能需要轮询）
        # 这里等待足够长时间让模拟任务完成
        await asyncio.sleep(10)

        # 4. 获取生成的大纲
        outline_get_response = await client.get(
            f"/api/v1/jobs/{job_id}/outline")
        assert outline_get_response.status_code == 200

        outline_data = outline_get_response.json()
        assert outline_data["job_id"] == job_id
        assert outline_data["outline_status"] == "READY"
        assert outline_data["outline"] is not None
        assert "title" in outline_data["outline"]
        assert "nodes" in outline_data["outline"]
        logger.info("成功获取生成的大纲")

        # 5. 更新大纲并触发最终生成
        updated_outline = {
            "outline": {
                "title":
                "机器学习基础教程（用户修改版）",
                "nodes": [{
                    "id": "node_1_updated",
                    "title": "机器学习概述（已修改）",
                    "content_summary": "介绍机器学习的基本概念和发展历史",
                    "children": []
                }, {
                    "id": "node_2_updated",
                    "title": "核心算法详解（已修改）",
                    "content_summary": "深入讲解常用的机器学习算法",
                    "children": []
                }]
            }
        }

        outline_update_response = await client.put(
            f"/api/v1/jobs/{job_id}/outline", json=updated_outline)
        assert outline_update_response.status_code == 200

        update_data = outline_update_response.json()
        assert update_data["job_id"] == job_id
        assert "message" in update_data
        logger.info("大纲更新成功，最终文档生成已开始")

    @pytest.mark.asyncio
    async def test_outline_not_found(self, client):
        """测试获取不存在作业的大纲"""
        logger.info("测试获取不存在作业的大纲")

        fake_job_id = "job-nonexistent"
        response = await client.get(f"/api/v1/jobs/{fake_job_id}/outline")

        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_outline_not_found(self, client):
        """测试为不存在的作业生成大纲"""
        logger.info("测试为不存在的作业生成大纲")

        fake_job_id = "job-nonexistent"
        response = await client.post(f"/api/v1/jobs/{fake_job_id}/outline")

        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_outline_not_found(self, client):
        """测试更新不存在作业的大纲"""
        logger.info("测试更新不存在作业的大纲")

        fake_job_id = "job-nonexistent"
        test_outline = {"outline": {"title": "测试大纲", "nodes": []}}

        response = await client.put(f"/api/v1/jobs/{fake_job_id}/outline",
                                    json=test_outline)

        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_context_validation_error(self, client):
        """测试创建上下文的验证错误"""
        logger.info("测试创建上下文的验证错误")

        # 发送无效数据
        invalid_data = {
            "files": []  # 空文件列表
        }

        response = await client.post("/api/v1/contexts", json=invalid_data)

        # 空文件列表应该能创建成功，但让我们测试缺少必需字段的情况
        incomplete_data = {
            "files": [{
                "file_id": "test-123"
                # 缺少file_name和storage_url
            }]
        }

        response = await client.post("/api/v1/contexts", json=incomplete_data)
        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_create_job_validation_error(self, client):
        """测试创建作业的验证错误"""
        logger.info("测试创建作业的验证错误")

        # 缺少必需字段
        invalid_data = {}

        response = await client.post("/api/v1/jobs", json=invalid_data)
        assert response.status_code == 422  # 验证错误


# 独立运行测试的主函数
if __name__ == "__main__":
    import sys
    import os

    # 添加项目根目录到路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 配置日志
    logger.add("logs/test_api_endpoints.log", rotation="1 day")

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
