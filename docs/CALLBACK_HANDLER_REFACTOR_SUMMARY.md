# RedisCallbackHandler 重构总结

## 🎯 **重构目标**

将 `RedisCallbackHandler` 重构为使用新的 `RedisStreamPublisher`，从 Redis Pub/Sub 模式迁移到 Redis Streams 模式。

## ✅ **重构内容**

### 1. **导入模块更新**

#### **修改前**
```python
# 导入Redis客户端
try:
    from ....workers.tasks import get_redis_client
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path

    # 添加项目根目录到Python路径
    current_file = Path(__file__)
    service_dir = current_file.parent.parent.parent.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    from workers.tasks import get_redis_client
```

#### **修改后**
```python
# 导入Redis Streams发布器
try:
    from ....core.redis_stream_publisher import RedisStreamPublisher
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path

    # 添加项目根目录到Python路径
    current_file = Path(__file__)
    service_dir = current_file.parent.parent.parent.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    from core.redis_stream_publisher import RedisStreamPublisher
```

### 2. **构造函数重构**

#### **修改前**
```python
def __init__(self, job_id: str):
    """
    初始化Redis回调处理器

    Args:
        job_id: 作业ID，用于构建Redis频道名称
    """
    super().__init__()
    self.job_id = job_id
    self.channel_name = f"job:{job_id}:events"
    self.redis_client = None

    logger.info(
        f"Redis回调处理器已初始化 - Job ID: {job_id}, Channel: {self.channel_name}")
```

#### **修改后**
```python
def __init__(self, job_id: str, publisher: RedisStreamPublisher):
    """
    初始化Redis回调处理器

    Args:
        job_id: 作业ID，用于构建事件流名称
        publisher: Redis Streams发布器实例
    """
    super().__init__()
    self.job_id = job_id
    self.publisher = publisher

    logger.info(
        f"Redis回调处理器已初始化 - Job ID: {job_id}")
```

### 3. **事件发布方法重构**

#### **修改前**
```python
async def _get_redis_client(self):
    """获取Redis客户端实例"""
    if self.redis_client is None:
        try:
            self.redis_client = await get_redis_client()
        except Exception as e:
            logger.error(f"获取Redis客户端失败: {e}")
            self.redis_client = None
    return self.redis_client

async def _publish_event(self, event_type: str, data: dict[str, Any]):
    """
    发布事件到Redis

    Args:
        event_type: 事件类型
        data: 事件数据
    """
    try:
        redis = await self._get_redis_client()
        if redis is None:
            return

        # 构建事件载荷
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "job_id": self.job_id
        }

        # 发布到Redis频道
        await redis.publish(self.channel_name,
                            json.dumps(payload, ensure_ascii=False))

        logger.debug(f"事件已发布 - 类型: {event_type}, 频道: {self.channel_name}")

    except Exception as e:
        logger.error(f"发布事件失败: {e}")
```

#### **修改后**
```python
async def _publish_event(self, event_type: str, data: dict[str, Any]):
    """
    发布事件到Redis Stream

    Args:
        event_type: 事件类型
        data: 事件数据
    """
    try:
        # 构建事件载荷
        event_payload = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "job_id": self.job_id
        }

        # 使用Redis Streams发布器发布事件
        await self.publisher.publish_event(self.job_id, event_payload)

        logger.debug(f"事件已发布到Stream - 类型: {event_type}, Job ID: {self.job_id}")

    except Exception as e:
        logger.error(f"发布事件失败: {e}")
```

### 4. **工厂函数更新**

#### **修改前**
```python
def create_redis_callback_handler(job_id: str) -> RedisCallbackHandler:
    """
    创建Redis回调处理器的工厂函数

    Args:
        job_id: 作业ID

    Returns:
        RedisCallbackHandler实例
    """
    return RedisCallbackHandler(job_id)
```

#### **修改后**
```python
def create_redis_callback_handler(job_id: str, publisher: RedisStreamPublisher) -> RedisCallbackHandler:
    """
    创建Redis回调处理器的工厂函数

    Args:
        job_id: 作业ID
        publisher: Redis Streams发布器实例

    Returns:
        RedisCallbackHandler实例
    """
    return RedisCallbackHandler(job_id, publisher)
```

## 🏗️ **技术改进**

### 1. **架构升级**
- **从 Pub/Sub 到 Streams** - 从 Redis Pub/Sub 模式迁移到 Redis Streams 模式
- **事件持久化** - Streams 提供事件持久化，支持历史记录查询
- **更好的可靠性** - Streams 提供更可靠的消息传递机制

### 2. **依赖注入**
- **解耦设计** - 通过依赖注入接收 `RedisStreamPublisher` 实例
- **更好的测试性** - 可以轻松模拟和测试
- **统一的发布器** - 使用统一的发布器管理所有事件

### 3. **事件结构优化**
- **标准化格式** - 使用统一的事件载荷格式
- **更好的类型支持** - 明确的事件类型字段
- **时间戳标准化** - 统一的时间戳格式

## 📊 **测试结果**

### ✅ **功能测试通过**
1. **回调处理器初始化** - 成功创建带有发布器的回调处理器
2. **链开始事件** - 成功发布链开始事件到 Stream
3. **链结束事件** - 成功发布链结束事件到 Stream
4. **工具事件** - 成功发布工具调用事件到 Stream
5. **错误事件** - 成功发布错误事件到 Stream
6. **LLM 事件** - 成功发布 LLM 调用事件到 Stream

### ✅ **事件验证**
- **事件类型** - 正确的事件类型标识
- **事件数据** - 完整的事件数据包含
- **时间戳** - 准确的时间戳记录
- **Job ID** - 正确的任务标识

## 🔧 **使用示例**

### 1. **创建回调处理器**
```python
# 获取 Redis 客户端和发布器
redis_client = await get_redis_client()
publisher = RedisStreamPublisher(redis_client)

# 创建回调处理器
callback_handler = create_redis_callback_handler(job_id, publisher)
```

### 2. **在 LangGraph 中使用**
```python
# 创建回调处理器
redis_client = await get_redis_client()
publisher = RedisStreamPublisher(redis_client)
callback_handler = create_redis_callback_handler(job_id, publisher)

# 在 LangGraph 配置中使用
config = {
    "callbacks": [callback_handler],
    "configurable": {
        "thread_id": job_id
    }
}

# 执行图
result = await graph.ainvoke(inputs, config=config)
```

### 3. **事件监控**
```python
# 监控事件流
stream_name = f"job_events:{job_id}"
events = await redis_client.xread({stream_name: "0"}, count=10)

for event_id, event_data in events[0][1]:
    print(f"Event ID: {event_id}")
    print(f"Event Type: {event_data.get('event_type', 'unknown')}")
    print(f"Data: {event_data.get('data', '')}")
```

## 🎯 **事件类型**

### 1. **链执行事件**
- `phase_update` - 阶段更新事件
- `done` - 链执行完成事件

### 2. **工具调用事件**
- `tool_call` - 工具调用开始事件
- `tool_result` - 工具调用结果事件

### 3. **LLM 事件**
- `thought` - LLM 思考过程事件

### 4. **错误事件**
- `error` - 错误事件

## 🎉 **重构优势**

### 1. **更好的事件管理**
- **持久化存储** - 事件持久化在 Redis Streams 中
- **历史记录** - 支持事件历史查询
- **可靠性** - 更可靠的消息传递机制

### 2. **统一的架构**
- **一致的发布器** - 使用统一的 `RedisStreamPublisher`
- **标准化的接口** - 统一的创建和使用方式
- **更好的集成** - 与新的 API 架构保持一致

### 3. **改进的可维护性**
- **依赖注入** - 更好的解耦和测试性
- **清晰的职责** - 明确的组件职责分工
- **统一的错误处理** - 一致的异常处理机制

### 4. **性能优化**
- **异步操作** - 支持异步事件发布
- **批量处理** - 支持事件批量读取
- **流式处理** - 支持实时事件流处理

## 🚀 **下一步工作**

### 1. **集成到 Celery 任务**
- 在 Celery 任务中使用重构后的回调处理器
- 实现完整的任务事件监控

### 2. **API 端点集成**
- 在 API 端点中使用回调处理器
- 实现实时事件推送

### 3. **监控和告警**
- 添加事件监控面板
- 实现异常事件告警

## 📝 **总结**

RedisCallbackHandler 重构成功完成！主要改进包括：

1. **架构升级** - 从 Redis Pub/Sub 迁移到 Redis Streams
2. **依赖注入** - 通过构造函数注入 `RedisStreamPublisher`
3. **事件结构优化** - 标准化的事件载荷格式
4. **更好的可靠性** - 持久化的事件存储和传递
5. **统一的接口** - 与新的 API 架构保持一致

重构后的回调处理器为后续的 Celery 任务实现和 API 集成提供了强大的事件处理基础！ 