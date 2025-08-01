#!/usr/bin/env python3
"""
URL内容获取工具

使用方法:
python fetch_url_content.py [URL]

示例:
python fetch_url_content.py "https://example.com"
python fetch_url_content.py "https://www.baidu.com"
"""

import asyncio
import sys
import os
import json
from urllib.parse import urlparse

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_search_module import WebSearchService, setup_logger


def print_usage():
    """打印使用说明"""
    print("""
URL内容获取工具

使用方法:
    python fetch_url_content.py [URL]

示例:
    python fetch_url_content.py "https://example.com"
    python fetch_url_content.py "https://www.baidu.com"

参数:
    [URL] - 要获取内容的网页URL

功能:
    1. 获取网页的完整文本内容
    2. 保存内容到本地文件
    3. 显示内容统计信息
    """)


async def fetch_url_content(url: str):
    """获取URL的完整内容"""
    print(f"🔍 正在获取URL内容: {url}")
    print("=" * 60)

    try:
        # 设置日志
        setup_logger()

        # 创建web搜索服务
        web_search_service = WebSearchService()

        # 获取完整内容
        content = await web_search_service.get_full_content_for_url(url)

        if content:
            print(f"✅ 成功获取内容！")
            print(f"   内容长度: {len(content)} 字符")
            print(f"   内容行数: {len(content.splitlines())}")

            # 统计信息
            words = content.split()
            print(f"   单词数量: {len(words)}")
            print(
                f"   平均单词长度: {sum(len(word) for word in words) / len(words):.1f}"
                if words else "   平均单词长度: 0")

            # 显示内容预览
            print(f"\n📄 内容预览 (前500字符):")
            print("-" * 40)
            print(content[:500])
            if len(content) > 500:
                print("...")
            print("-" * 40)

            # 保存到文件
            parsed_url = urlparse(url)
            safe_filename = f"content_{parsed_url.netloc.replace('.', '_')}_{parsed_url.path.replace('/', '_').replace('.', '_')}.txt"
            if len(safe_filename) > 100:  # 限制文件名长度
                safe_filename = f"content_{parsed_url.netloc.replace('.', '_')}.txt"

            with open(safe_filename, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"获取时间: {asyncio.get_event_loop().time()}\n")
                f.write("=" * 50 + "\n")
                f.write(content)

            print(f"\n💾 完整内容已保存到: {safe_filename}")

            # 显示文件大小
            file_size = os.path.getsize(safe_filename)
            print(f"   文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)")

        else:
            print("❌ 获取内容失败")
            print("可能的原因:")
            print("1. URL不存在或无法访问")
            print("2. 网络连接问题")
            print("3. 网站反爬虫机制")
            print("4. 需要JavaScript渲染的内容")

    except Exception as e:
        print(f"❌ 获取内容过程中出现错误: {e}")
        print("请检查:")
        print("1. URL格式是否正确")
        print("2. 网络连接是否正常")
        print("3. 是否安装了必要的依赖包")


def validate_url(url: str) -> bool:
    """验证URL格式"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


async def main():
    """主函数"""
    print("🚀 URL内容获取工具")
    print("=" * 60)

    # 获取URL参数
    if len(sys.argv) < 2:
        print("❌ 请提供要获取内容的URL")
        print_usage()
        return

    url = sys.argv[1]

    # 验证URL格式
    if not validate_url(url):
        print(f"❌ 无效的URL格式: {url}")
        print("请提供完整的URL，例如: https://example.com")
        return

    # 执行获取
    await fetch_url_content(url)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
    else:
        asyncio.run(main())
