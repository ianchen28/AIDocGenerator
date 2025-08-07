#!/usr/bin/env python3
"""
统一日志查看脚本
所有日志都输出到 logs/app.log
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

def view_log_file(log_file: str = "logs/app.log", lines: int = 50):
    """查看日志文件"""
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    print(f"📄 查看日志文件: {log_file}")
    print(f"📊 文件大小: {os.path.getsize(log_file) / 1024:.1f} KB")
    print("=" * 80)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        # 读取最后 N 行
        all_lines = f.readlines()
        last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        for line in last_lines:
            print(line.rstrip())

def monitor_log_file(log_file: str = "logs/app.log", interval: int = 2):
    """实时监控日志文件"""
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    print(f"🔍 开始监控日志文件: {log_file}")
    print("按 Ctrl+C 停止监控")
    print("=" * 80)
    
    last_size = os.path.getsize(log_file)
    while True:
        try:
            current_size = os.path.getsize(log_file)
            if current_size > last_size:
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    if new_content.strip():
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {new_content.rstrip()}")
                last_size = current_size
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 监控已停止")
            break
        except Exception as e:
            print(f"❌ 监控过程中出错: {e}")
            time.sleep(interval)

def search_log_file(log_file: str = "logs/app.log", keyword: str = ""):
    """搜索日志文件中的关键词"""
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    if not keyword:
        keyword = input("🔍 请输入搜索关键词: ")
    
    print(f"🔍 在 {log_file} 中搜索: {keyword}")
    print("=" * 80)
    
    found_count = 0
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if keyword.lower() in line.lower():
                print(f"第 {line_num} 行: {line.rstrip()}")
                found_count += 1
    
    print(f"✅ 找到 {found_count} 条匹配记录")

def show_log_stats(log_file: str = "logs/app.log"):
    """显示日志统计信息"""
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    print(f"📊 日志文件统计: {log_file}")
    print("=" * 80)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        total_lines = len(lines)
        
        # 统计不同级别的日志
        levels = {}
        for line in lines:
            if ' | ' in line:
                parts = line.split(' | ')
                if len(parts) >= 2:
                    level = parts[1].strip()
                    levels[level] = levels.get(level, 0) + 1
        
        print(f"📈 总行数: {total_lines}")
        print(f"📁 文件大小: {os.path.getsize(log_file) / 1024:.1f} KB")
        print("\n📊 日志级别统计:")
        for level, count in sorted(levels.items()):
            percentage = (count / total_lines) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")

def main():
    """主函数"""
    print("📝 统一日志查看工具")
    print("所有日志都输出到 logs/app.log")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python view_unified_logs.py view [行数]     # 查看日志")
        print("  python view_unified_logs.py monitor         # 实时监控")
        print("  python view_unified_logs.py search [关键词] # 搜索日志")
        print("  python view_unified_logs.py stats           # 显示统计")
        return
    
    command = sys.argv[1]
    
    if command == "view":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        view_log_file(lines=lines)
    elif command == "monitor":
        monitor_log_file()
    elif command == "search":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        search_log_file(keyword=keyword)
    elif command == "stats":
        show_log_stats()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()
