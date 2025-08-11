# AI文档生成器 - 新file_token功能测试指南

## 📋 概述

本文档介绍如何测试新实现的file_token功能，包括大纲生成和文档生成的新特性。

## 🆕 新功能特点

1. **大纲生成返回file_token**：大纲生成完成后，会在Redis流中返回file_token
2. **文档生成使用file_token**：文档生成时使用file_token而不是直接的大纲JSON
3. **支持context_files的file_token处理**：自动解析上传的上下文文件
4. **远程storage集成**：自动从远程storage下载和解析文件

## 🚀 快速开始

### 1. 启动服务

```bash
# 启动开发服务器
./start_dev_server.sh

# 或者手动启动
conda activate ai-doc
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 运行测试

#### 方法一：使用测试脚本（推荐）

```bash
# 运行完整的测试脚本
./test_new_file_token_api.sh
```

#### 方法二：使用HTTP文件

1. 在VS Code中安装REST Client扩展
2. 打开 `test_new_file_token_api.http`
3. 点击每个请求上方的"Send Request"按钮

#### 方法三：使用curl命令

```bash
# 复制粘贴命令到终端
cat curl_commands_new_features.txt | bash
```

## 📝 测试流程

### 1. 大纲生成测试

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_001",
    "taskPrompt": "请生成一份关于人工智能技术发展趋势的详细大纲",
    "isOnline": true,
    "contextFiles": [],
    "styleGuideContent": "请使用专业的技术文档风格",
    "requirements": "需要包含实际案例和未来发展趋势"
  }'
```

**预期响应**：
```json
{
  "redisStreamKey": "task_123456789",
  "sessionId": "test_session_001"
}
```

### 2. 获取file_token

大纲生成完成后，使用Redis命令获取file_token：

```bash
# 监听Redis流获取file_token
redis-cli XREAD COUNT 10 STREAMS task_123456789 0

# 查看历史事件
redis-cli XRANGE task_123456789 - +

# 查看流长度
redis-cli XLEN task_123456789
```

**预期Redis流内容**：
```json
{
  "event": "outline_generation",
  "status": "SUCCESS",
  "data": {
    "outline": { /* 大纲内容 */ },
    "file_token": "8b7e75b4150cde04bffba318da25068e",
    "description": "大纲生成完成，包含 3 个章节"
  }
}
```

### 3. 文档生成测试

使用获取到的file_token进行文档生成：

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "基于大纲生成一份详细的技术文档",
    "sessionId": "test_session_001",
    "outline": "8b7e75b4150cde04bffba318da25068e",
    "contextFiles": [],
    "isOnline": true
  }'
```

### 4. 带context_files的测试

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "taskPrompt": "基于大纲和提供的参考资料生成技术文档",
    "sessionId": "test_session_002",
    "outline": "8b7e75b4150cde04bffba318da25068e",
    "contextFiles": [
      {
        "attachmentFileToken": "example_file_token_001",
        "attachmentType": 1
      },
      {
        "attachmentFileToken": "example_file_token_002",
        "attachmentType": 2
      }
    ],
    "isOnline": false
  }'
```

## 🔍 监控和调试

### Redis流监听

```bash
# 实时监听事件
redis-cli XREAD COUNT 10 STREAMS <task_id> 0

# 查看特定事件
redis-cli XRANGE <task_id> <start_id> <end_id>

# 查看流统计信息
redis-cli XLEN <task_id>
```

### 日志查看

```bash
# 查看服务日志
tail -f logs/app.log

# 查看特定任务的日志
grep "task_123456789" logs/app.log
```

## 🧪 测试用例

### 正常流程测试

1. ✅ 大纲生成 → 获取file_token
2. ✅ 使用file_token生成文档
3. ✅ 带context_files的文档生成
4. ✅ 模拟文档生成

### 错误情况测试

1. ✅ 无效的file_token
2. ✅ 缺少必需参数
3. ✅ 网络连接问题
4. ✅ 文件解析错误

### 性能测试

1. ✅ 大文件处理
2. ✅ 并发请求处理
3. ✅ 内存使用情况
4. ✅ 响应时间测试

## 📊 预期结果

### 成功响应

- **大纲生成**：返回taskId，Redis流中包含file_token
- **文档生成**：返回taskId，开始后台生成任务
- **文件处理**：自动下载、解析和清理临时文件

### 错误响应

- **400 Bad Request**：参数错误或格式不正确
- **404 Not Found**：file_token不存在
- **500 Internal Server Error**：服务器内部错误

## 🔧 故障排除

### 常见问题

1. **服务未启动**
   ```bash
   # 检查服务状态
   curl http://localhost:8000/api/v1/health
   ```

2. **Redis连接问题**
   ```bash
   # 检查Redis连接
   redis-cli ping
   ```

3. **文件上传失败**
   ```bash
   # 检查存储服务
   curl http://ai.test.hcece.net/api/v1/health
   ```

4. **file_token无效**
   ```bash
   # 检查token格式（32位十六进制）
   echo "8b7e75b4150cde04bffba318da25068e" | grep -E "^[a-f0-9]{32}$"
   ```

### 调试命令

```bash
# 查看Redis中的所有流
redis-cli KEYS "*"

# 查看特定流的内容
redis-cli XRANGE <stream_name> - + COUNT 10

# 查看服务进程
ps aux | grep uvicorn

# 查看端口占用
lsof -i :8000
```

## 📚 相关文件

- `test_new_file_token_api.sh` - 完整的测试脚本
- `test_new_file_token_api.http` - HTTP客户端测试文件
- `curl_commands_new_features.txt` - curl命令集合
- `api/endpoints.py` - API端点定义
- `src/doc_agent/tools/file_module/` - 文件处理模块

## 🎯 下一步

1. 测试所有API端点
2. 验证file_token的完整流程
3. 测试错误处理机制
4. 性能优化和监控
5. 集成测试和端到端测试

---

**注意**：测试前请确保服务正常运行，Redis连接正常，存储服务可用。
