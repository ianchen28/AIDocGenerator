"""
测试新的统一 Source 类
"""

import pytest
from doc_agent.schemas import Source


def test_source_basic_creation():
    """测试基本的 Source 创建"""
    source = Source(id=1,
                    source_type="es_result",
                    title="测试文档",
                    content="这是一个测试文档的内容")

    assert source.id == 1
    assert source.source_type == "es_result"
    assert source.title == "测试文档"
    assert source.content == "这是一个测试文档的内容"


def test_source_alias_conversion():
    """测试 alias 转换功能"""
    source = Source(id=1,
                    source_type="es_result",
                    title="测试文档",
                    content="内容",
                    file_token="test_token")

    # 使用 model_dump() 测试 alias 转换
    source_dict = source.model_dump(by_alias=True)

    # 检查下划线字段转换为驼峰字段
    assert "fileToken" in source_dict
    assert source_dict["fileToken"] == "test_token"
    assert "sourceType" in source_dict
    assert source_dict["sourceType"] == "es_result"


def test_source_es_result_creation():
    """测试 ES 结果源的创建"""
    source = Source.create_es_result(id=1,
                                     title="ES搜索结果",
                                     content="ES搜索到的内容",
                                     file_token="es_token_123",
                                     page_number=5)

    assert source.source_type == "es_result"
    assert source.file_token == "es_token_123"
    assert source.page_number == 5

    # 检查前端字段自动填充
    assert source.file_token == "es_token_123"
    assert source.domain_id == "document"
    assert source.is_valid is True


def test_source_webpage_creation():
    """测试网页源的创建"""
    source = Source.create_webpage(id=2,
                                   title="测试网页",
                                   content="网页内容",
                                   url="https://example.com/test",
                                   date="2024-01-01")

    assert source.source_type == "webpage"
    assert source.url == "https://example.com/test"
    assert source.date == "2024-01-01"

    # 检查前端字段自动填充
    assert source.date_published == "2024-01-01"
    assert source.material_content == "网页内容"
    assert source.material_id == "web_2"
    assert source.material_title == "测试网页"
    assert source.site_name == "example.com"


def test_source_document_creation():
    """测试文档源的创建"""
    source = Source.create_document(id=3,
                                    title="测试文档",
                                    content="文档内容",
                                    file_token="doc_token_456")

    assert source.source_type == "document"
    assert source.file_token == "doc_token_456"

    # 检查前端字段自动填充
    assert source.file_token == "doc_token_456"
    assert source.material_id == "doc_3"


def test_source_metadata_auto_population():
    """测试元数据自动填充"""
    source = Source(id=4,
                    source_type="es_result",
                    title="带页码的文档",
                    content="文档内容",
                    page_number=10)

    # 检查元数据自动填充
    assert "file_name" in source.metadata
    assert source.metadata["file_name"] == "带页码的文档"
    assert "locations" in source.metadata
    assert len(source.metadata["locations"]) == 1
    assert source.metadata["locations"][0]["pagenum"] == 10
    assert source.metadata["source"] == "data_platform"


def test_source_content_length_limit():
    """测试内容长度限制"""
    long_content = "很长的内容" * 200  # 创建很长的内容

    source = Source(id=5,
                    source_type="es_result",
                    title="长内容文档",
                    content=long_content)

    # 检查内容被限制到1000字符
    assert len(source.origin_info) <= 1000
    assert len(source.material_content) <= 1000


def test_batch_to_redis_fe():
    """测试批量转换为前端格式"""
    sources = [
        Source.create_es_result(id=1, title="ES文档1", content="ES内容1"),
        Source.create_webpage(id=2,
                              title="网页1",
                              content="网页内容1",
                              url="https://example1.com"),
        Source.create_es_result(id=3, title="ES文档2", content="ES内容2")
    ]

    answer_origins, webs = Source.batch_to_redis_fe(sources)

    # 应该有2个 answer_origins (es_result)
    assert len(answer_origins) == 2
    assert answer_origins[0]["id"] == 1
    assert answer_origins[1]["id"] == 3

    # 应该有1个 webs (webpage)
    assert len(webs) == 1
    assert webs[0]["id"] == 2

    # 检查字段格式
    assert "fileToken" in answer_origins[0]
    assert "domainId" in answer_origins[0]
    assert "datePublished" in webs[0]
    assert "materialContent" in webs[0]


def test_source_to_dict_methods():
    """测试 to_dict 和 to_json 方法"""
    source = Source(id=6, source_type="es_result", title="测试文档", content="内容")

    # 测试 to_dict
    source_dict = source.to_dict()
    assert isinstance(source_dict, dict)
    assert source_dict["id"] == 6

    # 测试 to_dict with alias
    source_dict_alias = source.to_dict(by_alias=True)
    assert "sourceType" in source_dict_alias
    assert "fileToken" in source_dict_alias

    # 测试 to_json
    source_json = source.to_json()
    assert isinstance(source_json, str)
    assert "测试文档" in source_json


def test_source_extra_fields():
    """测试额外字段支持"""
    source = Source(id=7,
                    source_type="es_result",
                    title="测试文档",
                    content="内容",
                    detail_id="detail_123",
                    code="TEST_CODE",
                    gfid="GF_123")

    assert source.detail_id == "detail_123"
    assert source.code == "TEST_CODE"
    assert source.gfid == "GF_123"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
