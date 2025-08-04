# API测试指南

## 🚀 快速开始

### 1. 启动所有服务

```bash
# 1. 启动Redis服务
redis-server

# 2. 启动API服务器
cd service
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 3. 启动Celery Worker
cd service
python -m workers.celery_worker worker --loglevel=info
```

### 2. 运行API测试

```bash
# 运行完整的API测试
./test_outline_generation.sh
```

### 3. 监听任务进度

```bash
# 监听特定任务的Redis流
./monitor_redis_stream.sh outline_generation:test_session_001
```

## 📋 API端点说明

### 大纲生成API

**端点**: `POST /api/v1/jobs/outline`

**请求体**:
```json
{
  "sessionId": "unique_session_id",
  "taskPrompt": "请生成一份关于...的大纲",
  "isOnline": true,
  "contextFiles": []
}
```

**响应**:
```json
{
  "sessionId": "unique_session_id",
  "redisStreamKey": "outline_generation:unique_session_id",
  "status": "ACCEPTED",
  "message": "大纲生成任务已提交，请通过Redis流监听进度"
}
```

## 🧪 测试用例

### 测试1: 基本大纲生成
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_001",
    "taskPrompt": "请为我生成一份关于人工智能在医疗领域应用的详细大纲",
    "isOnline": true,
    "contextFiles": []
  }'
```

### 测试2: 带上下文文件的大纲生成
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_002",
    "taskPrompt": "基于提供的参考资料，生成一份关于区块链技术的应用大纲",
    "isOnline": false,
    "contextFiles": [
      {
        "file_id": "file_001",
        "file_name": "blockchain_guide.pdf",
        "storage_url": "https://example.com/files/blockchain_guide.pdf",
        "file_type": "content"
      }
    ]
  }'
```

### 测试3: 学术论文大纲
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_session_003",
    "taskPrompt": "生成一份关于机器学习在金融风控中的应用研究论文大纲",
    "isOnline": true,
    "contextFiles": []
  }'
```

## 🔍 监控任务进度

### 方法1: 使用Redis CLI
```bash
# 监听特定流
redis-cli --raw XREAD COUNT 10 BLOCK 5000 STREAMS "outline_generation:test_session_001" 0

# 查看流信息
redis-cli XLEN "outline_generation:test_session_001"

# 查看流内容
redis-cli XRANGE "outline_generation:test_session_001" - +
```

### 方法2: 使用监控脚本
```bash
./monitor_redis_stream.sh outline_generation:test_session_001
```

## 📊 健康检查

```bash
# 根端点
curl http://localhost:8000/

# 健康检查端点
curl http://localhost:8000/api/v1/health
```

## 🛠️ 故障排除

### 常见问题

1. **404错误**: 检查API服务器是否运行在正确的端口
2. **连接被拒绝**: 检查Redis服务是否运行
3. **任务不执行**: 检查Celery worker是否运行
4. **流监听无数据**: 检查Redis流key是否正确

### 检查服务状态

```bash
# 检查API服务器
ps aux | grep uvicorn

# 检查Redis服务
redis-cli ping

# 检查Celery worker
ps aux | grep celery
```

## 📝 日志查看

```bash
# API服务器日志
tail -f logs/api.log

# Celery worker日志
tail -f logs/celery.log

# Redis日志
tail -f /var/log/redis/redis-server.log
```

## 🎯 预期结果

成功的API调用应该返回：
- HTTP状态码: 202 (Accepted)
- 包含redisStreamKey的JSON响应
- 任务在后台异步执行
- Redis流中可以看到任务进度事件

## 📚 相关文件

- `test_outline_generation.sh`: 完整的API测试脚本
- `monitor_redis_stream.sh`: Redis流监听脚本
- `api/endpoints.py`: API端点定义
- `workers/tasks.py`: Celery任务定义
- `src/doc_agent/schemas.py`: 数据模型定义 