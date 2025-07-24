#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding 服务可用性测试脚本
"""

import sys
import os
import json
import httpx
from pathlib import Path
from loguru import logger

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/chenyuyang/git/AIDocGenerator/service'

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent / "service"
src_dir = service_dir / "src"
for p in [str(service_dir), str(src_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.doc_agent.llm_clients.providers import EmbeddingClient
from core.config import settings


def test_embedding_service():
    """测试 Embedding 服务可用性"""
    logger.info("开始测试 Embedding 服务可用性")

    # 获取 Embedding 配置
    embedding_config = settings.supported_models.get("gte_qwen")
    if not embedding_config:
        logger.error("❌ 未找到 gte_qwen 配置")
        return False

    logger.info(f"📋 Embedding 配置:")
    logger.info(f"  - URL: {embedding_config.url}")
    logger.info(f"  - API Key: {embedding_config.api_key}")
    logger.info(f"  - Model ID: {embedding_config.model_id}")

    # 测试 1: 直接 HTTP 请求测试
    logger.info("\n🔍 测试 1: 直接 HTTP 请求测试")
    try:
        test_data = {"inputs": "测试文本", "model": "gte-qwen"}
        headers = {"Content-Type": "application/json"}

        if embedding_config.api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {embedding_config.api_key}"

        with httpx.Client(timeout=10.0) as client:
            response = client.post(embedding_config.url,
                                   json=test_data,
                                   headers=headers)

            logger.info(f"✅ HTTP 请求成功")
            logger.info(f"  - 状态码: {response.status_code}")
            logger.info(f"  - 响应头: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"  - 响应内容类型: {type(result)}")
                logger.info(f"  - 响应内容长度: {len(str(result))}")
                logger.info(f"  - 响应预览: {str(result)[:200]}...")
            else:
                logger.error(f"❌ HTTP 请求失败: {response.status_code}")
                logger.error(f"  - 响应内容: {response.text}")
                return False

    except Exception as e:
        logger.error(f"❌ HTTP 请求异常: {str(e)}")
        return False

    # 测试 2: 使用 EmbeddingClient 类测试
    logger.info("\n🔍 测试 2: 使用 EmbeddingClient 类测试")
    try:
        embedding_client = EmbeddingClient(base_url=embedding_config.url,
                                           api_key=embedding_config.api_key)

        test_text = "人工智能赋能电力行业"
        result = embedding_client.invoke(test_text)

        logger.info(f"✅ EmbeddingClient 调用成功")
        logger.info(f"  - 输入文本: {test_text}")
        logger.info(f"  - 输出类型: {type(result)}")
        logger.info(f"  - 输出长度: {len(str(result))}")
        logger.info(f"  - 输出预览: {str(result)[:200]}...")

        # 尝试解析 JSON
        try:
            parsed_result = json.loads(result)
            logger.info(f"  - JSON 解析成功")
            if isinstance(parsed_result, list):
                logger.info(
                    f"  - 向量维度: {len(parsed_result[0]) if parsed_result else 0}"
                )
            elif isinstance(parsed_result, dict):
                logger.info(f"  - 响应格式: {list(parsed_result.keys())}")
        except json.JSONDecodeError:
            logger.warning(f"⚠️ 输出不是有效的 JSON 格式")

        return True

    except Exception as e:
        logger.error(f"❌ EmbeddingClient 调用失败: {str(e)}")
        return False


def test_alternative_endpoints():
    """测试其他可能的端点"""
    logger.info("\n🔍 测试 3: 测试其他可能的端点")

    base_url = "http://10.215.58.199:13031"
    test_endpoints = [
        "/embed", "/v1/embeddings", "/embeddings", "/", "/health", "/status"
    ]

    test_data = {"inputs": "测试文本", "model": "gte-qwen"}
    headers = {"Content-Type": "application/json"}

    for endpoint in test_endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"测试端点: {url}")

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(url, json=test_data, headers=headers)
                logger.info(f"  - 状态码: {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"  - ✅ 端点可用: {url}")
                else:
                    logger.info(f"  - ❌ 端点不可用: {response.status_code}")
        except Exception as e:
            logger.info(f"  - ❌ 端点异常: {str(e)[:50]}...")


def test_network_connectivity():
    """测试网络连通性"""
    logger.info("\n🔍 测试 4: 网络连通性测试")

    host = "10.215.58.199"
    port = 13031

    try:
        with httpx.Client(timeout=5.0) as client:
            # 测试 TCP 连接
            response = client.get(f"http://{host}:{port}")
            logger.info(f"✅ 网络连通性正常")
            logger.info(f"  - 主机: {host}")
            logger.info(f"  - 端口: {port}")
            logger.info(f"  - 响应状态: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ 网络连通性测试失败: {str(e)}")


def main():
    """主函数"""
    logger.info("🧪 Embedding 服务可用性测试")
    print("=" * 80)

    # 测试网络连通性
    test_network_connectivity()

    # 测试替代端点
    test_alternative_endpoints()

    # 测试主要服务
    success = test_embedding_service()

    if success:
        logger.info("✅ Embedding 服务测试完成")
        print("\n✅ Embedding 服务可用!")
    else:
        logger.error("❌ Embedding 服务测试失败")
        print("\n❌ Embedding 服务不可用!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
