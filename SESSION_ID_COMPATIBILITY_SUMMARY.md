# SessionId 兼容性修改总结

## 📋 修改概述

为了支持 long 类型的 sessionId，我们对代码进行了全面的兼容性修改，确保 API 能够正确处理 `Union[str, int]` 类型的 sessionId。

## 🔧 修改的文件

### 1. `service/src/doc_agent/schemas.py`
- **修改内容**: 更新 `OutlineGenerationRequest` 和 `OutlineGenerationResponse` 模型
- **变更**: `session_id` 字段类型从 `str` 改为 `Union[str, int]`
- **影响**: 支持字符串和长整型两种 sessionId 格式

```python
# 修改前
session_id: str = Field(..., alias="sessionId", description="会话ID，类似job_id")

# 修改后  
session_id: Union[str, int] = Field(..., alias="sessionId", description="会话ID，类似job_id，支持字符串或长整型")
```

### 2. `service/workers/tasks.py`
- **修改内容**: 更新所有 Celery 任务的 job_id 参数类型
- **变更**: 添加 `Union` 导入，更新函数签名
- **影响**: 确保 Celery 任务能处理 long 类型的 job_id

```python
# 添加导入
from typing import Union

# 更新函数签名
def generate_outline_from_query_task(job_id: Union[str, int], ...)
async def _generate_outline_from_query_task_async(job_id: Union[str, int], ...)
def generate_document_from_outline_task(job_id: Union[str, int], ...)
async def _generate_document_from_outline_task_async(job_id: Union[str, int], ...)
def get_job_status(job_id: Union[str, int], ...)
async def _get_job_status_async(job_id: Union[str, int], ...)
def generate_document_celery(job_id: Union[str, int], ...)
```

### 3. `service/src/doc_agent/core/redis_stream_publisher.py`
- **修改内容**: 更新 Redis 流发布器的所有 job_id 参数类型
- **变更**: 添加 `Union` 导入，更新所有相关方法
- **影响**: 确保 Redis 流发布能处理 long 类型的 job_id

```python
# 添加导入
from typing import Optional, Union

# 更新方法签名
async def publish_event(self, job_id: Union[str, int], ...)
async def publish_task_started(self, job_id: Union[str, int], ...)
async def publish_task_progress(self, job_id: Union[str, int], ...)
async def publish_task_completed(self, job_id: Union[str, int], ...)
async def publish_task_failed(self, job_id: Union[str, int], ...)
async def publish_outline_generated(self, job_id: Union[str, int], ...)
async def publish_document_generated(self, job_id: Union[str, int], ...)
async def get_stream_info(self, job_id: Union[str, int], ...)
async def get_stream_length(self, job_id: Union[str, int], ...)
```

### 4. `service/src/doc_agent/core/redis_stream_consumer.py`
- **修改内容**: 更新 Redis 流消费者的所有 job_id 参数类型
- **变更**: 添加 `Union` 导入，更新所有事件处理器
- **影响**: 确保 Redis 流消费能处理 long 类型的 job_id

```python
# 添加导入
from typing import Any, Callable, Union

# 更新处理器签名
async def default_task_started_handler(job_id: Union[str, int], ...)
async def default_task_progress_handler(job_id: Union[str, int], ...)
async def default_task_completed_handler(job_id: Union[str, int], ...)
async def default_task_failed_handler(job_id: Union[str, int], ...)
async def default_outline_generated_handler(job_id: Union[str, int], ...)
async def default_document_generated_handler(job_id: Union[str, int], ...)
```

## ✅ 测试验证

### 1. Pydantic 模型验证测试
- ✅ 支持 long 类型 sessionId: `1951106983556190200`
- ✅ 支持字符串类型 sessionId: `"test_session_001"`
- ✅ 自动类型转换和验证

### 2. API 兼容性测试
- ✅ HTTP 状态码: 202 (Accepted)
- ✅ 正确处理 long 类型的 sessionId
- ✅ Redis 流 key 正确生成: `outline_generation:1951106983556190200`
- ✅ 响应数据格式正确

### 3. 测试脚本
- `test_session_id_compatibility.py`: Python 测试脚本
- `test_curl_long_sessionid.sh`: curl 测试脚本

## 🎯 支持的 sessionId 格式

### 1. 字符串格式
```json
{
  "sessionId": "test_session_001",
  "taskPrompt": "生成一篇大纲"
}
```

### 2. 长整型格式
```json
{
  "sessionId": 1951106983556190200,
  "taskPrompt": "生成一篇大纲"
}
```

## 📝 你的 curl 命令

现在你的 curl 命令可以正常工作：

```bash
curl -X POST "http://10.215.58.199:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "contextFiles": [
        {
            "updateDate": 1754018774000,
            "isContentRefer": null,
            "attachmentType": 0,
            "isStyleImitative": null,
            "isWritingRequirement": null,
            "sessionId": 1951106983556190200,
            "attachmentFileSize": 12341,
            "knowledgeId": 1917036801803659800,
            "deleteFlag": 0,
            "createBy": "zhang_hy5",
            "attachmentFileType": "docx",
            "updateBy": "zhang_hy5",
            "attachmentName": "表格内公式.docx",
            "id": 402,
            "knowledgeBaseId": 1910317878493385700,
            "attachmentFileToken": "eb31f7496636d42d2945254c4db91ae0",
            "attachmentSource": "上传大纲",
            "createDate": 1754018774000
        }
    ],
    "isOnline": false,
    "sessionId": 1951106983556190200,
    "taskPrompt": "生成一篇大纲"
}'
```

## 🔄 向后兼容性

- ✅ 完全向后兼容，现有的字符串类型 sessionId 继续正常工作
- ✅ 新增对 long 类型 sessionId 的支持
- ✅ 所有相关组件都已更新以支持两种类型

## 🚀 部署建议

1. **重启服务**: 修改后需要重启 FastAPI 服务器和 Celery worker
2. **测试验证**: 使用提供的测试脚本验证功能
3. **监控日志**: 观察 Redis 流和任务执行日志

## 📊 测试结果

```
✅ Pydantic 模型验证成功!
✅ 字符串类型 sessionId 验证成功!
✅ API 请求成功!
✅ sessionId 类型兼容性验证通过: <class 'int'>
```

所有测试都通过了，修改完全成功！ 