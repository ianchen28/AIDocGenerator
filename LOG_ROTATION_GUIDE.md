# AIDocGenerator 日志轮转功能指南

## 问题描述

原始的 `quick_start.sh` 脚本中的日志配置存在以下问题：
- Celery 的 `--logfile` 参数不会自动进行日志轮转
- Uvicorn 的重定向 `>>` 也不会自动进行日志轮转
- 导致 `logs/app.log` 文件持续增长，可能占用大量磁盘空间

## 解决方案

我们提供了多种日志轮转解决方案：

### 方案1：改进版启动脚本 (推荐)

使用 `quick_start_improved.sh` 脚本，它会：
- 自动检测系统中可用的日志轮转工具
- 支持 `rotatelogs` 和 `logrotate` 两种工具
- 在启动时自动启用日志轮转功能

```bash
# 使用改进版启动脚本
./quick_start_improved.sh
```

### 方案2：手动日志轮转脚本

使用 `log_rotate.sh` 脚本手动轮转日志：

```bash
# 手动轮转日志
./log_rotate.sh
```

### 方案3：定时任务自动轮转

设置 crontab 定时任务，自动轮转日志：

```bash
# 设置定时任务
./setup_log_rotation.sh
```

## 安装日志轮转工具

### macOS
```bash
# 安装 rotatelogs (推荐)
brew install httpd

# 或安装 logrotate
brew install logrotate
```

### Ubuntu/Debian
```bash
# 安装 rotatelogs
sudo apt-get install apache2-utils

# 或安装 logrotate
sudo apt-get install logrotate
```

## 配置说明

### 日志轮转参数
- **最大文件大小**: 10M
- **保留备份数**: 5个
- **备份文件命名**: `app.log.1`, `app.log.2`, ..., `app.log.5`

### 定时任务频率选项
1. **每小时检查一次** (推荐)
2. **每天检查一次**
3. **每周检查一次**
4. **自定义频率**

## 使用方法

### 1. 使用改进版启动脚本

```bash
# 激活 conda 环境
conda activate ai-doc

# 使用改进版启动脚本
./quick_start_improved.sh
```

脚本会自动检测可用的日志轮转工具并启用相应功能。

### 2. 手动轮转日志

```bash
# 检查当前日志文件大小
ls -lh logs/app.log

# 手动轮转日志
./log_rotate.sh
```

### 3. 设置自动轮转

```bash
# 运行设置脚本
./setup_log_rotation.sh

# 按提示选择轮转频率
# 推荐选择 "每小时检查一次"
```

### 4. 管理定时任务

```bash
# 查看当前定时任务
crontab -l

# 编辑定时任务
crontab -e

# 移除所有定时任务
crontab -r
```

## 监控和管理

### 查看日志文件
```bash
# 查看当前日志
tail -f logs/app.log

# 查看备份日志
tail -f logs/app.log.1

# 查看所有日志文件
ls -lh logs/app.log*
```

### 查看定时任务日志
```bash
# 查看 cron 执行日志
tail -f logs/cron.log
```

### 检查服务状态
```bash
# 查看服务进程
ps aux | grep -E '(celery|uvicorn)'

# 查看日志文件大小
du -h logs/app.log*
```

## 故障排除

### 1. 日志轮转工具未找到
如果看到警告信息 "未找到日志轮转工具"：
- 安装相应的工具包
- 或使用手动轮转脚本

### 2. 定时任务未执行
检查 crontab 是否正确设置：
```bash
crontab -l
```

### 3. 权限问题
确保脚本有执行权限：
```bash
chmod +x quick_start_improved.sh
chmod +x log_rotate.sh
chmod +x setup_log_rotation.sh
```

### 4. 日志文件过大
如果日志文件已经很大，可以手动清理：
```bash
# 备份当前日志
cp logs/app.log logs/app.log.backup

# 清空日志文件
> logs/app.log

# 或使用轮转脚本
./log_rotate.sh
```

## 最佳实践

1. **定期监控**: 定期检查日志文件大小
2. **合理设置**: 根据系统资源调整最大文件大小和保留数量
3. **备份重要日志**: 在清理前备份重要的日志信息
4. **监控磁盘空间**: 确保有足够的磁盘空间存储日志文件

## 文件说明

- `quick_start_improved.sh`: 改进版启动脚本，支持自动日志轮转
- `log_rotate.sh`: 手动日志轮转脚本
- `setup_log_rotation.sh`: 定时任务设置脚本
- `logrotate.conf`: logrotate 配置文件
- `LOG_ROTATION_GUIDE.md`: 本说明文档

## 总结

通过使用这些工具，可以有效管理 `logs/app.log` 文件的大小，避免日志文件无限增长占用磁盘空间。推荐使用改进版启动脚本，它会自动检测并使用最佳的日志轮转方案。
