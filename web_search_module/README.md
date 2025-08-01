# Web搜索模块独立使用指南

## 概述

这是一个从cyber-rag项目中提取的独立web搜索模块，可以直接在其他项目中使用。**新增了网页全文抓取功能**，可以获取URL的完整内容。

## 文件结构

```
examples/
├── web_search_module.py      # 主要的web搜索模块
├── web_search_requirements.txt  # 依赖文件
├── standalone_example.py     # 独立使用示例
├── run_web_search.py        # 快速启动脚本
├── fetch_url_content.py     # URL内容获取工具
├── config.json              # 配置文件（从原项目复制）
└── README.md               # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r web_search_requirements.txt
```

### 2. 配置

确保 `config.json` 文件存在并包含正确的配置：

```json
{
    "web_search_params": {
        "url": "http://10.215.149.74:9930/api/v1/llm-qa/api/chat/net",
        "token": "your-api-token"
    },
    "embedding": {
        "gte_qwen_url": "http://10.215.58.199:13037/embed"
    }
}
```

### 3. 快速测试

#### 基本搜索
```bash
# 使用默认关键词测试
python run_web_search.py

# 使用自定义关键词测试
python run_web_search.py "水轮机"
python run_web_search.py "水利工程"
```

#### 获取完整内容
```bash
# 搜索并获取网页完整内容
python run_web_search.py "水轮机" --full-content

# 获取单个URL的完整内容
python fetch_url_content.py "https://example.com"
```

### 4. 在代码中使用

#### 基本搜索
```python
import asyncio
from web_search_module import WebSearchService, setup_logger

async def main():
    # 设置日志
    setup_logger()
    
    # 创建web搜索服务
    web_search_service = WebSearchService()
    
    # 执行搜索
    results = await web_search_service.get_web_docs("查询关键词")
    
    # 处理结果
    for doc in results:
        print(f"标题: {doc['meta_data'].get('docName')}")
        print(f"URL: {doc['doc_id']}")
        print(f"内容: {doc['text'][:100]}...")

# 运行
asyncio.run(main())
```

#### 获取完整内容
```python
import asyncio
from web_search_module import WebSearchService, setup_logger

async def main():
    # 设置日志
    setup_logger()
    
    # 创建web搜索服务
    web_search_service = WebSearchService()
    
    # 搜索并获取完整内容
    results = await web_search_service.get_web_docs("查询关键词", fetch_full_content=True)
    
    # 处理结果
    for doc in results:
        print(f"标题: {doc['meta_data'].get('docName')}")
        print(f"URL: {doc['doc_id']}")
        print(f"内容长度: {len(doc['text'])} 字符")
        print(f"是否获取完整内容: {doc.get('full_content_fetched', False)}")
        print(f"内容: {doc['text'][:200]}...")

# 运行
asyncio.run(main())
```

#### 获取单个URL的完整内容
```python
import asyncio
from web_search_module import WebSearchService, setup_logger

async def main():
    # 设置日志
    setup_logger()
    
    # 创建web搜索服务
    web_search_service = WebSearchService()
    
    # 获取单个URL的完整内容
    url = "https://example.com"
    content = await web_search_service.get_full_content_for_url(url)
    
    if content:
        print(f"成功获取内容，长度: {len(content)} 字符")
        print(f"内容预览: {content[:200]}...")
    else:
        print("获取内容失败")

# 运行
asyncio.run(main())
```

## 配置说明

### 环境变量

你可以通过环境变量覆盖配置文件中的设置：

```bash
export WEB_SEARCH_URL="http://your-api-url"
export WEB_SEARCH_TOKEN="your-api-token"
export EMBEDDING_URL="http://your-embedding-url"
export WEB_SEARCH_COUNT="10"
export WEB_SEARCH_TIMEOUT="3"
export WEB_SEARCH_RETRIES="5"
export WEB_SEARCH_DELAY="2"
export FETCH_FULL_CONTENT="true"  # 新增：是否获取完整内容
```

### 配置文件优先级

1. 环境变量（最高优先级）
2. config.json 文件
3. 默认值（最低优先级）

## API接口

### WebSearchService

#### get_web_docs(query: str, fetch_full_content: bool = None) -> List[Dict[str, Any]]

获取格式化的web搜索文档。

**参数:**
- query: 查询字符串
- fetch_full_content: 是否获取完整内容，None时使用配置中的设置

**返回:**
- 格式化的文档列表，每个文档包含：
  - doc_id: 文档ID (URL)
  - doc_type: 文档类型 ("text")
  - domain_ids: 域名列表 (["web"])
  - meta_data: 原始元数据
  - context_vector: 文本嵌入向量
  - text: 文档内容
  - _id: 材料ID
  - rank: 排名
  - full_content_fetched: 是否获取了完整内容

#### get_web_search(query: str) -> Optional[List[Dict[str, Any]]]

异步请求外部搜索接口。

**参数:**
- query: 查询字符串

**返回:**
- 成功时返回搜索结果列表
- 失败时返回None

#### get_full_content_for_url(url: str) -> Optional[str]

获取指定URL的完整内容。

**参数:**
- url: 网页URL

**返回:**
- 网页的完整文本内容

### EmbeddingService

#### get_embeddings(input_texts: List[str], max_retries: int = 3, timeout: int = 10) -> List[List[float]]

获取文本嵌入向量。

**参数:**
- input_texts: 文本列表
- max_retries: 最大重试次数
- timeout: 请求超时时间

**返回:**
- 嵌入向量列表

### WebScraper

#### fetch_full_content(url: str, timeout: int = 10) -> Optional[str]

获取网页的完整内容。

**参数:**
- url: 网页URL
- timeout: 超时时间

**返回:**
- 网页的完整文本内容，失败时返回None

## 网页全文抓取功能

### 功能特点

1. **智能内容提取**: 自动移除HTML标签，提取纯文本内容
2. **内容清理**: 去除多余的空白字符和格式
3. **错误处理**: 完善的异常处理机制
4. **超时控制**: 防止长时间等待
5. **用户代理**: 模拟真实浏览器访问

### 使用场景

1. **搜索结果增强**: 获取搜索结果的完整内容
2. **内容分析**: 对网页内容进行文本分析
3. **数据收集**: 批量获取网页内容
4. **文档处理**: 将网页内容转换为结构化数据

### 注意事项

1. **反爬虫机制**: 某些网站可能有反爬虫措施
2. **JavaScript渲染**: 动态内容可能无法获取
3. **访问频率**: 避免过于频繁的请求
4. **内容版权**: 注意遵守网站的使用条款

## 错误处理

模块内置了完善的错误处理机制：

1. **网络请求失败**: 自动重试，记录详细日志
2. **API响应错误**: 抛出异常并记录错误信息
3. **嵌入向量生成失败**: 返回空结果，记录错误日志
4. **配置错误**: 使用默认配置或抛出配置错误
5. **网页抓取失败**: 记录详细错误信息

## 日志配置

模块使用loguru进行日志记录：

- 控制台彩色输出
- 文件轮转日志（保存在 `logs/web_search.log`）
- 结构化日志格式

## 性能优化

1. **异步处理**: 所有网络请求都是异步的
2. **批量处理**: 嵌入向量生成支持批量处理
3. **超时控制**: 防止长时间等待
4. **重试机制**: 提高请求成功率
5. **文本截断**: 限制文本长度避免API限制
6. **内容缓存**: 避免重复抓取相同内容

## 移植到其他项目

1. 复制 `web_search_module.py` 到目标项目
2. 安装依赖: `pip install aiohttp loguru beautifulsoup4 lxml`
3. 配置搜索API和嵌入API地址
4. 根据需要调整配置参数
5. 集成到现有代码中

## 故障排除

### 常见问题

1. **配置文件不存在**
   - 确保 `config.json` 文件存在
   - 检查文件格式是否正确

2. **网络连接失败**
   - 检查网络连接
   - 验证API地址是否正确
   - 确认API服务是否可用

3. **认证失败**
   - 检查API token是否正确
   - 确认token是否过期

4. **嵌入向量生成失败**
   - 检查嵌入API地址
   - 确认API服务状态

5. **网页抓取失败**
   - 检查URL是否可访问
   - 确认网站是否有反爬虫机制
   - 验证网络连接

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 示例输出

### 基本搜索
```
🚀 Web搜索模块快速启动
============================================================
✅ 配置文件 config.json 检查通过
🔍 正在搜索: 水轮机
============================================================
✅ 搜索成功！找到 3 个结果:

📄 结果 1:
   标题: 水轮机技术规范
   URL: http://example.com/doc1
   排名: 1
   内容长度: 150 字符
   是否获取完整内容: False
   内容预览: 水轮机是一种将水能转换为机械能的装置...
   向量维度: 1024
------------------------------------------------------------
```

### 获取完整内容
```
🚀 Web搜索模块快速启动
============================================================
✅ 配置文件 config.json 检查通过
🔍 正在搜索: 水轮机
📄 将获取网页完整内容
============================================================
✅ 搜索成功！找到 3 个结果:

📄 结果 1:
   标题: 水轮机技术规范
   URL: http://example.com/doc1
   排名: 1
   内容长度: 2500 字符
   是否获取完整内容: True
   内容预览: 水轮机是一种将水能转换为机械能的装置，广泛应用于水力发电站...
   向量维度: 1024
------------------------------------------------------------
```

### URL内容获取
```
🚀 URL内容获取工具
============================================================
🔍 正在获取URL内容: https://example.com
============================================================
✅ 成功获取内容！
   内容长度: 1500 字符
   内容行数: 45
   单词数量: 250
   平均单词长度: 4.2

📄 内容预览 (前500字符):
----------------------------------------
Welcome to Example.com. This is a sample website...
----------------------------------------

💾 完整内容已保存到: content_example_com.txt
   文件大小: 2048 字节 (2.0 KB)
```

## 许可证

本模块遵循原项目的许可证条款。 