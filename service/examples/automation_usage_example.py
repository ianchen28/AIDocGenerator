#!/usr/bin/env python3
"""
自动化系统使用示例

展示在实际应用场景中如何使用自动化系统进行优雅标准的自动操作
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

# 设置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutomationUsageExample:
    """自动化系统使用示例"""

    def __init__(self):
        self.logger = logger

    async def example_1_basic_task_management(self):
        """示例1: 基础任务管理"""
        print("\n" + "=" * 60)
        print("📋 示例1: 基础任务管理")
        print("=" * 60)

        from simple_automation_demo import SimpleAutomationManager, TaskPriority

        # 创建自动化管理器
        manager = SimpleAutomationManager("output/automation_example")

        # 添加不同类型的任务
        tasks = [{
            "name": "技术规范文档",
            "topic": "水电站技术规范",
            "description": "生成水电站技术规范文档",
            "priority": TaskPriority.HIGH,
            "metadata": {
                "category": "technical",
                "urgency": "high"
            }
        }, {
            "name": "操作手册",
            "topic": "水电站操作手册",
            "description": "生成水电站操作手册",
            "priority": TaskPriority.NORMAL,
            "metadata": {
                "category": "operation",
                "urgency": "normal"
            }
        }, {
            "name": "维护指南",
            "topic": "水电站维护指南",
            "description": "生成水电站维护指南",
            "priority": TaskPriority.NORMAL,
            "metadata": {
                "category": "maintenance",
                "urgency": "normal"
            }
        }]

        task_ids = []
        for task_info in tasks:
            task_id = manager.add_task(**task_info)
            task_ids.append(task_id)
            print(
                f"✅ 任务已添加: {task_info['name']} (优先级: {task_info['priority'].name})"
            )

        # 按优先级执行任务
        print("\n🚀 按优先级执行任务...")
        for task_id in task_ids:
            await manager.execute_task(task_id)

        # 显示执行结果
        print("\n📊 执行结果:")
        for task_id in task_ids:
            task = manager.get_task(task_id)
            if task:
                duration = (task.completed_at - task.started_at).total_seconds(
                ) if task.completed_at and task.started_at else 0
                print(
                    f"  - {task.name}: {task.status.value} (耗时: {duration:.1f}秒)"
                )

        return manager

    async def example_2_batch_processing(self):
        """示例2: 批量处理"""
        print("\n" + "=" * 60)
        print("📋 示例2: 批量处理")
        print("=" * 60)

        from simple_automation_demo import SimpleAutomationManager, TaskPriority

        manager = SimpleAutomationManager("output/automation_example")

        # 批量创建任务
        batch_topics = [
            "水电站设计规范", "水电站施工标准", "水电站验收标准", "水电站运行规程", "水电站检修规程", "水电站应急预案"
        ]

        print(f"📋 批量创建 {len(batch_topics)} 个任务...")

        # 并发执行任务
        import asyncio
        task_ids = []

        # 创建所有任务
        for i, topic in enumerate(batch_topics, 1):
            task_id = manager.add_task(name=f"文档{i}: {topic}",
                                       topic=topic,
                                       description=f"生成关于 {topic} 的文档",
                                       priority=TaskPriority.NORMAL,
                                       metadata={
                                           "batch_id": "batch_1",
                                           "sequence": i
                                       })
            task_ids.append(task_id)

        print(f"✅ 批量任务已创建: {len(task_ids)} 个")

        # 并发执行（模拟）
        print("\n🚀 并发执行任务...")
        tasks = [manager.execute_task(task_id) for task_id in task_ids]
        await asyncio.gather(*tasks)

        # 统计结果
        completed_tasks = manager.get_tasks(
            status=manager.get_tasks.__annotations__['status'].__args__[0].
            COMPLETED)
        failed_tasks = manager.get_tasks(
            status=manager.get_tasks.__annotations__['status'].__args__[0].
            FAILED)

        print(f"\n📈 批量处理结果:")
        print(f"  - 总任务数: {len(task_ids)}")
        print(f"  - 成功完成: {len(completed_tasks)}")
        print(f"  - 执行失败: {len(failed_tasks)}")
        print(f"  - 成功率: {len(completed_tasks)/len(task_ids)*100:.1f}%")

        return manager

    async def example_3_error_handling_and_retry(self):
        """示例3: 错误处理和重试机制"""
        print("\n" + "=" * 60)
        print("📋 示例3: 错误处理和重试机制")
        print("=" * 60)

        from simple_automation_demo import SimpleAutomationManager, TaskPriority, TaskStatus

        manager = SimpleAutomationManager("output/automation_example")

        # 创建可能失败的任务
        problematic_tasks = [{
            "name": "正常任务",
            "topic": "正常文档生成",
            "description": "这个任务应该正常完成",
            "should_fail": False
        }, {
            "name": "模拟失败任务",
            "topic": "失败文档生成",
            "description": "这个任务会模拟失败",
            "should_fail": True
        }]

        task_ids = []
        for task_info in problematic_tasks:
            task_id = manager.add_task(
                name=task_info["name"],
                topic=task_info["topic"],
                description=task_info["description"],
                priority=TaskPriority.HIGH,
                metadata={"should_fail": task_info["should_fail"]})
            task_ids.append(task_id)

        # 执行任务（模拟错误处理）
        print("\n🚀 执行任务（包含错误处理）...")

        for task_id in task_ids:
            task = manager.get_task(task_id)
            if task and task.metadata.get("should_fail"):
                # 模拟失败任务
                task.status = TaskStatus.FAILED
                task.error_message = "模拟的任务失败"
                task.completed_at = datetime.now()
                print(f"❌ 任务失败: {task.name} - {task.error_message}")
            else:
                # 正常执行
                await manager.execute_task(task_id)
                print(f"✅ 任务完成: {task.name if task else 'Unknown'}")

        # 显示错误统计
        failed_tasks = manager.get_tasks(status=TaskStatus.FAILED)
        print(f"\n📊 错误统计:")
        print(f"  - 失败任务数: {len(failed_tasks)}")
        for task in failed_tasks:
            print(f"    - {task.name}: {task.error_message}")

        return manager

    async def example_4_data_persistence_and_recovery(self):
        """示例4: 数据持久化和恢复"""
        print("\n" + "=" * 60)
        print("📋 示例4: 数据持久化和恢复")
        print("=" * 60)

        from simple_automation_demo import SimpleAutomationManager, TaskPriority

        # 创建第一个管理器实例
        manager1 = SimpleAutomationManager("output/automation_example")

        # 添加一些任务
        task_ids = []
        for i in range(3):
            task_id = manager1.add_task(name=f"持久化测试任务{i+1}",
                                        topic=f"测试主题{i+1}",
                                        description=f"测试数据持久化的任务{i+1}",
                                        priority=TaskPriority.NORMAL)
            task_ids.append(task_id)

        print(f"✅ 在管理器1中创建了 {len(task_ids)} 个任务")

        # 执行部分任务
        await manager1.execute_task(task_ids[0])
        print("✅ 执行了第一个任务")

        # 创建第二个管理器实例（应该能恢复数据）
        manager2 = SimpleAutomationManager("output/automation_example")

        # 检查数据恢复
        recovered_tasks = manager2.get_tasks()
        print(f"📊 数据恢复结果:")
        print(f"  - 恢复的任务数: {len(recovered_tasks)}")

        for task in recovered_tasks:
            print(f"    - {task.name}: {task.status.value}")

        # 继续执行剩余任务
        print("\n🚀 继续执行剩余任务...")
        for task_id in task_ids[1:]:
            await manager2.execute_task(task_id)

        return manager2

    async def example_5_monitoring_and_statistics(self):
        """示例5: 监控和统计"""
        print("\n" + "=" * 60)
        print("📋 示例5: 监控和统计")
        print("=" * 60)

        from simple_automation_demo import SimpleAutomationManager, TaskPriority

        manager = SimpleAutomationManager("output/automation_example")

        # 创建不同优先级的任务
        tasks = [
            ("高优先级任务", TaskPriority.HIGH),
            ("普通优先级任务1", TaskPriority.NORMAL),
            ("普通优先级任务2", TaskPriority.NORMAL),
            ("低优先级任务", TaskPriority.LOW),
        ]

        task_ids = []
        for name, priority in tasks:
            task_id = manager.add_task(name=name,
                                       topic=f"{name}主题",
                                       description=f"测试{name}",
                                       priority=priority)
            task_ids.append(task_id)

        # 执行任务
        print("🚀 执行任务...")
        for task_id in task_ids:
            await manager.execute_task(task_id)

        # 获取详细统计
        stats = manager.get_statistics()
        all_tasks = manager.get_tasks()

        print(f"\n📈 详细统计信息:")
        print(f"  - 总任务数: {stats['total_tasks']}")
        print(f"  - 状态分布: {stats['status_counts']}")

        # 按优先级统计
        priority_stats = {}
        for task in all_tasks:
            priority = task.priority.name
            if priority not in priority_stats:
                priority_stats[priority] = 0
            priority_stats[priority] += 1

        print(f"  - 优先级分布: {priority_stats}")

        # 性能统计
        completed_tasks = [
            t for t in all_tasks if t.status.value == "completed"
        ]
        if completed_tasks:
            durations = []
            for task in completed_tasks:
                if task.completed_at and task.started_at:
                    duration = (task.completed_at -
                                task.started_at).total_seconds()
                    durations.append(duration)

            if durations:
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)

                print(f"  - 平均执行时间: {avg_duration:.2f}秒")
                print(f"  - 最短执行时间: {min_duration:.2f}秒")
                print(f"  - 最长执行时间: {max_duration:.2f}秒")

        return manager

    async def run_all_examples(self):
        """运行所有示例"""
        print("🚀 AI文档生成系统自动化操作完整示例")
        print("=" * 80)

        try:
            # 运行所有示例
            await self.example_1_basic_task_management()
            await self.example_2_batch_processing()
            await self.example_3_error_handling_and_retry()
            await self.example_4_data_persistence_and_recovery()
            await self.example_5_monitoring_and_statistics()

            print("\n" + "=" * 80)
            print("✅ 所有示例运行完成！")
            print("📁 结果保存在: output/automation_example/")
            print("📋 查看生成的文件:")
            print("  - tasks.json: 任务数据")
            print("  - 日志文件: 执行日志")
            print("=" * 80)

        except Exception as e:
            print(f"❌ 示例运行过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    example = AutomationUsageExample()
    await example.run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())
