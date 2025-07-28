#!/usr/bin/env python3
"""
简化自动化系统演示脚本

展示自动化系统的核心功能，避免复杂的依赖问题
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List

# 设置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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
    topic: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error_message: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id":
            self.id,
            "name":
            self.name,
            "topic":
            self.topic,
            "description":
            self.description,
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
            "result":
            self.result,
            "error_message":
            self.error_message,
            "metadata":
            self.metadata
        }


class SimpleAutomationManager:
    """简化自动化管理器"""

    def __init__(self, storage_path: str = "output/automation_demo"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.tasks: dict[str, AutomationTask] = {}
        self.running = False
        self.logger = logger

        # 加载已存在的任务
        self._load_tasks()

    def _load_tasks(self):
        """从存储加载任务"""
        tasks_file = self.storage_path / "tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        task = AutomationTask()
                        task.id = task_data.get("id", str(uuid.uuid4()))
                        task.name = task_data.get("name", "")
                        task.topic = task_data.get("topic", "")
                        task.description = task_data.get("description", "")
                        task.priority = TaskPriority(
                            task_data.get("priority", 2))
                        task.status = TaskStatus(
                            task_data.get("status", "pending"))
                        task.created_at = datetime.fromisoformat(
                            task_data.get("created_at",
                                          datetime.now().isoformat()))
                        task.started_at = datetime.fromisoformat(
                            task_data["started_at"]) if task_data.get(
                                "started_at") else None
                        task.completed_at = datetime.fromisoformat(
                            task_data["completed_at"]) if task_data.get(
                                "completed_at") else None
                        task.result = task_data.get("result")
                        task.error_message = task_data.get("error_message", "")
                        task.metadata = task_data.get("metadata", {})
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
                 metadata: Optional[dict] = None) -> str:
        """添加任务"""
        task = AutomationTask(name=name,
                              topic=topic,
                              description=description,
                              priority=priority,
                              metadata=metadata or {})

        self.tasks[task.id] = task
        self._save_tasks()

        self.logger.info(f"添加任务: {task.name} (ID: {task.id})")
        return task.id

    def get_task(self, task_id: str) -> Optional[AutomationTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_tasks(self,
                  status: Optional[TaskStatus] = None) -> list[AutomationTask]:
        """获取任务列表"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按优先级和创建时间排序
        tasks.sort(key=lambda t: (t.priority.value, t.created_at),
                   reverse=True)
        return tasks

    async def execute_task(self, task_id: str):
        """执行任务"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.status != TaskStatus.PENDING:
            raise ValueError(f"任务状态不正确: {task.status}")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_tasks()

        self.logger.info(f"开始执行任务: {task.name} (ID: {task.id})")

        try:
            # 模拟任务执行
            await asyncio.sleep(2)

            # 模拟成功结果
            task.result = {
                "status": "completed",
                "topic": task.topic,
                "generated_content": f"这是关于 {task.topic} 的生成文档内容...",
                "word_count": 1500,
                "generated_at": datetime.now().isoformat()
            }

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            self.logger.info(f"任务完成: {task.name} (ID: {task.id})")

        except Exception as e:
            task.error_message = str(e)
            task.status = TaskStatus.FAILED
            self.logger.error(f"任务失败: {task.name} (ID: {task.id}), 错误: {e}")

        finally:
            self._save_tasks()

    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = len(self.tasks)
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len(self.get_tasks(status=status))

        return {
            "total_tasks": total,
            "status_counts": status_counts,
            "running": self.running
        }


async def demo_basic_automation():
    """演示基础自动化功能"""
    print("\n" + "=" * 50)
    print("📋 简化自动化系统演示")
    print("=" * 50)

    # 创建自动化管理器
    manager = SimpleAutomationManager("output/automation_demo")

    try:
        # 添加多个任务
        tasks = [
            ("水电站技术文档", "水电站技术文档", "生成水电站技术相关文档"),
            ("水电站安全手册", "水电站安全管理", "生成水电站安全管理手册"),
            ("水电站运维指南", "水电站运行维护", "生成水电站运维指南"),
        ]

        task_ids = []
        for name, topic, description in tasks:
            task_id = manager.add_task(name=name,
                                       topic=topic,
                                       description=description,
                                       priority=TaskPriority.HIGH)
            task_ids.append(task_id)
            print(f"✅ 任务已添加: {name} (ID: {task_id})")

        # 执行任务
        print("\n🚀 开始执行任务...")
        for task_id in task_ids:
            await manager.execute_task(task_id)

        # 显示结果
        print("\n📊 任务执行结果:")
        for task_id in task_ids:
            task = manager.get_task(task_id)
            if task:
                print(f"  - {task.name}: {task.status.value}")
                if task.result:
                    print(f"    生成内容长度: {task.result.get('word_count', 0)} 字")

        # 获取统计信息
        stats = manager.get_statistics()
        print(f"\n📈 系统统计: {stats}")

        # 显示所有任务
        all_tasks = manager.get_tasks()
        print(f"\n📋 所有任务 ({len(all_tasks)} 个):")
        for task in all_tasks:
            print(f"  - {task.name} ({task.status.value}) - {task.topic}")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")

    print("\n" + "=" * 50)
    print("✅ 演示完成！")
    print("📁 结果保存在: output/automation_demo/")
    print("=" * 50)


async def main():
    """主函数"""
    print("🚀 AI文档生成系统简化自动化演示")
    print("=" * 60)

    await demo_basic_automation()


if __name__ == "__main__":
    asyncio.run(main())
