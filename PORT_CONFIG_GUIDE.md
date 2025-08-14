# 端口配置指南

## 快速配置

### 方法1: 修改脚本配置（推荐）
编辑 `quick_start_multi.sh` 文件开头：

```bash
# 默认配置 - 只需要修改这里的端口即可
DEFAULT_WORKERS=2
BASE_PORT=8000
LB_PORT=8081  # 负载均衡器端口，可以改为 8082, 8083, 9000 等
UNIFIED_LOG="logs/app.log"
```

然后正常启动：
```bash
./quick_start_multi.sh 4
```

### 方法2: 命令行指定端口
```bash
# 启动 4 个 worker，负载均衡器使用 8082 端口
./quick_start_multi.sh 4 8082

# 启动 8 个 worker，负载均衡器使用 9000 端口
./quick_start_multi.sh 8 9000
```

## 常用端口选择

### 推荐端口范围
- **8081-8089**: 开发环境常用
- **9000-9099**: 生产环境常用
- **3000-3999**: 前端开发常用

### 避免使用的端口
- **1024 以下**: 需要 root 权限
- **22, 80, 443**: 系统保留端口
- **3306, 5432**: 数据库端口
- **6379**: Redis 端口

## 端口检查

### 检查端口是否被占用
```bash
# 检查 8081 端口
lsof -i :8081

# 检查端口范围
lsof -i :8080-8090
```

### 查看当前服务端口
```bash
# 查看所有相关进程
ps aux | grep -E '(uvicorn|load_balancer)'

# 查看端口占用
netstat -tlnp | grep -E '(8000|8081)'
```

## 故障排除

### 端口被占用
```bash
# 错误信息
❌ 负载均衡器端口 8081 已被占用
   请选择其他端口，例如: ./quick_start_multi.sh 4 8082

# 解决方案
./quick_start_multi.sh 4 8082
```

### 权限问题
```bash
# 如果使用 1024 以下端口
❌ 负载均衡器端口必须在 1024-65535 之间

# 解决方案：使用 1024 以上端口
./quick_start_multi.sh 4 8081
```

## 示例配置

### 开发环境
```bash
# 2个 worker，端口 8081
./quick_start_multi.sh 2 8081

# 4个 worker，端口 8082
./quick_start_multi.sh 4 8082
```

### 生产环境
```bash
# 8个 worker，端口 9000
./quick_start_multi.sh 8 9000

# 16个 worker，端口 9001
./quick_start_multi.sh 16 9001
```

## 访问地址

启动后，通过以下地址访问：

```bash
# 负载均衡器地址
http://127.0.0.1:8081  # 或你配置的端口

# API 文档
http://127.0.0.1:8081/docs

# 健康检查
http://127.0.0.1:8081/health
```
