"""
自动化任务调度器

提供优雅的任务调度功能，支持：
- 定时任务调度
- 批量任务管理
- 任务优先级控制
- 失败重试机制
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AutomationTask:
    """自动化任务数据类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    topic: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: str = ""
    result: Optional[dict] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id":
            self.id,
            "name":
            self.name,
            "description":
            self.description,
            "topic":
            self.topic,
            "priority":
            self.priority.value,
            "status":
            self.status.value,
            "created_at":
            self.created_at.isoformat(),
            "started_at":
            self.started_at.isoformat() if self.started_at else None,
            "completed_at":
            self.completed_at.isoformat() if self.completed_at else None,
            "retry_count":
            self.retry_count,
            "max_retries":
            self.max_retries,
            "error_message":
            self.error_message,
            "result":
            self.result,
            "metadata":
            self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AutomationTask':
        """从字典创建任务"""
        task = cls()
        task.id = data.get("id", str(uuid.uuid4()))
        task.name = data.get("name", "")
        task.description = data.get("description", "")
        task.topic = data.get("topic", "")
        task.priority = TaskPriority(data.get("priority", 2))
        task.status = TaskStatus(data.get("status", "pending"))
        task.created_at = datetime.fromisoformat(
            data.get("created_at",
                     datetime.now().isoformat()))
        task.started_at = datetime.fromisoformat(
            data["started_at"]) if data.get("started_at") else None
        task.completed_at = datetime.fromisoformat(
            data["completed_at"]) if data.get("completed_at") else None
        task.retry_count = data.get("retry_count", 0)
        task.max_retries = data.get("max_retries", 3)
        task.error_message = data.get("error_message", "")
        task.result = data.get("result")
        task.metadata = data.get("metadata", {})
        return task


class AutomationScheduler:
    """自动化任务调度器"""

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化调度器
        Args:
            storage_path: 任务存储路径，默认为 output/automation
        """
        self.storage_path = Path(storage_path) if storage_path else Path(
            "output/automation")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.tasks: dict[str, AutomationTask] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

        # 加载已存在的任务
        self._load_tasks()

    def _load_tasks(self):
        """从存储加载任务"""
        tasks_file = self.storage_path / "tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file, encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        task = AutomationTask.from_dict(task_data)
                        self.tasks[task.id] = task
                self.logger.info(f"加载了 {len(self.tasks)} 个任务")
            except Exception as e:
                self.logger.error(f"加载任务失败: {e}")

    def _save_tasks(self):
        """保存任务到存储"""
        tasks_file = self.storage_path / "tasks.json"
        try:
            tasks_data = [task.to_dict() for task in self.tasks.values()]
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")

    def add_task(self,
                 name: str,
                 topic: str,
                 description: str = "",
                 priority: TaskPriority = TaskPriority.NORMAL,
                 max_retries: int = 3,
                 metadata: Optional[dict] = None) -> str:
        """
        添加新任务
        Args:
            name: 任务名称
            topic: 文档主题
            description: 任务描述
            priority: 任务优先级
            max_retries: 最大重试次数
            metadata: 额外元数据
        Returns:
            str: 任务ID
        """
        task = AutomationTask(name=name,
                              topic=topic,
                              description=description,
                              priority=priority,
                              max_retries=max_retries,
                              metadata=metadata or {})

        self.tasks[task.id] = task
        self._save_tasks()

        self.logger.info(f"添加任务: {task.name} (ID: {task.id})")
        return task.id

    def get_task(self, task_id: str) -> Optional[AutomationTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_tasks(
            self,
            status: Optional[TaskStatus] = None,
            priority: Optional[TaskPriority] = None) -> list[AutomationTask]:
        """获取任务列表"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        # 按优先级和创建时间排序
        tasks.sort(key=lambda t: (t.priority.value, t.created_at),
                   reverse=True)
        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
            task.status = TaskStatus.CANCELLED
            self._save_tasks()
            self.logger.info(f"取消任务: {task.name} (ID: {task_id})")
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            del self.tasks[task_id]
            self._save_tasks()
            self.logger.info(f"删除任务: {task.name} (ID: {task_id})")
            return True
        return False

    async def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        self.logger.info("自动化调度器已启动")

        try:
            while self.running:
                # 获取待执行的任务
                pending_tasks = self.get_tasks(status=TaskStatus.PENDING)

                if pending_tasks:
                    # 执行最高优先级的任务
                    task = pending_tasks[0]
                    await self._execute_task(task)

                # 等待一段时间再检查
                await asyncio.sleep(5)

        except Exception as e:
            self.logger.error(f"调度器运行错误: {e}")
        finally:
            self.running = False

    def stop(self):
        """停止调度器"""
        self.running = False
        self.logger.info("自动化调度器已停止")

    async def _execute_task(self, task: AutomationTask):
        """执行单个任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_tasks()

        self.logger.info(f"开始执行任务: {task.name} (ID: {task.id})")

        try:
            # 这里调用实际的文档生成逻辑
            from doc_agent.core.container import container
            result = await self._run_document_generation(task.topic)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            self.logger.info(f"任务完成: {task.name} (ID: {task.id})")

        except Exception as e:
            task.error_message = str(e)
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                task.status = TaskStatus.RETRYING
                self.logger.warning(
                    f"任务重试: {task.name} (ID: {task.id}), 重试次数: {task.retry_count}"
                )
            else:
                task.status = TaskStatus.FAILED
                self.logger.error(
                    f"任务失败: {task.name} (ID: {task.id}), 错误: {e}")

        finally:
            self._save_tasks()

    async def _run_document_generation(self, topic: str) -> dict:
        """运行文档生成"""
        # 这里调用您的文档生成图
        from doc_agent.core.container import container

        graph_input = {"topic": topic}
        result = None

        async for step in container.main_graph.astream(graph_input):
            step_name = list(step.keys())[0]
            step_output = list(step.values())[0]

            # 记录步骤执行
            self.logger.info(f"执行步骤: {step_name}")

            # 保存最终结果
            if step_name == "finalize_document":
                result = step_output

        return result or {"status": "completed", "topic": topic}

    def get_statistics(self) -> dict:
        """获取调度器统计信息"""
        total = len(self.tasks)
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len(self.get_tasks(status=status))

        return {
            "total_tasks": total,
            "status_counts": status_counts,
            "running": self.running
        }
