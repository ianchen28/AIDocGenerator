#!/usr/bin/env python3
"""
pytest配置文件
提供可重用的测试夹具(fixtures)
"""

import pytest


@pytest.fixture(scope="session")
def test_container():
    """
    Session级别的Container fixture
    提供全局容器实例，包含所有已配置的依赖
    """
    try:
        from doc_agent.core.container import container
        yield container
    except ImportError as e:
        pytest.skip(f"Container导入失败，跳过测试: {e}")
    except Exception as e:
        pytest.skip(f"Container初始化失败，跳过测试: {e}")


@pytest.fixture
def sample_research_state():
    """
    样例ResearchState数据
    包含完整的研究状态信息，用于测试各种节点和工作流
    """
    return {
        # 研究主题
        "topic":
        "人工智能在医疗诊断中的应用",

        # 初始研究数据
        "initial_gathered_data":
        """
        人工智能在医疗诊断领域展现出巨大潜力。深度学习技术，特别是卷积神经网络(CNN)，
        在医学影像分析中取得了显著成果。研究表明，AI系统在某些诊断任务中的准确率
        已经接近或超过专业医生的水平。

        主要应用领域包括：
        1. 医学影像诊断：X光、CT、MRI扫描分析
        2. 皮肤病变检测：黑色素瘤识别
        3. 眼科疾病：糖尿病视网膜病变检测
        4. 病理学：癌症细胞识别

        挑战包括数据隐私、监管合规、算法透明度等。
        """,

        # 文档大纲
        "document_outline": {
            "title":
            "人工智能在医疗诊断中的应用研究报告",
            "summary":
            "全面分析AI在医疗诊断领域的应用现状、技术原理、实际案例和未来发展趋势",
            "chapters": [{
                "chapter_number": 1,
                "chapter_title": "引言与背景",
                "description": "介绍人工智能医疗诊断的发展背景和重要性",
                "key_points": ["AI发展历程", "医疗诊断挑战", "技术融合机遇"],
                "estimated_sections": 3
            }, {
                "chapter_number": 2,
                "chapter_title": "核心技术原理",
                "description": "深入分析用于医疗诊断的AI技术原理",
                "key_points": ["深度学习基础", "卷积神经网络", "图像识别算法"],
                "estimated_sections": 4
            }],
            "total_chapters":
            2,
            "estimated_total_words":
            6000
        },

        # 章节处理信息
        "chapters_to_process": [{
            "chapter_title": "引言与背景",
            "description": "介绍人工智能医疗诊断的发展背景和重要性",
            "chapter_number": 1
        }],
        "current_chapter_index":
        0,
        "current_citation_index": 0,  # 添加引用索引初始化

        # 已完成章节内容
        "completed_chapters_content": [],

        # 最终文档
        "final_document":
        "",

        # 章节级研究状态
        "research_plan":
        "针对引言章节的研究计划：收集AI医疗发展历史和现状数据",
        "search_queries": ["人工智能医疗诊断发展历史", "AI医学影像识别技术原理"],
        "gathered_data":
        "AI医疗诊断市场预计2025年将达到450亿美元，FDA已批准超过100个AI医疗设备",

        # 对话历史
        "messages": []
    }


@pytest.fixture
def sample_outline():
    """
    样例文档大纲JSON
    标准的大纲结构，用于测试大纲生成和处理功能
    """
    return {
        "title":
        "机器学习基础教程",
        "nodes": [{
            "id":
            "intro",
            "title":
            "机器学习概述",
            "content_summary":
            "介绍机器学习的基本概念、历史发展和主要分类",
            "children": [{
                "id": "intro_basic",
                "title": "基本概念",
                "content_summary": "定义机器学习及其核心要素",
                "children": []
            }]
        }, {
            "id":
            "algorithms",
            "title":
            "核心算法",
            "content_summary":
            "详细介绍主要的机器学习算法原理和应用",
            "children": [{
                "id": "supervised",
                "title": "监督学习",
                "content_summary": "分类和回归算法详解",
                "children": []
            }]
        }]
    }


@pytest.fixture
def sample_job_data():
    """
    样例作业数据
    用于测试API端点和任务处理
    """
    return {
        "job_id": "job-test123456",
        "task_prompt": "编写一份关于区块链技术的技术白皮书",
        "context_id": "ctx-blockchain001",
        "status": "CREATED",
        "created_at": "2025-01-27T10:30:00Z"
    }


@pytest.fixture
def sample_context_data():
    """
    样例上下文数据
    用于测试上下文创建和管理功能
    """
    return {
        "context_id":
        "ctx-sample123",
        "files": [{
            "file_id": "file-001",
            "file_name": "technical_specification.pdf",
            "storage_url": "s3://test-bucket/specs.pdf"
        }, {
            "file_id": "file-002",
            "file_name": "market_analysis.docx",
            "storage_url": "s3://test-bucket/analysis.docx"
        }],
        "status":
        "READY",
        "created_at":
        "2025-01-27T09:15:00Z"
    }


@pytest.fixture
def mock_redis_data():
    """
    模拟Redis数据
    用于测试Redis相关功能
    """
    return {
        "job:job-test123456": {
            "job_id": "job-test123456",
            "task_prompt": "测试任务提示",
            "status": "processing",
            "created_at": "2025-01-27T10:30:00Z"
        },
        "job:job-test123456:outline": {
            "outline_status": "READY",
            "outline_data": '{"title": "测试大纲", "nodes": []}',
            "completed_at": "2025-01-27T10:35:00Z"
        },
        "job:job-test123456:document": {
            "content": "这是生成的测试文档内容...",
            "word_count": 150,
            "char_count": 800,
            "created_at": "2025-01-27T10:45:00Z"
        }
    }


@pytest.fixture
def sample_api_requests():
    """
    样例API请求数据
    用于测试各种API端点
    """
    return {
        "create_context": {
            "files": [{
                "file_id": "api-test-001",
                "file_name": "requirement.pdf",
                "storage_url": "s3://api-test/requirement.pdf"
            }]
        },
        "create_job": {
            "task_prompt": "基于需求文档编写技术方案",
            "context_id": "ctx-api-test"
        },
        "update_outline": {
            "outline": {
                "title":
                "技术方案文档",
                "nodes": [{
                    "id": "overview",
                    "title": "方案概述",
                    "content_summary": "整体技术方案的概述",
                    "children": []
                }]
            }
        }
    }
