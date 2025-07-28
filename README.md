# AI文档生成器 (AIDocGenerator)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io)

## 🚀 项目简介

AIDocGenerator 是一个**企业级AI文档自动生成平台**，集成了多种大语言模型、智能检索系统和实时事件流监控。支持从需求分析到文档生成的完整工作流，具备大纲交互、实时监控、异步处理等企业级特性。

### ✨ 核心特性

- 🤖 **多模型支持**：OpenAI、Gemini、Qwen、DeepSeek、企业内网模型等
- 📋 **交互式大纲**：用户可编辑大纲，支持个性化定制
- 🔄 **实时事件流**：Redis驱动的实时监控，支持SSE事件推送
- 🛠️ **异步架构**：基于FastAPI + Redis的高性能异步处理
- 🔍 **多源检索**：Elasticsearch、网络搜索、向量检索等
- 📊 **完整监控**：从任务创建到文档生成的全链路追踪
- 🧩 **插件化设计**：可扩展的Agent工具生态

---

## 📁 项目架构

```plaintext
AIDocGenerator/
├── service/
│   ├── api/                      # 🌐 REST API层
│   │   ├── main.py              # FastAPI应用入口
│   │   └── endpoints.py         # API端点实现
│   ├── workers/                  # ⚡ 异步任务处理
│   │   └── tasks.py             # Redis任务队列
│   ├── src/doc_agent/
│   │   ├── graph/               # 🔗 LangGraph工作流
│   │   │   ├── callbacks.py    # Redis事件回调
│   │   │   ├── main_orchestrator/ # 主编排器
│   │   │   └── chapter_workflow/  # 章节处理
│   │   ├── llm_clients/         # 🧠 LLM客户端封装
│   │   ├── tools/               # 🛠️ Agent工具集
│   │   └── schemas.py           # 📝 数据模型
│   ├── core/                    # ⚙️ 核心配置
│   │   ├── container.py         # 依赖注入容器
│   │   ├── config.py/.yaml      # 配置管理
│   │   └── logging_config.py    # 日志配置
│   ├── examples/                # 📚 演示脚本
│   │   ├── api_demo.py         # API完整演示
│   │   └── redis_events_demo.py # 事件流演示
│   ├── tests/                   # 🧪 测试套件
│   └── docs/                    # 📖 项目文档
├── examples/                    # 💡 使用示例
└── tests/                       # 🔬 集成测试
```

---

## 🎯 核心功能

### 1. 📋 交互式大纲生成

- 智能分析用户需求，生成结构化大纲
- 支持用户编辑和个性化定制
- 大纲确认后自动触发文档生成

### 2. 🔄 实时事件监控

- Redis驱动的实时事件流
- 支持阶段更新、工具调用、错误处理等事件
- 完整的执行过程透明化

### 3. 🤖 智能文档生成

- 多阶段工作流：研究 → 规划 → 写作 → 验证
- 支持多种检索源：ES、网络搜索、向量检索
- 自动化的内容生成和质量控制

### 4. 🌐 企业级API

- RESTful设计，支持完整的CRUD操作
- 异步处理，高并发支持
- 完整的错误处理和状态管理

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Redis 7.0+
- Elasticsearch 8.0+ (可选)

### 1. 安装依赖

```bash
cd service
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件：
```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0

# LLM API Keys
OPENAI_API_KEY=your_openai_key
CHATAI_API_KEY=your_chatai_key
DEEPSEEK_API_KEY=your_deepseek_key

# 网络搜索
TAVILY_API_KEY=your_tavily_key

# 企业内网模型配置
ONE_API_BASE=http://your-api-gateway/v1
ONE_API_KEY=your_enterprise_key
```

### 3. 启动服务

```bash
# 启动Redis
redis-server

# 启动API服务
uvicorn service.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 验证安装

```bash
# 健康检查
curl http://localhost:8000/
curl http://localhost:8000/api/v1/health
```

---

## 📖 API使用指南

### 完整工作流

#### 1. 创建上下文（可选）

```bash
curl -X POST "http://localhost:8000/api/v1/contexts" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "file_id": "doc-001", 
        "file_name": "参考文档.pdf",
        "storage_url": "s3://bucket/doc.pdf"
      }
    ]
  }'
```

#### 2. 创建文档生成作业

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "task_prompt": "编写一份关于机器学习基础知识的技术文档",
    "context_id": "ctx-abc123"
  }'
```

#### 3. 生成大纲

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/job-xyz789/outline"
```

#### 4. 获取生成的大纲

```bash
curl "http://localhost:8000/api/v1/jobs/job-xyz789/outline"
```

#### 5. 编辑并确认大纲

```bash
curl -X PUT "http://localhost:8000/api/v1/jobs/job-xyz789/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "outline": {
      "title": "机器学习基础教程",
      "nodes": [
        {
          "id": "intro",
          "title": "机器学习导论", 
          "content_summary": "介绍机器学习的基本概念",
          "children": []
        }
      ]
    }
  }'
```

### API端点总览

| 端点 | 方法 | 描述 | 状态码 |
|------|------|-----|--------|
| `/` | GET | 根健康检查 | 200 |
| `/api/v1/health` | GET | API健康检查 | 200 |
| `/api/v1/contexts` | POST | 创建文件上下文 | 202 |
| `/api/v1/jobs` | POST | 创建文档生成作业 | 201 |
| `/api/v1/jobs/{job_id}/outline` | POST | 触发大纲生成 | 202 |
| `/api/v1/jobs/{job_id}/outline` | GET | 获取生成的大纲 | 200 |
| `/api/v1/jobs/{job_id}/outline` | PUT | 更新大纲并开始最终生成 | 200 |

---

## 🎭 演示脚本

### 1. 完整API演示

```bash
python examples/api_demo.py
```
展示完整的API使用流程：创建作业 → 生成大纲 → 编辑确认 → 最终生成

### 2. 实时事件流演示

```bash
# 完整演示（自动创建作业并监听事件）
python examples/redis_events_demo.py

# 简单监听（输入现有作业ID）
python examples/redis_events_demo.py simple
```

### 3. 传统命令行测试

```bash
# 端到端文档生成（无API）
python _test_graph.py

# 快速模式测试
python test_fast_mode.py
```

---

## 📡 实时事件监控

系统通过Redis发布以下实时事件：

| 事件类型 | 描述 | 示例数据 |
|---------|------|----------|
| `phase_update` | 工作流阶段更新 | `{"phase": "RETRIEVAL", "message": "开始检索信息..."}` |
| `thought` | LLM思考过程 | `{"text": "正在分析用户需求...", "model_name": "qwen"}` |
| `tool_call` | 工具调用事件 | `{"tool_name": "web_search", "status": "START"}` |
| `source_found` | 发现信息源 | `{"source_type": "document", "title": "研究报告"}` |
| `error` | 错误事件 | `{"code": 5001, "message": "网络连接超时"}` |
| `done` | 任务完成 | `{"task": "main_workflow", "message": "文档生成完成"}` |

### 监听事件示例

```python
import aioredis
import json

async def listen_events(job_id):
    redis = aioredis.from_url("redis://localhost:6379")
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"job:{job_id}:events")
    
    async for message in pubsub.listen():
        if message['type'] == 'message':
            event = json.loads(message['data'])
            print(f"事件: {event['event']} - {event['data']}")
```

---

## 🧪 测试

### 运行所有测试

```bash
# API端点测试
pytest tests/test_api_endpoints.py -v

# Redis回调处理器测试  
pytest tests/test_redis_callbacks.py -v

# 服务层测试
cd service
python tests/run_all_tests.py
```

### 测试覆盖

- Unit Tests: 核心组件单元测试
- Integration Tests: API集成测试
- E2E Tests: 端到端工作流测试

---

## ⚙️ 配置说明

### 主配置文件 (`service/core/config.yaml`)

```yaml
# 支持的模型配置
supported_models:
  qwen_2_5_235b_a22b:
    name: "Qwen3-235B-A22B"
    type: "enterprise_generate"
    url: "${ONE_API_BASE}"
    api_key: "${ONE_API_KEY}"
  
  gemini_1_5_pro:
    name: "Gemini 1.5 Pro"
    type: "external_generate"
    url: "${CHATAI_BASE_URL}"
    api_key: "${CHATAI_API_KEY}"

# Agent组件配置
agent_config:
  default_llm: "qwen_2_5_235b_a22b"
  task_planner:
    provider: "qwen_2_5_235b_a22b"
    temperature: 0.7
    max_tokens: 2000
```

### 环境变量配置

- 敏感信息通过 `.env` 文件管理
- 支持环境变量替换
- 多环境配置支持

---

## 🏗️ 高级功能

### 1. 自定义LLM客户端

```python
from service.src.doc_agent.llm_clients import get_llm_client

# 获取特定模型客户端
client = get_llm_client("qwen_2_5_235b_a22b") 
result = client.invoke("你的提示")
```

### 2. 扩展Agent工具

```python
from service.src.doc_agent.tools import register_tool

@register_tool
def custom_tool(input_str: str) -> str:
    """自定义工具实现"""
    return f"处理结果: {input_str}"
```

### 3. 自定义回调处理器

```python
from service.src.doc_agent.graph.callbacks import RedisCallbackHandler

class CustomCallback(RedisCallbackHandler):
    def on_custom_event(self, data):
        # 自定义事件处理逻辑
        pass
```

---

## 🚀 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t aidoc-generator .

# 运行容器
docker run -p 8000:8000 -e REDIS_URL=redis://host:6379 aidoc-generator
```

### 生产环境推荐

- 使用Nginx作为反向代理
- Redis集群配置
- 监控和日志聚合
- 负载均衡配置

---

## 📊 性能特点

- **并发处理**：支持多作业并行执行
- **异步架构**：基于FastAPI的高性能异步处理
- **实时监控**：毫秒级事件推送
- **内存优化**：流式处理大文档
- **错误恢复**：完整的异常处理和重试机制

---

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 开发规范

- 代码请放在对应的目录：`examples/`（演示）、`tests/`（测试）、`docs/`（文档）
- 使用loguru进行日志记录
- 遵循现有的代码风格和架构

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🆘 常见问题

### Q: Redis连接失败？

A: 确保Redis服务正在运行，检查连接配置和网络设置。

### Q: API返回422错误？

A: 检查请求数据格式，确保必需字段都已提供。

### Q: 大纲生成一直是GENERATING状态？

A: 检查LLM配置和API密钥，查看日志获取详细错误信息。

### Q: 如何添加新的LLM模型？

A: 在`config.yaml`中添加模型配置，确保API密钥和地址正确。

---

## 📞 联系方式

- 🐛 问题报告：[GitHub Issues](https://github.com/your-repo/issues)
- 💬 讨论交流：[GitHub Discussions](https://github.com/your-repo/discussions)  
- 📧 邮件联系：your-email@example.com

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**