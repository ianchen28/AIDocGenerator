#!/usr/bin/env python3
"""
实时日志监控脚本
"""

import time
import os
from pathlib import Path


def monitor_log_file(log_file_path: str, interval: float = 0.1):
    """
    实时监控日志文件
    
    Args:
        log_file_path: 日志文件路径
        interval: 检查间隔（秒）
    """
    print(f"🔍 开始监控日志文件: {log_file_path}")
    print("按 Ctrl+C 停止监控")
    print("-" * 80)
    
    # 获取文件初始大小
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # 移动到文件末尾
            last_position = f.tell()
    else:
        last_position = 0
    
    try:
        while True:
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    if new_content:
                        print(new_content, end='', flush=True)
                        last_position = f.tell()
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  停止监控")

if __name__ == "__main__":
    # 从service目录找到项目根目录
    log_file = Path(__file__).parent.parent / "logs" / "app.log"
    monitor_log_file(str(log_file))
