# Celery 任务重构总结

## 🎯 **重构目标**

将 Worker 任务拆分为两个独立的、与新 API 对应的任务，实现无状态和解耦的架构。

## ✅ **重构内容**

### 1. **删除旧任务**

#### **删除的任务**
- `generate_outline_task` - 旧的大纲生成任务
- `run_main_workflow` - 旧的主工作流任务

### 2. **创建新任务**

#### **`generate_outline_from_query_task`**
```python
@celery_app.task
def generate_outline_from_query_task(job_id: str, task_prompt: str, context_files: dict = None) -> str:
    """
    从查询生成大纲的异步任务

    Args:
        job_id: 作业ID
        task_prompt: 用户的核心指令
        context_files: 上下文文件列表（可选）

    Returns:
        任务状态
    """
```

**核心功能**：
- 接收 `OutlineGenerationRequest` 的字典形式
- 调用新的"从 Query 到大纲"的 LangGraph 图（待实现）
- 执行初步研究和生成大纲的步骤
- 将生成的大纲 JSON 存入 Redis 的 `job_result:{job_id}` 键中

#### **`generate_document_from_outline_task`**
```python
@celery_app.task
def generate_document_from_outline_task(job_id: str, outline: dict) -> str:
    """
    从大纲生成文档的异步任务

    Args:
        job_id: 作业ID
        outline: 结构化的大纲对象

    Returns:
        任务状态
    """
```

**核心功能**：
- 接收 `DocumentGenerationRequest` 的字典形式
- 调用新的"从大纲到文档"的 LangGraph 图（待实现）
- 执行章节拆分、循环处理章节、融合和生成参考文献的步骤
- 将最终文档内容存入 Redis

### 3. **事件发布集成**

#### **Redis Streams 发布器集成**
```python
# 获取 Redis 客户端和发布器
redis = await get_redis_client()
from core.redis_stream_publisher import RedisStreamPublisher
publisher = RedisStreamPublisher(redis)

# 发布任务开始事件
await publisher.publish_task_started(
    job_id=job_id,
    task_type="outline_generation",
    task_prompt=task_prompt
)

# 发布进度事件
await publisher.publish_task_progress(
    job_id=job_id,
    task_type="outline_generation",
    progress="正在分析用户需求",
    step="analysis"
)

# 发布任务完成事件
await publisher.publish_task_completed(
    job_id=job_id,
    task_type="outline_generation",
    result={"outline": outline_result},
    duration="7s"
)
```

### 4. **API 端点更新**

#### **大纲生成端点**
```python
@router.post("/jobs/outline",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_outline_from_query(request: OutlineGenerationRequest):
    # 触发 Celery 任务
    from workers.tasks import generate_outline_from_query_task
    generate_outline_from_query_task.delay(
        job_id=request.job_id,
        task_prompt=request.task_prompt,
        context_files=request.context_files.model_dump() if request.context_files else None
    )
```

#### **文档生成端点**
```python
@router.post("/jobs/document",
             response_model=TaskCreationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_document_from_outline(request: DocumentGenerationRequest):
    # 触发 Celery 任务
    from workers.tasks import generate_document_from_outline_task
    generate_document_from_outline_task.delay(
        job_id=request.job_id,
        outline=request.outline.model_dump()
    )
```

## 🏗️ **技术实现**

### 1. **任务结构**
- **异步实现** - 使用 `asyncio.run()` 包装异步函数
- **错误处理** - 完整的异常捕获和日志记录
- **事件发布** - 集成 Redis Streams 发布器
- **结果存储** - 使用 Redis 存储任务结果

### 2. **事件流**
- **任务开始** - `task_started` 事件
- **进度更新** - `task_progress` 事件
- **任务完成** - `task_completed` 事件
- **任务失败** - `task_failed` 事件

### 3. **数据存储**
- **结果键** - `job_result:{job_id}`
- **过期时间** - 1小时自动过期
- **数据格式** - JSON 序列化

## 📊 **测试验证**

### ✅ **API 端点测试**
```bash
# 大纲生成端点
curl -X POST http://127.0.0.1:8000/api/v1/jobs/outline \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test_job_001", "task_prompt": "请生成一份关于人工智能的技术文档大纲"}'

# 响应
{
  "job_id": "test_job_001"
}

# 文档生成端点
curl -X POST http://127.0.0.1:8000/api/v1/jobs/document \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test_doc_001", "outline": {"title": "人工智能技术文档", "nodes": [...]}}'

# 响应
{
  "job_id": "test_doc_001"
}
```

### ✅ **任务注册验证**
```python
# 注册的任务列表
['workers.tasks.generate_outline_from_query_task', 
 'workers.tasks.generate_document_from_outline_task',
 'celery.chord', 'celery.chunks', 'celery.chord_unlock', 
 'celery.group', 'celery.map', 'celery.chain', 
 'celery.starmap', 'celery.accumulate']
```

## 🎯 **任务特点**

### 1. **无状态设计**
- 每个任务都是独立的
- 不依赖外部状态
- 通过参数传递所有必要数据

### 2. **解耦架构**
- 大纲生成和文档生成完全分离
- 可以独立扩展和优化
- 支持不同的处理策略

### 3. **事件驱动**
- 实时事件发布
- 支持进度监控
- 完整的生命周期跟踪

### 4. **错误恢复**
- 详细的错误日志
- 失败事件发布
- 支持任务重试

## 🚀 **下一步工作**

### 1. **LangGraph 图实现**
- 实现"从 Query 到大纲"的图
- 实现"从大纲到文档"的图
- 集成到 Celery 任务中

### 2. **监控和告警**
- 添加任务监控面板
- 实现异常告警机制
- 性能指标统计

### 3. **扩展功能**
- 支持任务取消
- 实现任务重试机制
- 添加任务优先级

## 📝 **总结**

Celery 任务重构成功完成！主要改进包括：

1. **任务拆分** - 将单一工作流拆分为两个独立任务
2. **无状态设计** - 每个任务都是独立的，不依赖外部状态
3. **事件集成** - 集成 Redis Streams 发布器，支持实时事件
4. **API 集成** - 与新的 API 架构完全兼容
5. **错误处理** - 完整的异常处理和日志记录

新的任务架构为后续的 LangGraph 图实现和系统扩展提供了坚实的基础！ 