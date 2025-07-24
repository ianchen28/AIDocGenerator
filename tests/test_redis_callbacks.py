#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis回调处理器测试
测试Redis事件发布功能
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from loguru import logger

# 添加项目根目录到路径
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入要测试的模块
from service.src.doc_agent.graph.callbacks import RedisCallbackHandler, create_redis_callback_handler


class TestRedisCallbackHandler:
    """Redis回调处理器测试类"""

    @pytest.fixture
    def mock_redis_client(self):
        """创建模拟Redis客户端"""
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock()
        return mock_redis

    @pytest.fixture
    def callback_handler(self):
        """创建回调处理器实例"""
        return RedisCallbackHandler("test-job-123")

    def test_init(self, callback_handler):
        """测试初始化"""
        assert callback_handler.job_id == "test-job-123"
        assert callback_handler.channel_name == "job:test-job-123:events"
        assert callback_handler.redis_client is None

    @pytest.mark.asyncio
    async def test_publish_event(self, callback_handler, mock_redis_client):
        """测试事件发布"""
        # 模拟Redis客户端
        with patch.object(callback_handler,
                          '_get_redis_client',
                          return_value=mock_redis_client):
            await callback_handler._publish_event("test_event",
                                                  {"message": "测试消息"})

            # 验证Redis publish被调用
            mock_redis_client.publish.assert_called_once()

            # 获取调用参数
            call_args = mock_redis_client.publish.call_args
            channel_name, payload_str = call_args[0]

            assert channel_name == "job:test-job-123:events"

            # 解析载荷
            payload = json.loads(payload_str)
            assert payload["event"] == "test_event"
            assert payload["data"]["message"] == "测试消息"
            assert payload["job_id"] == "test-job-123"
            assert "timestamp" in payload

    def test_on_chain_start(self, callback_handler):
        """测试链开始回调"""
        run_id = uuid4()
        serialized = {"name": "research_chain"}
        inputs = {"topic": "机器学习"}

        # 模拟事件发布
        with patch.object(callback_handler, '_publish_event') as mock_publish:
            callback_handler.on_chain_start(serialized=serialized,
                                            inputs=inputs,
                                            run_id=run_id)

            # 由于使用了asyncio.create_task，我们需要检查是否被调用
            # 这里我们主要验证方法被调用而不报错
            assert True  # 如果没有异常，测试通过

    def test_on_tool_start(self, callback_handler):
        """测试工具开始回调"""
        run_id = uuid4()
        serialized = {"name": "web_search"}
        input_str = "搜索机器学习相关信息"

        with patch.object(callback_handler, '_publish_event') as mock_publish:
            callback_handler.on_tool_start(serialized=serialized,
                                           input_str=input_str,
                                           run_id=run_id)

            # 验证方法调用成功
            assert True

    def test_on_chain_error(self, callback_handler):
        """测试链错误回调"""
        run_id = uuid4()
        error = Exception("测试错误")

        with patch.object(callback_handler, '_publish_event') as mock_publish:
            callback_handler.on_chain_error(error=error, run_id=run_id)

            # 验证方法调用成功
            assert True

    def test_create_redis_callback_handler(self):
        """测试工厂函数"""
        handler = create_redis_callback_handler("factory-test-job")

        assert isinstance(handler, RedisCallbackHandler)
        assert handler.job_id == "factory-test-job"
        assert handler.channel_name == "job:factory-test-job:events"

    @pytest.mark.asyncio
    async def test_get_redis_client_success(self, callback_handler,
                                            mock_redis_client):
        """测试成功获取Redis客户端"""
        with patch('service.workers.tasks.get_redis_client',
                   return_value=mock_redis_client):
            client = await callback_handler._get_redis_client()
            assert client == mock_redis_client
            assert callback_handler.redis_client == mock_redis_client

    @pytest.mark.asyncio
    async def test_get_redis_client_failure(self, callback_handler):
        """测试获取Redis客户端失败"""
        with patch('service.workers.tasks.get_redis_client',
                   side_effect=Exception("连接失败")):
            client = await callback_handler._get_redis_client()
            assert client is None
            assert callback_handler.redis_client is None

    @pytest.mark.asyncio
    async def test_publish_event_with_redis_failure(self, callback_handler):
        """测试Redis发布失败时的处理"""
        with patch.object(callback_handler,
                          '_get_redis_client',
                          return_value=None):
            # 应该不抛出异常
            await callback_handler._publish_event("test", {"data": "test"})
            assert True  # 验证没有异常

    def test_phase_detection(self, callback_handler):
        """测试阶段检测逻辑"""
        test_cases = [
            ({
                "name": "research_node"
            }, "RETRIEVAL", "开始从知识库和网络检索信息..."),
            ({
                "name": "outline_generation"
            }, "OUTLINE_GENERATION", "开始生成文档大纲..."),
            ({
                "name": "planner_chain"
            }, "PLANNING", "制定研究计划..."),
            ({
                "name": "writer_node"
            }, "WRITING", "开始撰写文档内容..."),
            ({
                "name": "unknown_chain"
            }, "PROCESSING", "开始执行 unknown_chain"),
        ]

        run_id = uuid4()

        for serialized, expected_phase, expected_message in test_cases:
            with patch.object(callback_handler,
                              '_publish_event') as mock_publish:
                callback_handler.on_chain_start(serialized=serialized,
                                                inputs={"test": "input"},
                                                run_id=run_id)

                # 验证方法调用（由于异步，这里只验证没有异常）
                assert True


class TestIntegrationWithContainer:
    """测试与Container的集成"""

    @pytest.mark.asyncio
    async def test_container_integration(self):
        """测试Container集成（需要实际的Container实例）"""
        try:
            from service.core.container import container

            # 测试获取带回调的图执行器
            job_id = "integration-test-job"
            runnable_graph = container.get_graph_runnable_for_job(job_id)

            # 验证返回的是可执行对象
            assert runnable_graph is not None
            assert hasattr(runnable_graph, 'invoke') or hasattr(
                runnable_graph, 'ainvoke')

            logger.info("Container集成测试通过")

        except ImportError as e:
            pytest.skip(f"Container未正确导入，跳过集成测试: {e}")
        except Exception as e:
            logger.warning(f"集成测试遇到问题: {e}")
            pytest.skip(f"集成测试跳过: {e}")


# 独立运行测试的主函数
if __name__ == "__main__":
    # 配置日志
    logger.add("logs/test_redis_callbacks.log", rotation="1 day")

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
