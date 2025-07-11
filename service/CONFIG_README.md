# 配置系统使用说明

## 概述

本项目的配置系统支持从环境变量和YAML文件加载配置，提供了灵活的配置管理方案。系统采用分层配置架构，支持环境变量替换、类型安全验证和缓存机制。

## 配置架构

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
# 支持的模型配置
supported_models:
  # 企业内网部署的模型
  hdy_model:
    name: "HDY模型"
    type: "enterprise_generate"
    model_id: "hdy_model"
    url: "http://10.238.130.28:10004/v1"
    description: "基于 qwen-32b 精调的行业知识问答模型"
    api_key: "EMPTY"
  
  qwen_2_5_235b_a22b:
    name: "Qwen3-235B-A22B (推理)"
    type: "enterprise_generate"
    model_id: "Qwen3-235B-A22B"
    url: "http://10.218.108.245:9966/v1"
    description: "千问 235b 最强推理模型量化版"
    api_key: "EMPTY"
  
  # 外部模型
  gemini_1_5_pro:
    name: "Gemini 1.5 Pro"
    type: "external_generate"
    model_id: "gemini-1.5-pro-latest"
    url: "${CHATAI_BASE_URL}"
    api_key: "${CHATAI_API_KEY}"
    description: "Google Gemini 1.5 Pro - 高质量版本"

# Elasticsearch配置
elasticsearch:
  hosts:
    - "https://10.238.130.43:9200"
    - "https://10.238.130.44:9200"
    - "https://10.238.130.45:9200"
  port: 9200
  scheme: "https"
  username: "devops"
  password: "your_password"
  verify_certs: false
  index_prefix: "doc_gen"
  timeout: 30
  max_retries: 3
  retry_on_timeout: true

# Tavily网络搜索配置
tavily:
  api_key: "${TAVILY_API_KEY}"
  search_depth: "advanced"
  max_results: 6

# Agent组件配置
agent_config:
  task_planner:
    name: "task_planner"
    description: "任务规划器"
    provider: "qwen_2_5_235b_a22b"
    model: "qwen_2_5_235b_a22b"
    temperature: 0.7
    max_tokens: 2000
    timeout: 180
    retry_count: 5
    enable_logging: true
    extra_params:
      connect_timeout: 60
      read_timeout: 180
  
  composer:
    name: "composer"
    description: "写作器"
    provider: "qwen_2_5_235b_a22b"
    model: "qwen_2_5_235b_a22b"
    temperature: 0.8
    max_tokens: 3000
    timeout: 300
    retry_count: 8
    enable_logging: true
    extra_params:
      connect_timeout: 60
      read_timeout: 300
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
    print(f"模型类型: {qwen_model.type}")
    print(f"模型URL: {qwen_model.url}")
    print(f"模型描述: {qwen_model.description}")
```

### 3. 服务配置访问

```python
# Elasticsearch配置
es_config = settings.elasticsearch_config
print(f"ES Hosts: {es_config.hosts}")
print(f"ES Username: {es_config.username}")
print(f"ES Index Prefix: {es_config.index_prefix}")

# Tavily配置
tavily_config = settings.tavily_config
print(f"Tavily API Key: {tavily_config.api_key}")
print(f"Search Depth: {tavily_config.search_depth}")
```

### 4. Agent组件配置访问

```python
# 获取Agent整体配置
agent_config = settings.agent_config

# 获取特定组件配置
composer_config = settings.get_agent_component_config("composer")
if composer_config:
    print(f"组件名称: {composer_config.name}")
    print(f"Temperature: {composer_config.temperature}")
    print(f"Max Tokens: {composer_config.max_tokens}")
    print(f"Timeout: {composer_config.timeout}")
    print(f"Retry Count: {composer_config.retry_count}")
    print(f"Extra Params: {composer_config.extra_params}")
```

## 配置特性

### 1. 环境变量替换

YAML文件中的 `${VARIABLE_NAME}` 格式会被自动替换为环境变量值：

```yaml
url: "${CHATAI_BASE_URL}"  # 会被替换为环境变量CHATAI_BASE_URL的值
api_key: "${CHATAI_API_KEY}"  # 会被替换为环境变量CHATAI_API_KEY的值
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
timeout: int = 180        # 必须是整数
enable_logging: bool = True  # 必须是布尔值
```

### 4. 默认值支持

配置系统提供合理的默认值，确保应用在配置不完整时也能运行：

```python
# 如果config.yaml不存在，使用默认配置
default_component = AgentComponentConfig(
    name="default",
    description="默认组件",
    provider="qwen_2_5_235b_a22b",
    model="qwen_2_5_235b_a22b",
    temperature=0.7,
    max_tokens=2000,
    timeout=180,
    retry_count=5,
    enable_logging=True
)
```

### 5. 模型类型支持

系统支持多种模型类型：

- `enterprise_generate`: 企业内网生成模型
- `enterprise_reranker`: 企业内网重排序模型
- `enterprise_embedding`: 企业内网嵌入模型
- `external_generate`: 外部生成模型

## 测试配置

### 1. 运行配置测试

```bash
cd service
python -m pytest tests/test_config.py -v
```

### 2. 运行所有测试

```bash
cd service
python -m pytest tests/ -v
```

### 3. 测试配置验证

```python
# 测试配置加载
from core.config import settings

def test_config_loading():
    # 验证基本配置
    assert settings.redis_url is not None
    
    # 验证模型配置
    models = settings.supported_models
    assert len(models) > 0
    
    # 验证ES配置
    es_config = settings.elasticsearch_config
    assert es_config.hosts is not None
    
    # 验证Agent配置
    agent_config = settings.agent_config
    assert agent_config.task_planner is not None
    assert agent_config.composer is not None
```

## 最佳实践

### 1. 敏感信息管理

- API密钥等敏感信息应通过环境变量提供
- 不要在YAML文件中直接写入敏感信息
- 使用环境变量替换语法 `${VARIABLE_NAME}`

### 2. 配置验证

- 启动时自动验证配置的完整性和正确性
- 使用类型注解确保配置类型安全
- 提供清晰的错误信息

### 3. 环境隔离

- 开发环境：使用本地配置
- 测试环境：使用测试专用配置
- 生产环境：使用生产环境变量

### 4. 配置更新

- 修改配置后需要重启应用
- 使用配置缓存提高性能
- 支持配置热重载（需要重启）

## 故障排除

### 1. 常见问题

**问题**: 配置加载失败

```plaintext
解决方案: 检查config.yaml文件格式和路径
```

**问题**: 环境变量未替换

```plaintext
解决方案: 确保环境变量已正确设置
```

**问题**: 类型验证错误

```plaintext
解决方案: 检查配置值的类型是否符合要求
```

### 2. 调试技巧

```python
# 打印完整配置
from core.config import settings
import json

# 打印模型配置
print("支持的模型:")
for key, model in settings.supported_models.items():
    print(f"  {key}: {model.name}")

# 打印Agent配置
print("Agent组件:")
for component_name, component in settings.agent_config.dict().items():
    print(f"  {component_name}: {component['name']}")
```

## 注意事项

1. **敏感信息**: API密钥等敏感信息应通过环境变量提供，不要直接写在YAML文件中
2. **环境变量优先级**: 环境变量配置会覆盖YAML文件中的配置
3. **配置验证**: 启动时会自动验证配置的完整性和正确性
4. **错误处理**: 配置错误时会提供清晰的错误信息
5. **资源管理**: 使用异步上下文管理器确保资源正确释放
6. **测试覆盖**: 所有配置功能都有对应的测试用例
