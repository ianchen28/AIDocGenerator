#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis事件流演示脚本
展示如何监听和处理LangGraph执行过程中的实时事件
"""

import asyncio
import aioredis
import json
import aiohttp
from loguru import logger
from datetime import datetime


class RedisEventsListener:
    """Redis事件监听器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.is_listening = False

    async def connect(self):
        """连接到Redis"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url,
                                                  encoding="utf-8",
                                                  decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Redis连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            return False

    async def listen_to_job_events(self, job_id: str, timeout: int = 300):
        """
        监听指定作业的事件流
        
        Args:
            job_id: 作业ID
            timeout: 超时时间（秒）
        """
        channel_name = f"job:{job_id}:events"
        logger.info(f"🎧 开始监听作业事件: {channel_name}")

        try:
            # 创建订阅
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel_name)

            self.is_listening = True
            start_time = asyncio.get_event_loop().time()

            logger.info(f"📡 等待事件... (超时: {timeout}秒)")

            async for message in pubsub.listen():
                # 检查超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"⏰ 监听超时 ({timeout}秒)")
                    break

                # 跳过订阅确认消息
                if message['type'] != 'message':
                    continue

                try:
                    # 解析事件数据
                    event_data = json.loads(message['data'])
                    await self._handle_event(event_data)

                    # 检查是否为完成事件
                    if (event_data.get('event') == 'done' and event_data.get(
                            'data', {}).get('task') == 'main_workflow'):
                        logger.info("🎉 主工作流完成，停止监听")
                        break

                except json.JSONDecodeError as e:
                    logger.error(f"❌ 事件数据解析失败: {e}")
                except Exception as e:
                    logger.error(f"❌ 处理事件时出错: {e}")

            await pubsub.unsubscribe(channel_name)
            logger.info("📴 事件监听结束")

        except Exception as e:
            logger.error(f"❌ 事件监听失败: {e}")
        finally:
            self.is_listening = False

    async def _handle_event(self, event_data: dict):
        """处理单个事件"""
        event_type = event_data.get('event', 'unknown')
        data = event_data.get('data', {})
        timestamp = event_data.get('timestamp', '')

        # 格式化时间戳
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            else:
                time_str = datetime.now().strftime('%H:%M:%S')
        except:
            time_str = "??:??:??"

        # 根据事件类型处理
        if event_type == 'phase_update':
            phase = data.get('phase', 'UNKNOWN')
            message = data.get('message', '')
            logger.info(f"🔄 [{time_str}] 阶段更新: {phase} - {message}")

        elif event_type == 'thought':
            text = data.get('text', '')[:100] + ('...' if len(
                data.get('text', '')) > 100 else '')
            model = data.get('model_name', 'LLM')
            logger.info(f"💭 [{time_str}] {model} 思考: {text}")

        elif event_type == 'tool_call':
            tool_name = data.get('tool_name', 'Unknown')
            status = data.get('status', 'UNKNOWN')
            if status == 'START':
                input_text = data.get('input', '')[:50] + ('...' if len(
                    data.get('input', '')) > 50 else '')
                logger.info(
                    f"🔧 [{time_str}] 工具调用: {tool_name} - 输入: {input_text}")
            else:
                output_len = data.get('output_length', 0)
                logger.info(
                    f"✅ [{time_str}] 工具完成: {tool_name} - 输出长度: {output_len}")

        elif event_type == 'source_found':
            source_type = data.get('source_type', 'unknown')
            title = data.get('title', 'Unknown Source')
            snippet = data.get('snippet', '')[:80] + ('...' if len(
                data.get('snippet', '')) > 80 else '')
            logger.info(
                f"📚 [{time_str}] 发现资源: {title} ({source_type}) - {snippet}")

        elif event_type == 'error':
            code = data.get('code', 'N/A')
            message = data.get('message', 'Unknown error')
            logger.error(f"❌ [{time_str}] 错误 ({code}): {message}")

        elif event_type == 'done':
            task = data.get('task', 'unknown')
            message = data.get('message', 'Task completed')
            logger.success(f"✅ [{time_str}] 完成: {task} - {message}")

        else:
            logger.debug(f"📝 [{time_str}] 其他事件: {event_type} - {data}")

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔌 Redis连接已关闭")


class APIClient:
    """API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def create_job(self, task_prompt: str) -> str:
        """创建作业"""
        data = {"task_prompt": task_prompt}
        async with self.session.post(f"{self.base_url}/api/v1/jobs",
                                     json=data) as response:
            if response.status == 201:
                result = await response.json()
                return result["job_id"]
            else:
                error = await response.text()
                raise Exception(f"创建作业失败: {error}")

    async def generate_outline(self, job_id: str):
        """生成大纲"""
        async with self.session.post(
                f"{self.base_url}/api/v1/jobs/{job_id}/outline") as response:
            if response.status != 202:
                error = await response.text()
                raise Exception(f"大纲生成失败: {error}")

    async def wait_for_outline(self, job_id: str, max_attempts: int = 30):
        """等待大纲完成"""
        for _ in range(max_attempts):
            async with self.session.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}/outline"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result["outline_status"] == "READY":
                        return result["outline"]
                    elif result["outline_status"] == "FAILED":
                        raise Exception("大纲生成失败")
            await asyncio.sleep(2)
        raise Exception("大纲生成超时")

    async def update_outline_and_start_generation(self, job_id: str,
                                                  outline: dict):
        """更新大纲并开始最终生成"""
        data = {"outline": outline}
        async with self.session.put(
                f"{self.base_url}/api/v1/jobs/{job_id}/outline",
                json=data) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"大纲更新失败: {error}")


async def run_complete_demo():
    """运行完整的演示"""
    logger.info("🚀 开始Redis事件流完整演示")

    # 创建事件监听器
    listener = RedisEventsListener()
    if not await listener.connect():
        return

    try:
        async with APIClient() as api:
            # 1. 创建作业
            logger.info("📝 创建新作业...")
            task_prompt = "编写一份关于深度学习在计算机视觉中应用的技术报告"
            job_id = await api.create_job(task_prompt)
            logger.info(f"✅ 作业创建成功: {job_id}")

            # 2. 生成大纲
            logger.info("📋 开始生成大纲...")
            await api.generate_outline(job_id)

            # 3. 等待大纲完成
            logger.info("⏳ 等待大纲生成完成...")
            outline = await api.wait_for_outline(job_id)
            logger.info(f"✅ 大纲生成完成: {outline['title']}")

            # 4. 启动事件监听（异步）
            logger.info("🎧 启动事件监听...")
            listen_task = asyncio.create_task(
                listener.listen_to_job_events(job_id, timeout=600)  # 10分钟超时
            )

            # 5. 稍等一下确保监听器准备好
            await asyncio.sleep(2)

            # 6. 更新大纲并触发最终生成（这将产生大量事件）
            logger.info("🚀 更新大纲并开始最终文档生成...")
            await api.update_outline_and_start_generation(job_id, outline)

            # 7. 等待事件监听完成
            logger.info("⏳ 等待工作流完成...")
            await listen_task

            logger.info("🎉 演示完成！")

    except Exception as e:
        logger.error(f"❌ 演示过程中发生错误: {e}")
    finally:
        await listener.close()


async def run_simple_demo():
    """运行简单的事件监听演示"""
    logger.info("🎧 简单事件监听演示")
    logger.info("💡 请在另一个终端中创建和运行作业，然后输入作业ID")

    job_id = input("请输入要监听的作业ID: ").strip()
    if not job_id:
        logger.error("❌ 作业ID不能为空")
        return

    listener = RedisEventsListener()
    if not await listener.connect():
        return

    try:
        await listener.listen_to_job_events(job_id, timeout=600)
    except KeyboardInterrupt:
        logger.info("🛑 用户中断监听")
    finally:
        await listener.close()


if __name__ == "__main__":
    import sys

    # 配置日志
    logger.add("logs/redis_events_demo.log", rotation="1 day", level="INFO")

    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        # 简单模式：只监听事件
        asyncio.run(run_simple_demo())
    else:
        # 完整演示：创建作业并监听事件
        asyncio.run(run_complete_demo())
