#!/usr/bin/env python3
"""
简单的日志查看脚本
"""

import os
import time
from pathlib import Path


def view_logs():
    """查看日志文件"""
    # 从service目录找到项目根目录
    log_file = Path(__file__).parent.parent / "logs" / "app.log"

    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        return

    print(f"📄 日志文件: {log_file}")
    print(f"📊 文件大小: {log_file.stat().st_size} 字节")
    print("-" * 80)

    # 显示最后10行
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.rstrip())


def monitor_logs():
    """实时监控日志"""
    # 从service目录找到项目根目录
    log_file = Path(__file__).parent.parent / "logs" / "app.log"

    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        return

    print(f"🔍 开始监控日志文件: {log_file}")
    print("按 Ctrl+C 停止监控")
    print("-" * 80)

    # 获取文件初始大小
    with open(log_file, 'r', encoding='utf-8') as f:
        f.seek(0, 2)  # 移动到文件末尾
        last_position = f.tell()

    try:
        while True:
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(last_position)
                new_content = f.read()
                if new_content:
                    print(new_content, end='', flush=True)
                    last_position = f.tell()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n⏹️  停止监控")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_logs()
    else:
        view_logs()
