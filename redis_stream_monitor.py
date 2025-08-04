#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 流持续监控工具
支持实时监控Redis Streams，直到手动停止
"""

import redis
import json
import time
import signal
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any


class RedisStreamMonitor:
    """Redis流监控器"""

    def __init__(self, host: str, port: int, password: str, db: int = 0):
        """初始化监控器"""
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.client = None
        self.running = False
        self.last_heartbeat = 0

        # 颜色定义
        self.colors = {
            'red': '\033[0;31m',
            'green': '\033[0;32m',
            'yellow': '\033[1;33m',
            'blue': '\033[0;34m',
            'purple': '\033[0;35m',
            'cyan': '\033[0;36m',
            'nc': '\033[0m'
        }

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        print(f"\n{self.colors['yellow']}🛑 正在停止监控...{self.colors['nc']}")
        self.running = False

    def _print_colored(self, text: str, color: str = 'nc'):
        """打印彩色文本"""
        print(f"{self.colors[color]}{text}{self.colors['nc']}")

    def connect(self) -> bool:
        """连接Redis"""
        try:
            self._print_colored("🔍 检查Redis连接...", "blue")
            self.client = redis.Redis(host=self.host,
                                      port=self.port,
                                      password=self.password,
                                      db=self.db,
                                      decode_responses=True,
                                      socket_connect_timeout=5,
                                      socket_timeout=5)

            # 测试连接
            self.client.ping()
            self._print_colored("✅ Redis连接正常", "green")
            return True

        except Exception as e:
            self._print_colored(f"❌ Redis连接失败: {e}", "red")
            return False

    def get_stream_info(self, stream_key: str) -> Dict[str, Any]:
        """获取流信息"""
        try:
            stream_length = self.client.xlen(stream_key)
            return {
                'exists': True,
                'length': stream_length,
                'empty': stream_length == 0
            }
        except Exception:
            return {'exists': False, 'length': 0, 'empty': True}

    def pretty_print_message(self, stream_key: str, message_id: str,
                             fields: Dict[str, str]):
        """美化打印消息"""
        print(f"{self.colors['cyan']}{'='*60}{self.colors['nc']}")
        print(f"{self.colors['purple']}📨 新消息{self.colors['nc']}")
        print(f"{self.colors['blue']}流:{self.colors['nc']} {stream_key}")
        print(f"{self.colors['blue']}ID:{self.colors['nc']} {message_id}")
        print(
            f"{self.colors['blue']}时间:{self.colors['nc']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print()

        for field, value in fields.items():
            if field == "data":
                try:
                    # 尝试解析JSON数据
                    data = json.loads(value)
                    print(f"{self.colors['green']}数据:{self.colors['nc']}")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print(
                        f"{self.colors['green']}数据:{self.colors['nc']} {value}"
                    )
            elif field in ["eventType", "event_type"]:
                print(
                    f"{self.colors['green']}事件类型:{self.colors['nc']} {value}")
            else:
                print(
                    f"{self.colors['green']}{field}:{self.colors['nc']} {value}"
                )

        print(f"{self.colors['cyan']}{'='*60}{self.colors['nc']}")
        print()

    def monitor_single_stream(self,
                              job_id: str,
                              block_timeout: int = 5000,
                              pretty: bool = True):
        """监控单个流"""
        stream_key = f"job_events:{job_id}"
        last_id = "0"

        # 获取流信息
        stream_info = self.get_stream_info(stream_key)

        if stream_info['empty']:
            self._print_colored(f"⚠️  流 {stream_key} 不存在或为空", "yellow")
            self._print_colored("💡 等待新消息...", "blue")
        else:
            self._print_colored(f"📊 流长度: {stream_info['length']}", "green")

        print()
        self._print_colored(f"🔍 开始监控流: {stream_key}", "blue")
        self._print_colored("按 Ctrl+C 停止监控", "yellow")
        print()

        self.running = True

        while self.running:
            try:
                # 读取新消息
                messages = self.client.xread(count=10,
                                             block=block_timeout,
                                             streams={stream_key: last_id})

                if messages:
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            if pretty:
                                self.pretty_print_message(
                                    stream, message_id, fields)
                            else:
                                self._print_colored(f"📨 新消息: {message_id}",
                                                    "green")
                                print(f"字段: {fields}")
                                print()

                            last_id = message_id

                # 显示心跳
                current_time = time.time()
                if current_time - self.last_heartbeat >= 30:
                    self._print_colored(
                        f"💓 监控中... {datetime.now().strftime('%H:%M:%S')}",
                        "yellow")
                    self.last_heartbeat = current_time

            except Exception as e:
                self._print_colored(f"❌ 监控错误: {e}", "red")
                time.sleep(1)

    def monitor_all_streams(self, block_timeout: int = 5000):
        """监控所有流"""
        self._print_colored("🔍 开始监控所有流...", "blue")
        self._print_colored("按 Ctrl+C 停止监控", "yellow")
        print()

        # 获取所有流
        try:
            all_keys = self.client.keys("job_events:*")
            if not all_keys:
                self._print_colored("⚠️  没有找到任何流", "yellow")
                return

            self._print_colored("📋 监控的流:", "green")
            for key in all_keys:
                print(f"  {key}")
            print()

            # 构建流参数
            streams = {key: "0" for key in all_keys}

            self.running = True

            while self.running:
                try:
                    # 读取所有流的新消息
                    messages = self.client.xread(count=10,
                                                 block=block_timeout,
                                                 streams=streams)

                    if messages:
                        self._print_colored("📨 收到新消息:", "green")
                        for stream, stream_messages in messages:
                            for message_id, fields in stream_messages:
                                print(f"流: {stream}")
                                print(f"ID: {message_id}")
                                print(f"字段: {fields}")
                                print()

                                # 更新流的最后ID
                                streams[stream] = message_id

                    # 显示心跳
                    current_time = time.time()
                    if current_time - self.last_heartbeat >= 30:
                        self._print_colored(
                            f"💓 监控中... {datetime.now().strftime('%H:%M:%S')}",
                            "yellow")
                        self.last_heartbeat = current_time

                except Exception as e:
                    self._print_colored(f"❌ 监控错误: {e}", "red")
                    time.sleep(1)

        except Exception as e:
            self._print_colored(f"❌ 获取流列表失败: {e}", "red")

    def run(self,
            job_id: Optional[str] = None,
            monitor_all: bool = False,
            block_timeout: int = 5000,
            pretty: bool = True):
        """运行监控"""
        self._print_colored("🚀 Redis 流持续监控工具", "blue")
        print("=" * 50)
        self._print_colored(f"服务器: {self.host}:{self.port}", "blue")
        self._print_colored(f"超时: {block_timeout}ms", "blue")

        if monitor_all:
            self._print_colored("模式: 监控所有流", "blue")
        else:
            self._print_colored(f"任务ID: {job_id}", "blue")
            self._print_colored(f"流: job_events:{job_id}", "blue")

        if pretty:
            self._print_colored("输出格式: 美化", "blue")

        print()

        # 连接Redis
        if not self.connect():
            return

        # 开始监控
        if monitor_all:
            self.monitor_all_streams(block_timeout)
        else:
            self.monitor_single_stream(job_id, block_timeout, pretty)

        self._print_colored("✅ 监控已停止", "green")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Redis 流持续监控工具")
    parser.add_argument("job_id",
                        nargs="?",
                        default="test_session_001",
                        help="任务ID (默认: test_session_001)")
    parser.add_argument("-a", "--all", action="store_true", help="监控所有流")
    parser.add_argument("-t",
                        "--timeout",
                        type=int,
                        default=5000,
                        help="阻塞超时时间(毫秒) (默认: 5000)")
    parser.add_argument("-p",
                        "--pretty",
                        action="store_true",
                        default=True,
                        help="使用美化输出格式")
    parser.add_argument("--host", default="10.215.149.74", help="Redis主机地址")
    parser.add_argument("--port", type=int, default=26379, help="Redis端口")
    parser.add_argument("--password",
                        default="xJrhp*4mnHxbBWN2grqq",
                        help="Redis密码")
    parser.add_argument("--db", type=int, default=0, help="Redis数据库")

    args = parser.parse_args()

    # 创建监控器
    monitor = RedisStreamMonitor(host=args.host,
                                 port=args.port,
                                 password=args.password,
                                 db=args.db)

    # 运行监控
    monitor.run(job_id=args.job_id,
                monitor_all=args.all,
                block_timeout=args.timeout,
                pretty=args.pretty)


if __name__ == "__main__":
    main()
