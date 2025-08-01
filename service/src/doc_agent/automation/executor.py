"""
自动化执行器

提供批量任务执行和结果管理功能，包括：
- 批量文档生成
- 任务队列管理
- 结果归档和检索
- 执行报告生成
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


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """批量作业数据类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    topics: list[str] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    results: list[dict] = field(default_factory=list)
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
            "topics":
            self.topics,
            "status":
            self.status.value,
            "created_at":
            self.created_at.isoformat(),
            "started_at":
            self.started_at.isoformat() if self.started_at else None,
            "completed_at":
            self.completed_at.isoformat() if self.completed_at else None,
            "total_tasks":
            self.total_tasks,
            "completed_tasks":
            self.completed_tasks,
            "failed_tasks":
            self.failed_tasks,
            "results":
            self.results,
            "metadata":
            self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BatchJob':
        """从字典创建批量作业"""
        job = cls()
        job.id = data.get("id", str(uuid.uuid4()))
        job.name = data.get("name", "")
        job.description = data.get("description", "")
        job.topics = data.get("topics", [])
        job.status = ExecutionStatus(data.get("status", "pending"))
        job.created_at = datetime.fromisoformat(
            data.get("created_at",
                     datetime.now().isoformat()))
        job.started_at = datetime.fromisoformat(
            data["started_at"]) if data.get("started_at") else None
        job.completed_at = datetime.fromisoformat(
            data["completed_at"]) if data.get("completed_at") else None
        job.total_tasks = data.get("total_tasks", 0)
        job.completed_tasks = data.get("completed_tasks", 0)
        job.failed_tasks = data.get("failed_tasks", 0)
        job.results = data.get("results", [])
        job.metadata = data.get("metadata", {})
        return job


class AutomationExecutor:
    """自动化执行器"""

    def __init__(self,
                 scheduler,
                 storage_path: Optional[str] = None,
                 max_concurrent_tasks: int = 3):
        """
        初始化执行器
        
        Args:
            scheduler: 调度器实例
            storage_path: 结果存储路径
            max_concurrent_tasks: 最大并发任务数
        """
        self.scheduler = scheduler
        self.storage_path = Path(storage_path) if storage_path else Path(
            "output/automation/executor")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.max_concurrent_tasks = max_concurrent_tasks
        self.batch_jobs: dict[str, BatchJob] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

        # 加载已存在的批量作业
        self._load_batch_jobs()

    def _load_batch_jobs(self):
        """从存储加载批量作业"""
        jobs_file = self.storage_path / "batch_jobs.json"
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    jobs_data = json.load(f)
                    for job_data in jobs_data:
                        job = BatchJob.from_dict(job_data)
                        self.batch_jobs[job.id] = job
                self.logger.info(f"加载了 {len(self.batch_jobs)} 个批量作业")
            except Exception as e:
                self.logger.error(f"加载批量作业失败: {e}")

    def _save_batch_jobs(self):
        """保存批量作业到存储"""
        jobs_file = self.storage_path / "batch_jobs.json"
        try:
            jobs_data = [job.to_dict() for job in self.batch_jobs.values()]
            with open(jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存批量作业失败: {e}")

    def create_batch_job(self,
                         name: str,
                         topics: list[str],
                         description: str = "",
                         metadata: Optional[dict] = None) -> str:
        """
        创建批量作业
        Args:
            name: 作业名称
            topics: 主题列表
            description: 作业描述
            metadata: 额外元数据
        Returns:
            str: 作业ID
        """
        job = BatchJob(name=name,
                       topics=topics,
                       description=description,
                       total_tasks=len(topics),
                       metadata=metadata or {})

        self.batch_jobs[job.id] = job
        self._save_batch_jobs()

        self.logger.info(
            f"创建批量作业: {job.name} (ID: {job.id}), 任务数: {job.total_tasks}")
        return job.id

    def get_batch_job(self, job_id: str) -> Optional[BatchJob]:
        """获取批量作业"""
        return self.batch_jobs.get(job_id)

    def get_batch_jobs(self,
                       status: Optional[ExecutionStatus] = None
                       ) -> list[BatchJob]:
        """获取批量作业列表"""
        jobs = list(self.batch_jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # 按创建时间倒序排列
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    def cancel_batch_job(self, job_id: str) -> bool:
        """取消批量作业"""
        job = self.batch_jobs.get(job_id)
        if job and job.status in [
                ExecutionStatus.PENDING, ExecutionStatus.RUNNING
        ]:
            job.status = ExecutionStatus.CANCELLED
            self._save_batch_jobs()
            self.logger.info(f"取消批量作业: {job.name} (ID: {job_id})")
            return True
        return False

    def delete_batch_job(self, job_id: str) -> bool:
        """删除批量作业"""
        if job_id in self.batch_jobs:
            job = self.batch_jobs[job_id]
            del self.batch_jobs[job_id]
            self._save_batch_jobs()
            self.logger.info(f"删除批量作业: {job.name} (ID: {job_id})")
            return True
        return False

    async def execute_batch_job(self, job_id: str):
        """执行批量作业"""
        job = self.batch_jobs.get(job_id)
        if not job:
            raise ValueError(f"批量作业不存在: {job_id}")

        if job.status != ExecutionStatus.PENDING:
            raise ValueError(f"批量作业状态不正确: {job.status}")

        job.status = ExecutionStatus.RUNNING
        job.started_at = datetime.now()
        self._save_batch_jobs()

        self.logger.info(f"开始执行批量作业: {job.name} (ID: {job_id})")

        try:
            # 创建信号量控制并发数
            semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

            # 创建所有任务
            tasks = []
            for i, topic in enumerate(job.topics):
                task_name = f"{job.name}_task_{i+1}"
                task = asyncio.create_task(
                    self._execute_single_task(semaphore, job, topic,
                                              task_name))
                tasks.append(task)

            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)

            # 更新作业状态
            job.status = ExecutionStatus.COMPLETED
            job.completed_at = datetime.now()

            self.logger.info(f"批量作业完成: {job.name} (ID: {job_id})")

        except Exception as e:
            job.status = ExecutionStatus.FAILED
            self.logger.error(f"批量作业失败: {job.name} (ID: {job_id}), 错误: {e}")

        finally:
            self._save_batch_jobs()

    async def _execute_single_task(self, semaphore: asyncio.Semaphore,
                                   job: BatchJob, topic: str, task_name: str):
        """执行单个任务"""
        async with semaphore:
            try:
                self.logger.info(f"开始执行任务: {task_name} (主题: {topic})")

                # 添加任务到调度器
                task_id = self.scheduler.add_task(
                    name=task_name,
                    topic=topic,
                    description=f"批量作业 {job.name} 的子任务",
                    priority=self.scheduler.TaskPriority.NORMAL)

                # 等待任务完成
                while True:
                    task = self.scheduler.get_task(task_id)
                    if not task:
                        break

                    if task.status in [
                            self.scheduler.TaskStatus.COMPLETED,
                            self.scheduler.TaskStatus.FAILED,
                            self.scheduler.TaskStatus.CANCELLED
                    ]:
                        break

                    await asyncio.sleep(2)

                # 获取任务结果
                task = self.scheduler.get_task(task_id)
                if task:
                    result = {
                        "task_id":
                        task_id,
                        "topic":
                        topic,
                        "status":
                        task.status.value,
                        "result":
                        task.result,
                        "error_message":
                        task.error_message,
                        "duration":
                        (task.completed_at - task.started_at).total_seconds()
                        if task.completed_at and task.started_at else None
                    }

                    job.results.append(result)

                    if task.status == self.scheduler.TaskStatus.COMPLETED:
                        job.completed_tasks += 1
                        self.logger.info(f"任务完成: {task_name}")
                    else:
                        job.failed_tasks += 1
                        self.logger.error(
                            f"任务失败: {task_name}, 错误: {task.error_message}")

            except Exception as e:
                job.failed_tasks += 1
                self.logger.error(f"任务执行异常: {task_name}, 错误: {e}")

    def archive_results(self,
                        job_id: str,
                        archive_name: Optional[str] = None) -> str:
        """
        归档作业结果
        Args:
            job_id: 作业ID
            archive_name: 归档名称，默认为作业名称
        Returns:
            str: 归档文件路径
        """
        job = self.batch_jobs.get(job_id)
        if not job:
            raise ValueError(f"批量作业不存在: {job_id}")

        if not archive_name:
            archive_name = f"{job.name}_{job.id[:8]}"

        # 创建归档目录
        archive_dir = self.storage_path / "archives" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 保存作业信息
        job_file = archive_dir / "job_info.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job.to_dict(), f, ensure_ascii=False, indent=2)

        # 保存结果文件
        for i, result in enumerate(job.results):
            if result.get("result") and isinstance(result["result"], dict):
                result_file = archive_dir / f"result_{i+1}_{result['topic']}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

        # 生成执行报告
        report_file = archive_dir / "execution_report.md"
        self._generate_execution_report(job, report_file)

        self.logger.info(f"结果已归档: {archive_dir}")
        return str(archive_dir)

    def _generate_execution_report(self, job: BatchJob, report_file: Path):
        """生成执行报告"""
        report_content = f"""# 批量作业执行报告

## 作业信息
- **作业名称**: {job.name}
- **作业ID**: {job.id}
- **描述**: {job.description}
- **创建时间**: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **开始时间**: {job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else 'N/A'}
- **完成时间**: {job.completed_at.strftime('%Y-%m-%d %H:%M:%S') if job.completed_at else 'N/A'}

## 执行统计
- **总任务数**: {job.total_tasks}
- **完成任务数**: {job.completed_tasks}
- **失败任务数**: {job.failed_tasks}
- **成功率**: {(job.completed_tasks / job.total_tasks * 100):.1f}% (如果总任务数 > 0)

## 任务详情

"""

        for i, result in enumerate(job.results, 1):
            report_content += f"""### 任务 {i}: {result.get('topic', 'N/A')}

- **任务ID**: {result.get('task_id', 'N/A')}
- **状态**: {result.get('status', 'N/A')}
- **执行时长**: {result.get('duration', 'N/A')} 秒
- **错误信息**: {result.get('error_message', 'N/A')}

"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

    def get_statistics(self) -> dict:
        """获取执行器统计信息"""
        total_jobs = len(self.batch_jobs)
        status_counts = {}
        for status in ExecutionStatus:
            status_counts[status.value] = len(
                self.get_batch_jobs(status=status))

        total_tasks = sum(job.total_tasks for job in self.batch_jobs.values())
        completed_tasks = sum(job.completed_tasks
                              for job in self.batch_jobs.values())
        failed_tasks = sum(job.failed_tasks
                           for job in self.batch_jobs.values())

        return {
            "total_jobs":
            total_jobs,
            "status_counts":
            status_counts,
            "total_tasks":
            total_tasks,
            "completed_tasks":
            completed_tasks,
            "failed_tasks":
            failed_tasks,
            "success_rate":
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
