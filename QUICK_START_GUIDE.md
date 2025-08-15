# AIDocGenerator 快速启动指南

## 概述

现在你可以使用两个一键启动脚本来启动 AIDocGenerator 服务，两个脚本都集成了自动日志轮转功能。

## 启动脚本

### 1. quick_start.sh - 单服务启动

启动单个 FastAPI 服务 + Celery Worker，适合开发和测试环境。

```bash
# 使用默认端口 8000
./quick_start.sh

# 使用自定义端口
./quick_start.sh 8001
```

**功能特性：**
- ✅ 自动检查 Redis 服务
- ✅ 自动检查 conda 环境
- ✅ 自动日志轮转（10M 大小限制）
- ✅ 后台运行，可安全关闭终端
- ✅ 统一日志输出到 `logs/app.log`

### 2. quick_start_multi.sh - 多 Worker + 负载均衡器

启动多个 Worker + 负载均衡器，适合生产环境和高并发场景。

```bash
# 启动 2 个 Worker，负载均衡器端口 8081
./quick_start_multi.sh 2 8081

# 启动 4 个 Worker，负载均衡器端口 8082
./quick_start_multi.sh 4 8082

# 使用默认配置（2 个 Worker，端口 8081）
./quick_start_multi.sh
```

**功能特性：**
- ✅ 支持 1-20 个 Worker
- ✅ 自动负载均衡
- ✅ 自动日志轮转（10M 大小限制）
- ✅ 健康检查
- ✅ 高并发处理能力

## 前置条件

### 1. 激活 conda 环境
```bash
conda activate ai-doc
```

### 2. 启动 Redis 服务
```bash
# 如果使用本地 Redis
redis-server

# 或者使用远程 Redis（项目默认配置）
```

## 使用方法

### 启动服务

```bash
# 单服务模式
./quick_start.sh

# 多 Worker 模式
./quick_start_multi.sh 4 8081
```

### 验证服务

```bash
# 单服务模式
curl http://127.0.0.1:8000/

# 多 Worker 模式
curl http://127.0.0.1:8081/
curl http://127.0.0.1:8081/health
```

### 查看日志

```bash
# 查看实时日志
tail -f logs/app.log

# 查看日志备份文件
ls -lh logs/app.log*

# 查看特定备份文件
tail -f logs/app.log.1
```

### 停止服务

```bash
# 停止单服务
./stop_dev_server.sh

# 停止多 Worker
./stop_multi.sh
```

## 日志轮转功能

### 自动轮转
- 日志文件大小超过 10M 时自动轮转
- 保留 5 个备份文件（app.log.1, app.log.2, ...）
- 每 30 秒检查一次文件大小

### 手动轮转
```bash
./log_rotate.sh
```

### 测试轮转功能
```bash
./test_log_rotation.sh
```

## 配置选项

可以通过修改脚本中的以下变量来自定义配置：

```bash
# 日志轮转配置
LOG_SIZE="10M"           # 文件大小限制 (支持 K, M, G)
LOG_ROTATE_COUNT=5       # 保留的备份文件数量

# 多 Worker 配置
DEFAULT_WORKERS=2        # 默认 Worker 数量
BASE_PORT=8000          # Worker 起始端口
LB_PORT=8081            # 负载均衡器端口
```

## 故障排除

### 1. 端口被占用
```bash
# 检查端口占用
lsof -i :8000
lsof -i :8081

# 停止占用端口的进程
kill -9 <PID>
```

### 2. Redis 连接失败
```bash
# 检查 Redis 服务
redis-cli ping

# 如果使用本地 Redis
redis-server
```

### 3. conda 环境问题
```bash
# 检查当前环境
echo $CONDA_DEFAULT_ENV

# 激活正确环境
conda activate ai-doc
```

### 4. 服务启动失败
```bash
# 查看详细日志
tail -f logs/app.log

# 检查进程状态
ps aux | grep -E "(celery|uvicorn|load_balancer)"

# 强制停止所有服务
./stop_dev_server.sh
./stop_multi.sh
```

## 性能建议

### 单服务模式
- 适合开发和测试
- 支持热重载（--reload）
- 内存占用较低

### 多 Worker 模式
- 适合生产环境
- 支持高并发
- 建议 Worker 数量 = CPU 核心数 × 2

## 监控和管理

### 查看服务状态
```bash
# 查看所有相关进程
ps aux | grep -E "(celery|uvicorn|load_balancer)"

# 查看端口占用
netstat -tlnp | grep -E "(8000|8001|8081)"
```

### 性能测试
```bash
# 运行性能测试
python simple_log_test.py
```

### 日志管理
```bash
# 设置定时轮转
./setup_log_rotation.sh

# 查看 cron 任务
crontab -l
```

## 总结

现在你可以：

✅ **一键启动单服务**：`./quick_start.sh`  
✅ **一键启动多 Worker**：`./quick_start_multi.sh 4 8081`  
✅ **自动日志轮转**：防止日志文件无限增长  
✅ **后台运行**：启动后可安全关闭终端  
✅ **健康检查**：自动监控服务状态  
✅ **高并发支持**：多 Worker 负载均衡  

两个脚本都已经过测试，可以正常使用！
