# AI文档生成系统自动化操作指南

## 概述

本指南介绍如何使用AI文档生成系统的自动化操作功能，实现优雅标准的自动文档生成流程。

## 系统架构

### 核心组件

1. **自动化管理器 (AutomationManager)**
   - 统一管理所有自动化组件
   - 提供简洁的API接口
   - 处理系统配置和状态管理

2. **任务调度器 (AutomationScheduler)**
   - 管理单个文档生成任务
   - 支持任务优先级和重试机制
   - 持久化任务状态

3. **批量执行器 (AutomationExecutor)**
   - 处理批量文档生成作业
   - 控制并发执行数量
   - 生成执行报告和结果归档

4. **智能监控器 (AutomationMonitor)**
   - 实时监控系统性能
   - 检测异常并生成告警
   - 收集性能指标历史

## 快速开始

### 1. 基本使用

```python
import asyncio
from src.doc_agent.automation import AutomationManager, TaskPriority

async def main():
    # 创建自动化管理器
    manager = AutomationManager(
        storage_path="output/automation",
        max_concurrent_tasks=3
    )
    
    # 启动系统
    await manager.start()
    
    # 添加单个任务
    task_id = manager.add_task(
        name="技术文档生成",
        topic="水电站技术文档",
        priority=TaskPriority.HIGH
    )
    
    # 停止系统
    manager.stop()

asyncio.run(main())
```

### 2. 批量作业

```python
# 创建批量作业
topics = [
    "水电站建设技术",
    "水电站运行维护", 
    "水电站安全管理"
]

job_id = manager.create_batch_job(
    name="水电站系列文档",
    topics=topics,
    description="批量生成水电站相关文档"
)

# 执行批量作业
await manager.execute_batch_job(job_id)

# 归档结果
archive_path = manager.archive_results(job_id)
```

### 3. 监控和告警

```python
def alert_callback(alert):
    print(f"告警: {alert.message}")

# 创建带告警回调的管理器
manager = AutomationManager(
    alert_callbacks=[alert_callback]
)

# 手动添加告警
manager.add_alert(
    level=AlertLevel.WARNING,
    message="CPU使用率过高",
    source="monitor"
)

# 获取告警列表
alerts = manager.get_alerts(resolved=False)
```

## 详细功能

### 任务管理

#### 添加任务
```python
task_id = manager.add_task(
    name="任务名称",
    topic="文档主题",
    description="任务描述",
    priority=TaskPriority.HIGH,  # LOW, NORMAL, HIGH, URGENT
    max_retries=3,
    metadata={"category": "technical"}
)
```

#### 任务状态
- `PENDING`: 等待执行
- `RUNNING`: 正在执行
- `COMPLETED`: 执行完成
- `FAILED`: 执行失败
- `CANCELLED`: 已取消
- `RETRYING`: 重试中

#### 任务操作
```python
# 获取任务
task = manager.get_task(task_id)

# 获取任务列表
tasks = manager.get_tasks(status=TaskStatus.PENDING)

# 取消任务
manager.cancel_task(task_id)

# 删除任务
manager.delete_task(task_id)
```

### 批量作业管理

#### 创建批量作业
```python
job_id = manager.create_batch_job(
    name="批量作业名称",
    topics=["主题1", "主题2", "主题3"],
    description="作业描述",
    metadata={"category": "batch"}
)
```

#### 批量作业状态
- `PENDING`: 等待执行
- `RUNNING`: 正在执行
- `COMPLETED`: 执行完成
- `FAILED`: 执行失败
- `CANCELLED`: 已取消

#### 批量作业操作
```python
# 执行批量作业
await manager.execute_batch_job(job_id)

# 获取作业信息
job = manager.get_batch_job(job_id)

# 取消作业
manager.cancel_batch_job(job_id)

# 归档结果
archive_path = manager.archive_results(job_id)
```

### 监控功能

#### 性能指标
```python
# 获取历史性能指标
metrics = manager.get_metrics_history(hours=24)

for metric in metrics:
    print(f"CPU: {metric.cpu_percent}%")
    print(f"内存: {metric.memory_percent}%")
    print(f"磁盘: {metric.disk_usage_percent}%")
```

#### 告警管理
```python
# 添加告警
manager.add_alert(
    level=AlertLevel.WARNING,  # INFO, WARNING, ERROR, CRITICAL
    message="告警消息",
    source="monitor",
    details={"cpu_percent": 85.0}
)

# 获取告警
alerts = manager.get_alerts(
    level=AlertLevel.WARNING,
    resolved=False
)

# 解决告警
manager.resolve_alert(alert_id)
```

### 配置管理

#### 获取配置
```python
config = manager.get_config()
print(f"CPU阈值: {config['monitor']['cpu_threshold']}%")
print(f"最大并发任务: {config['executor']['max_concurrent_tasks']}")
```

#### 更新配置
```python
new_config = {
    "monitor": {
        "cpu_threshold": 90.0,
        "memory_threshold": 90.0,
        "disk_threshold": 95.0,
        "task_failure_threshold": 0.2
    },
    "executor": {
        "max_concurrent_tasks": 5
    }
}

manager.update_config(new_config)
```

### 数据管理

#### 导出数据
```python
manager.export_data("output/export")
```

#### 导入数据
```python
manager.import_data("output/export")
```

#### 清理旧数据
```python
# 清理30天前的数据
manager.cleanup_old_data(days=30)
```

## 系统统计

### 获取统计信息
```python
stats = manager.get_system_statistics()

print(f"调度器统计: {stats['scheduler']}")
print(f"监控器统计: {stats['monitor']}")
print(f"执行器统计: {stats['executor']}")
print(f"系统状态: {stats['system']}")
```

## 最佳实践

### 1. 错误处理
```python
try:
    await manager.start()
    task_id = manager.add_task("任务", "主题")
    # 处理任务...
except Exception as e:
    print(f"错误: {e}")
finally:
    manager.stop()
```

### 2. 资源管理
```python
# 使用上下文管理器
async with manager:
    task_id = manager.add_task("任务", "主题")
    # 自动处理启动和停止
```

### 3. 监控告警
```python
def custom_alert_handler(alert):
    if alert.level == AlertLevel.CRITICAL:
        # 发送紧急通知
        send_emergency_notification(alert)
    elif alert.level == AlertLevel.WARNING:
        # 记录警告日志
        log_warning(alert)

manager = AutomationManager(alert_callbacks=[custom_alert_handler])
```

### 4. 批量处理
```python
# 分批处理大量任务
topics = ["主题1", "主题2", "主题3", ...]
batch_size = 10

for i in range(0, len(topics), batch_size):
    batch_topics = topics[i:i+batch_size]
    job_id = manager.create_batch_job(f"批次{i//batch_size+1}", batch_topics)
    await manager.execute_batch_job(job_id)
```

## 配置说明

### 监控阈值
- `cpu_threshold`: CPU使用率阈值 (默认80%)
- `memory_threshold`: 内存使用率阈值 (默认85%)
- `disk_threshold`: 磁盘使用率阈值 (默认90%)
- `task_failure_threshold`: 任务失败率阈值 (默认30%)

### 执行器配置
- `max_concurrent_tasks`: 最大并发任务数 (默认3)

### 存储配置
- `storage_path`: 数据存储路径 (默认output/automation)

## 故障排除

### 常见问题

1. **任务执行失败**
   - 检查LLM服务连接
   - 验证配置参数
   - 查看错误日志

2. **系统性能问题**
   - 调整并发任务数
   - 检查资源使用情况
   - 优化监控阈值

3. **数据丢失**
   - 检查存储路径权限
   - 验证数据文件完整性
   - 使用备份恢复

### 日志查看
```bash
# 查看自动化日志
tail -f output/automation/automation.log

# 查看任务日志
cat output/automation/scheduler/tasks.json

# 查看告警日志
cat output/automation/monitor/alerts.json
```

## 扩展开发

### 自定义告警处理器
```python
class CustomAlertHandler:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def __call__(self, alert):
        # 发送到外部系统
        send_webhook(self.webhook_url, alert.to_dict())

handler = CustomAlertHandler("https://api.example.com/webhook")
manager = AutomationManager(alert_callbacks=[handler])
```

### 自定义监控指标
```python
class CustomMetrics:
    def collect_custom_metrics(self):
        # 收集自定义指标
        return {
            "custom_metric": 42.0,
            "timestamp": datetime.now()
        }
```

## 总结

自动化系统提供了完整的文档生成自动化解决方案，包括：

- ✅ 优雅的任务调度和管理
- ✅ 智能的监控和告警
- ✅ 高效的批量处理
- ✅ 完善的配置管理
- ✅ 可靠的数据持久化
- ✅ 详细的执行报告

通过合理使用这些功能，可以大大提高文档生成的效率和质量。 