#!/usr/bin/env python3
"""
自动化系统演示脚本

展示如何使用自动化管理器进行优雅标准的自动操作
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
import sys

current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# 修复导入路径
try:
    from src.doc_agent.automation import AutomationManager, TaskPriority, AlertLevel
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path

    # 添加项目根目录到Python路径
    current_file = Path(__file__)
    service_dir = current_file.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    from src.doc_agent.automation import AutomationManager, TaskPriority, AlertLevel


def alert_callback(alert):
    """告警回调函数示例"""
    print(f"🚨 收到告警 [{alert.level.value}]: {alert.message}")


async def demo_single_task():
    """演示单个任务执行"""
    print("\n" + "=" * 50)
    print("📋 演示1: 单个任务执行")
    print("=" * 50)

    # 创建自动化管理器
    manager = AutomationManager(storage_path="output/automation_demo",
                                max_concurrent_tasks=2,
                                alert_callbacks=[alert_callback])

    try:
        # 启动系统
        await manager.start()

        # 添加单个任务
        task_id = manager.add_task(name="水电站技术文档生成",
                                   topic="水电站技术文档",
                                   description="生成关于水电站技术的详细文档",
                                   priority=TaskPriority.HIGH,
                                   metadata={
                                       "category": "technical",
                                       "urgency": "high"
                                   })

        print(f"✅ 任务已添加: {task_id}")

        # 监控任务状态
        for i in range(10):
            task = manager.get_task(task_id)
            if task:
                print(f"📊 任务状态: {task.status.value}")
                if task.status.value in ["completed", "failed"]:
                    break
            await asyncio.sleep(2)

        # 获取系统统计
        stats = manager.get_system_statistics()
        print(f"📈 系统统计: {stats}")

    finally:
        manager.stop()


async def demo_batch_jobs():
    """演示批量作业执行"""
    print("\n" + "=" * 50)
    print("📋 演示2: 批量作业执行")
    print("=" * 50)

    # 创建自动化管理器
    manager = AutomationManager(storage_path="output/automation_demo",
                                max_concurrent_tasks=2,
                                alert_callbacks=[alert_callback])

    try:
        # 启动系统
        await manager.start()

        # 创建批量作业
        topics = ["水电站建设技术", "水电站运行维护", "水电站安全管理", "水电站环境影响"]

        job_id = manager.create_batch_job(name="水电站系列文档生成",
                                          topics=topics,
                                          description="批量生成水电站相关技术文档",
                                          metadata={
                                              "category": "batch",
                                              "priority": "normal"
                                          })

        print(f"✅ 批量作业已创建: {job_id}")

        # 执行批量作业
        await manager.execute_batch_job(job_id)

        # 获取作业结果
        job = manager.get_batch_job(job_id)
        if job:
            print(f"📊 作业完成状态: {job.status.value}")
            print(
                f"📈 完成情况: {job.completed_tasks}/{job.total_tasks} 成功, {job.failed_tasks} 失败"
            )

        # 归档结果
        archive_path = manager.archive_results(job_id)
        print(f"📁 结果已归档: {archive_path}")

    finally:
        manager.stop()


async def demo_monitoring():
    """演示监控功能"""
    print("\n" + "=" * 50)
    print("📋 演示3: 监控功能")
    print("=" * 50)

    # 创建自动化管理器
    manager = AutomationManager(storage_path="output/automation_demo",
                                max_concurrent_tasks=1,
                                alert_callbacks=[alert_callback])

    try:
        # 启动系统
        await manager.start()

        # 添加一些测试告警
        manager.add_alert(level=AlertLevel.INFO,
                          message="系统启动成功",
                          source="system",
                          details={"component": "automation_manager"})

        manager.add_alert(level=AlertLevel.WARNING,
                          message="CPU使用率较高",
                          source="monitor",
                          details={
                              "cpu_percent": 85.5,
                              "threshold": 80.0
                          })

        # 获取告警列表
        alerts = manager.get_alerts()
        print(f"📊 当前告警数量: {len(alerts)}")

        for alert in alerts[:3]:  # 显示前3个告警
            print(f"  - [{alert.level.value}] {alert.message}")

        # 获取性能指标历史
        metrics = manager.get_metrics_history(hours=1)
        print(f"📈 性能指标记录数: {len(metrics)}")

        if metrics:
            latest = metrics[-1]
            print(f"  - CPU: {latest.cpu_percent:.1f}%")
            print(f"  - 内存: {latest.memory_percent:.1f}%")
            print(f"  - 磁盘: {latest.disk_usage_percent:.1f}%")

        # 获取系统统计
        stats = manager.get_system_statistics()
        print(f"📊 系统统计: {stats}")

    finally:
        manager.stop()


async def demo_configuration():
    """演示配置管理"""
    print("\n" + "=" * 50)
    print("📋 演示4: 配置管理")
    print("=" * 50)

    # 创建自动化管理器
    manager = AutomationManager(storage_path="output/automation_demo",
                                max_concurrent_tasks=2,
                                alert_callbacks=[alert_callback])

    try:
        # 获取当前配置
        config = manager.get_config()
        print("📋 当前配置:")
        print(f"  - CPU阈值: {config['monitor']['cpu_threshold']}%")
        print(f"  - 内存阈值: {config['monitor']['memory_threshold']}%")
        print(f"  - 最大并发任务: {config['executor']['max_concurrent_tasks']}")

        # 更新配置
        new_config = {
            "monitor": {
                "cpu_threshold": 90.0,
                "memory_threshold": 90.0,
                "disk_threshold": 95.0,
                "task_failure_threshold": 0.2
            },
            "executor": {
                "max_concurrent_tasks": 5
            }
        }

        manager.update_config(new_config)
        print("✅ 配置已更新")

        # 验证配置更新
        updated_config = manager.get_config()
        print("📋 更新后配置:")
        print(f"  - CPU阈值: {updated_config['monitor']['cpu_threshold']}%")
        print(f"  - 内存阈值: {updated_config['monitor']['memory_threshold']}%")
        print(
            f"  - 最大并发任务: {updated_config['executor']['max_concurrent_tasks']}"
        )

    finally:
        manager.stop()


async def demo_data_management():
    """演示数据管理"""
    print("\n" + "=" * 50)
    print("📋 演示5: 数据管理")
    print("=" * 50)

    # 创建自动化管理器
    manager = AutomationManager(storage_path="output/automation_demo",
                                max_concurrent_tasks=2,
                                alert_callbacks=[alert_callback])

    try:
        # 启动系统
        await manager.start()

        # 添加一些测试数据
        manager.add_task("测试任务1", "测试主题1")
        manager.add_task("测试任务2", "测试主题2")
        manager.add_alert(AlertLevel.INFO, "测试告警", "demo")

        # 导出数据
        export_path = "output/automation_demo/export"
        manager.export_data(export_path)
        print(f"✅ 数据已导出到: {export_path}")

        # 清理旧数据
        manager.cleanup_old_data(days=1)
        print("✅ 旧数据已清理")

        # 获取系统统计
        stats = manager.get_system_statistics()
        print(f"📊 清理后统计: {stats}")

    finally:
        manager.stop()


async def main():
    """主演示函数"""
    print("🚀 AI文档生成系统自动化操作演示")
    print("=" * 60)

    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    # 运行各个演示
    await demo_single_task()
    await demo_batch_jobs()
    await demo_monitoring()
    await demo_configuration()
    await demo_data_management()

    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("📁 结果保存在: output/automation_demo/")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
