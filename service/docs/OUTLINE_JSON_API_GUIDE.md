# Outline JSON API 使用指南

## 概述

新的 `/jobs/document-from-outline` API端点允许你通过发送outline的JSON序列化字符串来生成完整文档。这个端点将outline集成到二阶段工作流程中，为每个章节执行详细的研究和写作。

## API端点

### POST /jobs/document-from-outline

**功能**: 从outline JSON字符串生成完整文档

**请求体**:
```json
{
  "job_id": "unique_job_id",
  "outline_json": "{\"title\":\"文档标题\",\"nodes\":[...]}",
  "session_id": "optional_session_id"
}
```

**参数说明**:
- `job_id` (必需): 唯一的任务ID
- `outline_json` (必需): outline的JSON序列化字符串
- `session_id` (可选): 会话ID，用于追踪

**响应**:
```json
{
  "job_id": "unique_job_id"
}
```

## Outline JSON 格式

outline JSON必须包含以下结构：

```json
{
  "title": "文档标题",
  "nodes": [
    {
      "id": "node_1",
      "title": "章节标题",
      "content_summary": "章节描述",
      "children": []
    }
  ]
}
```

## 使用示例

### 1. Python 示例

```python
import json
import requests

# 准备outline数据
outline_data = {
    "title": "人工智能技术发展报告",
    "nodes": [
        {
            "id": "node_1",
            "title": "引言",
            "content_summary": "介绍人工智能的基本概念和发展背景"
        },
        {
            "id": "node_2",
            "title": "发展历史",
            "content_summary": "从图灵测试到深度学习的演进历程"
        }
    ]
}

# 准备请求
request_data = {
    "job_id": "test_001",
    "outline_json": json.dumps(outline_data, ensure_ascii=False),
    "session_id": "session_001"
}

# 发送请求
response = requests.post(
    "http://localhost:8000/api/v1/jobs/document-from-outline",
    json=request_data
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
```

### 2. cURL 示例

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_001",
    "outline_json": "{\"title\":\"AI报告\",\"nodes\":[{\"id\":\"node_1\",\"title\":\"引言\",\"content_summary\":\"介绍AI概念\"}]}",
    "session_id": "session_001"
  }'
```

## 工作流程

1. **接收请求**: API接收包含outline JSON的请求
2. **解析验证**: 解析JSON并验证格式
3. **初始化状态**: 将outline集成到ResearchState中
4. **章节处理**: 为每个章节执行：
   - 规划研究策略
   - 收集相关信息
   - 撰写章节内容
5. **合并文档**: 将所有章节内容合并为最终文档
6. **返回结果**: 通过Redis流推送进度和结果

## 进度监控

任务执行过程中会通过Redis流推送进度信息：

- `task_started`: 任务开始
- `task_progress`: 处理进度（分析大纲、处理章节等）
- `document_generated`: 文档生成完成
- `task_completed`: 任务完成

## 错误处理

API会返回以下错误：

- `400 Bad Request`: outline JSON格式无效或缺少必需字段
- `500 Internal Server Error`: 服务器内部错误

## 测试

使用提供的测试脚本：

```bash
# Python测试
cd service/examples
python test_outline_json_api.py

# cURL测试
cd service/examples
bash curl_test_outline_json.sh
```

## 注意事项

1. 确保outline JSON格式正确
2. job_id必须是唯一的
3. 任务执行可能需要较长时间，建议通过Redis流监控进度
4. 生成的文档会包含引用和来源信息 