#!/usr/bin/env python3
"""
文件模块测试脚本
测试上传、下载和解析功能
"""

import os
import json
import tempfile
from pathlib import Path
from loguru import logger

# 导入文件处理器
from file_processor import FileProcessor


def create_test_files():
    """创建测试文件"""
    test_files = {}

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    logger.info(f"创建临时目录: {temp_dir}")

    # 1. 创建测试文本文件
    text_content = """这是一个测试文档
包含多个段落的内容。

第二段落包含一些重要信息：
- 项目名称：AI文档生成器
- 版本：1.0.0
- 功能：自动生成文档大纲和内容

第三段落包含技术细节：
使用Python和FastAPI构建的后端服务，
支持多种文档格式的解析和处理。"""

    text_file = os.path.join(temp_dir, "test_document.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    test_files['txt'] = text_file

    # 2. 创建测试JSON文件
    json_content = {
        "title":
        "测试大纲",
        "sections": [{
            "title": "第一章 介绍",
            "content": "本章介绍项目背景和目标"
        }, {
            "title": "第二章 技术架构",
            "content": "本章描述系统的技术架构设计"
        }, {
            "title": "第三章 实现细节",
            "content": "本章详细说明具体的实现方案"
        }]
    }

    json_file = os.path.join(temp_dir, "test_outline.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_content, f, ensure_ascii=False, indent=2)
    test_files['json'] = json_file

    # 3. 创建测试Markdown文件
    md_content = """# 测试文档

## 项目概述
这是一个用于测试文件模块的示例文档。

### 功能特性
- 支持多种文件格式
- 自动解析和提取内容
- 集成存储服务

### 技术栈
- Python 3.8+
- FastAPI
- Redis
- Elasticsearch

## 使用说明
1. 上传文件到存储服务
2. 获取文件token
3. 使用token下载和解析文件

## 注意事项
请确保网络连接正常，存储服务可用。
"""

    md_file = os.path.join(temp_dir, "test_document.md")
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    test_files['md'] = md_file

    return test_files, temp_dir


def test_file_processor():
    """测试文件处理器功能"""
    logger.info("开始测试文件处理器...")

    # 初始化文件处理器
    processor = FileProcessor(storage_base_url="http://ai.test.hcece.net",
                              app="hdec",
                              app_secret="hdec_secret",
                              tenant_id="100023")

    # 创建测试文件
    test_files, temp_dir = create_test_files()

    try:
        # 测试1: 上传文件
        logger.info("=== 测试1: 文件上传 ===")
        uploaded_tokens = {}

        for file_type, file_path in test_files.items():
            logger.info(f"上传 {file_type} 文件: {file_path}")
            try:
                file_token = processor.upload_file(file_path)
                uploaded_tokens[file_type] = file_token
                logger.success(f"{file_type} 文件上传成功，Token: {file_token}")
            except Exception as e:
                logger.error(f"{file_type} 文件上传失败: {e}")

        # 测试2: 生成下载URL
        logger.info("=== 测试2: 生成下载URL ===")
        for file_type, token in uploaded_tokens.items():
            try:
                download_url = processor.generate_download_url(token)
                logger.info(f"{file_type} 文件下载URL: {download_url}")
            except Exception as e:
                logger.error(f"生成 {file_type} 下载URL失败: {e}")

        # 测试3: 下载并解析文件
        logger.info("=== 测试3: 下载并解析文件 ===")
        download_dir = os.path.join(temp_dir, "downloads")
        os.makedirs(download_dir, exist_ok=True)

        for file_type, token in uploaded_tokens.items():
            try:
                logger.info(f"下载并解析 {file_type} 文件...")
                parsed_content = processor.download_and_parse(
                    token, file_type, download_dir)
                logger.success(
                    f"{file_type} 文件解析成功，内容长度: {len(parsed_content)}")

                # 打印解析结果的前几项
                for i, item in enumerate(parsed_content[:3]):
                    logger.info(f"  内容项 {i+1}: {item[0]} - {item[1][:100]}...")

            except Exception as e:
                logger.error(f"{file_type} 文件下载解析失败: {e}")

        # 测试4: 测试大纲内容上传
        logger.info("=== 测试4: 大纲内容上传 ===")
        outline_content = {
            "title":
            "AI文档生成器技术文档",
            "sections": [{
                "title":
                "1. 项目概述",
                "subsections": [{
                    "title": "1.1 项目背景",
                    "content": "介绍项目背景和目标"
                }, {
                    "title": "1.2 技术栈",
                    "content": "描述使用的技术栈"
                }]
            }, {
                "title":
                "2. 系统架构",
                "subsections": [{
                    "title": "2.1 整体架构",
                    "content": "系统整体架构设计"
                }, {
                    "title": "2.2 核心模块",
                    "content": "核心功能模块说明"
                }]
            }]
        }

        # 将大纲内容保存为临时文件
        outline_file = os.path.join(temp_dir, "outline.json")
        with open(outline_file, 'w', encoding='utf-8') as f:
            json.dump(outline_content, f, ensure_ascii=False, indent=2)

        try:
            outline_token = processor.upload_file(outline_file)
            logger.success(f"大纲文件上传成功，Token: {outline_token}")

            # 模拟从token下载并解析大纲
            parsed_outline = processor.download_and_parse(
                outline_token, "json", download_dir)
            logger.success(f"大纲解析成功，内容长度: {len(parsed_outline)}")

        except Exception as e:
            logger.error(f"大纲文件处理失败: {e}")

        logger.success("所有测试完成！")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"临时目录已清理: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logger.add("test_file_module.log", rotation="1 MB", level="INFO")

    test_file_processor()
