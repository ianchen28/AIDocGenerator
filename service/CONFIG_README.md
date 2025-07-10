# 配置系统使用说明

## 概述

本项目的配置系统支持从环境变量和YAML文件加载配置，提供了灵活的配置管理方案。

## 配置结构

### 1. 环境变量配置

创建 `.env` 文件，包含以下配置：

```bash
# 基础配置
REDIS_URL=redis://localhost:6379/0

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# 内部LLM配置
INTERNAL_LLM_API_URL=http://localhost:8000/v1
INTERNAL_LLM_API_KEY=your_internal_api_key_here

# Reranker配置
RERANKER_API_URL=http://localhost:39939/reranker
RERANKER_API_KEY=your_reranker_api_key_here

# Embedding配置
EMBEDDING_API_URL=http://localhost:13031/embed
EMBEDDING_API_KEY=your_embedding_api_key_here

# Tavily搜索配置
TAVILY_API_KEY=your_tavily_api_key_here

# Agent配置
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4096

# 外部API配置
CHATAI_BASE_URL=https://api.chatai.com/v1
CHATAI_API_KEY=your_chatai_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 配置文件路径
CONFIG_FILE=config.yaml
```

### 2. YAML配置文件

`config.yaml` 文件包含详细的模型和服务配置，支持环境变量替换：

```yaml
supported_models:
  qwen_2_5_235b_a22b:
    name: "Qwen3-235B-A22B (推理)"
    type: "enterprise"
    model_id: "Qwen3-235B-A22B"
    url: "http://10.218.108.245:9966/v1"
    api_key: "EMPTY"
  
  gemini_1_5_pro:
    name: "Gemini 1.5 Pro"
    type: "external"
    model_id: "gemini-1.5-pro-latest"
    url: "${CHATAI_BASE_URL}"
    api_key: "${CHATAI_API_KEY}"

elasticsearch:
  hosts:
    - "https://10.238.130.43:9200"
  username: "devops"
  password: "your_password"

agent_config:
  task_planner:
    name: "task_planner"
    provider: "qwen_2_5_235b_a22b"
    model: "qwen_2_5_235b_a22b"
    temperature: 0.7
    max_tokens: 2000
```

## 使用方法

### 1. 基本配置访问

```python
from core.config import settings

# 访问基本配置
redis_url = settings.redis_url
openai_api_key = settings.openai.api_key
```

### 2. 模型配置访问

```python
# 获取所有支持的模型
models = settings.supported_models

# 获取特定模型配置
qwen_model = settings.get_model_config("qwen_2_5_235b_a22b")
if qwen_model:
    print(f"模型名称: {qwen_model.name}")
    print(f"模型URL: {qwen_model.url}")
```

### 3. 服务配置访问

```python
# Elasticsearch配置
es_config = settings.elasticsearch_config
print(f"ES Hosts: {es_config.hosts}")

# Tavily配置
tavily_config = settings.tavily_config
print(f"Tavily API Key: {tavily_config.api_key}")
```

### 4. Agent组件配置访问

```python
# 获取Agent整体配置
agent_config = settings.agent_config

# 获取特定组件配置
composer_config = settings.get_agent_component_config("composer")
if composer_config:
    print(f"Temperature: {composer_config.temperature}")
    print(f"Max Tokens: {composer_config.max_tokens}")
    print(f"Timeout: {composer_config.timeout}")
```

## 配置特性

### 1. 环境变量替换

YAML文件中的 `${VARIABLE_NAME}` 格式会被自动替换为环境变量值：

```yaml
url: "${CHATAI_BASE_URL}"  # 会被替换为环境变量CHATAI_BASE_URL的值
```

### 2. 配置缓存

配置系统使用懒加载和缓存机制，提高性能：

- 首次访问时加载配置
- 后续访问使用缓存
- 支持配置热重载（需要重启应用）

### 3. 类型安全

所有配置都使用Pydantic模型，提供类型检查和验证：

```python
# 自动类型检查
temperature: float = 0.7  # 必须是浮点数
max_tokens: int = 2000    # 必须是整数
```

### 4. 默认值支持

配置系统提供合理的默认值，确保应用在配置不完整时也能运行：

```python
# 如果config.yaml不存在，使用默认配置
default_component = AgentComponentConfig(
    name="default",
    provider="qwen_2_5_235b_a22b",
    model="qwen_2_5_235b_a22b"
)
```

## 测试配置

运行测试脚本验证配置是否正确：

```bash
cd service
python test_config.py
```

## 注意事项

1. **敏感信息**: API密钥等敏感信息应通过环境变量提供，不要直接写在YAML文件中
2. **环境变量优先级**: 环境变量配置会覆盖YAML文件中的配置
3. **配置验证**: 启动时会自动验证配置的完整性和正确性
4. **错误处理**: 配置错误时会提供清晰的错误信息 