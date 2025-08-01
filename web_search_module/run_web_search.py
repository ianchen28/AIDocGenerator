#!/usr/bin/env python3
"""
Web搜索模块快速启动脚本

使用方法:
python run_web_search.py [查询关键词] [--full-content]

示例:
python run_web_search.py "水轮机"
python run_web_search.py "水利工程" --full-content
"""

import asyncio
import sys
import os
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_search_module import WebSearchService, setup_logger


def print_usage():
    """打印使用说明"""
    print("""
Web搜索模块快速启动脚本

使用方法:
    python run_web_search.py [查询关键词] [--full-content]

示例:
    python run_web_search.py "水轮机"
    python run_web_search.py "水利工程" --full-content

参数:
    [查询关键词] - 要搜索的关键词，如果不提供则使用默认关键词
    --full-content - 获取网页的完整内容（可选）

配置文件:
    请确保 config.json 文件存在并包含正确的配置信息
    """)


async def search_and_display(query: str, fetch_full_content: bool = False):
    """执行搜索并显示结果"""
    # 设置日志
    setup_logger()

    print(f"🔍 正在搜索: {query}")
    if fetch_full_content:
        print("📄 将获取网页完整内容")
    print("=" * 60)

    try:
        # 创建web搜索服务
        web_search_service = WebSearchService()

        # 执行搜索
        result = await web_search_service.get_web_docs(
            query, fetch_full_content=fetch_full_content)

        if result:
            print(f"✅ 搜索成功！找到 {len(result)} 个结果:")
            print()

            for i, doc in enumerate(result, 1):
                print(f"📄 结果 {i}:")
                print(f"   标题: {doc['meta_data'].get('docName', 'Unknown')}")
                print(f"   URL: {doc['doc_id']}")
                print(f"   排名: {doc['rank']}")
                print(f"   内容长度: {len(doc['text'])} 字符")
                print(f"   是否获取完整内容: {doc.get('full_content_fetched', False)}")

                # 显示内容预览
                content_preview = doc['text'][:] + "..." if len(
                    doc['text']) > 300 else doc['text']
                print(f"   内容预览: {content_preview}")
                print(f"   向量维度: {len(doc['context_vector'])}")
                print("-" * 60)
        else:
            print("❌ 搜索失败或无结果")

    except Exception as e:
        print(f"❌ 搜索过程中出现错误: {e}")
        print("请检查:")
        print("1. 配置文件 config.json 是否存在且格式正确")
        print("2. 网络连接是否正常")
        print("3. API服务是否可用")


async def fetch_single_url(url: str):
    """获取单个URL的完整内容"""
    print(f"🔍 正在获取URL内容: {url}")
    print("=" * 60)

    try:
        # 创建web搜索服务
        web_search_service = WebSearchService()

        # 获取完整内容
        content = await web_search_service.get_full_content_for_url(url)

        if content:
            print(f"✅ 成功获取内容！")
            print(f"   内容长度: {len(content)} 字符")
            print(f"   内容预览: {content[:500]}...")

            # 保存到文件
            filename = f"content_{url.replace('://', '_').replace('/', '_').replace('.', '_')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   完整内容已保存到: {filename}")
        else:
            print("❌ 获取内容失败")

    except Exception as e:
        print(f"❌ 获取内容过程中出现错误: {e}")


def check_config_file():
    """检查配置文件"""
    config_files = ["config.json", "standalone_config.json"]

    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                web_params = config.get('web_search_params', {})
                embedding_config = config.get('embedding', {})

                if web_params.get('url') and web_params.get('token'):
                    print(f"✅ 配置文件 {config_file} 检查通过")
                    return True
                else:
                    print(f"⚠️  配置文件 {config_file} 中缺少必要的配置项")

            except Exception as e:
                print(f"❌ 配置文件 {config_file} 解析失败: {e}")

    print("❌ 未找到有效的配置文件")
    print("请确保 config.json 或 standalone_config.json 文件存在且包含正确的配置")
    return False


async def main():
    """主函数"""
    print("🚀 Web搜索模块快速启动")
    print("=" * 60)

    # 检查配置文件
    if not check_config_file():
        return

    # 解析命令行参数
    args = sys.argv[1:]
    fetch_full_content = False
    query = None
    single_url = None

    i = 0
    while i < len(args):
        if args[i] == "--full-content":
            fetch_full_content = True
            i += 1
        elif args[i] == "--url" and i + 1 < len(args):
            single_url = args[i + 1]
            i += 2
        elif args[i] in ["-h", "--help", "help"]:
            print_usage()
            return
        else:
            query = args[i]
            i += 1

    # 如果没有提供查询关键词，使用默认值
    if not query and not single_url:
        query = "水轮机"  # 默认查询
        print(f"未提供查询关键词，使用默认关键词: {query}")

    # 执行操作
    if single_url:
        await fetch_single_url(single_url)
    else:
        await search_and_display(query, fetch_full_content)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
    else:
        asyncio.run(main())
