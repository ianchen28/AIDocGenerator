# AIDocGenerator 脚本使用说明

## 📋 脚本概览

本项目提供了三个主要脚本来管理 AI 文档生成器服务：

### 1. `quick_start.sh` - 快速启动脚本 (后台运行版)
- **功能**: 清理环境 → 检查依赖 → 启动 Celery → 启动 Uvicorn → 后台运行
- **特点**: 服务在后台运行，可以安全关闭终端
- **用法**: `./quick_start.sh [端口号]`

### 2. `stop_dev_server.sh` - 停止服务脚本
- **功能**: 优雅地停止所有相关服务进程
- **特点**: 先尝试优雅终止，再强制终止，确保端口释放
- **用法**: `./stop_dev_server.sh`

### 3. `check_status.sh` - 状态检查脚本
- **功能**: 检查服务运行状态、端口占用、日志文件等
- **特点**: 提供详细的服务状态信息
- **用法**: `./check_status.sh`

## 🚀 快速开始

### 启动服务
```bash
# 使用默认端口 8000
./quick_start.sh

# 使用自定义端口
./quick_start.sh 8080
```

### 检查状态
```bash
./check_status.sh
```

### 停止服务
```bash
./stop_dev_server.sh
```

## 📁 文件结构

启动服务后，会生成以下文件：

```
AIDocGenerator/
├── service.pid          # 进程ID文件
├── logs/               # 日志目录
│   ├── celery_worker.log  # Celery Worker 日志
│   └── uvicorn.log       # Uvicorn 服务日志
├── quick_start.sh      # 启动脚本
├── stop_dev_server.sh  # 停止脚本
└── check_status.sh     # 状态检查脚本
```

## 🔧 管理命令

### 查看实时日志
```bash
# 查看所有日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/celery_worker.log
tail -f logs/uvicorn.log
```

### 查看进程状态
```bash
# 查看所有相关进程
ps aux | grep -E '(celery|uvicorn)'

# 查看端口占用
lsof -i :8000
```

### 手动停止进程
```bash
# 如果脚本无法停止，可以手动停止
kill -9 $(cat service.pid)
```

## ⚠️ 注意事项

1. **环境要求**: 确保已激活 `ai-doc` conda 环境
2. **Redis 服务**: 确保 Redis 服务正在运行
3. **端口冲突**: 如果端口被占用，脚本会自动处理
4. **权限问题**: 某些进程可能需要更高权限才能终止

## 🐛 故障排除

### 服务启动失败
1. 检查 conda 环境: `conda info --envs`
2. 检查 Redis 服务: `redis-cli ping`
3. 查看日志文件: `tail -f logs/*.log`

### 端口被占用
1. 使用状态检查: `./check_status.sh`
2. 手动停止: `./stop_dev_server.sh`
3. 检查端口: `lsof -i :8000`

### 进程无法停止
1. 检查权限: `sudo ./stop_dev_server.sh`
2. 手动终止: `kill -9 $(pgrep -f "uvicorn")`
3. 重启系统: 最后手段

## 📞 服务信息

- **服务地址**: http://127.0.0.1:8000
- **API文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health

## 🔄 工作流程

1. **启动**: `./quick_start.sh` → 服务在后台运行
2. **使用**: 访问 API 或文档页面
3. **监控**: `./check_status.sh` → 查看状态
4. **停止**: `./stop_dev_server.sh` → 清理环境
