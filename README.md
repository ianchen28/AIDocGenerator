# AIDocGenerator 项目说明

## 项目简介

AIDocGenerator 是一个面向企业的 AI 文档自动生成与智能检索平台，支持多种大模型（LLM）、多通道检索、自动化文档编写与验证，具备灵活的插件式架构，便于二次开发和集成。

---

## 目录结构

```plaintext
AIDocGenerator/
├── service/
│   ├── src/
│   │   └── doc_agent/
│   │       ├── llm_clients/      # 封装各类 LLM/Embedding/Reranker 客户端
│   │       ├── tools/            # Agent 可用工具（如 web_search、es_search 等）
│   │       ├── graph/            # LangGraph 工作流与节点实现
│   │       ├── schemas.py        # Pydantic 数据模型
│   │       └── common.py         # 通用工具/常量
│   ├── api/                      # FastAPI 接口层（如未启用可忽略）
│   ├── workers/                  # 异步任务（如 Celery/ARQ）
│   ├── core/                     # 配置、依赖注入、日志
│   ├── examples/                 # 典型用法/演示脚本
│   ├── tests/                    # 单元与集成测试
│   ├── docs/                     # 项目文档
│   ├── Dockerfile                # 容器化部署
│   └── pyproject.toml            # Python 项目依赖
├── demo/                         # 轻量级演示入口
└── README.md                     # 项目说明
```

---

## 主要功能

- **多模型支持**：支持 OpenAI、Gemini、Qwen、DeepSeek、Moonshot、企业内网模型等
- **多检索通道**：Elasticsearch、Tavily、WebSearch 等
- **自动化文档生成**：任务规划、检索、写作、验证全流程自动化
- **插件式工具体系**：可扩展的 Agent 工具（如代码执行、重排序、嵌入生成等）
- **灵活配置**：支持 YAML/ENV 配置，便于环境切换和多租户部署
- **日志与监控**：集成 loguru，支持多级日志与文件轮转

---

## 快速上手

1. **安装依赖**
   ```bash
   cd service
   pip install -r requirements.txt
   # 或
   poetry install
   ```

2. **配置环境变量**
   - 复制 `.env.example` 为 `.env`，并根据实际填写 API Key、ES 地址等

3. **端到端文档生成测试**
   - 推荐直接运行根目录下的 `_test_graph.py`，可完整体验文档自动生成全流程：
   ```bash
   python _test_graph.py
   ```
   - 运行后会在 `output/` 目录下自动生成本次测试的详细日志、研究数据和最终文档。
   - 可在 `_test_graph.py` 顶部修改主题、参数等，适配不同业务场景。

4. **运行全部单元测试**
   ```bash
   cd service
   python tests/run_all_tests.py
   ```

---

## 主要配置说明

- `service/core/config.yaml`：主配置文件，包含模型、检索、Agent、日志等参数
- `.env`：敏感信息（API Key、数据库密码等），**切勿提交到 git**
- `service/core/config.py`：配置加载与解析逻辑

---

## 典型用法

- **调用 LLM 生成内容**
  ```python
  from src.doc_agent.llm_clients import get_llm_client
  client = get_llm_client("qwen_2_5_235b_a22b")
  result = client.invoke("请介绍一下人工智能")
  print(result)
  ```

- **获取 Embedding 向量**
  ```python
  from src.doc_agent.llm_clients import get_embedding_client
  embedding = get_embedding_client().invoke("文本内容")
  ```

---

## 测试与开发

- 所有测试用例位于 `service/tests/`，可单独或批量运行
- 推荐开发时使用 loguru 日志，便于调试和问题定位
- demo 代码请放在 `examples/`，测试代码请放在 `tests/`，文档请放在 `docs/`

---

## 贡献与反馈

如需贡献代码、提交 issue 或建议，请先阅读 `docs/automation_guide.md` 和 `docs/dev_progress_summary.md`。

---

如需进一步定制 README 内容（如 API 文档、部署说明、CI/CD 指南等），请随时告知！