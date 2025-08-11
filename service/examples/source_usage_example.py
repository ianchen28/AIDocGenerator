"""
Source 类使用示例

展示如何使用新的统一 Source 类来处理不同类型的信息源
"""

from doc_agent.schemas import Source


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 创建不同类型的源
    es_source = Source.create_es_result(id=1,
                                        title="ES搜索结果文档",
                                        content="这是从ES搜索到的相关内容...",
                                        file_token="es_token_123",
                                        page_number=5)

    web_source = Source.create_webpage(id=2,
                                       title="网页搜索结果",
                                       content="这是从网页搜索到的内容...",
                                       url="https://example.com/article",
                                       date="2024-01-15")

    doc_source = Source.create_document(id=3,
                                        title="用户上传文档",
                                        content="这是用户上传的文档内容...",
                                        file_token="doc_token_456")

    print(f"ES源: {es_source.title} (类型: {es_source.source_type})")
    print(f"网页源: {web_source.title} (类型: {web_source.source_type})")
    print(f"文档源: {doc_source.title} (类型: {doc_source.source_type})")


def example_alias_conversion():
    """alias 转换示例"""
    print("\n=== Alias 转换示例 ===")

    source = Source(id=1,
                    source_type="es_result",
                    title="测试文档",
                    content="内容",
                    file_token="test_token",
                    page_number=10)

    # 使用下划线命名（Python风格）
    print(f"Python风格字段:")
    print(f"  source_type: {source.source_type}")
    print(f"  file_token: {source.file_token}")
    print(f"  page_number: {source.page_number}")

    # 转换为驼峰命名（前端风格）
    source_dict = source.model_dump(by_alias=True)
    print(f"\n前端风格字段:")
    print(f"  sourceType: {source_dict['sourceType']}")
    print(f"  fileToken: {source_dict['fileToken']}")
    print(f"  domainId: {source_dict['domainId']}")
    print(f"  originInfo: {source_dict['originInfo'][:50]}...")


def example_redis_integration():
    """Redis 集成示例"""
    print("\n=== Redis 集成示例 ===")

    sources = [
        Source.create_es_result(id=1, title="ES文档1", content="ES内容1"),
        Source.create_webpage(id=2,
                              title="网页1",
                              content="网页内容1",
                              url="https://example1.com"),
        Source.create_es_result(id=3, title="ES文档2", content="ES内容2"),
        Source.create_webpage(id=4,
                              title="网页2",
                              content="网页内容2",
                              url="https://example2.com")
    ]

    # 批量转换为前端格式
    answer_origins, webs = Source.batch_to_redis_fe(sources)

    print(f"answer_origins 数量: {len(answer_origins)}")
    print(f"webs 数量: {len(webs)}")

    # 显示 answer_origins 示例
    if answer_origins:
        print(f"\nanswer_origins 示例:")
        origin = answer_origins[0]
        print(f"  id: {origin['id']}")
        print(f"  title: {origin['title']}")
        print(f"  fileToken: {origin['fileToken']}")
        print(f"  domainId: {origin['domainId']}")

    # 显示 webs 示例
    if webs:
        print(f"\nwebs 示例:")
        web = webs[0]
        print(f"  id: {web['id']}")
        print(f"  materialTitle: {web['materialTitle']}")
        print(f"  siteName: {web['siteName']}")
        print(f"  url: {web['url']}")


def example_serialization():
    """序列化示例"""
    print("\n=== 序列化示例 ===")

    source = Source(id=1,
                    source_type="es_result",
                    title="测试文档",
                    content="这是一个测试文档的内容，用于演示序列化功能。",
                    file_token="serialization_test_token",
                    page_number=15)

    # 转换为字典
    source_dict = source.to_dict()
    print(f"字典格式 (Python风格):")
    print(f"  {source_dict}")

    # 转换为字典（前端风格）
    source_dict_alias = source.to_dict(by_alias=True)
    print(f"\n字典格式 (前端风格):")
    print(f"  {source_dict_alias}")

    # 转换为JSON
    source_json = source.to_json(by_alias=True)
    print(f"\nJSON格式:")
    print(f"  {source_json}")


def example_metadata_handling():
    """元数据处理示例"""
    print("\n=== 元数据处理示例 ===")

    source = Source(id=1,
                    source_type="es_result",
                    title="带元数据的文档",
                    content="文档内容",
                    page_number=25,
                    detail_id="detail_123",
                    code="TEST_CODE",
                    gfid="GF_123")

    print(f"基础字段:")
    print(f"  id: {source.id}")
    print(f"  title: {source.title}")
    print(f"  page_number: {source.page_number}")

    print(f"\n扩展字段:")
    print(f"  detail_id: {source.detail_id}")
    print(f"  code: {source.code}")
    print(f"  gfid: {source.gfid}")

    print(f"\n自动生成的元数据:")
    print(f"  metadata: {source.metadata}")


if __name__ == "__main__":
    example_basic_usage()
    example_alias_conversion()
    example_redis_integration()
    example_serialization()
    example_metadata_handling()

    print("\n=== 示例完成 ===")
