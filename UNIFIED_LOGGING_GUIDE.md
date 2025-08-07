# 统一日志配置指南

## 📝 概述

现在所有日志都统一输出到 `logs/app.log` 文件中，不再分散到多个文件。

## 🔧 配置变更

### 1. 日志输出位置
- **之前**：多个文件（`logs/app.log`、`logs/celery_worker.log`、控制台等）
- **现在**：统一输出到 `logs/app.log`

### 2. 日志格式
```
{时间戳} | {日志级别} | {模块名}:{函数名}:{行号} | {run_id} | {消息内容}
```

## 🚀 启动服务

### 方法1：使用统一启动脚本
```bash
cd service
./start_unified_logging.sh
```

### 方法2：手动启动
```bash
cd service
conda activate ai-doc
celery -A workers.celery_worker worker --loglevel=INFO --concurrency=1 --logfile=logs/app.log
```

## 📊 查看日志

### 1. 使用统一日志查看工具
```bash
# 查看最后50行日志
python view_unified_logs.py view 50

# 实时监控日志
python view_unified_logs.py monitor

# 搜索日志
python view_unified_logs.py search "researcher"

# 显示日志统计
python view_unified_logs.py stats
```

### 2. 直接查看文件
```bash
# 查看最后100行
tail -n 100 logs/app.log

# 实时监控
tail -f logs/app.log

# 搜索关键词
grep "researcher" logs/app.log
```

## 🔍 日志内容

现在 `logs/app.log` 包含：

1. **API 请求日志**
   - 请求接收、处理、响应
   - 错误和异常信息

2. **Celery 任务日志**
   - 任务开始、执行、完成
   - 任务错误和异常

3. **工作流节点日志**
   - `researcher.py` 中的所有日志
   - `supervisor.py` 的决策日志
   - 其他节点的执行日志

4. **搜索工具日志**
   - ES 搜索日志
   - 网络搜索日志
   - 错误和异常信息

5. **系统配置日志**
   - 应用启动配置
   - 组件初始化日志

## 📋 日志级别

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **SUCCESS**: 成功信息

## 🎯 优势

1. **统一管理**：所有日志在一个文件中
2. **易于查找**：不需要在多个文件间切换
3. **完整追踪**：从 API 请求到任务完成的完整链路
4. **便于调试**：错误信息集中，便于问题定位

## 🔧 故障排除

### 如果日志文件过大
```bash
# 压缩旧日志
gzip logs/app.log.2025-08-07_*

# 清理旧日志
find logs/ -name "*.log.*" -mtime +7 -delete
```

### 如果需要控制台输出
编辑 `service/src/doc_agent/core/logging_config.py`，取消注释控制台输出部分。

## 📝 示例

### 查看特定任务的日志
```bash
# 搜索特定任务ID
python view_unified_logs.py search "1754568273124304685"

# 查看 researcher 节点的错误
python view_unified_logs.py search "researcher.*ERROR"
```

### 实时监控任务执行
```bash
# 启动监控
python view_unified_logs.py monitor

# 在另一个终端提交任务
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test_logging", "outline_json": "{\"title\": \"测试\", \"nodes\": []}", "session_id": "test"}'
```

现在所有日志都统一输出到 `logs/app.log`，方便查看和调试！🎉
