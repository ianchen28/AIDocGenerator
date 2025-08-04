#!/usr/bin/env python3
"""
解码Redis流中的中文数据
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis
from loguru import logger


def decode_redis_stream_data(job_id: str):
    """解码Redis流中的中文数据"""
    logger.info(f"🔍 解码Redis流数据: {job_id}")

    # 连接远程Redis
    r = redis.Redis(host='10.215.149.74',
                    port=26379,
                    password='xJrhp*4mnHxbBWN2grqq',
                    decode_responses=True)

    stream_key = f"job_events:{job_id}"

    try:
        # 获取流长度
        stream_length = r.xlen(stream_key)
        logger.info(f"📊 流长度: {stream_length}")

        if stream_length == 0:
            logger.warning("⚠️ 流中无数据")
            return

        # 获取所有消息
        messages = r.xrange(stream_key, "-", "+")

        logger.info(f"📋 解码后的流内容:")
        logger.info("=" * 80)

        for msg_id, fields in messages:
            logger.info(f"消息ID: {msg_id}")

            for field, value in fields.items():
                if field == "data":
                    try:
                        # 解析JSON数据
                        data = json.loads(value)
                        logger.info(f"  {field}:")
                        logger.info(
                            f"    {json.dumps(data, ensure_ascii=False, indent=2)}"
                        )
                    except json.JSONDecodeError:
                        logger.info(f"  {field}: {value}")
                else:
                    logger.info(f"  {field}: {value}")

            logger.info("-" * 40)

    except Exception as e:
        logger.error(f"❌ 解码失败: {e}")
    finally:
        r.close()


def decode_specific_message(job_id: str, message_id: str):
    """解码特定的消息"""
    logger.info(f"🔍 解码特定消息: {job_id} -> {message_id}")

    r = redis.Redis(host='10.215.149.74',
                    port=26379,
                    password='xJrhp*4mnHxbBWN2grqq',
                    decode_responses=True)

    stream_key = f"job_events:{job_id}"

    try:
        # 获取特定消息
        messages = r.xrange(stream_key, message_id, message_id)

        if not messages:
            logger.warning("⚠️ 未找到指定消息")
            return

        msg_id, fields = messages[0]
        logger.info(f"消息ID: {msg_id}")

        for field, value in fields.items():
            if field == "data":
                try:
                    data = json.loads(value)
                    logger.info(f"  {field}:")
                    logger.info(
                        f"    {json.dumps(data, ensure_ascii=False, indent=2)}"
                    )
                except json.JSONDecodeError:
                    logger.info(f"  {field}: {value}")
            else:
                logger.info(f"  {field}: {value}")

    except Exception as e:
        logger.error(f"❌ 解码失败: {e}")
    finally:
        r.close()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format=
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO")

    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        if len(sys.argv) > 2:
            message_id = sys.argv[2]
            decode_specific_message(job_id, message_id)
        else:
            decode_redis_stream_data(job_id)
    else:
        # 默认解码你测试的job_id
        decode_redis_stream_data("1951106983556190200")
