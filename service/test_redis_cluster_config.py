#!/usr/bin/env python3
"""
Redis集群配置测试脚本

用于测试新的Redis配置结构是否正常工作，包括单节点和集群模式。
统一使用原生redis，避免异步/同步混用。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.config import settings
from doc_agent.core.redis_health_check import init_redis_pool, get_redis_client, check_redis_connection
from doc_agent.core.redis_stream_publisher import RedisStreamPublisher
from loguru import logger


def test_redis_config():
    """测试Redis配置"""
    logger.info("🧪 开始测试Redis配置...")

    # 1. 测试配置读取
    logger.info("📋 当前Redis配置:")
    redis_config = settings.redis_config
    mode = redis_config.get('mode', 'single')
    logger.info(f"   - 模式: {mode}")

    if mode == 'cluster':
        cluster_config = redis_config.get('cluster', {})
        nodes = cluster_config.get('nodes', [])
        password = cluster_config.get('password', '')
        logger.info(f"   - 节点数量: {len(nodes)}")
        logger.info(f"   - 节点列表: {nodes}")
        logger.info(f"   - 密码: {'已设置' if password else '未设置'}")
    else:
        single_config = redis_config.get('single', {})
        host = single_config.get('host', '127.0.0.1')
        port = single_config.get('port', 6379)
        password = single_config.get('password', '')
        logger.info(f"   - 主机: {host}")
        logger.info(f"   - 端口: {port}")
        logger.info(f"   - 密码: {'已设置' if password else '未设置'}")

    # 2. 测试Redis URL生成
    logger.info("🔗 Redis URL:")
    redis_url = settings.redis_url
    logger.info(f"   - {redis_url}")

    # 3. 测试连接初始化
    logger.info("🔌 初始化Redis连接...")
    try:
        init_redis_pool()
        logger.info("✅ Redis连接初始化成功")
    except Exception as e:
        logger.error(f"❌ Redis连接初始化失败: {e}")
        return False

    # 4. 测试连接健康检查
    logger.info("🏥 测试连接健康检查...")
    try:
        is_healthy = check_redis_connection()
        if is_healthy:
            logger.info("✅ Redis连接健康检查通过")
        else:
            logger.error("❌ Redis连接健康检查失败")
            return False
    except Exception as e:
        logger.error(f"❌ Redis连接健康检查异常: {e}")
        return False

    # 5. 测试Redis客户端获取
    logger.info("🔧 测试Redis客户端获取...")
    try:
        client = get_redis_client()
        logger.info(f"✅ Redis客户端获取成功 (类型: {type(client).__name__})")
    except Exception as e:
        logger.error(f"❌ Redis客户端获取失败: {e}")
        return False

    # 6. 测试Stream Publisher
    logger.info("📡 测试Redis Stream Publisher...")
    try:
        publisher = RedisStreamPublisher(client, "test_stream")
        logger.info("✅ Redis Stream Publisher创建成功")

        # 测试发布事件
        test_event = {
            "eventType": "test",
            "message": "测试事件",
            "timestamp": "2024-01-01T00:00:00"
        }

        # 使用同步方法发布事件
        publisher.publish_event("test_job_001",
                                test_event,
                                enable_listen_logger=False)
        logger.info("✅ Redis Stream事件发布成功")

    except Exception as e:
        logger.error(f"❌ Redis Stream Publisher测试失败: {e}")
        return False

    logger.info("🎉 所有Redis配置测试通过！")
    return True


def test_config_switching():
    """测试配置切换功能"""
    logger.info("🔄 测试配置切换功能...")

    # 这里可以添加测试配置切换的逻辑
    # 由于涉及文件修改，这里只做概念性测试
    logger.info("📝 配置切换功能需要手动运行 config_redis.sh 脚本")
    logger.info("   可用的选项:")
    logger.info("   1. 本地Redis (127.0.0.1:6379)")
    logger.info("   2. 远程Redis (10.215.149.74:26379)")
    logger.info("   3. Redis集群 (6节点集群)")
    logger.info("   4. 自定义单节点配置")
    logger.info("   5. 自定义集群配置")


def main():
    """主函数"""
    logger.info("🚀 Redis集群配置测试开始")
    logger.info("=" * 50)

    # 测试基本配置
    success = test_redis_config()

    if success:
        logger.info("=" * 50)
        test_config_switching()

    logger.info("=" * 50)
    logger.info("🏁 Redis集群配置测试完成")


if __name__ == "__main__":
    main()
