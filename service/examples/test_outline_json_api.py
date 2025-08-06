#!/usr/bin/env python3
"""
测试outline JSON API端点的脚本
"""

import json
import requests
from loguru import logger

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


def test_outline_json_api():
    """测试从outline JSON生成文档的API端点"""

    # 示例outline JSON
    outline_json = {
        "title":
        "人工智能技术发展报告",
        "nodes": [{
            "id": "node_1",
            "title": "引言",
            "content_summary": "介绍人工智能的基本概念和发展背景"
        }, {
            "id": "node_2",
            "title": "人工智能发展历史",
            "content_summary": "从图灵测试到深度学习的演进历程"
        }, {
            "id": "node_3",
            "title": "当前技术现状",
            "content_summary": "机器学习、深度学习、自然语言处理等技术的现状"
        }, {
            "id": "node_4",
            "title": "未来发展趋势",
            "content_summary": "AI技术的未来发展方向和挑战"
        }]
    }

    # 准备请求数据
    request_data = {
        "job_id": "test_outline_json_001",
        "outline_json": json.dumps(outline_json, ensure_ascii=False),
        "session_id": "session_001"
    }

    logger.info("开始测试outline JSON API端点")
    logger.info(f"请求URL: {BASE_URL}/jobs/document-from-outline")
    logger.info(
        f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        # 发送POST请求
        response = requests.post(f"{BASE_URL}/jobs/document-from-outline",
                                 json=request_data,
                                 headers={"Content-Type": "application/json"})

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")

        if response.status_code == 202:
            logger.success("✅ API端点测试成功！任务已提交")
            result = response.json()
            logger.info(f"任务ID: {result.get('job_id')}")
        else:
            logger.error(f"❌ API端点测试失败，状态码: {response.status_code}")
            logger.error(f"错误信息: {response.text}")

    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")


def test_health_check():
    """测试健康检查端点"""
    try:
        response = requests.get("http://localhost:8000/")
        logger.info(f"健康检查响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 开始测试outline JSON API功能")

    # 首先测试健康检查
    if test_health_check():
        logger.info("✅ 服务器连接正常")
        # 测试outline JSON API
        test_outline_json_api()
    else:
        logger.error("❌ 服务器连接失败，请先启动服务器")
