# Celery 使用说明

## 从根目录运行 Celery

### 1. 启动 Celery Worker

有两种方式启动 Celery worker：

#### 方式一：使用启动脚本
```bash
./start_celery.sh
```

#### 方式二：直接运行
```bash
python celery_worker.py worker --loglevel=info --concurrency=1 -Q default
```

### 2. 测试 Celery 任务

```bash
python test_celery_detailed.py
```

### 3. 检查 Celery 配置

```bash
python test_celery_config.py
```

## 从 service 目录运行 Celery

### 1. 启动 Celery Worker

```bash
cd service
celery -A workers.celery_app worker --loglevel=info --concurrency=1 -Q default
```

### 2. 测试任务

```bash
cd service
python -c "from workers.tasks import test_celery_task; result = test_celery_task.delay('Hello!'); print(f'任务ID: {result.id}'); import time; time.sleep(3); print(f'结果: {result.get()}')"
```

## 可用的任务

- `test_celery_task`: 测试任务
- `generate_outline_task`: 生成大纲任务
- `run_main_workflow`: 主工作流任务
- `get_job_status`: 获取任务状态
- `generate_document_celery`: 文档生成任务

## 注意事项

1. 确保 Redis 服务正在运行
2. Worker 需要监听 `default` 队列
3. 任务路由配置将任务发送到 `default` 队列
4. 从根目录运行时，Python 路径会自动配置

## 故障排除

### 任务状态为 PENDING
- 检查 worker 是否正在运行
- 确认 worker 监听正确的队列
- 检查 Redis 连接

### 导入错误
- 确保在正确的目录下运行
- 检查 Python 路径配置 