"""
自动化管理器

统一管理自动化系统的所有组件，提供：
- 统一的API接口
- 系统状态管理
- 配置管理
- 日志管理
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .executor import AutomationExecutor, ExecutionStatus
from .monitor import AlertLevel, AutomationMonitor
from .scheduler import AutomationScheduler, TaskPriority, TaskStatus


class AutomationManager:
    """自动化管理器"""

    def __init__(self,
                 storage_path: Optional[str] = None,
                 max_concurrent_tasks: int = 3,
                 alert_callbacks: Optional[list[Callable]] = None):
        """
        初始化自动化管理器
        Args:
            storage_path: 存储路径
            max_concurrent_tasks: 最大并发任务数
            alert_callbacks: 告警回调函数列表
        """
        self.storage_path = Path(storage_path) if storage_path else Path(
            "output/automation")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.scheduler = AutomationScheduler(
            str(self.storage_path / "scheduler"))
        self.monitor = AutomationMonitor(self.scheduler,
                                         str(self.storage_path / "monitor"),
                                         alert_callbacks)
        self.executor = AutomationExecutor(self.scheduler,
                                           str(self.storage_path / "executor"),
                                           max_concurrent_tasks)

        self.running = False
        self.logger = logging.getLogger(__name__)

        # 设置日志
        self._setup_logging()

        self.logger.info("自动化管理器初始化完成")

    def _setup_logging(self):
        """设置日志配置"""
        log_file = self.storage_path / "automation.log"

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    async def start(self):
        """启动自动化系统"""
        if self.running:
            return

        self.running = True
        self.logger.info("启动自动化系统...")

        try:
            # 启动调度器和监控器
            await asyncio.gather(self.scheduler.start(), self.monitor.start())
        except Exception as e:
            self.logger.error(f"启动自动化系统失败: {e}")
            self.running = False
            raise

    def stop(self):
        """停止自动化系统"""
        self.running = False
        self.scheduler.stop()
        self.monitor.stop()
        self.logger.info("自动化系统已停止")

    # ==================== 任务管理 ====================

    def add_task(self,
                 name: str,
                 topic: str,
                 description: str = "",
                 priority: TaskPriority = TaskPriority.NORMAL,
                 max_retries: int = 3,
                 metadata: Optional[dict] = None) -> str:
        """添加任务"""
        return self.scheduler.add_task(name=name,
                                       topic=topic,
                                       description=description,
                                       priority=priority,
                                       max_retries=max_retries,
                                       metadata=metadata)

    def get_task(self, task_id: str):
        """获取任务"""
        return self.scheduler.get_task(task_id)

    def get_tasks(self,
                  status: Optional[TaskStatus] = None,
                  priority: Optional[TaskPriority] = None):
        """获取任务列表"""
        return self.scheduler.get_tasks(status=status, priority=priority)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self.scheduler.cancel_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        return self.scheduler.delete_task(task_id)

    # ==================== 批量作业管理 ====================

    def create_batch_job(self,
                         name: str,
                         topics: list[str],
                         description: str = "",
                         metadata: Optional[dict] = None) -> str:
        """创建批量作业"""
        return self.executor.create_batch_job(name=name,
                                              topics=topics,
                                              description=description,
                                              metadata=metadata)

    def get_batch_job(self, job_id: str):
        """获取批量作业"""
        return self.executor.get_batch_job(job_id)

    def get_batch_jobs(self, status: Optional[ExecutionStatus] = None):
        """获取批量作业列表"""
        return self.executor.get_batch_jobs(status=status)

    async def execute_batch_job(self, job_id: str):
        """执行批量作业"""
        return await self.executor.execute_batch_job(job_id)

    def cancel_batch_job(self, job_id: str) -> bool:
        """取消批量作业"""
        return self.executor.cancel_batch_job(job_id)

    def delete_batch_job(self, job_id: str) -> bool:
        """删除批量作业"""
        return self.executor.delete_batch_job(job_id)

    def archive_results(self,
                        job_id: str,
                        archive_name: Optional[str] = None) -> str:
        """归档作业结果"""
        return self.executor.archive_results(job_id, archive_name)

    # ==================== 监控管理 ====================

    def add_alert(self,
                  level: AlertLevel,
                  message: str,
                  source: str,
                  details: Optional[dict] = None):
        """添加告警"""
        return self.monitor.add_alert(level, message, source, details)

    def get_alerts(self,
                   level: Optional[AlertLevel] = None,
                   resolved: Optional[bool] = None):
        """获取告警列表"""
        return self.monitor.get_alerts(level=level, resolved=resolved)

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        return self.monitor.resolve_alert(alert_id)

    def get_metrics_history(self, hours: int = 24):
        """获取历史性能指标"""
        return self.monitor.get_metrics_history(hours)

    # ==================== 统计信息 ====================

    def get_system_statistics(self) -> dict:
        """获取系统统计信息"""
        scheduler_stats = self.scheduler.get_statistics()
        monitor_stats = self.monitor.get_statistics()
        executor_stats = self.executor.get_statistics()

        return {
            "scheduler": scheduler_stats,
            "monitor": monitor_stats,
            "executor": executor_stats,
            "system": {
                "running": self.running,
                "storage_path": str(self.storage_path),
                "uptime": self._get_uptime()
            }
        }

    def _get_uptime(self) -> Optional[float]:
        """获取系统运行时间（秒）"""
        # 这里可以实现更复杂的运行时间计算
        # 暂时返回None
        return None

    # ==================== 配置管理 ====================

    def update_config(self, config: dict):
        """更新配置"""
        # 更新监控器配置
        if "monitor" in config:
            monitor_config = config["monitor"]
            if "cpu_threshold" in monitor_config:
                self.monitor.cpu_threshold = monitor_config["cpu_threshold"]
            if "memory_threshold" in monitor_config:
                self.monitor.memory_threshold = monitor_config[
                    "memory_threshold"]
            if "disk_threshold" in monitor_config:
                self.monitor.disk_threshold = monitor_config["disk_threshold"]
            if "task_failure_threshold" in monitor_config:
                self.monitor.task_failure_threshold = monitor_config[
                    "task_failure_threshold"]

        # 更新执行器配置
        if "executor" in config:
            executor_config = config["executor"]
            if "max_concurrent_tasks" in executor_config:
                self.executor.max_concurrent_tasks = executor_config[
                    "max_concurrent_tasks"]

        self.logger.info("配置已更新")

    def get_config(self) -> dict:
        """获取当前配置"""
        return {
            "monitor": {
                "cpu_threshold": self.monitor.cpu_threshold,
                "memory_threshold": self.monitor.memory_threshold,
                "disk_threshold": self.monitor.disk_threshold,
                "task_failure_threshold": self.monitor.task_failure_threshold,
                "monitoring_interval": self.monitor.monitoring_interval
            },
            "executor": {
                "max_concurrent_tasks": self.executor.max_concurrent_tasks
            },
            "storage_path": str(self.storage_path)
        }

    # ==================== 系统维护 ====================

    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        # 清理旧的任务
        old_tasks = [
            task for task in self.scheduler.tasks.values()
            if task.created_at < cutoff_date and task.status in
            [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]

        for task in old_tasks:
            self.scheduler.delete_task(task.id)

        # 清理旧的告警
        old_alerts = [
            alert for alert in self.monitor.alerts
            if alert.timestamp < cutoff_date and alert.resolved
        ]

        for alert in old_alerts:
            self.monitor.alerts.remove(alert)

        # 清理旧的性能指标
        old_metrics = [
            metric for metric in self.monitor.metrics_history
            if metric.timestamp < cutoff_date
        ]

        for metric in old_metrics:
            self.monitor.metrics_history.remove(metric)

        self.logger.info(
            f"清理了 {len(old_tasks)} 个旧任务, {len(old_alerts)} 个旧告警, {len(old_metrics)} 条旧指标"
        )

    def export_data(self, export_path: str):
        """导出数据"""
        export_dir = Path(export_path)
        export_dir.mkdir(parents=True, exist_ok=True)

        # 导出任务数据
        tasks_data = [task.to_dict() for task in self.scheduler.tasks.values()]
        with open(export_dir / "tasks.json", 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # 导出告警数据
        alerts_data = [alert.to_dict() for alert in self.monitor.alerts]
        with open(export_dir / "alerts.json", 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, ensure_ascii=False, indent=2)

        # 导出性能指标数据
        metrics_data = [
            metric.to_dict() for metric in self.monitor.metrics_history
        ]
        with open(export_dir / "metrics.json", 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, ensure_ascii=False, indent=2)

        # 导出批量作业数据
        jobs_data = [
            job.to_dict() for job in self.executor.batch_jobs.values()
        ]
        with open(export_dir / "batch_jobs.json", 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"数据已导出到: {export_path}")

    def import_data(self, import_path: str):
        """导入数据"""
        import_dir = Path(import_path)

        # 导入任务数据
        tasks_file = import_dir / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file, encoding='utf-8') as f:
                tasks_data = json.load(f)
                for task_data in tasks_data:
                    task = self.scheduler.AutomationTask.from_dict(task_data)
                    self.scheduler.tasks[task.id] = task

        # 导入告警数据
        alerts_file = import_dir / "alerts.json"
        if alerts_file.exists():
            with open(alerts_file, encoding='utf-8') as f:
                alerts_data = json.load(f)
                for alert_data in alerts_data:
                    alert = self.monitor.Alert(
                        id=alert_data["id"],
                        level=AlertLevel(alert_data["level"]),
                        message=alert_data["message"],
                        source=alert_data["source"],
                        timestamp=datetime.fromisoformat(
                            alert_data["timestamp"]),
                        details=alert_data["details"],
                        resolved=alert_data["resolved"],
                        resolved_at=datetime.fromisoformat(
                            alert_data["resolved_at"])
                        if alert_data.get("resolved_at") else None)
                    self.monitor.alerts.append(alert)

        # 导入性能指标数据
        metrics_file = import_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file, encoding='utf-8') as f:
                metrics_data = json.load(f)
                for metric_data in metrics_data:
                    metric = self.monitor.PerformanceMetrics(
                        timestamp=datetime.fromisoformat(
                            metric_data["timestamp"]),
                        cpu_percent=metric_data["cpu_percent"],
                        memory_percent=metric_data["memory_percent"],
                        memory_used_mb=metric_data["memory_used_mb"],
                        disk_usage_percent=metric_data["disk_usage_percent"],
                        active_tasks=metric_data["active_tasks"],
                        completed_tasks=metric_data["completed_tasks"],
                        failed_tasks=metric_data["failed_tasks"],
                        avg_task_duration=metric_data["avg_task_duration"])
                    self.monitor.metrics_history.append(metric)

        # 导入批量作业数据
        jobs_file = import_dir / "batch_jobs.json"
        if jobs_file.exists():
            with open(jobs_file, encoding='utf-8') as f:
                jobs_data = json.load(f)
                for job_data in jobs_data:
                    job = self.executor.BatchJob.from_dict(job_data)
                    self.executor.batch_jobs[job.id] = job

        self.logger.info(f"数据已从 {import_path} 导入")
