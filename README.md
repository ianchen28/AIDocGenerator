# 架构

my_document_agent/
├── service/
│   ├── src/
│   │   └── doc_agent/
│   │       ├── __init__.py
│   │       │
│   │       ├── schemas.py         # <--- 【基础】定义所有Pydantic数据模型 (API请求/响应)
│   │       │
│   │       ├── llm_clients/       # <--- 封装对不同LLM API的调用
│   │       │   ├── __init__.py    # <--- 实现获取Client的工厂函数
│   │       │   ├── base.py
│   │       │   └── providers.py   # <--- 具体实现 (OpenAI, Anthropic, Internal...)
│   │       │
│   │       ├── tools/             # <--- Agent可以使用的工具
│   │       │   ├── __init__.py
│   │       │   └── web_search.py
│   │       │
│   │       └── graph/             # <--- 【核心】所有LangGraph的逻辑
│   │           ├── __init__.py
│   │           ├── state.py       # <--- 定义图的状态对象 (ResearchState)
│   │           ├── nodes.py       # <--- 定义所有节点的具体实现函数
│   │           ├── router.py      # <--- 定义条件路由 (Supervisor的决策逻辑)
│   │           └── builder.py     # <--- 搭建和编译整个图
│   │
│   ├── api/                     # <--- FastAPI 接口层
│   │   ├── __init__.py
│   │   ├── endpoints.py         # <--- API路由 (start, status, result)
│   │   └── dependencies.py      # <--- API层的依赖项 (如任务队列客户端)
│   │
│   ├── workers/                 # <--- 异步任务处理 (Celery/ARQ)
│   │   ├── __init__.py
│   │   └── tasks.py             # <--- 定义异步任务，任务内部调用Graph
│   │
│   ├── core/                    # <--- 应用的核心配置和启动管理
│   │   ├── __init__.py
│   │   ├── config.py            # <--- 加载环境变量和配置
│   │   └── container.py         # <--- 【关键】依赖注入容器，实例化所有服务
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
│
├── demo/
│   ├── app.py
│   └── requirements.txt
│
└── README.md
