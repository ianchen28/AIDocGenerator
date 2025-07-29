# Genre-Aware API 功能总结

## 概述

成功实现了完整的 genre-aware API 功能，从请求模型到 Celery 任务执行，整个流程都支持根据文档类型选择相应的 prompt 策略。

## 主要变更

### 1. Schema 更新

#### `CreateJobRequest` 模型增强
在 `service/src/doc_agent/schemas.py` 中添加了 `genre` 字段：

```python
class CreateJobRequest(BaseModel):
    """创建作业请求"""
    context_id: Optional[str] = None
    task_prompt: str = Field(..., description="用户的核心任务指令")
    genre: str = Field("default", description="文档类型，用于选择相应的prompt策略")
```

**特性**：
- ✅ **可选字段**：默认为 `"default"`
- ✅ **类型安全**：使用 Pydantic 进行验证
- ✅ **向后兼容**：现有 API 调用不受影响

### 2. API 端点更新

#### `POST /jobs` 端点增强
在 `service/api/endpoints.py` 中更新了作业创建逻辑：

```python
# 存储作业信息到Redis
job_data = {
    "job_id": job_id,
    "task_prompt": request.task_prompt,
    "genre": request.genre,  # 新增
    "status": "CREATED",
    "created_at": datetime.now().isoformat()
}

logger.info(f"作业 {job_id} 使用 genre: {request.genre}")
```

**功能**：
- ✅ **Genre 存储**：将 genre 信息存储到 Redis
- ✅ **日志记录**：记录使用的 genre 类型
- ✅ **数据完整性**：确保 genre 信息在整个流程中传递

#### `PUT /jobs/{job_id}/outline` 端点更新
更新了大纲确认和文档生成启动逻辑：

```python
# 获取任务提示和genre，准备启动最终文档生成
task_prompt = job_data.get("task_prompt", "")
genre = job_data.get("genre", "default")

# 启动最终文档生成工作流 - 使用Celery任务
run_main_workflow.delay(job_id, task_prompt, genre)
```

**改进**：
- ✅ **Genre 传递**：从 Redis 读取 genre 并传递给 Celery 任务
- ✅ **默认值处理**：如果 genre 不存在，使用 `"default"`
- ✅ **错误处理**：优雅处理缺失的 genre 信息

### 3. Celery 任务更新

#### `run_main_workflow` 任务增强
在 `service/workers/tasks.py` 中更新了任务签名和实现：

```python
@celery_app.task
def run_main_workflow(job_id: str, topic: str, genre: str = "default") -> str:
    """
    主要的异步工作流函数
    使用真实的图执行器和Redis回调处理器

    Args:
        job_id: 任务ID
        topic: 文档主题
        genre: 文档类型，用于选择相应的prompt策略

    Returns:
        任务状态
    """
    logger.info(f"主工作流开始 - Job ID: {job_id}, Topic: {topic}, Genre: {genre}")

    try:
        # 使用同步方式运行异步函数
        return asyncio.run(_run_main_workflow_async(job_id, topic, genre))
    except Exception as e:
        logger.error(f"主工作流任务失败: {e}")
        return "FAILED"
```

**异步实现更新**：
```python
async def _run_main_workflow_async(job_id: str, topic: str, genre: str = "default") -> str:
    """异步主工作流任务的内部实现"""
    try:
        # 获取Redis客户端
        redis = await get_redis_client()

        # 更新任务状态为进行中
        await redis.hset(f"job:{job_id}",
                         mapping={
                             "status": "processing",
                             "topic": topic,
                             "genre": genre,  # 新增
                             "started_at": str(asyncio.get_event_loop().time())
                         })

        # 获取带有Redis回调处理器的图执行器
        logger.info(f"Job {job_id}: 获取图执行器...")
        container = get_container()
        runnable = container.get_graph_runnable_for_job(job_id, genre)  # 传递 genre
```

**关键改进**：
- ✅ **Genre 参数**：任务签名包含 genre 参数
- ✅ **状态更新**：在 Redis 中记录 genre 信息
- ✅ **Container 集成**：将 genre 传递给 Container 的图执行器

### 4. Container 增强

#### `get_graph_runnable_for_job` 方法更新
在 `service/core/container.py` 中增强了图执行器获取方法：

```python
def get_graph_runnable_for_job(self, job_id: str, genre: str = "default"):
    """
    为指定作业获取带有Redis回调处理器的图执行器

    Args:
        job_id: 作业ID，用于创建特定的回调处理器
        genre: 文档类型，用于选择相应的prompt策略

    Returns:
        配置了Redis回调处理器的图执行器
    """
    # 创建Redis回调处理器
    redis_handler = create_redis_callback_handler(job_id)

    # 根据genre创建相应的节点绑定
    configured_graph = self._get_genre_aware_graph(genre, redis_handler)

    logger.info(f"为作业 {job_id} (genre: {genre}) 创建了带回调处理器的图执行器")
    return configured_graph
```

#### 新增 `_get_genre_aware_graph` 方法
实现了根据 genre 动态创建图执行器的功能：

```python
def _get_genre_aware_graph(self, genre: str, redis_handler):
    """
    根据genre获取相应的图执行器

    Args:
        genre: 文档类型
        redis_handler: Redis回调处理器

    Returns:
        配置了回调处理器的图执行器
    """
    # 验证genre是否存在
    if genre not in self.genre_strategies:
        logger.warning(f"Genre '{genre}' 不存在，使用默认genre")
        genre = "default"

    # 根据genre创建节点绑定
    chapter_planner_node = partial(chapter_nodes.planner_node,
                                   llm_client=self.llm_client,
                                   prompt_selector=self.prompt_selector,
                                   genre=genre)
    chapter_writer_node = partial(chapter_nodes.writer_node,
                                  llm_client=self.llm_client,
                                  prompt_selector=self.prompt_selector,
                                  genre=genre)
    chapter_supervisor_router = partial(
        chapter_router.supervisor_router,
        llm_client=self.llm_client,
        prompt_selector=self.prompt_selector,
        genre=genre)

    # 创建chapter workflow graph
    chapter_graph = build_chapter_workflow_graph(
        planner_node=chapter_planner_node,
        researcher_node=self.chapter_graph.nodes["researcher_node"],
        writer_node=chapter_writer_node,
        supervisor_router_func=chapter_supervisor_router)

    # 创建main orchestrator节点绑定
    main_outline_generation_node = partial(
        main_orchestrator_nodes.outline_generation_node,
        llm_client=self.llm_client,
        prompt_selector=self.prompt_selector,
        genre=genre)

    # 创建main orchestrator graph
    main_graph = build_main_orchestrator_graph(
        initial_research_node=self.main_graph.nodes["initial_research_node"],
        outline_generation_node=main_outline_generation_node,
        split_chapters_node=self.main_graph.nodes["split_chapters_node"],
        chapter_workflow_graph=chapter_graph)

    # 使用回调处理器配置图
    configured_graph = main_graph.with_config({"callbacks": [redis_handler]})

    return configured_graph
```

**核心功能**：
- ✅ **Genre 验证**：检查 genre 是否存在于策略中
- ✅ **动态节点绑定**：根据 genre 创建相应的节点绑定
- ✅ **图构建**：动态构建 chapter 和 main orchestrator 图
- ✅ **错误处理**：自动回退到默认 genre

## 工作流程

### 1. 请求处理流程
```
1. 客户端发送 POST /jobs 请求，包含 genre 参数
2. API 端点验证请求并存储 genre 到 Redis
3. 客户端调用 PUT /jobs/{job_id}/outline 确认大纲
4. API 从 Redis 读取 genre 并传递给 Celery 任务
5. Celery 任务使用 genre 创建相应的图执行器
6. 图执行器根据 genre 选择相应的 prompt 策略
```

### 2. Genre 传递链路
```
CreateJobRequest (genre) 
    ↓
POST /jobs (存储到 Redis)
    ↓
PUT /jobs/{job_id}/outline (从 Redis 读取)
    ↓
run_main_workflow.delay(job_id, topic, genre)
    ↓
container.get_graph_runnable_for_job(job_id, genre)
    ↓
_get_genre_aware_graph(genre, redis_handler)
    ↓
节点使用 genre 调用 prompt_selector.get_prompt(..., genre)
```

## 测试验证

### 测试覆盖范围
1. ✅ **Schema 测试**：验证 `CreateJobRequest` 的 genre 字段
2. ✅ **字段验证**：测试 genre 字段的验证逻辑
3. ✅ **序列化测试**：验证请求对象的序列化功能
4. ✅ **反序列化测试**：验证 JSON 到对象的转换
5. ✅ **Container 集成**：测试 genre-aware container 功能
6. ✅ **Celery 任务支持**：验证任务签名和参数
7. ✅ **工作流集成**：测试完整的 genre 工作流

### 测试结果
- **通过**: 7/7 测试
- **功能**: 完全正常工作
- **错误处理**: 正确捕获和处理异常
- **向后兼容**: 保持与现有系统的兼容性

## API 使用示例

### 基本使用
```bash
# 创建默认 genre 的作业
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "task_prompt": "生成一份关于人工智能的报告"
  }'

# 创建特定 genre 的作业
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "task_prompt": "生成一份工作报告",
    "genre": "work_report"
  }'

# 创建讲话稿类型的作业
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "task_prompt": "生成一份关于环保的讲话稿",
    "genre": "speech_draft"
  }'
```

### 支持的 Genre 类型
- `"default"` - 通用文档（默认）
- `"work_report"` - 工作报告
- `"speech_draft"` - 讲话稿

## 优势

### 1. 灵活性和扩展性
- 支持多种文档类型
- 每种类型可以有不同的 prompt 策略
- 易于添加新的 genre

### 2. 向后兼容
- 现有 API 调用不受影响
- 默认使用 `"default"` genre
- 渐进式升级路径

### 3. 错误处理和容错
- 自动验证 genre 是否存在
- 自动回退到默认 genre
- 详细的日志记录

### 4. 数据完整性
- Genre 信息在整个流程中传递
- Redis 中完整存储 genre 信息
- 确保数据一致性

## 下一步计划

1. **API 文档更新**：更新 OpenAPI 文档以包含 genre 参数
2. **UI 支持**：在用户界面中提供 genre 选择
3. **更多 Genre**：根据实际需求添加更多文档类型
4. **性能优化**：考虑添加 genre 缓存机制
5. **监控和指标**：添加 genre 使用情况的监控

## 总结

Genre-aware API 功能成功实现，实现了：

- ✅ **完整集成**：从 API 请求到 Celery 任务执行的完整 genre 支持
- ✅ **数据传递**：Genre 信息在整个工作流程中正确传递
- ✅ **动态图构建**：根据 genre 动态创建相应的图执行器
- ✅ **错误处理**：优雅处理无效 genre 和异常情况
- ✅ **向后兼容**：保持与现有系统的完全兼容
- ✅ **测试验证**：全面的测试覆盖确保功能正确

这个更新为整个系统提供了强大的 genre-aware 能力，用户现在可以根据不同的文档类型选择最合适的 prompt 策略，大大提高了系统的适应性和用户体验！ 