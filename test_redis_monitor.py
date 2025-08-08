#!/usr/bin/env python3
"""
测试Redis监听功能
"""
import redis
import json
import time

# Redis配置
REDIS_HOST = "10.215.149.74"
REDIS_PORT = 26379
REDIS_PASSWORD = "xJrhp*4mnHxbBWN2grqq"
REDIS_DB = 0


def test_redis_stream():
    """测试Redis Stream"""
    try:
        # 连接Redis
        client = redis.Redis(host=REDIS_HOST,
                             port=REDIS_PORT,
                             password=REDIS_PASSWORD,
                             db=REDIS_DB,
                             decode_responses=True)

        # 测试连接
        client.ping()
        print("✅ Redis连接成功")

        # 检查指定的流
        job_id = "1754657877360474300"
        stream_key = f"job:{job_id}"

        print(f"🔍 检查流: {stream_key}")

        # 获取流信息
        stream_length = client.xlen(stream_key)
        print(f"📊 流长度: {stream_length}")

        if stream_length > 0:
            # 读取所有消息
            messages = client.xread(count=stream_length,
                                    streams={stream_key: "0"})
            print(f"📨 找到 {len(messages)} 个流")

            for stream, stream_messages in messages:
                print(f"流: {stream}")
                for message_id, fields in stream_messages:
                    print(f"  ID: {message_id}")
                    for field, value in fields.items():
                        if field == "data":
                            try:
                                data = json.loads(value)
                                print(
                                    f"    数据: {json.dumps(data, ensure_ascii=False, indent=2)}"
                                )
                            except:
                                print(f"    数据: {value}")
                        else:
                            print(f"    {field}: {value}")
                    print()
        else:
            print("⚠️  流为空或不存在")

        # 检查所有job:前缀的流
        print("🔍 检查所有job:前缀的流:")
        all_keys = client.keys("job:*")
        print(f"找到 {len(all_keys)} 个键:")
        for key in all_keys:
            try:
                # 检查键的类型
                key_type = client.type(key)
                if key_type == "stream":
                    length = client.xlen(key)
                    print(f"  {key}: {length} 条消息 (Stream)")
                else:
                    print(f"  {key}: 类型为 {key_type} (不是Stream)")
            except Exception as e:
                print(f"  {key}: 检查失败 - {e}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        print(f"完整错误: {traceback.format_exc()}")


if __name__ == "__main__":
    test_redis_stream()
