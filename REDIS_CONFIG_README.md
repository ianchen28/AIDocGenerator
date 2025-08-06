# Redis 配置管理说明

## 📋 当前配置

**默认配置**: 远程Redis服务器
- **主机**: 10.215.149.74
- **端口**: 26379
- **密码**: xJrhp*4mnHxbBWN2grqq
- **类型**: 🌐 远程Redis

## 🚀 快速使用

### 1. 启动服务（使用默认远程Redis）
```bash
./quick_start.sh
```

### 2. 检查服务状态
```bash
./check_status.sh
```

### 3. 切换到本地Redis（如需要）
```bash
./config_redis.sh
# 选择选项 1: 本地Redis
# 然后重启服务
./stop_dev_server.sh && ./quick_start.sh
```

### 4. 切换回远程Redis
```bash
./config_redis.sh
# 选择选项 2: 远程Redis
# 然后重启服务
./stop_dev_server.sh && ./quick_start.sh
```

## 🔧 配置管理

### 查看当前配置
```bash
./config_redis.sh
```

### 测试Redis连接
```bash
./config_redis.sh
# 选择选项 4: 测试当前配置
```

### 自定义配置
```bash
./config_redis.sh
# 选择选项 3: 自定义配置
# 按提示输入主机、端口、数据库、密码
```

## 📊 状态检查

运行状态检查脚本会显示：
- 📋 配置的Redis服务器信息
- 🌐 远程Redis 或 🏠 本地Redis
- ✅ Redis服务运行状态
- 📋 Redis版本和运行时间

## 🔄 配置切换流程

1. **查看当前配置**:
   ```bash
   ./check_status.sh
   ```

2. **切换配置**:
   ```bash
   ./config_redis.sh
   ```

3. **重启服务**:
   ```bash
   ./stop_dev_server.sh
   ./quick_start.sh
   ```

4. **验证配置**:
   ```bash
   ./check_status.sh
   ```

## 📝 配置文件位置

- **主配置文件**: `service/src/doc_agent/core/config.yaml`
- **备份文件**: `service/src/doc_agent/core/config.yaml.backup.YYYYMMDD_HHMMSS`

## ⚠️ 注意事项

1. **默认使用远程Redis**: 系统默认配置为远程Redis，无需本地Redis服务
2. **切换后需重启**: 修改配置后需要重启服务才能生效
3. **自动备份**: 配置切换时会自动创建备份文件
4. **网络连接**: 使用远程Redis需要确保网络连接正常

## 🆘 故障排除

### 远程Redis连接失败
1. 检查网络连接
2. 确认Redis服务器地址和端口正确
3. 验证密码是否正确

### 本地Redis连接失败
1. 启动本地Redis服务: `brew services start redis`
2. 检查Redis服务状态: `redis-cli ping`

### 配置读取失败
1. 检查配置文件是否存在
2. 验证配置文件格式是否正确
3. 查看错误日志: `tail -f output.log`

## 📞 常用命令速查

| 命令 | 功能 |
|------|------|
| `./quick_start.sh` | 启动服务（使用当前配置） |
| `./check_status.sh` | 检查服务状态 |
| `./config_redis.sh` | 管理Redis配置 |
| `./stop_dev_server.sh` | 停止所有服务 |
| `tail -f output.log` | 查看运行日志 |
| `curl http://127.0.0.1:8000/api/v1/health` | 健康检查 | 