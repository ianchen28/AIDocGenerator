# Prompts 模块

本模块包含所有用于文档生成的提示词模板，方便统一管理和调整。

## 📁 文件结构

```
prompts/
├── __init__.py              # 模块初始化文件
├── outline_generation.py    # 大纲生成提示词
├── planner.py              # 规划器提示词
├── writer.py               # 写作器提示词
├── supervisor.py           # 监督器提示词
├── content_processor.py    # 内容处理器提示词
└── README.md              # 本文件
```

## 🎯 功能说明

### 1. 大纲生成提示词 (`outline_generation.py`)
- **用途**: 基于初始研究数据生成文档的结构化大纲
- **输入**: 主题、初始研究数据
- **输出**: JSON格式的文档大纲，包含章节结构

### 2. 规划器提示词 (`planner.py`)
- **用途**: 为每个章节制定详细的研究计划和搜索策略
- **输入**: 文档主题、章节标题、章节描述
- **输出**: 研究计划和搜索查询列表

### 3. 写作器提示词 (`writer.py`)
- **用途**: 基于研究数据撰写章节内容
- **输入**: 文档主题、章节信息、研究数据、已完成章节内容
- **输出**: 格式化的章节内容
- **包含**: 完整版本和简化版本（用于长度限制）

### 4. 监督器提示词 (`supervisor.py`)
- **用途**: 评估收集的研究数据是否足够撰写高质量文档
- **输入**: 主题、数据摘要（来源数量、总字符数）
- **输出**: 决策（FINISH/CONTINUE）

### 5. 内容处理器提示词 (`content_processor.py`)
- **用途**: 处理研究数据，包括摘要、关键要点提取、内容压缩
- **包含**:
  - `RESEARCH_DATA_SUMMARY_PROMPT`: 研究数据总结
  - `KEY_POINTS_EXTRACTION_PROMPT`: 关键要点提取
  - `CONTENT_COMPRESSION_PROMPT`: 内容压缩

## 🔧 使用方法

### 导入提示词模板

```python
from src.doc_agent.prompts import (
    OUTLINE_GENERATION_PROMPT,
    PLANNER_PROMPT,
    WRITER_PROMPT,
    WRITER_PROMPT_SIMPLE,
    SUPERVISOR_PROMPT,
    RESEARCH_DATA_SUMMARY_PROMPT,
    KEY_POINTS_EXTRACTION_PROMPT,
    CONTENT_COMPRESSION_PROMPT
)
```

### 使用示例

```python
# 大纲生成
outline_prompt = OUTLINE_GENERATION_PROMPT.format(
    topic="人工智能在医疗领域的应用",
    initial_gathered_data="这是一些研究数据..."
)

# 规划器
planner_prompt = PLANNER_PROMPT.format(
    topic="人工智能在医疗领域的应用",
    chapter_title="医疗AI技术概述",
    chapter_description="介绍医疗AI的基本概念和技术"
)

# 写作器
writer_prompt = WRITER_PROMPT.format(
    topic="人工智能在医疗领域的应用",
    chapter_title="医疗AI技术概述",
    chapter_description="介绍医疗AI的基本概念和技术",
    chapter_number=1,
    total_chapters=5,
    previous_chapters_context="这是第一章，没有前置内容。",
    gathered_data="这是一些研究数据..."
)

# 监督器
supervisor_prompt = SUPERVISOR_PROMPT.format(
    topic="人工智能在医疗领域的应用",
    num_sources=3,
    total_length=500
)
```

## ✏️ 自定义提示词

### 修改现有提示词

1. 直接编辑对应的 `.py` 文件
2. 修改模板字符串中的内容
3. 保持占位符格式 `{variable_name}`

### 添加新的提示词

1. 在对应的文件中添加新的模板字符串
2. 在 `__init__.py` 中添加导入
3. 更新 `__all__` 列表

### 示例：添加新的提示词

```python
# 在 writer.py 中添加
NEW_WRITER_PROMPT = """
**角色:** 你是一位专业的文档撰写专家。

**任务:** {task_description}

**要求:** {requirements}

请开始撰写内容。
"""

# 在 __init__.py 中添加
from .writer import NEW_WRITER_PROMPT

__all__ = [
    # ... 现有项目
    'NEW_WRITER_PROMPT'
]
```

## 📋 提示词设计原则

1. **清晰明确**: 角色定位、任务要求、输出格式都要清晰
2. **结构化**: 使用标题、列表等格式提高可读性
3. **参数化**: 使用占位符便于动态替换
4. **一致性**: 保持不同提示词之间的风格一致
5. **可扩展**: 便于后续添加新的提示词模板

## 🔄 版本管理

- 修改提示词时建议记录变更原因
- 重大修改前建议备份原版本
- 测试修改后的提示词效果

## 📝 注意事项

1. 占位符名称要与调用代码中的参数名一致
2. 字符串格式化时注意转义字符
3. 长提示词要考虑 LLM 的 token 限制
4. 保持提示词的逻辑性和完整性 