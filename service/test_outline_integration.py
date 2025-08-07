#!/usr/bin/env python3
"""
Outline JSON集成测试脚本
测试从outline JSON到文档生成的完整流程
"""

import json
import time
import requests
from doc_agent.core.logger import logger

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


def create_test_outline():
    """创建测试用的outline数据"""
    return {
        "title":
        "人工智能技术发展报告",
        "nodes": [{
            "id": "node_1",
            "title": "引言",
            "content_summary": "介绍人工智能的基本概念和发展背景，包括AI的定义、分类和应用领域"
        }, {
            "id": "node_2",
            "title": "人工智能发展历史",
            "content_summary": "从图灵测试到深度学习的演进历程，包括关键里程碑和技术突破"
        }, {
            "id": "node_3",
            "title": "当前技术现状",
            "content_summary": "机器学习、深度学习、自然语言处理等技术的现状和发展水平"
        }, {
            "id": "node_4",
            "title": "未来发展趋势",
            "content_summary": "AI技术的未来发展方向、挑战和机遇"
        }]
    }


def test_outline_json_api():
    """测试outline JSON API端点"""
    logger.info("🚀 开始测试outline JSON API集成")

    # 创建测试数据
    outline_data = create_test_outline()
    job_id = f"test_outline_{int(time.time())}"

    # 准备请求数据
    request_data = {
        "job_id": job_id,
        "outline_json": json.dumps(outline_data, ensure_ascii=False),
        "session_id": f"session_{int(time.time())}"
    }

    logger.info(f"📋 测试数据:")
    logger.info(f"  Job ID: {job_id}")
    logger.info(f"  Outline 标题: {outline_data['title']}")
    logger.info(f"  章节数量: {len(outline_data['nodes'])}")

    try:
        # 发送POST请求
        logger.info("📤 发送API请求...")
        response = requests.post(f"{BASE_URL}/jobs/document-from-outline",
                                 json=request_data,
                                 headers={"Content-Type": "application/json"},
                                 timeout=30)

        logger.info(f"📥 收到响应:")
        logger.info(f"  状态码: {response.status_code}")
        logger.info(f"  响应内容: {response.text}")

        if response.status_code == 202:
            logger.success("✅ API端点测试成功！任务已提交")
            result = response.json()
            logger.info(f"  任务ID: {result.get('job_id')}")
            return job_id
        else:
            logger.error(f"❌ API端点测试失败，状态码: {response.status_code}")
            logger.error(f"  错误信息: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到API服务器，请确保服务器正在运行")
        return None
    except requests.exceptions.Timeout:
        logger.error("❌ 请求超时")
        return None
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return None


def test_invalid_outline():
    """测试无效的outline JSON"""
    logger.info("🧪 测试无效outline JSON处理")

    # 测试缺少title的outline
    invalid_outline = {"nodes": [{"id": "node_1", "title": "章节1"}]}

    request_data = {
        "job_id": "test_invalid_001",
        "outline_json": json.dumps(invalid_outline, ensure_ascii=False)
    }

    try:
        response = requests.post(f"{BASE_URL}/jobs/document-from-outline",
                                 json=request_data,
                                 headers={"Content-Type": "application/json"})

        if response.status_code == 400:
            logger.success("✅ 无效outline JSON被正确拒绝")
        else:
            logger.warning(
                f"⚠️  无效outline JSON未被拒绝，状态码: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ 测试无效outline时发生错误: {e}")


def test_malformed_json():
    """测试格式错误的JSON"""
    logger.info("🧪 测试格式错误的JSON处理")

    request_data = {
        "job_id":
        "test_malformed_001",
        "outline_json":
        '{"title": "测试", "nodes": [{"id": "node_1", "title": "章节1"}]'  # 缺少闭合括号
    }

    try:
        response = requests.post(f"{BASE_URL}/jobs/document-from-outline",
                                 json=request_data,
                                 headers={"Content-Type": "application/json"})

        if response.status_code == 400:
            logger.success("✅ 格式错误的JSON被正确拒绝")
        else:
            logger.warning(f"⚠️  格式错误的JSON未被拒绝，状态码: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ 测试格式错误JSON时发生错误: {e}")


def main():
    """主测试函数"""
    logger.info("🎯 开始Outline JSON API集成测试")

    # 测试健康检查
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            logger.success("✅ 服务器连接正常")
        else:
            logger.error("❌ 服务器连接异常")
            return
    except Exception as e:
        logger.error(f"❌ 无法连接到服务器: {e}")
        return

    # 测试正常流程
    job_id = test_outline_json_api()

    # 测试错误处理
    test_invalid_outline()
    test_malformed_json()

    if job_id:
        logger.success(f"🎉 集成测试完成！任务ID: {job_id}")
        logger.info("💡 你可以通过Redis流监控任务进度")
    else:
        logger.error("❌ 集成测试失败")


if __name__ == "__main__":
    main()
