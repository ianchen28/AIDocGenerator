# 模拟文档生成服务

这是一个简化的模拟服务，用于在后端同事无法连接内网模型服务的条件下，模拟真实的 `/jobs/document-from-outline` 响应逻辑。

## 功能特性

- ✅ 接收 outline JSON 格式的请求
- ✅ 模拟真实的文档生成流程
- ✅ 向 Redis 流式推送事件
- ✅ 支持章节级别的实时进度反馈
- ✅ 生成模拟的章节内容

## 事件流设计

### 事件类型

1. **`task_started`** - 任务开始
2. **`task_progress`** - 任务进度（分析大纲）
3. **`chapter_started`** - 章节开始处理
4. **`chapter_progress`** - 章节内部进度（planner → researcher → writer）
5. **`chapter_completed`** - 章节完成，包含章节内容
6. **`writer_started`** - Writer开始编写最终文档
7. **`document_content_stream`** - 流式输出文档内容token
8. **`document_content_completed`** - 文档内容流式输出完成
9. **`citations_completed`** - 参考文献生成完成
10. **`task_completed`** - 所有章节处理完成

### 事件格式

所有事件都包含以下基础字段：
- `eventType`: 事件类型
- `taskType`: 任务类型（document_generation）
- `status`: 状态（started/running/completed/failed）
- `timestamp`: 时间戳
- `redis_id`: Redis 事件ID

## 使用方法

### 1. 启动服务

```bash
# 确保 Redis 已启动
redis-cli ping

# 启动模拟服务
./start_mock_service.sh
```

服务将在 `http://localhost:8001` 启动

### 2. 发送请求

```bash
curl -X POST http://localhost:8001/jobs/document-from-outline \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_job_001",
    "outline_json": "{\"title\":\"测试文档\",\"nodes\":[{\"id\":\"node_1\",\"title\":\"第一章\",\"content_summary\":\"测试内容\"}]}",
    "session_id": "1234567890"
  }'
```

### 3. 监听 Redis 事件

```bash
# 监听特定 job_id 的事件流
redis-cli xread count 10 streams 1234567890 0
```

### 4. 运行测试

```bash
python test_mock_service.py
```

## API 接口

### POST /jobs/document-from-outline

**请求体:**
```json
{
  "job_id": "string",
  "outline_json": "string",
  "session_id": "string (可选)"
}
```

**响应:**
```json
{
  "job_id": "string"
}
```

**状态码:** 202 Accepted

## Redis 流格式

每个事件都存储在以 `job_id` 命名的 Redis Stream 中：

```
job_id -> [event_id -> {data: json_string}]
```

事件数据示例：

**章节完成事件:**
```json
{
  "eventType": "chapter_completed",
  "taskType": "document_generation", 
  "chapterTitle": "第一章",
  "chapterContent": "章节内容...",
  "chapterIndex": 0,
  "status": "completed",
  "timestamp": "2024-01-01T12:00:00",
  "redis_id": "test_job_001-5"
}
```

**文档内容流式输出事件:**
```json
{
  "eventType": "document_content_stream",
  "taskType": "document_generation",
  "content": "文档内容片段...",
  "tokenIndex": 100,
  "totalTokens": 500,
  "progress": "110/500",
  "status": "streaming",
  "timestamp": "2024-01-01T12:00:00",
  "redis_id": "test_job_001-15"
}
```

**参考文献完成事件:**
```json
{
  "eventType": "citations_completed",
  "taskType": "document_generation",
  "citations": {
    "answerOrigins": [...],
    "webs": [...]
  },
  "totalAnswerOrigins": 9,
  "totalWebSources": 6,
  "status": "completed",
  "timestamp": "2024-01-01T12:00:00",
  "redis_id": "test_job_001-103"
}
```

## 开发说明

### 文件结构

- `mock_document_service.py` - 主服务文件
- `start_mock_service.sh` - 启动脚本
- `test_mock_service.py` - 测试脚本
- `logs/` - 日志目录

### 扩展点

1. **章节内容生成**: 修改 `generate_mock_chapter_content()` 函数
2. **事件类型**: 在 `simulate_document_generation()` 中添加新事件
3. **处理时间**: 调整 `asyncio.sleep()` 的时间来模拟不同的处理速度
4. **错误处理**: 在 `publish_event()` 中添加更详细的错误处理

### 注意事项

- 确保 Redis 服务正在运行
- 服务默认运行在端口 8001
- 日志文件保存在 `logs/mock_service.log`
- 每个 job_id 对应一个独立的 Redis Stream 