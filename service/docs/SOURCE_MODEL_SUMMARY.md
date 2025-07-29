# Source 模型实现总结

## 概述

成功在 `service/src/doc_agent/schemas.py` 中实现了新的 `Source` 模型，用于追踪和引用信息来源。同时更新了 `service/src/doc_agent/graph/state.py` 中的 `ResearchState` 来包含源追踪功能。

## Source 模型定义

### 字段说明

```python
class Source(BaseModel):
    """信息源模型，用于追踪和引用信息来源"""
    id: int = Field(..., description="唯一顺序标识符，用于引用（如 1, 2, 3...）")
    source_type: str = Field(..., description="信息源类型（如 'webpage', 'document', 'es_result'）")
    title: str = Field(..., description="信息源标题")
    url: Optional[str] = Field(None, description="信息源URL，如果可用")
    content: str = Field(..., description="信息源的实际文本内容片段")
```

### 字段详解

1. **`id: int`** - 唯一顺序标识符
   - 用于在文档中引用特定信息源
   - 通常从 1 开始递增
   - 便于生成引用格式如 `[1]`, `[2]` 等

2. **`source_type: str`** - 信息源类型
   - `"webpage"` - 网页内容
   - `"document"` - 文档内容
   - `"es_result"` - Elasticsearch 搜索结果
   - 可扩展其他类型

3. **`title: str`** - 信息源标题
   - 描述性标题，便于识别
   - 用于生成引用和索引

4. **`url: Optional[str]`** - 信息源URL
   - 可选字段，适用于有URL的源
   - 用于直接链接到原始信息

5. **`content: str`** - 实际文本内容
   - 从源中提取的实际文本片段
   - 用于内容分析和引用

## ResearchState 集成

在 `ResearchState` 中添加了 `sources` 字段：

```python
class ResearchState(TypedDict):
    # ... 其他字段 ...
    
    # 源追踪 - 用于引用和溯源
    sources: list[Source]  # 当前章节收集的所有信息源
```

## 使用场景

### 1. 信息源追踪
```python
# 创建不同类型的源
webpage_source = Source(
    id=1,
    source_type="webpage",
    title="水电站技术发展现状",
    url="https://www.example.com/hydropower-tech",
    content="水电站技术在过去几十年中取得了显著进展..."
)

document_source = Source(
    id=2,
    source_type="document",
    title="水电站设计规范 GB 50287-2016",
    content="本标准规定了水电站设计的基本要求..."
)
```

### 2. 引用生成
```python
# 生成引用格式
for source in sources:
    if source.url:
        print(f"[{source.id}] {source.title} - {source.url}")
    else:
        print(f"[{source.id}] {source.title} ({source.source_type})")
```

### 3. 按类型分组
```python
# 按源类型分组
source_types = {}
for source in sources:
    if source.source_type not in source_types:
        source_types[source.source_type] = []
    source_types[source.source_type].append(source)
```

### 4. JSON 序列化
```python
# 序列化为 JSON
json_data = source.model_dump()

# 从 JSON 反序列化
source_from_json = Source(**json_data)
```

## 技术特性

### 1. Pydantic 集成
- 自动数据验证
- JSON 序列化/反序列化
- 类型安全

### 2. 灵活性
- 支持可选的 URL 字段
- 可扩展的源类型
- 兼容现有工作流

### 3. 可追踪性
- 唯一标识符便于引用
- 完整的源信息记录
- 支持溯源和验证

## 测试结果

✅ **功能测试通过**
- Source 模型创建和验证
- JSON 序列化/反序列化
- ResearchState 集成
- 不同类型源的处理

✅ **使用示例验证**
- 网页源、文档源、ES 结果源
- 引用格式生成
- 按类型分组
- 研究状态集成

## 应用价值

### 1. 文档质量提升
- 提供信息来源追踪
- 支持引用和验证
- 增强文档可信度

### 2. 研究过程优化
- 记录研究过程中使用的所有信息源
- 便于回溯和验证
- 支持增量信息收集

### 3. 合规性支持
- 满足学术引用要求
- 支持版权和来源声明
- 便于审计和验证

## 后续扩展建议

1. **引用格式扩展**
   - 支持不同的引用格式（APA、MLA等）
   - 自动生成参考文献列表

2. **源质量评估**
   - 添加源可信度评分
   - 支持源优先级排序

3. **内容去重**
   - 检测重复或相似内容
   - 合并相似源

4. **元数据扩展**
   - 添加时间戳、作者等信息
   - 支持更丰富的元数据

## 总结

新的 `Source` 模型为文档生成系统提供了：

- 🔍 **完整的信息追踪** - 记录所有信息来源
- 📚 **规范的引用支持** - 便于生成标准引用格式
- 🛡️ **质量保证机制** - 支持信息验证和溯源
- 🔧 **灵活的扩展性** - 支持多种源类型和格式

这个实现为 AI 文档生成系统增加了重要的可信度和可追溯性功能，提升了生成文档的质量和可靠性。 