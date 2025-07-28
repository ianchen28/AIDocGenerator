"""
自动化监控器

提供智能监控和告警功能，包括：
- 任务执行监控
- 性能指标收集
- 异常检测和告警
- 资源使用监控
"""

import asyncio
import json
import logging

# 添加项目路径
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

import psutil

current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir and str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警数据类"""
    id: str
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id":
            self.id,
            "level":
            self.level.value,
            "message":
            self.message,
            "source":
            self.source,
            "timestamp":
            self.timestamp.isoformat(),
            "details":
            self.details,
            "resolved":
            self.resolved,
            "resolved_at":
            self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    disk_usage_percent: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration: float = 0.0

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "disk_usage_percent": self.disk_usage_percent,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_task_duration": self.avg_task_duration
        }


class AutomationMonitor:
    """自动化监控器"""

    def __init__(self,
                 scheduler,
                 storage_path: Optional[str] = None,
                 alert_callbacks: Optional[list[Callable]] = None):
        """
        初始化监控器
        Args:
            scheduler: 调度器实例
            storage_path: 监控数据存储路径
            alert_callbacks: 告警回调函数列表
        """
        self.scheduler = scheduler
        self.storage_path = Path(storage_path) if storage_path else Path(
            "output/automation/monitor")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.alert_callbacks = alert_callbacks or []
        self.alerts: list[Alert] = []
        self.metrics_history: list[PerformanceMetrics] = []
        self.running = False
        self.logger = logging.getLogger(__name__)

        # 监控配置
        self.monitoring_interval = 30  # 30秒监控间隔
        self.max_metrics_history = 1000  # 最多保存1000条指标记录
        self.max_alerts_history = 500  # 最多保存500条告警记录

        # 阈值配置
        self.cpu_threshold = 80.0  # CPU使用率阈值
        self.memory_threshold = 85.0  # 内存使用率阈值
        self.disk_threshold = 90.0  # 磁盘使用率阈值
        self.task_failure_threshold = 0.3  # 任务失败率阈值

        # 加载历史数据
        self._load_monitor_data()

    def _load_monitor_data(self):
        """加载监控数据"""
        # 加载告警历史
        alerts_file = self.storage_path / "alerts.json"
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r', encoding='utf-8') as f:
                    alerts_data = json.load(f)
                    for alert_data in alerts_data:
                        alert = Alert(id=alert_data["id"],
                                      level=AlertLevel(alert_data["level"]),
                                      message=alert_data["message"],
                                      source=alert_data["source"],
                                      timestamp=datetime.fromisoformat(
                                          alert_data["timestamp"]),
                                      details=alert_data["details"],
                                      resolved=alert_data["resolved"],
                                      resolved_at=datetime.fromisoformat(
                                          alert_data["resolved_at"]) if
                                      alert_data.get("resolved_at") else None)
                        self.alerts.append(alert)
                self.logger.info(f"加载了 {len(self.alerts)} 条告警记录")
            except Exception as e:
                self.logger.error(f"加载告警数据失败: {e}")

        # 加载性能指标历史
        metrics_file = self.storage_path / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                    for metric_data in metrics_data:
                        metric = PerformanceMetrics(
                            timestamp=datetime.fromisoformat(
                                metric_data["timestamp"]),
                            cpu_percent=metric_data["cpu_percent"],
                            memory_percent=metric_data["memory_percent"],
                            memory_used_mb=metric_data["memory_used_mb"],
                            disk_usage_percent=metric_data[
                                "disk_usage_percent"],
                            active_tasks=metric_data["active_tasks"],
                            completed_tasks=metric_data["completed_tasks"],
                            failed_tasks=metric_data["failed_tasks"],
                            avg_task_duration=metric_data["avg_task_duration"])
                        self.metrics_history.append(metric)
                self.logger.info(f"加载了 {len(self.metrics_history)} 条性能指标记录")
            except Exception as e:
                self.logger.error(f"加载性能指标失败: {e}")

    def _save_monitor_data(self):
        """保存监控数据"""
        # 保存告警数据
        alerts_file = self.storage_path / "alerts.json"
        try:
            alerts_data = [
                alert.to_dict()
                for alert in self.alerts[-self.max_alerts_history:]
            ]
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存告警数据失败: {e}")

        # 保存性能指标数据
        metrics_file = self.storage_path / "metrics.json"
        try:
            metrics_data = [
                metric.to_dict()
                for metric in self.metrics_history[-self.max_metrics_history:]
            ]
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存性能指标失败: {e}")

    def add_alert(self,
                  level: AlertLevel,
                  message: str,
                  source: str,
                  details: Optional[dict] = None):
        """添加告警"""
        import uuid

        alert = Alert(id=str(uuid.uuid4()),
                      level=level,
                      message=message,
                      source=source,
                      details=details or {})

        self.alerts.append(alert)

        # 限制告警历史数量
        if len(self.alerts) > self.max_alerts_history:
            self.alerts = self.alerts[-self.max_alerts_history:]

        self._save_monitor_data()

        # 调用告警回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"告警回调函数执行失败: {e}")

        self.logger.warning(f"新增告警 [{level.value}]: {message} (来源: {source})")

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self._save_monitor_data()
                self.logger.info(f"告警已解决: {alert.message}")
                return True
        return False

    def get_alerts(self,
                   level: Optional[AlertLevel] = None,
                   resolved: Optional[bool] = None) -> list[Alert]:
        """获取告警列表"""
        alerts = list(self.alerts)

        if level:
            alerts = [a for a in alerts if a.level == level]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        # 按时间倒序排列
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts

    def collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # 系统资源指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # 任务统计
        stats = self.scheduler.get_statistics()
        active_tasks = stats["status_counts"].get("running", 0)
        completed_tasks = stats["status_counts"].get("completed", 0)
        failed_tasks = stats["status_counts"].get("failed", 0)

        # 计算平均任务时长
        avg_task_duration = 0.0
        completed_tasks_list = self.scheduler.get_tasks(
            status=self.scheduler.tasks.get("COMPLETED"))
        if completed_tasks_list:
            total_duration = sum([
                (task.completed_at - task.started_at).total_seconds()
                for task in completed_tasks_list
                if task.completed_at and task.started_at
            ])
            avg_task_duration = total_duration / len(completed_tasks_list)

        metrics = PerformanceMetrics(cpu_percent=cpu_percent,
                                     memory_percent=memory.percent,
                                     memory_used_mb=memory.used / 1024 / 1024,
                                     disk_usage_percent=disk.percent,
                                     active_tasks=active_tasks,
                                     completed_tasks=completed_tasks,
                                     failed_tasks=failed_tasks,
                                     avg_task_duration=avg_task_duration)

        self.metrics_history.append(metrics)

        # 限制历史记录数量
        if len(self.metrics_history) > self.max_metrics_history:
            self.metrics_history = self.metrics_history[-self.
                                                        max_metrics_history:]

        return metrics

    def check_thresholds(self, metrics: PerformanceMetrics):
        """检查阈值并生成告警"""
        # CPU使用率检查
        if metrics.cpu_percent > self.cpu_threshold:
            self.add_alert(level=AlertLevel.WARNING if metrics.cpu_percent < 95
                           else AlertLevel.CRITICAL,
                           message=f"CPU使用率过高: {metrics.cpu_percent:.1f}%",
                           source="system_monitor",
                           details={
                               "cpu_percent": metrics.cpu_percent,
                               "threshold": self.cpu_threshold
                           })

        # 内存使用率检查
        if metrics.memory_percent > self.memory_threshold:
            self.add_alert(level=AlertLevel.WARNING if metrics.memory_percent
                           < 95 else AlertLevel.CRITICAL,
                           message=f"内存使用率过高: {metrics.memory_percent:.1f}%",
                           source="system_monitor",
                           details={
                               "memory_percent": metrics.memory_percent,
                               "threshold": self.memory_threshold
                           })

        # 磁盘使用率检查
        if metrics.disk_usage_percent > self.disk_threshold:
            self.add_alert(
                level=AlertLevel.WARNING
                if metrics.disk_usage_percent < 95 else AlertLevel.CRITICAL,
                message=f"磁盘使用率过高: {metrics.disk_usage_percent:.1f}%",
                source="system_monitor",
                details={
                    "disk_usage_percent": metrics.disk_usage_percent,
                    "threshold": self.disk_threshold
                })

        # 任务失败率检查
        total_tasks = metrics.completed_tasks + metrics.failed_tasks
        if total_tasks > 0:
            failure_rate = metrics.failed_tasks / total_tasks
            if failure_rate > self.task_failure_threshold:
                self.add_alert(level=AlertLevel.ERROR,
                               message=f"任务失败率过高: {failure_rate:.1%}",
                               source="task_monitor",
                               details={
                                   "failure_rate": failure_rate,
                                   "threshold": self.task_failure_threshold
                               })

    async def start(self):
        """启动监控器"""
        if self.running:
            return

        self.running = True
        self.logger.info("自动化监控器已启动")

        try:
            while self.running:
                # 收集性能指标
                metrics = self.collect_metrics()

                # 检查阈值
                self.check_thresholds(metrics)

                # 保存监控数据
                self._save_monitor_data()

                # 等待下次监控
                await asyncio.sleep(self.monitoring_interval)

        except Exception as e:
            self.logger.error(f"监控器运行错误: {e}")
        finally:
            self.running = False

    def stop(self):
        """停止监控器"""
        self.running = False
        self.logger.info("自动化监控器已停止")

    def get_statistics(self) -> dict:
        """获取监控统计信息"""
        # 告警统计
        alert_stats = {}
        for level in AlertLevel:
            alert_stats[level.value] = len(
                self.get_alerts(level=level, resolved=False))

        # 性能指标统计
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            metrics_stats = latest_metrics.to_dict()
        else:
            metrics_stats = {}

        return {
            "alerts": alert_stats,
            "metrics": metrics_stats,
            "running": self.running
        }

    def get_metrics_history(self, hours: int = 24) -> list[PerformanceMetrics]:
        """获取历史性能指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]
