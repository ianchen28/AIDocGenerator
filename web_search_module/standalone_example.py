#!/usr/bin/env python3
"""
Web搜索模块独立使用示例

使用方法:
1. 确保 config.json 文件存在并包含正确的配置
2. 运行: python standalone_example.py
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_search_module import WebSearchService, setup_logger


async def search_example():
    """搜索示例"""
    # 设置日志
    setup_logger()

    print("=== Web搜索模块独立使用示例 ===")

    # 创建web搜索服务
    web_search_service = WebSearchService()

    # 测试查询
    queries = ["水轮机", "水利工程", "发电机组"]

    for query in queries:
        print(f"\n正在搜索: {query}")
        print("-" * 50)

        try:
            result = await web_search_service.get_web_docs(query)

            if result:
                print(f"✅ 搜索到 {len(result)} 个结果:")
                for i, doc in enumerate(result[:2]):  # 只显示前2个结果
                    print(
                        f"  {i+1}. {doc['meta_data'].get('docName', 'Unknown')}"
                    )
                    print(f"     URL: {doc['doc_id']}")
                    print(f"     内容: {doc['text'][:80]}...")
                    print()
            else:
                print("❌ 搜索失败或无结果")

        except Exception as e:
            print(f"❌ 搜索出错: {e}")


async def test_embedding():
    """测试嵌入向量服务"""
    print("\n=== 测试嵌入向量服务 ===")

    from web_search_module import EmbeddingService

    embedding_service = EmbeddingService()

    test_texts = ["这是一个测试文本", "另一个测试文本"]

    try:
        vectors = await embedding_service.get_embeddings(test_texts)
        print(f"✅ 成功生成 {len(vectors)} 个嵌入向量")
        print(f"   向量维度: {len(vectors[0]) if vectors else 0}")
    except Exception as e:
        print(f"❌ 嵌入向量生成失败: {e}")


def check_config():
    """检查配置文件"""
    print("=== 检查配置文件 ===")

    config_files = ["config.json", "standalone_config.json"]

    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ 找到配置文件: {config_file}")
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # 检查web_search_params
                web_params = config.get('web_search_params', {})
                if web_params.get('url') and web_params.get('token'):
                    print(f"   ✅ Web搜索配置完整")
                else:
                    print(f"   ⚠️  Web搜索配置不完整")

                # 检查embedding配置
                embedding_config = config.get('embedding', {})
                if embedding_config.get('gte_qwen_url'):
                    print(f"   ✅ 嵌入向量配置完整")
                else:
                    print(f"   ⚠️  嵌入向量配置不完整")

            except Exception as e:
                print(f"   ❌ 配置文件解析失败: {e}")
        else:
            print(f"❌ 配置文件不存在: {config_file}")


async def main():
    """主函数"""
    print("Web搜索模块独立使用示例")
    print("=" * 50)

    # 检查配置
    check_config()

    # 测试嵌入向量
    await test_embedding()

    # 执行搜索示例
    await search_example()

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
