import asyncio
import json
import sys
from typing import Optional

import redis.asyncio as aredis
from doc_agent.core.config import settings


class Colors:
    """用于在终端美化输出的颜色代码"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


async def listen_to_stream(stream_name: str,
                           redis_url: str,
                           job_id_filter: Optional[str] = None):
    """
    连接到 Redis Stream 并监听指定 job_id 的事件。
    """
    try:
        # 使用异步 redis 客户端
        r = aredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await r.ping()
        print(f"{Colors.OKGREEN}✅ 成功连接到 Redis at {redis_url}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}👂 正在监听 Stream '{stream_name}'...{Colors.ENDC}")
        if job_id_filter:
            print(
                f"{Colors.OKBLUE}🔍 只显示 Job ID = {job_id_filter} 的事件{Colors.ENDC}"
            )
        else:
            print(f"{Colors.WARNING}⚠️ 未指定 Job ID, 将显示所有事件{Colors.ENDC}")
        print("-" * 50)

    except Exception as e:
        print(f"{Colors.FAIL}❌ 连接 Redis 失败: {e}{Colors.ENDC}")
        return

    last_id = '0'  # 从头开始监听
    while True:
        try:
            # 使用 XREAD 阻塞式地等待新消息
            response = await r.xread(
                {stream_name: last_id},
                count=10,
                block=0  # block=0 表示无限等待
            )

            if not response:
                continue

            for _, messages in response:
                for message_id, message_data in messages:
                    job_id = message_data.get('job_id')

                    # 如果设置了过滤，并且 job_id 不匹配，则跳过
                    if job_id_filter and job_id != job_id_filter:
                        continue

                    try:
                        # 解析内部的 JSON 数据
                        data_json = json.loads(message_data.get('data', '{}'))
                        event_type = data_json.get('eventType', 'unknown')

                        # 格式化输出
                        print(f"{Colors.HEADER}--- New Event ---{Colors.ENDC}")
                        print(
                            f"{Colors.BOLD}Stream ID:{Colors.ENDC} {message_id}"
                        )
                        print(f"{Colors.BOLD}Job ID:   {Colors.ENDC} {job_id}")
                        print(
                            f"{Colors.BOLD}Event Type:{Colors.ENDC} {Colors.OKGREEN}{event_type}{Colors.ENDC}"
                        )

                        # 如果是 token 流，直接打印 token
                        if event_type == 'on_llm_token':
                            token_data = data_json.get('data', {})
                            token = token_data.get('token', '')
                            # 使用 end='' 来实现打字机效果
                            print(token, end='', flush=True)
                        else:
                            # 对于其他事件，美化打印其数据内容
                            print(f"\n{Colors.BOLD}Data:{Colors.ENDC}")
                            pretty_data = json.dumps(data_json.get('data', {}),
                                                     indent=2,
                                                     ensure_ascii=False)
                            print(f"{Colors.OKCYAN}{pretty_data}{Colors.ENDC}")
                            print("-" * 50)

                    except json.JSONDecodeError:
                        print(
                            f"{Colors.FAIL}无法解析消息中的 JSON 数据: {message_data.get('data')}{Colors.ENDC}"
                        )

                    last_id = message_id

        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}🛑 停止监听。{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.FAIL}监听时发生错误: {e}{Colors.ENDC}")
            await asyncio.sleep(5)  # 稍等后重试

    await r.close()


if __name__ == "__main__":
    # 从命令行参数获取要过滤的 job_id
    target_job_id = sys.argv[1] if len(sys.argv) > 1 else None

    stream = settings.REDIS_STREAM_NAME
    url = settings.REDIS_URL

    asyncio.run(listen_to_stream(stream, url, target_job_id))
