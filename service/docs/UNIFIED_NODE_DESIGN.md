# 基于配置的统一节点设计方案

## 概述

本文档描述如何通过配置参数统一快速节点和普通节点，避免维护两套代码。

## 设计原则

1. **单一代码库**：所有节点共享同一套代码
2. **配置驱动**：通过配置参数控制行为差异
3. **灵活扩展**：易于添加新的复杂度级别
4. **向后兼容**：保持现有API不变

## 配置结构

在 `config.yaml` 中定义了三个复杂度级别：

- **fast**: 快速生成模式（3-5分钟）
- **standard**: 标准模式（默认）
- **comprehensive**: 全面深入模式

## 实现示例

### 1. 统一的初始研究节点

将原来的 `initial_research_node` 和 `fast_initial_research_node` 合并：

```python
# service/src/doc_agent/graph/main_orchestrator/nodes.py

async def initial_research_node(state: ResearchState,
                                web_search_tool: WebSearchTool,
                                es_search_tool: ESSearchTool,
                                reranker_tool: RerankerTool = None,
                                llm_client: LLMClient = None) -> dict:
    """
    统一的初始研究节点
    根据配置自动调整搜索深度和查询数量
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("主题不能为空")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    
    logger.info(f"🔍 开始初始研究 (模式: {complexity_config['level']}): {topic}")

    # 根据配置生成查询数量
    num_queries = complexity_config['initial_search_queries']
    
    # 生成搜索查询
    if num_queries == 2:  # 快速模式
        initial_queries = [f"{topic} 概述", f"{topic} 主要内容"]
    elif num_queries <= 5:  # 标准模式
        initial_queries = [
            f"{topic} 概述",
            f"{topic} 主要内容",
            f"{topic} 关键要点",
            f"{topic} 最新发展",
            f"{topic} 重要性"
        ][:num_queries]
    else:  # 全面模式
        initial_queries = [
            f"{topic} 概述",
            f"{topic} 主要内容",
            f"{topic} 关键要点",
            f"{topic} 最新发展",
            f"{topic} 重要性",
            f"{topic} 实践案例",
            f"{topic} 未来趋势",
            f"{topic} 相关技术"
        ][:num_queries]

    # ... 执行搜索逻辑 ...
    
    # 根据配置决定是否截断数据
    truncate_length = complexity_config['data_truncate_length']
    if truncate_length > 0 and len(raw_data) > truncate_length:
        logger.info(f"📊 数据量较大，截断至 {truncate_length} 字符")
        truncated_data = raw_data[:truncate_length] + "\n\n... (内容已截断)"
        return {"initial_gathered_data": truncated_data}
    
    return {"initial_gathered_data": raw_data}
```

### 2. 统一的章节拆分节点

```python
def split_chapters_node(state: ResearchState) -> dict:
    """
    统一的章节拆分节点
    根据配置限制章节数量
    """
    document_outline = state.get("document_outline", {})
    
    if not document_outline or "chapters" not in document_outline:
        raise ValueError("文档大纲不存在或格式无效")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    max_chapters = complexity_config['max_chapters']
    
    logger.info(f"📂 开始拆分章节任务 (模式: {complexity_config['level']})")

    # 从大纲中提取章节信息
    chapters = document_outline.get("chapters", [])
    
    # 根据配置限制章节数量
    if max_chapters > 0:
        chapters = chapters[:max_chapters]
        logger.info(f"🔧 限制章节数量为 {len(chapters)} 个")
    
    # ... 继续处理 ...
```

### 3. 统一的提示词选择

```python
def get_prompt_template(prompt_type: str) -> str:
    """
    根据配置选择合适的提示词模板
    """
    complexity_config = settings.get_complexity_config()
    
    if complexity_config['use_simplified_prompts']:
        # 使用简化的提示词
        from doc_agent.fast_prompts import (
            FAST_OUTLINE_GENERATION_PROMPT,
            FAST_PLANNER_PROMPT,
            FAST_WRITER_PROMPT
        )
        prompt_map = {
            'outline': FAST_OUTLINE_GENERATION_PROMPT,
            'planner': FAST_PLANNER_PROMPT,
            'writer': FAST_WRITER_PROMPT
        }
    else:
        # 使用完整的提示词
        from doc_agent.prompts import (
            OUTLINE_GENERATION_PROMPT,
            PLANNER_PROMPT,
            WRITER_PROMPT
        )
        prompt_map = {
            'outline': OUTLINE_GENERATION_PROMPT,
            'planner': PLANNER_PROMPT,
            'writer': WRITER_PROMPT
        }
    
    return prompt_map.get(prompt_type, "")
```

### 4. 统一的构建器

原来的 `build_graph` 和 `build_fast_graph` 可以合并为一个：

```python
def build_workflow(web_search_tool=None,
                   es_search_tool=None,
                   reranker_tool=None,
                   llm_client=None):
    """
    统一的工作流构建器
    根据配置自动调整流程
    """
    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    
    logger.info(f"🏗️ 构建工作流 (模式: {complexity_config['level']})")
    
    # 所有模式使用相同的节点，只是行为不同
    from functools import partial
    
    initial_research_node_bound = partial(
        initial_research_node,
        web_search_tool=web_search_tool,
        es_search_tool=es_search_tool,
        reranker_tool=reranker_tool,
        llm_client=llm_client
    )
    
    # ... 绑定其他节点 ...
    
    # 构建图结构（所有模式相同）
    workflow = StateGraph(ResearchState)
    workflow.add_node("initial_research", initial_research_node_bound)
    workflow.add_node("outline_generation", outline_generation_node_bound)
    # ... 添加其他节点和边 ...
    
    return workflow.compile()
```

## 使用方式

### 1. 通过环境变量设置

```bash
# 快速模式
DOC_GENERATION_COMPLEXITY_LEVEL=fast python main.py

# 标准模式（默认）
DOC_GENERATION_COMPLEXITY_LEVEL=standard python main.py

# 全面模式
DOC_GENERATION_COMPLEXITY_LEVEL=comprehensive python main.py
```

### 2. 通过API参数

```python
# 在API请求中指定复杂度
{
    "topic": "人工智能发展史",
    "complexity_level": "fast"  # 可选: fast, standard, comprehensive
}
```

### 3. 动态切换

```python
# 在运行时修改配置
settings._yaml_config['document_generation']['generation_complexity']['level'] = 'fast'
```

## 迁移计划

1. **第一阶段**：实现统一节点，保留快速节点作为兼容层
2. **第二阶段**：将所有调用点迁移到统一节点
3. **第三阶段**：删除快速节点相关代码
4. **第四阶段**：优化和清理代码结构

## 优势

1. **代码复用**：减少50%以上的重复代码
2. **易于维护**：只需维护一套节点逻辑
3. **灵活配置**：通过配置文件即可调整行为
4. **扩展性强**：轻松添加新的复杂度级别
5. **统一测试**：一套测试覆盖所有模式

## 注意事项

1. 确保配置参数的默认值合理
2. 添加配置验证，防止无效配置
3. 记录不同模式下的性能指标
4. 保持API的向后兼容性