# AIDocGenerator 服务启动指南

## 🚀 快速启动

### 方法一：使用快速启动脚本（推荐）

```bash
# 使用默认端口 8000
./quick_start.sh

# 使用自定义端口
./quick_start.sh 8001
```

### 方法二：直接启动开发服务器

```bash
# 使用默认端口 8000
./start_dev_server.sh

# 使用自定义端口
./start_dev_server.sh 8001
```

## 📋 启动流程

1. **环境检查**
   - 检查 Redis 服务状态
   - 激活 conda 环境 (ai-doc)

2. **依赖安装**
   - 安装项目依赖包
   - 配置开发环境

3. **服务启动**
   - 启动 Celery Worker (后台)
   - 启动 FastAPI 服务器 (前台)

## 🔧 服务配置

### 端口配置
- **默认端口**: 8000
- **自定义端口**: 通过命令行参数指定
- **示例**: `./quick_start.sh 8001` 使用端口 8001

### Redis 配置
- **远程 Redis**: 10.215.149.74:26379
- **认证**: 使用密码认证
- **数据库**: 0

### 环境要求
- **Python**: 3.8+
- **Conda**: ai-doc 环境
- **Redis**: 本地或远程服务

## 📊 服务状态

### 检查服务状态
```bash
# 查看进程
ps aux | grep uvicorn
ps aux | grep celery

# 查看日志
tail -f output.log
tail -f celery_worker.log
```

### 测试服务
```bash
# 健康检查
curl http://127.0.0.1:8000/

# API 文档
curl http://127.0.0.1:8000/docs

# 测试大纲生成
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_001",
    "taskPrompt": "请为我生成一份关于人工智能的详细大纲",
    "isOnline": true,
    "contextFiles": []
  }'
```

## 🛑 停止服务

### 方法一：使用 Ctrl+C
在运行 `start_dev_server.sh` 的终端中按 `Ctrl+C`

### 方法二：杀死进程
```bash
# 查找进程 PID
ps aux | grep uvicorn
ps aux | grep celery

# 杀死进程
kill <PID>
```

## 📝 日志文件

- **服务日志**: `output.log`
- **Celery 日志**: `celery_worker.log`
- **Redis 监控**: 使用 `monitor_redis_stream_pretty.sh`

## 🔍 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000
   
   # 杀死进程
   kill -9 <PID>
   ```

2. **Redis 连接失败**
   ```bash
   # 测试 Redis 连接
   redis-cli ping
   
   # 测试远程 Redis
   redis-cli -h 10.215.149.74 -p 26379 -a "xJrhp*4mnHxbBWN2grqq" ping
   ```

3. **环境激活失败**
   ```bash
   # 手动激活环境
   source ~/miniforge3/etc/profile.d/conda.sh
   conda activate ai-doc
   ```

4. **依赖安装失败**
   ```bash
   # 重新安装依赖
   cd service
   pip install -e . -i https://mirrors.aliyun.com/pypi/simple/
   ```

## 📚 相关文档

- [API 使用指南](service/docs/API_Usage_Guide.md)
- [Redis 流监控](service/monitor_redis_stream_pretty.sh)
- [测试脚本](service/test_complete_flow.sh) 