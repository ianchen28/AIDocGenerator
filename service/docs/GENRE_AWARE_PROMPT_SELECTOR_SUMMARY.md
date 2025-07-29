# Genre-aware PromptSelector 升级总结

## 概述

成功将 `PromptSelector` 升级为支持 "genre-aware" 功能，现在可以根据不同的文档类型（genre）自动选择相应的 prompt 版本。

## 主要变更

### 1. PromptSelector 类升级

#### 构造函数变更
- **之前**: `__init__(self)`
- **现在**: `__init__(self, genre_strategies: Optional[Dict] = None)`
- **功能**: 支持从 `genres.yaml` 文件加载 genre 策略，或接受自定义策略字典

#### get_prompt 方法签名变更
- **之前**: `get_prompt(workflow_type: str, node_name: str, version: str) -> str`
- **现在**: `get_prompt(workflow_type: str, node_name: str, genre: str = "default") -> str`
- **功能**: 使用 genre 参数替代 version 参数，版本由 genre 策略自动决定

### 2. 新增功能

#### Genre 策略管理
- `_load_genre_strategies()`: 从 `genres.yaml` 加载 genre 策略
- `_get_default_genre_strategies()`: 提供默认的 genre 策略
- `get_genre_info(genre: str)`: 获取指定 genre 的详细信息
- `list_available_genres()`: 列出所有可用的 genres
- `list_available_nodes_for_genre(genre: str)`: 列出指定 genre 的可用节点

#### 错误处理增强
- 新增 `ValueError` 异常处理，用于无效的 genre 或节点配置
- 提供详细的错误信息，包括可用的 genres 和节点列表

### 3. 节点函数签名更新

更新了以下节点函数的签名，移除 `prompt_version` 参数，添加 `genre` 参数：

#### Chapter Workflow 节点
- `planner_node()`: 添加 `genre: str = "default"` 参数
- `writer_node()`: 添加 `genre: str = "default"` 参数

#### Chapter Workflow 路由器
- `supervisor_router()`: 添加 `genre: str = "default"` 参数

#### Main Orchestrator 节点
- `outline_generation_node()`: 添加 `genre: str = "default"` 参数

### 4. Container 更新

更新了 `service/core/container.py` 中的节点绑定：
- 移除了所有 `prompt_version` 参数
- 保留了 `prompt_selector` 参数
- 现在版本选择由 genre 策略自动决定

## Genre 策略配置

### genres.yaml 结构
```yaml
genres:
  default:
    name: "通用文档"
    description: "适用于大多数标准报告和分析。"
    prompt_versions:
      planner: "v1_default"
      supervisor: "v1_metadata_based"
      writer: "v1_default"
      outline_generation: "v1_default"

  work_report:
    name: "工作报告"
    description: "生成结构严谨、语言正式的工作报告或周报。"
    prompt_versions:
      planner: "v1_work_report"
      supervisor: "v1_metadata_based"
      writer: "v2_formal_style"
      outline_generation: "v2_structured"

  speech_draft:
    name: "讲话稿"
    description: "生成富有感染力、口语化的讲话稿。"
    prompt_versions:
      planner: "v1_speech"
      supervisor: "v1_metadata_based"
      writer: "v3_conversational"
      outline_generation: "v3_keynote_style"
```

## 使用示例

### 基本使用
```python
from src.doc_agent.common.prompt_selector import PromptSelector

# 创建 PromptSelector 实例
selector = PromptSelector()

# 获取默认 genre 的 prompt
prompt = selector.get_prompt("prompts", "writer", "default")

# 获取工作报告 genre 的 prompt
prompt = selector.get_prompt("prompts", "writer", "work_report")

# 获取讲话稿 genre 的 prompt
prompt = selector.get_prompt("prompts", "writer", "speech_draft")
```

### 便捷函数
```python
from src.doc_agent.common.prompt_selector import get_prompt

# 直接获取 prompt
prompt = get_prompt("prompts", "writer", "work_report")
```

### 自定义 Genre 策略
```python
custom_strategies = {
    "academic_paper": {
        "name": "学术论文",
        "description": "生成严谨的学术论文",
        "prompt_versions": {
            "writer": "v1_default",
            "planner": "v1_default"
        }
    }
}

selector = PromptSelector(custom_strategies)
prompt = selector.get_prompt("prompts", "writer", "academic_paper")
```

## 测试验证

创建了全面的测试套件验证新功能：

### 测试覆盖范围
1. ✅ PromptSelector 初始化
2. ✅ Genre 策略加载
3. ✅ 使用 genre 获取 prompt
4. ✅ Genre 信息获取
5. ✅ 列出可用 genres
6. ✅ 列出指定 genre 的可用节点
7. ✅ 无效 genre 处理
8. ✅ Prompt 验证
9. ✅ 便捷函数测试
10. ✅ 自定义 genre 策略测试

### 测试结果
- **通过**: 10/10 测试
- **功能**: 完全正常工作
- **错误处理**: 正确捕获和处理异常

## 向后兼容性

### 保持兼容的功能
- 所有现有的 prompt 模块继续工作
- 现有的 `PROMPTS` 字典结构保持不变
- 节点函数的其他参数保持不变

### 需要更新的地方
- 节点函数调用需要移除 `prompt_version` 参数
- 如果需要特定版本，需要在 `genres.yaml` 中配置

## 优势

### 1. 灵活性
- 支持多种文档类型
- 每种类型可以有不同的 prompt 策略
- 易于添加新的 genre

### 2. 可维护性
- 集中管理 prompt 版本策略
- 清晰的配置结构
- 易于调试和修改

### 3. 扩展性
- 支持自定义 genre 策略
- 可以动态加载不同的策略文件
- 支持运行时策略切换

### 4. 错误处理
- 详细的错误信息
- 优雅的降级处理
- 清晰的异常类型

## 下一步计划

1. **添加更多 Genre**: 根据实际需求添加更多文档类型
2. **Prompt 版本**: 为不同 genre 创建专门的 prompt 版本
3. **API 集成**: 在 API 层面支持 genre 参数
4. **UI 支持**: 在用户界面中提供 genre 选择
5. **性能优化**: 考虑添加 prompt 缓存机制

## 总结

Genre-aware PromptSelector 升级成功完成，提供了更灵活、更易维护的 prompt 管理方案。新系统能够根据文档类型自动选择最合适的 prompt 版本，大大提高了系统的适应性和可扩展性。 