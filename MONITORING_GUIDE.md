# 文档生成系统监控指南

## 概述

本文档介绍如何使用各种监控工具来跟踪文档生成任务的执行状态和调试问题。

## 日志文件位置

### 主要日志文件

1. **应用日志**: `logs/app.log`
   - 包含API端点的调用日志
   - 记录任务提交和响应信息

2. **Celery Worker日志**: `logs/celery_worker.log`
   - 包含任务执行的详细日志
   - 记录工作流节点的执行过程
   - 显示错误和异常信息

3. **Uvicorn日志**: `logs/uvicorn.log`
   - 包含Web服务器的访问日志
   - 记录HTTP请求和响应

4. **Mock服务日志**: `logs/mock_service.log`
   - 包含模拟服务的运行日志

## 监控工具

### 1. 任务监控脚本 (`monitor_tasks.py`)

实时监控指定任务的执行状态。

#### 使用方法

```bash
# 列出最近的任务
python monitor_tasks.py

# 监控指定任务
python monitor_tasks.py <task_id>

# 示例
python monitor_tasks.py 1754567324119284091
```

#### 功能特点

- 🔍 实时监控Redis流事件
- 📊 显示任务进度和状态
- ⚠️ 显示错误和异常信息
- 📝 显示章节处理进度
- 📚 显示参考文献生成状态

#### 事件类型说明

- `task_started`: 任务开始
- `task_progress`: 任务进度更新
- `chapter_started`: 章节开始处理
- `chapter_progress`: 章节处理进度
- `chapter_completed`: 章节完成
- `writer_started`: 写作开始
- `document_content_stream`: 文档内容流式输出
- `citations_completed`: 参考文献完成
- `document_generated`: 文档生成完成
- `task_completed`: 任务完成
- `task_failed`: 任务失败
- `chapter_failed`: 章节失败

### 2. 日志查看脚本 (`view_logs.py`)

查看和管理各种日志文件。

#### 使用方法

```bash
# 列出可用的日志文件
python view_logs.py list

# 查看日志文件的最后几行
python view_logs.py view <log_file> [lines]

# 实时监控日志文件
python view_logs.py monitor <log_file> [interval]

# 示例
python view_logs.py view logs/celery_worker.log 100
python view_logs.py monitor logs/celery_worker.log 2
```

#### 功能特点

- 📋 列出所有可用的日志文件
- 📄 查看日志文件的最后几行
- 🔍 实时监控日志文件的变化
- ⏱️ 可配置刷新间隔

## 增强的日志记录

### API端点日志

在 `service/api/endpoints.py` 中添加了详细的日志记录：

- 📥 请求接收日志
- 📋 请求详情记录
- 🆔 任务ID生成日志
- 🔍 JSON解析日志
- 🚀 任务提交日志
- 📤 响应返回日志
- ❌ 错误处理和堆栈跟踪

### 任务执行日志

在 `service/workers/tasks.py` 中添加了详细的检查点：

- 🚀 任务开始和结束
- 🔗 Redis连接状态
- 📢 事件发布状态
- 🏗️ 状态初始化
- 📖 章节信息提取
- 🔧 工作流图获取
- 📝 章节处理进度
- ⚙️ 步骤执行状态
- 🚀 工作流执行
- 📄 结果提取
- 📚 引用源收集
- 🎭 模拟数据生成
- 💾 结果保存
- 🎉 任务完成

## 常见问题排查

### 1. 任务卡住

**症状**: 任务长时间处于运行状态，没有进度更新

**排查步骤**:
1. 使用监控脚本查看任务状态
2. 检查Celery worker日志
3. 查看Redis中的事件流

```bash
# 监控任务
python monitor_tasks.py <task_id>

# 查看worker日志
python view_logs.py view logs/celery_worker.log 100
```

### 2. 递归限制错误

**症状**: 出现 "Recursion limit of 25 reached" 错误

**原因**: 工作流图陷入无限循环

**解决方案**:
1. 检查supervisor路由逻辑
2. 增加递归限制
3. 优化搜索策略

### 3. 搜索失败

**症状**: ES搜索或网络搜索失败

**排查步骤**:
1. 检查ES连接配置
2. 验证网络搜索API
3. 查看搜索工具日志

### 4. 事件发布失败

**症状**: Redis事件发布失败

**排查步骤**:
1. 检查Redis连接
2. 验证Redis配置
3. 查看网络连接

## 性能监控

### 任务执行时间

通过日志可以监控：
- 任务总执行时间
- 各章节处理时间
- 搜索耗时
- 内容生成时间

### 资源使用

监控：
- Redis连接状态
- 内存使用情况
- CPU使用率
- 网络连接状态

## 最佳实践

### 1. 定期检查日志

```bash
# 每天检查一次日志
python view_logs.py view logs/app.log 50
python view_logs.py view logs/celery_worker.log 50
```

### 2. 实时监控重要任务

```bash
# 监控正在执行的任务
python monitor_tasks.py <task_id>
```

### 3. 设置日志轮转

确保日志文件不会无限增长：
- 设置日志文件大小限制
- 配置日志保留时间
- 启用日志压缩

### 4. 错误告警

设置监控脚本定期检查：
- 任务失败率
- 错误日志数量
- 系统资源使用

## 故障排除

### 1. 日志文件过大

```bash
# 压缩旧日志
gzip logs/app.log.1
gzip logs/celery_worker.log.1
```

### 2. Redis连接问题

```bash
# 测试Redis连接
redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" ping
```

### 3. Celery Worker问题

```bash
# 检查worker状态
cd service && celery -A workers.celery_worker inspect active

# 重启worker
pkill -f "celery.*worker"
cd service && celery -A workers.celery_worker worker --loglevel=INFO
```

## 总结

通过使用这些监控工具，您可以：

1. 🔍 **实时监控** 任务执行状态
2. 📊 **跟踪进度** 和性能指标
3. ⚠️ **快速定位** 问题和错误
4. 📈 **优化性能** 和资源使用
5. 🛠️ **调试问题** 和异常情况

这些工具将帮助您更好地管理和维护文档生成系统。
