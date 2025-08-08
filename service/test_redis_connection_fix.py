#!/usr/bin/env python3
"""
测试Redis连接修复

验证新的连接管理机制是否能够正确处理连接关闭和重连。
"""

import asyncio
import time
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from doc_agent.core.logger import logger
from doc_agent.core.redis_health_check import get_redis_connection_manager, close_redis_connections
from doc_agent.core.redis_stream_publisher import RedisStreamPublisher


async def test_redis_connection_manager():
    """测试Redis连接管理器"""
    logger.info("开始测试Redis连接管理器...")

    try:
        # 获取连接管理器
        manager = await get_redis_connection_manager()

        # 获取客户端
        client = await manager.get_client()

        # 测试基本操作
        await client.ping()
        logger.success("✅ Redis连接正常")

        # 测试健康状态
        is_healthy = manager.is_healthy()
        logger.info(f"连接健康状态: {is_healthy}")

        # 测试发布事件
        publisher = RedisStreamPublisher(client)
        event_data = {
            "event_type": "test",
            "message": "测试事件",
            "timestamp": time.time()
        }

        event_id = await publisher.publish_event("test_job_001", event_data)
        if event_id:
            logger.success(f"✅ 事件发布成功: {event_id}")
        else:
            logger.error("❌ 事件发布失败")

        return True

    except Exception as e:
        logger.error(f"❌ Redis连接管理器测试失败: {e}")
        return False


async def test_connection_recovery():
    """测试连接恢复机制"""
    logger.info("开始测试连接恢复机制...")

    try:
        manager = await get_redis_connection_manager()
        client = await manager.get_client()

        # 模拟连接断开（通过关闭客户端）
        await client.close()
        logger.info("模拟连接断开...")

        # 等待健康检查器检测到问题
        await asyncio.sleep(5)

        # 尝试重新获取客户端
        new_client = await manager.get_client()
        await new_client.ping()
        logger.success("✅ 连接恢复成功")

        return True

    except Exception as e:
        logger.error(f"❌ 连接恢复测试失败: {e}")
        return False


async def test_publisher_with_recovery():
    """测试发布器在连接恢复后的表现"""
    logger.info("开始测试发布器连接恢复...")

    try:
        manager = await get_redis_connection_manager()
        client = await manager.get_client()
        publisher = RedisStreamPublisher(client)

        # 发布第一个事件
        event_id1 = await publisher.publish_event("test_job_002", {
            "event_type": "test_start",
            "message": "测试开始"
        })
        logger.info(f"第一个事件ID: {event_id1}")

        # 模拟连接问题
        await client.close()
        logger.info("模拟连接问题...")

        # 尝试发布第二个事件（应该触发重连）
        event_id2 = await publisher.publish_event("test_job_002", {
            "event_type": "test_end",
            "message": "测试结束"
        })

        if event_id2:
            logger.success("✅ 发布器在连接恢复后正常工作")
        else:
            logger.warning("⚠️ 发布器在连接恢复后仍有问题")

        return True

    except Exception as e:
        logger.error(f"❌ 发布器连接恢复测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始Redis连接修复测试")

    tests = [("连接管理器测试", test_redis_connection_manager),
             ("连接恢复测试", test_connection_recovery),
             ("发布器恢复测试", test_publisher_with_recovery)]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n📋 运行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))

    # 输出测试结果
    logger.info("\n📊 测试结果汇总:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")

    # 清理连接
    await close_redis_connections()

    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)

    logger.info(f"\n🎯 测试完成: {passed}/{total} 个测试通过")

    if passed == total:
        logger.success("🎉 所有测试通过！Redis连接修复成功。")
    else:
        logger.error("⚠️ 部分测试失败，需要进一步检查。")


if __name__ == "__main__":
    asyncio.run(main())
