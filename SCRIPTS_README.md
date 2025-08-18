# AIDocGenerator 脚本管理指南

## 📁 脚本目录结构

```
AIDocGenerator/
├── manage.sh                    # 主管理脚本（推荐使用）
├── scripts/                     # 脚本目录
│   ├── quick_start_multi.sh     # 启动多 Worker 服务
│   ├── stop_multi.sh           # 停止服务
│   ├── monitor_all_workers.sh   # 多 Worker 日志监控
│   ├── watch_logs.sh           # 日志查看器
│   ├── log_rotate.sh           # 手动日志轮转
│   ├── cleanup_logs.sh         # 日志清理
│   ├── demo_log_rotation.sh    # 轮转演示
│   ├── demo_archive.sh         # 归档演示
│   └── config_redis.sh         # Redis 配置
└── logs/                       # 日志目录
    ├── app.log                 # 统一日志
    ├── load_balancer.log       # 负载均衡器日志
    ├── worker_1.log           # Worker 1 日志
    ├── worker_2.log           # Worker 2 日志
    ├── ...
    ├── worker_8.log           # Worker 8 日志
    └── archive/               # 归档目录
        ├── 2025-08/          # 按月份归档
        └── ...
```

## 🎛️ 主管理脚本 (推荐)

使用 `./manage.sh` 作为主要管理工具：

### 🚀 服务管理

```bash
# 启动 8 个 Worker，负载均衡器端口 8081
./manage.sh start 8 8081

# 启动 4 个 Worker，负载均衡器端口 8082
./manage.sh start 4 8082

# 停止服务
./manage.sh stop
```

### 📊 日志监控

```bash
# 实时监控所有日志
./manage.sh monitor realtime 8

# 监控错误日志
./manage.sh monitor errors 8

# 监控警告日志
./manage.sh monitor warnings 8

# 显示统计信息
./manage.sh monitor summary 8

# 监控特定 Worker
./manage.sh monitor worker 8
```

### 📄 日志管理

```bash
# 手动轮转日志
./manage.sh logs rotate

# 清理过老日志（保留30天）
./manage.sh logs cleanup

# 查看日志状态
./manage.sh logs status
```

### 🎬 演示功能

```bash
# 演示日志轮转
./manage.sh demo rotation

# 演示日志归档
./manage.sh demo archive
```

## 📊 多 Worker 日志监控

### 🔍 监控模式

1. **实时监控 (realtime/rt)**
   - 同时监控所有 Worker 日志
   - 实时显示日志输出
   - 按 Ctrl+C 停止

2. **错误监控 (errors/error)**
   - 搜索所有日志文件中的错误
   - 显示最近的错误信息

3. **警告监控 (warnings/warn)**
   - 搜索所有日志文件中的警告
   - 显示最近的警告信息

4. **统计监控 (summary/stats)**
   - 显示每个日志文件的统计信息
   - 包括文件大小、行数、错误数、警告数

5. **特定 Worker 监控 (worker/w)**
   - 监控特定 Worker 的日志
   - 交互式选择 Worker 编号

### 💡 使用示例

```bash
# 从根目录使用主管理脚本
./manage.sh monitor realtime 8

# 直接使用监控脚本
cd scripts
./monitor_all_workers.sh 8 realtime
./monitor_all_workers.sh 8 errors
./monitor_all_workers.sh 8 summary
```

## 📦 日志归档系统

### 🏗️ 归档策略

1. **轮转触发**：文件大小超过 10MB 时自动轮转
2. **保留策略**：
   - 主目录：保留最近 5 个备份文件（.log.1 到 .log.5）
   - 归档目录：过老的备份文件移动到 archive/YYYY-MM/
3. **清理策略**：
   - 主目录备份：超过 7 天自动删除
   - 归档文件：超过 30 天自动删除

### 📁 归档目录结构

```
logs/archive/
├── 2025-08/                    # 2025年8月归档
│   ├── app.log.6              # 过老的备份
│   ├── app.log.7              # 过老的备份
│   ├── worker_1.log.6         # 过老的备份
│   └── ...
└── 2025-07/                    # 2025年7月归档
    └── ...
```

## 🛠️ 直接脚本使用

如果需要直接使用脚本，请确保在正确的目录下运行：

### 从根目录运行

```bash
# 启动服务（在根目录）
./scripts/quick_start_multi.sh 8 8081

# 停止服务（在根目录）
./scripts/stop_multi.sh
```

### 从 scripts 目录运行

```bash
cd scripts

# 监控日志
./monitor_all_workers.sh 8 realtime

# 手动轮转
./log_rotate.sh 8

# 清理日志
./cleanup_logs.sh 30

# 查看日志
./watch_logs.sh 8
```

## 🔧 日志轮转原理

### 📋 轮转过程

1. **检测阶段**：每30秒检查一次文件大小
2. **触发条件**：当文件超过10MB时触发轮转
3. **轮转步骤**：
   - 移动现有备份：.log.1 → .log.2，.log.2 → .log.3，...
   - 备份当前文件：.log → .log.1
   - 创建新文件：新的空 .log 文件
   - 归档过老文件：.log.6+ → archive/YYYY-MM/

### 💡 关键要点

- **写入位置**：始终写入 .log 文件，不写入备份文件
- **服务连续性**：轮转过程中服务不中断
- **备份机制**：备份文件是只读的，用于历史查看
- **自动清理**：超过保留期限的文件会被自动删除

## 📈 性能优化

### ✅ 优势

1. **避免并发冲突**：每个 Worker 有独立的日志文件
2. **便于调试**：可以单独查看每个 Worker 的日志
3. **自动管理**：文件大小控制和轮转
4. **易于维护**：清晰的日志文件结构
5. **性能优化**：减少文件锁定和写入冲突

### 🎯 最佳实践

1. **定期清理**：建议每周运行一次 `./manage.sh logs cleanup`
2. **监控磁盘**：定期检查 `logs/archive/` 目录大小
3. **备份重要日志**：重要的历史日志可以单独备份
4. **设置定时任务**：可以添加到 crontab 自动清理

## 🆘 故障排除

### 常见问题

1. **脚本权限问题**
   ```bash
   chmod +x scripts/*.sh
   chmod +x manage.sh
   ```

2. **路径问题**
   - 确保在正确的目录下运行脚本
   - 检查日志目录是否存在

3. **服务未启动**
   ```bash
   # 检查服务状态
   ps aux | grep uvicorn
   ps aux | grep load_balancer
   ```

4. **日志文件不存在**
   ```bash
   # 检查日志文件
   ls -lh logs/
   ```

### 获取帮助

```bash
# 查看主管理脚本帮助
./manage.sh help

# 查看监控帮助
./manage.sh monitor

# 查看日志管理帮助
./manage.sh logs help

# 查看演示帮助
./manage.sh demo help
```
