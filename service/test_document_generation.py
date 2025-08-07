#!/usr/bin/env python3
"""
测试改进后的文档生成功能
"""

import asyncio
import json
import requests
from doc_agent.core.logger import logger

# 测试配置
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_OUTLINE = {
    "title":
    "人工智能技术发展趋势",
    "nodes": [{
        "id": "node_1",
        "title": "人工智能概述",
        "content_summary": "介绍人工智能的基本概念、发展历史和核心原理"
    }, {
        "id": "node_2",
        "title": "核心技术发展",
        "content_summary": "详细分析机器学习、深度学习、自然语言处理等核心技术的最新进展"
    }, {
        "id": "node_3",
        "title": "应用领域拓展",
        "content_summary": "探讨AI在医疗、金融、教育、制造等领域的应用现状和前景"
    }]
}


async def test_document_generation():
    """测试文档生成功能"""
    logger.info("开始测试文档生成功能")

    # 1. 测试文档生成请求
    request_data = {
        "jobId": "test_job_001",  # 添加必需的job_id字段
        "outlineJson": json.dumps(TEST_OUTLINE, ensure_ascii=False),
        "sessionId": "test_session_001"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/jobs/document-from-outline",
                                 json=request_data,
                                 headers={"Content-Type": "application/json"})

        if response.status_code == 202:
            result = response.json()
            task_id = result.get("redisStreamKey")  # 使用正确的别名
            session_id = result.get("sessionId")  # 使用正确的别名

            logger.success(f"文档生成任务已提交")
            logger.info(f"Task ID: {task_id}")
            logger.info(f"Session ID: {session_id}")

            # 2. 监控任务状态
            await monitor_task_progress(task_id)

        else:
            logger.error(f"请求失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")

    except Exception as e:
        logger.error(f"测试失败: {e}")


async def monitor_task_progress(task_id: str):
    """监控任务进度"""
    logger.info(f"开始监控任务进度: {task_id}")

    # 这里可以添加Redis Stream监控逻辑
    # 暂时使用简单的等待
    import time
    for i in range(30):  # 最多等待30秒
        logger.info(f"等待任务完成... ({i+1}/30)")
        await asyncio.sleep(1)

    logger.info("任务监控完成")


def test_mock_document_generation():
    """测试模拟文档生成功能"""
    logger.info("开始测试模拟文档生成功能")

    request_data = {
        "jobId": "test_mock_job_001",  # 添加必需的job_id字段
        "outlineJson": json.dumps(TEST_OUTLINE, ensure_ascii=False),
        "sessionId": "test_mock_session_001"
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/jobs/document-from-outline-mock",
            json=request_data,
            headers={"Content-Type": "application/json"})

        if response.status_code == 202:
            result = response.json()
            task_id = result.get("redisStreamKey")  # 使用正确的别名
            session_id = result.get("sessionId")  # 使用正确的别名

            logger.success(f"模拟文档生成任务已提交")
            logger.info(f"Task ID: {task_id}")
            logger.info(f"Session ID: {session_id}")

        else:
            logger.error(f"模拟请求失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")

    except Exception as e:
        logger.error(f"模拟测试失败: {e}")


if __name__ == "__main__":
    logger.info("=== 文档生成功能测试 ===")

    # 测试模拟功能
    test_mock_document_generation()

    # 测试真实功能
    asyncio.run(test_document_generation())

    logger.info("测试完成")
