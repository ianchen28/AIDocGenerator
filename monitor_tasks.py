#!/usr/bin/env python3
"""
任务监控脚本
用于实时监控文档生成任务的执行状态
"""

import asyncio
import json
import redis.asyncio as redis
import time
from datetime import datetime
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sink=lambda msg: print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"),
    format="{message}",
    level="INFO")


class TaskMonitor:

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None

    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url,
                                               encoding="utf-8",
                                               decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise

    async def monitor_task_stream(self, task_id: str, duration: int = 300):
        """
        监控指定任务的Redis流
        
        Args:
            task_id: 任务ID
            duration: 监控持续时间（秒）
        """
        logger.info(f"🔍 开始监控任务: {task_id}")
        logger.info(f"⏱️ 监控持续时间: {duration}秒")

        start_time = time.time()
        last_event_id = "0"

        while time.time() - start_time < duration:
            try:
                # 获取新事件
                events = await self.redis_client.xread(
                    {task_id: last_event_id},
                    count=10,
                    block=1000  # 等待1秒
                )

                if events:
                    for stream_name, stream_events in events:
                        for event_id, event_data in stream_events:
                            if event_id != last_event_id:
                                await self._process_event(event_id, event_data)
                                last_event_id = event_id

                # 检查任务是否完成
                if await self._is_task_completed(task_id):
                    logger.info(f"✅ 任务 {task_id} 已完成")
                    break

            except Exception as e:
                logger.error(f"❌ 监控过程中出错: {e}")
                await asyncio.sleep(1)

        logger.info(f"🏁 监控结束: {task_id}")

    async def _process_event(self, event_id: str, event_data: dict):
        """处理单个事件"""
        try:
            data_str = event_data.get("data", "{}")
            data = json.loads(data_str)

            event_type = data.get("eventType", "unknown")
            timestamp = data.get("timestamp", "")

            # 根据事件类型输出不同的信息
            if event_type == "task_started":
                logger.info(f"🚀 任务开始 - {data.get('outline_title', '未知标题')}")

            elif event_type == "task_progress":
                progress = data.get("progress", "")
                step = data.get("step", "")
                logger.info(f"📊 进度更新 - {step}: {progress}")

            elif event_type == "chapter_started":
                chapter_title = data.get("chapterTitle", "")
                chapter_index = data.get("chapterIndex", 0)
                total_chapters = data.get("totalChapters", 0)
                logger.info(
                    f"📝 章节开始 - {chapter_index + 1}/{total_chapters}: {chapter_title}"
                )

            elif event_type == "chapter_progress":
                chapter_title = data.get("chapterTitle", "")
                step = data.get("step", "")
                progress = data.get("progress", "")
                logger.info(f"⚙️ 章节进度 - {chapter_title} - {step}: {progress}")

            elif event_type == "chapter_completed":
                chapter_title = data.get("chapterTitle", "")
                logger.info(f"✅ 章节完成 - {chapter_title}")

            elif event_type == "writer_started":
                progress = data.get("progress", "")
                logger.info(f"✍️ 写作开始 - {progress}")

            elif event_type == "document_content_stream":
                content = data.get("content", "")
                progress = data.get("progress", "")
                logger.info(f"📤 内容流 - {progress}: {content[:50]}...")

            elif event_type == "citations_completed":
                total_origins = data.get("totalAnswerOrigins", 0)
                total_webs = data.get("totalWebSources", 0)
                logger.info(
                    f"📚 参考文献完成 - {total_origins}个文档源, {total_webs}个网页源")

            elif event_type == "document_generated":
                document = data.get("document", {})
                title = document.get("title", "")
                word_count = document.get("word_count", 0)
                char_count = document.get("char_count", 0)
                logger.info(
                    f"📄 文档生成 - {title} ({word_count}字, {char_count}字符)")

            elif event_type == "task_completed":
                logger.info(f"🎉 任务完成!")

            elif event_type == "task_failed":
                error = data.get("error", "")
                logger.error(f"❌ 任务失败: {error}")

            elif event_type == "chapter_failed":
                chapter_title = data.get("chapterTitle", "")
                error = data.get("error", "")
                logger.error(f"❌ 章节失败 - {chapter_title}: {error}")

            else:
                logger.debug(f"🔍 未知事件类型: {event_type}")

        except Exception as e:
            logger.error(f"❌ 处理事件失败: {e}")

    async def _is_task_completed(self, task_id: str) -> bool:
        """检查任务是否已完成"""
        try:
            # 检查是否有完成或失败事件
            events = await self.redis_client.xrevrange(task_id, count=5)
            for event_id, event_data in events:
                data_str = event_data.get("data", "{}")
                data = json.loads(data_str)
                event_type = data.get("eventType", "")
                if event_type in ["task_completed", "task_failed"]:
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ 检查任务状态失败: {e}")
            return False

    async def list_recent_tasks(self, limit: int = 10):
        """列出最近的任务"""
        logger.info(f"📋 列出最近 {limit} 个任务:")

        try:
            # 获取所有流
            keys = await self.redis_client.keys("*")
            task_streams = [
                key for key in keys if key.isdigit() and len(key) > 10
            ]

            task_info = []
            for task_id in task_streams[-limit:]:
                try:
                    # 获取第一个和最后一个事件
                    first_event = await self.redis_client.xrange(task_id,
                                                                 count=1)
                    last_event = await self.redis_client.xrevrange(task_id,
                                                                   count=1)

                    if first_event and last_event:
                        first_data = json.loads(first_event[0][1].get(
                            "data", "{}"))
                        last_data = json.loads(last_event[0][1].get(
                            "data", "{}"))

                        task_info.append({
                            "task_id":
                            task_id,
                            "title":
                            first_data.get("outline_title", "未知"),
                            "start_time":
                            first_data.get("timestamp", ""),
                            "last_event":
                            last_data.get("eventType", ""),
                            "status":
                            "running" if last_data.get("eventType") not in [
                                "task_completed", "task_failed"
                            ] else "completed"
                        })
                except Exception as e:
                    logger.error(f"❌ 获取任务 {task_id} 信息失败: {e}")

            # 按时间排序
            task_info.sort(key=lambda x: x["start_time"], reverse=True)

            for task in task_info:
                status_emoji = "🟢" if task["status"] == "completed" else "🟡"
                logger.info(
                    f"{status_emoji} {task['task_id']} - {task['title']} ({task['status']})"
                )

        except Exception as e:
            logger.error(f"❌ 列出任务失败: {e}")


async def main():
    """主函数"""
    # Redis配置
    redis_url = "redis://:xJrhp*4mnHxbBWN2grqq@10.215.149.74:26379/0"

    monitor = TaskMonitor(redis_url)
    await monitor.connect()

    # 列出最近的任务
    await monitor.list_recent_tasks()

    # 如果有命令行参数，监控指定任务
    import sys
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        await monitor.monitor_task_stream(task_id)
    else:
        logger.info("💡 使用方法: python monitor_tasks.py <task_id>")
        logger.info("💡 例如: python monitor_tasks.py 1754566940616110086")


if __name__ == "__main__":
    asyncio.run(main())
