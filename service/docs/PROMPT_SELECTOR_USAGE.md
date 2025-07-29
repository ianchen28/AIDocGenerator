# PromptSelector 使用指南

## 概述

`PromptSelector` 是一个用于动态导入prompt模块并选择特定版本prompt的类。它提供了灵活的prompt管理功能，支持不同的工作流类型、节点名称和版本。

## 功能特性

- 🔄 **动态导入**: 使用 `importlib` 动态导入prompt模块
- 🎯 **版本选择**: 支持特定版本的prompt选择
- 🛡️ **错误处理**: 完善的错误处理机制
- 🔍 **验证功能**: 提供prompt存在性验证
- 📋 **列表功能**: 列出可用的工作流、节点和版本
- 🚀 **便捷函数**: 提供便捷的全局函数

## 基本用法

### 1. 创建 PromptSelector 实例

```python
from src.doc_agent.common.prompt_selector import PromptSelector

# 创建实例
selector = PromptSelector()
```

### 2. 获取特定prompt

```python
# 获取writer prompt
writer_prompt = selector.get_prompt("prompts", "writer", "default")

# 获取fast_prompts中的writer prompt
fast_writer_prompt = selector.get_prompt("fast_prompts", "writer", "default")

# 获取planner prompt
planner_prompt = selector.get_prompt("prompts", "planner", "default")
```

### 3. 使用便捷函数

```python
from src.doc_agent.common.prompt_selector import get_prompt

# 直接获取prompt，无需创建实例
prompt = get_prompt("prompts", "writer", "default")
```

## 支持的工作流类型

### prompts
- `writer`: 写作器prompt
- `planner`: 规划器prompt
- `supervisor`: 监督器prompt
- `content_processor`: 内容处理器prompt
- `outline_generation`: 大纲生成prompt

### fast_prompts
- `writer`: 快速写作器prompt
- `planner`: 快速规划器prompt
- `supervisor`: 快速监督器prompt
- `content_processor`: 快速内容处理器prompt
- `outline_generation`: 快速大纲生成prompt

## 高级功能

### 1. 列出可用工作流

```python
workflows = selector.list_available_workflows()
print(workflows)  # ['prompts', 'fast_prompts']
```

### 2. 列出可用节点

```python
nodes = selector.list_available_nodes("prompts")
print(nodes)  # ['writer', 'planner', 'supervisor', 'content_processor', 'outline_generation']
```

### 3. 列出可用版本

```python
versions = selector.list_available_versions("prompts", "writer")
print(versions)  # ['v1_default', 'simple', 'detailed', 'default']
```

### 4. 验证prompt存在性

```python
is_valid = selector.validate_prompt("prompts", "writer", "default")
print(is_valid)  # True
```

## 错误处理

### 1. 模块不存在

```python
try:
    prompt = selector.get_prompt("nonexistent", "writer", "default")
except ImportError as e:
    print(f"模块不存在: {e}")
```

### 2. 节点不存在

```python
try:
    prompt = selector.get_prompt("prompts", "nonexistent", "default")
except ImportError as e:
    print(f"节点不存在: {e}")
```

### 3. 版本不存在

```python
try:
    prompt = selector.get_prompt("prompts", "writer", "nonexistent_version")
except KeyError as e:
    print(f"版本不存在: {e}")
```

## 实际使用示例

### 示例1: 获取写作器prompt

```python
from src.doc_agent.common.prompt_selector import PromptSelector

selector = PromptSelector()

# 获取标准写作器prompt
writer_prompt = selector.get_prompt("prompts", "writer", "default")
print(f"写作器prompt长度: {len(writer_prompt)} 字符")

# 获取快速写作器prompt
fast_writer_prompt = selector.get_prompt("fast_prompts", "writer", "default")
print(f"快速写作器prompt长度: {len(fast_writer_prompt)} 字符")
```

### 示例2: 批量获取prompt

```python
from src.doc_agent.common.prompt_selector import PromptSelector

selector = PromptSelector()

# 获取所有可用的工作流
workflows = selector.list_available_workflows()

prompts = {}
for workflow in workflows:
    nodes = selector.list_available_nodes(workflow)
    for node in nodes:
        try:
            prompt = selector.get_prompt(workflow, node, "default")
            prompts[f"{workflow}.{node}"] = prompt
            print(f"✅ 成功获取 {workflow}.{node}.default")
        except Exception as e:
            print(f"❌ 获取 {workflow}.{node}.default 失败: {e}")

print(f"总共获取了 {len(prompts)} 个prompt")
```

### 示例3: 验证所有prompt

```python
from src.doc_agent.common.prompt_selector import PromptSelector

selector = PromptSelector()

# 验证所有prompt
workflows = selector.list_available_workflows()
valid_prompts = []
invalid_prompts = []

for workflow in workflows:
    nodes = selector.list_available_nodes(workflow)
    for node in nodes:
        if selector.validate_prompt(workflow, node, "default"):
            valid_prompts.append(f"{workflow}.{node}")
        else:
            invalid_prompts.append(f"{workflow}.{node}")

print(f"有效prompt: {len(valid_prompts)}")
print(f"无效prompt: {len(invalid_prompts)}")
```

## 模块结构

### 标准prompt模块结构

```python
# prompts/writer.py
WRITER_PROMPT = """
**角色:** 你是一位专业的研究员和文档撰写专家...
"""

# 或者使用PROMPTS字典
PROMPTS = {
    "default": WRITER_PROMPT,
    "simple": WRITER_PROMPT_SIMPLE,
    "detailed": WRITER_PROMPT_DETAILED
}
```

### 快速prompt模块结构

```python
# fast_prompts/writer.py
FAST_WRITER_PROMPT = """
**角色:** 你是一位专业的研究员和文档撰写专家...
"""
```

## 最佳实践

1. **使用默认版本**: 大多数情况下使用 "default" 版本
2. **错误处理**: 始终包含适当的错误处理
3. **验证**: 在关键操作前验证prompt存在性
4. **缓存**: 对于频繁使用的prompt，考虑缓存结果
5. **日志**: 使用logger记录prompt获取过程

## 注意事项

1. **模块路径**: 确保prompt模块在正确的路径下
2. **变量命名**: prompt变量应该遵循约定的命名模式
3. **版本管理**: 不同版本的prompt应该保持兼容性
4. **性能**: 动态导入可能影响性能，考虑缓存机制

## 故障排除

### 常见问题

1. **ModuleNotFoundError**: 检查模块路径是否正确
2. **AttributeError**: 检查模块是否包含预期的prompt变量
3. **KeyError**: 检查版本是否存在

### 调试技巧

```python
import logging
from loguru import logger

# 启用调试日志
logger.add("debug.log", level="DEBUG")

# 测试特定prompt
selector = PromptSelector()
try:
    prompt = selector.get_prompt("prompts", "writer", "default")
    print("✅ 成功获取prompt")
except Exception as e:
    print(f"❌ 获取prompt失败: {e}")
    logger.error(f"详细错误: {e}")
``` 