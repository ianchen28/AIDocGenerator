# 智能文档生成服务 API 交互协议 v1.0

## 目录

- [概述](#1-概述)
- [核心资源与端点](#2-核心资源与端点)
- [实时事件流协议](#3-实时事件流协议)
- [数据模型定义](#4-数据模型定义)
- [典型工作流示例](#5-典型工作流示例)

## 1. 概述

### 1.1. 设计哲学

本协议旨在为一套复杂的、多步骤的、人机协同的文档生成流程提供支持。其设计遵循以下核心原则：

- **RESTful**: 接口设计遵循 RESTful 风格，以资源为中心。
- **异步优先 (Asynchronous-First)**: 所有耗时操作（超过500ms）均设计为异步任务，客户端通过轮询或事件流获取状态。
- **状态化 (Stateful)**: 通过唯一的 `job_id` 跟踪一次完整的、从开始到结束的生成作业，实现有状态的交互。
- **事件驱动 (Event-Driven)**: 复杂任务的执行过程通过 Server-Sent Events (SSE) 实时对外广播，实现过程的透明化。

### 1.2. 核心概念

- **上下文 (Context)**: 代表由用户上传的一个或多个文件构成的知识背景。它被预处理和索引，可供后续的生成作业使用。由 `context_id` 标识。
- **作业 (Job)**: 代表一次完整的文档生成任务，从用户输入初始指令到最终文档产出。它包含了任务的状态、中间产物（如大纲）和最终结果。由 `job_id` 标识。

### 1.3. 基础 URL

所有 API 端点的基础路径为：
`https://api.your-algo-service.com/v1`

### 1.4. 认证

所有对本服务的请求，必须在 HTTP Header 中包含一个有效的 API 密钥。

- **Header**: `X-API-KEY: <your_secret_api_key>`

### 1.5. 错误处理

API 将使用标准的 HTTP 状态码来表示请求的成功或失败。当发生错误时，响应体将包含一个标准的 JSON 对象：

```json
{
  "error": {
    "code": 4001,
    "message": "Invalid job_id provided.",
    "details": "The job_id 'job-123' does not exist."
  }
}
```

---

## 2. 核心资源与端点

### 2.1. 上下文资源 (`/contexts`)

#### 2.1.1. 创建文件上下文

- **`POST /contexts`**
- **描述**: 提交一个或多个文件信息，启动后台索引任务，创建一个可供后续作业使用的上下文。
- **请求体** (`application/json`):

```json
{
  "files": [
    {
      "file_id": "unique-file-id-123",
      "file_name": "annual_report_2024.pdf",
      "storage_url": "s3://bucket-name/path/to/file1.pdf"
    }
  ]
}
```

- **成功响应** (`202 Accepted`):

```json
{
  "context_id": "ctx-abcde12345",
  "status": "INDEXING" // 枚举值: PENDING, INDEXING, READY, FAILED
}
```

- **备注**: 这是一个异步操作。

#### 2.1.2. 查询上下文状态

- **`GET /contexts/{context_id}/status`**
- **描述**: 查询文件上下文的索引状态。
- **成功响应** (`200 OK`):

```json
{
  "context_id": "ctx-abcde12345",
  "status": "READY" // 枚举值: PENDING, INDEXING, READY, FAILED
}
```

### 2.2. 作业资源 (`/jobs`)

#### 2.2.1. 启动新生成作业

- **`POST /jobs`**
- **描述**: 根据用户核心指令创建一个新的生成作业。
- **请求体** (`application/json`):

```json
{
  "context_id": "ctx-abcde12345", // 可选
  "task_prompt": "写一篇关于我们公司Q2财报的分析报告，突出市场增长点。" // 用户的核心 Query
}
```

- **成功响应** (`201 Created`):

```json
{
  "job_id": "job-fghij67890",
  "status": "CREATED",
  "created_at": "2025-07-14T10:50:00Z"
}
```

#### 2.2.2. 生成大纲

- **`POST /jobs/{job_id}/outline`**
- **描述**: 触发指定作业的大纲生成任务。
- **成功响应** (`202 Accepted`):

```json
{
  "job_id": "job-fghij67890",
  "outline_status": "GENERATING" // 枚举值: GENERATING, READY, FAILED
}
```

- **备注**: 触发后，客户端应连接到 `GET /jobs/{job_id}/events` 获取实时进度。

#### 2.2.3. 获取/查询大纲

- **`GET /jobs/{job_id}/outline`**
- **描述**: 获取已生成的大纲结构。
- **成功响应** (`200 OK`):

```json
{
  "job_id": "job-fghij67890",
  "outline_status": "READY", // GENERATING, READY, FAILED
  "outline": { /* Outline 对象, 见 4. 数据模型定义 */ }
}
```

- **备注**: 建议在从事件流收到大纲生成完成的 `done` 事件后再调用此接口。

#### 2.2.4. 更新/确认大纲

- **`PUT /jobs/{job_id}/outline`**
- **描述**: 提交用户修改或确认后的大纲。
- **请求体** (`application/json`): 完整的 `Outline` 对象。
- **成功响应** (`200 OK`):

```json
{ "job_id": "job-fghij67890", "message": "Outline updated successfully." }
```

#### 2.2.5. 获取实时事件流

- **`GET /jobs/{job_id}/events`**
- **描述**: 建立 SSE 长连接，接收任务执行过程中的实时状态和思考过程。
- **成功响应** (`200 OK`, `Content-Type: text/event-stream`):
  - 见下面的 `3. 实时事件流协议`。

#### 2.2.6. 生成并流式获取最终文档

- **`GET /jobs/{job_id}/document/stream`**
- **描述**: 建立 SSE 长连接，接收最终生成的文档内容文本流。
- **成功响应** (`200 OK`, `Content-Type: text/event-stream`):

```text
event: token
data: {"text": "根据"}

event: token
data: {"text": "最新..."}

event: done
data: {"message": "Stream finished."}
```

---

## 3. 实时事件流协议

### 3.1. 连接方式

Server-Sent Events (SSE)。客户端应使用 `EventSource` API 或等效的库来连接。

### 3.2. 事件格式

每个事件都遵循 `event: <event_name>\ndata: <json_payload>\n\n` 的格式。

### 3.3. 事件类型详解

| Event Name | 描述 | Data Payload (JSON) 示例 |
| :--- | :--- | :--- |
| **`phase_update`** | 告知任务进入了新的主要阶段。 | `{"phase": "RETRIEVAL", "message": "开始从知识库和网络检索信息..."}` |
| **`thought`** | Agent 的实时思考过程或内心独白。 | `{"text": "用户的核心是Q1/Q2对比，我需要确保两份数据都已找到。"}` |
| **`tool_call`** | 告知正在调用某个工具。 | `{"tool_name": "web_search", "status": "START", "input": {"query": "公司2025年Q2财报"}}` |
| **`source_found`** | 每找到一个有效的信息源时广播。 | `{"source_type": "document", "title": "2025_Q2_report.pdf", "url": "s3://...", "snippet": "核心利润增长15%..."}` |
| **`error`** | 报告执行中遇到的非致命错误。 | `{"code": 5001, "message": "部分网页访问超时，已跳过。"}` |
| **`done`** | 告知一个主要的异步任务段落已完成。 | `{"task": "outline_generation", "message": "Outline generation complete."}` |

---

## 4. 数据模型定义

以下是接口中使用的核心数据对象的 Pydantic 定义。

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# --- Context Models ---
class ContextFile(BaseModel):
    file_id: str
    file_name: str
    storage_url: str

class CreateContextRequest(BaseModel):
    files: List[ContextFile]

class ContextStatusResponse(BaseModel):
    context_id: str
    status: Literal["PENDING", "INDEXING", "READY", "FAILED"]

# --- Job & Outline Models ---
class CreateJobRequest(BaseModel):
    context_id: Optional[str] = None
    task_prompt: str

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str

class OutlineNode(BaseModel):
    id: str
    title: str
    content_summary: Optional[str] = None
    children: List['OutlineNode'] = []

# Support recursive model reference
OutlineNode.model_rebuild()

class Outline(BaseModel):
    title: str
    nodes: List[OutlineNode]

class OutlineResponse(BaseModel):
    job_id: str
    outline_status: Literal["GENERATING", "READY", "FAILED"]
    outline: Optional[Outline] = None

class UpdateOutlineRequest(BaseModel):
    outline: Outline
```

---

## 5. 典型工作流示例

1. **(FE -\> BE)**: 用户在前端上传 `report.pdf`。
2. **(BE)**: 将文件存入对象存储（如S3），获得 `storage_url`。
3. **(BE -\> Algo)**: 调用 `POST /contexts`，传入文件信息。获得 `context_id: "ctx-123"`。
4. **(BE \<-\> Algo)**: 后端轮询 `GET /contexts/ctx-123/status`，直到状态为 `READY`。
5. **(FE -\> BE)**: 用户输入核心指令 "写一篇Q2财报亮点分析"，并关联已上传的文件。
6. **(BE -\> Algo)**: 调用 `POST /jobs`，请求体为 `{"context_id": "ctx-123", "task_prompt": "..."}`。获得 `job_id: "job-abc"`。
7. **(FE -\> BE -\> Algo)**: 用户点击“生成大纲”。后端调用 `POST /jobs/job-abc/outline`。
8. **(BE \<-\> Algo & BE -\> FE)**: 后端立即连接到 `GET /jobs/job-abc/events`，并将所有 SSE 事件实时转发给前端。前端展示思考过程和找到的资料。
9. **(Algo -\> BE -\> FE)**: 事件流中出现 `event: done, data: {"task": "outline_generation"}`。
10. **(FE -\> BE -\> Algo)**: 前端根据 `done` 事件，通过后端调用 `GET /jobs/job-abc/outline`，获取完整大纲并展示。
11. **(FE -\> BE -\> Algo)**: 用户在前端编辑大纲后，点击“确认”。后端调用 `PUT /jobs/job-abc/outline`，提交最终版大纲。
12. **(FE -\> BE -\> Algo)**: 用户点击“生成全文”。
13. **(BE \<-\> Algo & BE -\> FE)**: 后端**同时**连接到 `GET /jobs/job-abc/events`（用于显示思考过程）和 `GET /jobs/job-abc/document/stream`（用于显示正文），并将两路数据流实时转发给前端。
14. **(FE)**: 前端在不同区域分别渲染思考过程和文档正文，直到两个流都收到 `done` 事件。
15. **流程结束**。
