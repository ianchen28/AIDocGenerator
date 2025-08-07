#!/usr/bin/env python3
"""
日志查看脚本
用于实时查看各种日志文件
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path


def tail_log_file(log_file: str, lines: int = 50):
    """查看日志文件的最后几行"""
    try:
        if not os.path.exists(log_file):
            print(f"❌ 日志文件不存在: {log_file}")
            return

        with open(log_file, 'r', encoding='utf-8') as f:
            # 读取最后几行
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(
                all_lines) > lines else all_lines

            print(f"📄 {log_file} (最后 {len(last_lines)} 行):")
            print("=" * 80)
            for line in last_lines:
                print(line.rstrip())
            print("=" * 80)

    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")


def monitor_log_file(log_file: str, interval: int = 2):
    """实时监控日志文件"""
    try:
        if not os.path.exists(log_file):
            print(f"❌ 日志文件不存在: {log_file}")
            return

        print(f"🔍 开始监控日志文件: {log_file}")
        print(f"⏱️ 刷新间隔: {interval}秒")
        print("按 Ctrl+C 停止监控")
        print("-" * 80)

        # 获取文件的初始大小
        last_size = os.path.getsize(log_file)

        while True:
            try:
                current_size = os.path.getsize(log_file)

                if current_size > last_size:
                    # 文件有新内容
                    with open(log_file, 'r', encoding='utf-8') as f:
                        f.seek(last_size)
                        new_content = f.read()
                        if new_content.strip():
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] {new_content.rstrip()}"
                            )

                    last_size = current_size

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n🛑 监控已停止")
                break
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                time.sleep(interval)

    except Exception as e:
        print(f"❌ 启动监控失败: {e}")


def list_log_files():
    """列出可用的日志文件"""
    log_files = [
        "logs/app.log", "logs/celery_worker.log", "logs/uvicorn.log",
        "logs/mock_service.log"
    ]

    print("📋 可用的日志文件:")
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            print(
                f"  📄 {log_file} ({size} bytes, 修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')})"
            )
        else:
            print(f"  ❌ {log_file} (不存在)")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("📋 日志查看工具")
        print("使用方法:")
        print("  python view_logs.py list                    # 列出日志文件")
        print("  python view_logs.py view <log_file> [lines] # 查看日志文件")
        print("  python view_logs.py monitor <log_file>      # 实时监控日志文件")
        print("\n示例:")
        print("  python view_logs.py list")
        print("  python view_logs.py view logs/app.log 100")
        print("  python view_logs.py monitor logs/celery_worker.log")
        return

    command = sys.argv[1]

    if command == "list":
        list_log_files()

    elif command == "view":
        if len(sys.argv) < 3:
            print("❌ 请指定日志文件路径")
            return

        log_file = sys.argv[2]
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        tail_log_file(log_file, lines)

    elif command == "monitor":
        if len(sys.argv) < 3:
            print("❌ 请指定日志文件路径")
            return

        log_file = sys.argv[2]
        interval = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        monitor_log_file(log_file, interval)

    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
