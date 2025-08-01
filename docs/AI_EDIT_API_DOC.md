# AI 编辑 API 文档

## 1. 概述 (Overview)

本接口提供了一套混合模式的文本编辑能力。它既支持预设的、标准化的编辑动作（如润色、扩写），也支持通过自然语言命令进行灵活、开放的自定义编辑。所有操作均为**流式响应**，提供实时编辑体验。

- 基础 URL: http://<your-algo-service-host>:8000/api/v1
- 通用 Header: X-API-KEY: <your_secret_key>

---

## 2. 端点详解 (Endpoint Specification)

### POST /actions/edit

**功能描述**: 对指定的文本执行一种 AI 编辑操作。根据传入的 action 类型，系统会选择执行标准操作或自定义命令。

**请求 (Request)**:
- 方法: POST
- 路径: /actions/edit
- 请求头 (Headers):
  - Content-Type: application/json
  - Accept: text/event-stream (用于流式响应)
  - X-API-KEY: <your_secret_key>

**请求体 (Body)**:
```json
{
  "action": "polish|expand|summarize|continue_writing|custom",
  "text": "要编辑的文本内容",
  "polish_style": "professional|conversational|readable|subtle|academic|literary",
  "command": "自定义编辑指令",
  "context": "上下文信息"
}
```

**字段说明**:
- `action` (必填): 编辑操作类型
  - `polish`: 润色文本，需要配合 `polish_style` 参数
  - `expand`: 扩写文本，增加更多细节和深度
  - `summarize`: 总结文本，提取关键要点
  - `continue_writing`: 续写文本，基于上下文继续创作
  - `custom`: 自定义编辑，根据用户指令进行编辑
- `text` (必填): 要编辑的文本内容
- `polish_style` (可选): 润色风格，仅在 `action` 为 `polish` 时必填
  - `professional`: 专业严谨风格，适合正式场合
  - `conversational`: 口语化风格，更自然易懂
  - `readable`: 易读易懂风格，简洁清晰
  - `subtle`: 微妙润色风格，保持原文风格
  - `academic`: 学术风格，符合学术写作规范
  - `literary`: 文学风格，富有文学性和艺术美感
- `command` (可选): 自定义编辑指令，仅在 `action` 为 `custom` 时必填
- `context` (可选): 上下文信息，仅在 `action` 为 `continue_writing` 时可选

**响应 (Response)**:
- 成功响应 (200 OK): Server-Sent Events (SSE) 流式响应
- 错误响应 (422 Unprocessable Entity): 参数验证错误
- 错误响应 (500 Internal Server Error): 服务器内部错误

---

## 3. 流式响应 (SSE) 详解

后端服务在调用此接口后，会收到一个持续的 HTTP 连接，服务器会通过此连接推送事件。

**事件格式**: 每个事件都遵循 `data: <json_payload>\n\n` 的格式。

**主要事件类型**:
- `start`: 编辑开始事件
- `text`: 编辑内容片段
- `end`: 编辑完成事件
- `error`: 错误事件

**事件示例**:
```
data: {"event": "start", "action": "polish"}

data: {"text": "人工智能"}

data: {"text": "（AI）"}

data: {"text": "是计算机科学的重要分支"}

data: {"event": "end", "action": "polish"}
```

---

## 4. 调用示例

### 示例 A：专业润色

**请求体**:
```json
{
  "action": "polish",
  "text": "这个报告主要是关于我们二季度的市场表现情况，数据还不错。",
  "polish_style": "professional"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "polish"}

data: {"text": "本报告"}

data: {"text": "旨在"}

data: {"text": "详细阐述"}

data: {"text": "公司"}

data: {"text": "第二季度"}

data: {"text": "的市场"}

data: {"text": "表现。"}

data: {"text": "总体来看"}

data: {"text": "，各项"}

data: {"text": "关键数据"}

data: {"text": "指标均"}

data: {"text": "呈现积极"}

data: {"text": "态势。"}

data: {"event": "end", "action": "polish"}
```

**最终结果**: "本报告旨在详细阐述公司第二季度的市场表现。总体来看，各项关键数据指标均呈现积极态势。"

### 示例 B：口语化润色

**请求体**:
```json
{
  "action": "polish",
  "text": "人工智能是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。",
  "polish_style": "conversational"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "polish"}

data: {"text": "人工智能"}

data: {"text": "，简称AI"}

data: {"text": "，其实是计算机科学的一个方向"}

data: {"text": "，主要目标是让机器做那些原本只有人类才能搞定的事"}

data: {"text": "。"}

data: {"event": "end", "action": "polish"}
```

**最终结果**: "人工智能，简称AI，其实是计算机科学的一个方向，主要目标是让机器做那些原本只有人类才能搞定的事。"

### 示例 C：文学风格润色

**请求体**:
```json
{
  "action": "polish",
  "text": "人工智能是计算机科学的瑰宝，致力于将机器塑造成能够承载人类智慧的载体。",
  "polish_style": "literary"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "polish"}

data: {"text": "人工智能"}

data: {"text": "（AI）"}

data: {"text": "，这门计算机科学的璀璨瑰宝"}

data: {"text": "，孜孜不倦地追求着将机器塑造成能够承载人类智慧之光的载体"}

data: {"text": "。"}

data: {"event": "end", "action": "polish"}
```

**最终结果**: "人工智能（AI），这门计算机科学的璀璨瑰宝，孜孜不倦地追求着将机器塑造成能够承载人类智慧之光的载体。"

### 示例 D：扩写功能

**请求体**:
```json
{
  "action": "expand",
  "text": "AI 技术正在快速发展。"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "expand"}

data: {"text": "人工智能"}

data: {"text": "（AI）技术"}

data: {"text": "正在以惊人的速度快速发展"}

data: {"text": "，在各个领域都展现出巨大的潜力和应用价值"}

data: {"text": "。"}

data: {"event": "end", "action": "expand"}
```

### 示例 E：续写功能（带上下文）

**请求体**:
```json
{
  "action": "continue_writing",
  "text": "在云原生时代，可观测性的三大支柱——指标、日志和追踪，共同构成了理解复杂系统的基础。",
  "context": "本文正在讨论 Prometheus, Zabbix 和 OpenTelemetry 的对比。"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "continue_writing"}

data: {"text": "然而"}

data: {"text": "，"}

data: {"text": "这三者"}

data: {"text": "并非简单的替代关系"}

data: {"text": "，而是代表了不同的技术理念和应用场景"}

data: {"text": "。"}

data: {"event": "end", "action": "continue_writing"}
```

### 示例 F：续写功能（不带上下文）

**请求体**:
```json
{
  "action": "continue_writing",
  "text": "人工智能技术正在快速发展，机器学习算法在各个领域都有广泛应用。"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "continue_writing"}

data: {"text": "特别是在"}

data: {"text": "医疗"}

data: {"text": "、"}

data: {"text": "金融"}

data: {"text": "和"}

data: {"text": "交通"}

data: {"text": "等行业"}

data: {"text": "。"}

data: {"event": "end", "action": "continue_writing"}
```

### 示例 G：自定义编辑

**请求体**:
```json
{
  "action": "custom",
  "text": "这是一个测试文本。",
  "command": "将文本改写为更正式的语气"
}
```

**响应流示例**:
```
data: {"event": "start", "action": "custom"}

data: {"text": "此乃"}

data: {"text": "一测试文本"}

data: {"text": "。"}

data: {"event": "end", "action": "custom"}
```

---

## 5. 错误处理

### 参数验证错误 (422)

**缺少润色风格参数**:
```json
{
  "action": "polish",
  "text": "测试文本"
  // 缺少 polish_style 参数
}
```

**响应**:
```
data: {"event": "error", "error": "参数错误", "detail": "当 action 为 'polish' 时，polish_style 字段为必填项"}
```

**无效润色风格**:
```json
{
  "action": "polish",
  "text": "测试文本",
  "polish_style": "invalid_style"
}
```

**响应**:
```
data: {"event": "error", "error": "参数错误", "detail": "无效的润色风格 'invalid_style'。可用风格: professional, conversational, readable, subtle, academic, literary"}
```

### 服务器错误 (500)

**响应**:
```
data: {"event": "error", "error": "编辑失败", "detail": "具体错误信息"}
```

---

## 6. 性能指标

基于实际测试结果：

| 指标 | 值 | 说明 |
|------|----|----- |
| 首个token延迟 | ~0.11秒 | 流式响应开始时间 |
| 总响应时间 | ~0.31秒 | 完整编辑完成时间 |
| 流式token数量 | 10-20个 | 根据文本长度变化 |
| 错误处理准确率 | 100% | 完善的参数验证 |

---

## 7. 最佳实践

1. **选择合适的润色风格**:
   - 正式文档：使用 `professional` 或 `academic`
   - 日常交流：使用 `conversational` 或 `readable`
   - 文学创作：使用 `literary`
   - 轻微调整：使用 `subtle`

2. **流式处理**:
   - 实时显示接收到的文本片段
   - 监听 `end` 事件确认完成
   - 处理 `error` 事件显示错误信息

3. **错误处理**:
   - 检查 HTTP 状态码
   - 解析 SSE 错误事件
   - 提供用户友好的错误提示

---

## 8. 更新日志

- **v1.1.0**: 新增六种润色风格支持
- **v1.0.0**: 初始版本，支持基础编辑功能
