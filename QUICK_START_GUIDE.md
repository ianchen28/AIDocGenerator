# 🚀 快速启动指南 (统一日志版)

## 📝 概述

现在使用 `quick_start.sh` 一键启动所有服务，所有日志统一输出到 `logs/app.log`。

## 🎯 使用方法

### 1. **一键启动**
```bash
# 启动所有服务（后台运行）
./quick_start.sh

# 或者指定端口
./quick_start.sh 8000
```

### 2. **查看日志**
```bash
# 实时查看统一日志
tail -f logs/app.log

# 使用日志查看工具
python view_unified_logs.py monitor
```

### 3. **停止服务**
```bash
./stop_dev_server.sh
```

## 📊 日志管理

### 查看日志
```bash
# 查看最后50行
python view_unified_logs.py view 50

# 实时监控
python view_unified_logs.py monitor

# 搜索关键词
python view_unified_logs.py search "researcher"

# 显示统计
python view_unified_logs.py stats
```

### 直接查看文件
```bash
# 查看最后100行
tail -n 100 logs/app.log

# 实时监控
tail -f logs/app.log

# 搜索关键词
grep "researcher" logs/app.log
```

## 🔍 包含的日志内容

`logs/app.log` 现在包含：

- ✅ **API 请求日志** - 所有 HTTP 请求和响应
- ✅ **Celery 任务日志** - 任务执行全过程
- ✅ **工作流节点日志** - researcher、supervisor、writer 等
- ✅ **搜索工具日志** - ES 搜索、网络搜索
- ✅ **错误和异常** - 完整的错误堆栈信息
- ✅ **系统配置日志** - 应用启动和初始化

## 🎉 优势

1. **一键启动** - 不需要分别启动多个服务
2. **统一日志** - 所有日志在一个文件中，便于调试
3. **后台运行** - 启动后可以关闭终端
4. **完整追踪** - 从 API 请求到任务完成的完整链路

## 📋 服务信息

启动成功后，你会看到：

```
🎉 服务启动成功！
==========================================
   - 服务地址: http://127.0.0.1:8000
   - API文档: http://127.0.0.1:8000/docs
   - 统一日志: logs/app.log
   - PID文件: service.pid
```

## 🔧 故障排除

### 如果启动失败
```bash
# 1. 检查环境
conda activate ai-doc

# 2. 检查 Redis
redis-cli ping

# 3. 强制停止旧服务
./stop_dev_server.sh

# 4. 重新启动
./quick_start.sh
```

### 如果日志文件过大
```bash
# 压缩旧日志
gzip logs/app.log.2025-08-07_*

# 清理旧日志
find logs/ -name "*.log.*" -mtime +7 -delete
```

## 📝 示例工作流

```bash
# 1. 启动服务
./quick_start.sh

# 2. 提交任务
curl -X POST "http://localhost:8000/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test", "outline_json": "{\"title\": \"测试\", \"nodes\": []}", "session_id": "test"}'

# 3. 查看日志
python view_unified_logs.py monitor

# 4. 停止服务
./stop_dev_server.sh
```

现在只需要运行 `./quick_start.sh` 就能启动所有服务，所有日志都会统一输出到 `logs/app.log`！🎉
