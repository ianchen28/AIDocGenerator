#!/usr/bin/env python3
"""
查看测试输出文件的工具脚本
"""

import json
from pathlib import Path


def list_sessions():
    """列出所有测试会话"""
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ output 目录不存在")
        return []

    sessions = []
    for item in output_dir.iterdir():
        if item.is_dir() and item.name.startswith("test_session_"):
            sessions.append(item)

    # 按时间排序，最新的在前
    sessions.sort(key=lambda x: x.name, reverse=True)
    return sessions


def show_session_info(session_dir: Path):
    """显示会话信息"""
    print(f"\n📁 会话目录: {session_dir.name}")

    # 读取摘要信息
    summary_file = session_dir / "test_summary.json"
    if summary_file.exists():
        with open(summary_file, encoding='utf-8') as f:
            summary = json.load(f)

        print(f"📅 时间: {summary['timestamp']}")
        print(f"📝 主题: {summary['topic']}")
        print(f"📄 文档长度: {summary['document_length']} 字符")
        print(f"📊 日志条目: {summary['log_entries']}")

    # 列出文件
    print("\n📋 文件列表:")
    for file in session_dir.iterdir():
        if file.is_file():
            size = file.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            print(f"  📄 {file.name} ({size_str})")


def view_document(session_dir: Path):
    """查看生成的文档"""
    # 查找 .md 文件
    md_files = list(session_dir.glob("*.md"))
    if not md_files:
        print("❌ 未找到生成的文档文件")
        return

    doc_file = md_files[0]  # 取第一个 .md 文件
    print(f"\n📄 查看文档: {doc_file.name}")
    print("=" * 80)

    with open(doc_file, encoding='utf-8') as f:
        content = f.read()

    # 显示前 500 字符
    preview = content[:500]
    print(preview)
    if len(content) > 500:
        print(f"\n... (文档总长度: {len(content)} 字符)")
        print("💡 提示: 使用 'cat' 命令查看完整文档")


def view_log(session_dir: Path):
    """查看测试日志"""
    log_file = session_dir / "test_log.txt"
    if not log_file.exists():
        print("❌ 未找到测试日志文件")
        return

    print(f"\n📋 查看测试日志: {log_file.name}")
    print("=" * 80)

    with open(log_file, encoding='utf-8') as f:
        lines = f.readlines()

    # 显示最后 20 行
    if len(lines) > 20:
        print("... (显示最后 20 行)")
        for line in lines[-20:]:
            print(line.rstrip())
    else:
        for line in lines:
            print(line.rstrip())


def main():
    """主函数"""
    print("🔍 测试输出查看工具")
    print("=" * 50)

    sessions = list_sessions()
    if not sessions:
        print("❌ 没有找到测试会话")
        return

    print(f"📁 找到 {len(sessions)} 个测试会话:")
    for i, session in enumerate(sessions[:5]):  # 只显示最近5个
        show_session_info(session)

    if len(sessions) > 5:
        print(f"\n... 还有 {len(sessions) - 5} 个更早的会话")

    # 询问用户要查看哪个会话
    if len(sessions) == 1:
        latest_session = sessions[0]
        print(f"\n🎯 自动选择最新会话: {latest_session.name}")
    else:
        print(f"\n请选择要查看的会话 (1-{min(len(sessions), 5)}):")
        for i, session in enumerate(sessions[:5]):
            print(f"  {i+1}. {session.name}")

        try:
            choice = int(input("请输入选择 (默认1): ") or "1")
            if 1 <= choice <= len(sessions[:5]):
                latest_session = sessions[choice - 1]
            else:
                print("❌ 无效选择，使用最新会话")
                latest_session = sessions[0]
        except ValueError:
            print("❌ 无效输入，使用最新会话")
            latest_session = sessions[0]

    # 显示会话信息
    show_session_info(latest_session)

    # 询问要查看什么
    print("\n请选择要查看的内容:")
    print("  1. 查看生成的文档")
    print("  2. 查看测试日志")
    print("  3. 查看研究数据")
    print("  4. 全部查看")

    try:
        choice = input("请输入选择 (默认1): ").strip() or "1"

        if choice == "1":
            view_document(latest_session)
        elif choice == "2":
            view_log(latest_session)
        elif choice == "3":
            research_file = latest_session / "research_data.txt"
            if research_file.exists():
                print(f"\n📚 研究数据文件大小: {research_file.stat().st_size:,} bytes")
                print("💡 提示: 文件较大，建议使用 'less' 或 'head' 命令查看")
            else:
                print("❌ 未找到研究数据文件")
        elif choice == "4":
            view_document(latest_session)
            view_log(latest_session)
        else:
            print("❌ 无效选择")

    except KeyboardInterrupt:
        print("\n👋 再见!")


if __name__ == "__main__":
    main()
