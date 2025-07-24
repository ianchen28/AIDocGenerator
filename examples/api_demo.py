#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 演示脚本
展示完整的文档生成API使用流程，包括大纲交互
"""

import asyncio
import aiohttp
import json
from loguru import logger


class APIDemo:
    """API演示客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def create_context(self, files: list) -> str:
        """创建文件上下文"""
        logger.info("📁 创建文件上下文...")

        data = {"files": files}
        async with self.session.post(f"{self.base_url}/api/v1/contexts",
                                     json=data) as response:
            if response.status == 202:
                result = await response.json()
                context_id = result["context_id"]
                logger.info(f"✅ 上下文创建成功：{context_id}")
                return context_id
            else:
                error = await response.text()
                logger.error(f"❌ 上下文创建失败：{error}")
                raise Exception(f"创建上下文失败：{error}")

    async def create_job(self,
                         task_prompt: str,
                         context_id: str = None) -> str:
        """创建文档生成作业"""
        logger.info("🚀 创建文档生成作业...")

        data = {"task_prompt": task_prompt}
        if context_id:
            data["context_id"] = context_id

        async with self.session.post(f"{self.base_url}/api/v1/jobs",
                                     json=data) as response:
            if response.status == 201:
                result = await response.json()
                job_id = result["job_id"]
                logger.info(f"✅ 作业创建成功：{job_id}")
                logger.info(f"📝 任务提示：{task_prompt}")
                return job_id
            else:
                error = await response.text()
                logger.error(f"❌ 作业创建失败：{error}")
                raise Exception(f"创建作业失败：{error}")

    async def generate_outline(self, job_id: str) -> str:
        """触发大纲生成"""
        logger.info("📋 开始生成大纲...")

        async with self.session.post(
                f"{self.base_url}/api/v1/jobs/{job_id}/outline") as response:
            if response.status == 202:
                result = await response.json()
                logger.info(f"✅ 大纲生成已启动，状态：{result['outline_status']}")
                return result['outline_status']
            else:
                error = await response.text()
                logger.error(f"❌ 大纲生成启动失败：{error}")
                raise Exception(f"大纲生成启动失败：{error}")

    async def wait_for_outline(self,
                               job_id: str,
                               max_attempts: int = 20) -> dict:
        """等待大纲生成完成"""
        logger.info("⏳ 等待大纲生成完成...")

        for attempt in range(max_attempts):
            async with self.session.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}/outline"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    status = result["outline_status"]

                    if status == "READY":
                        logger.info("✅ 大纲生成完成！")
                        return result
                    elif status == "FAILED":
                        logger.error("❌ 大纲生成失败")
                        raise Exception("大纲生成失败")
                    else:
                        logger.info(
                            f"⏳ 大纲状态：{status}，等待中... ({attempt + 1}/{max_attempts})"
                        )
                        await asyncio.sleep(2)
                else:
                    error = await response.text()
                    logger.error(f"❌ 获取大纲状态失败：{error}")
                    raise Exception(f"获取大纲状态失败：{error}")

        raise Exception("大纲生成超时")

    async def update_outline(self, job_id: str, outline: dict) -> str:
        """更新大纲并触发最终文档生成"""
        logger.info("📝 更新大纲并开始最终文档生成...")

        data = {"outline": outline}
        async with self.session.put(
                f"{self.base_url}/api/v1/jobs/{job_id}/outline",
                json=data) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ {result['message']}")
                return result["message"]
            else:
                error = await response.text()
                logger.error(f"❌ 大纲更新失败：{error}")
                raise Exception(f"大纲更新失败：{error}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"🟢 服务健康状态：{result['status']}")
                    return True
                else:
                    logger.warning(f"🟡 服务响应异常：{response.status}")
                    return False
        except Exception as e:
            logger.error(f"🔴 服务连接失败：{e}")
            return False


async def run_demo():
    """运行完整的API演示"""
    logger.info("🎬 开始API演示")

    async with APIDemo() as demo:
        try:
            # 1. 健康检查
            if not await demo.health_check():
                logger.error("❌ 服务不可用，请先启动API服务")
                return

            # 2. 创建上下文（可选）
            files = [{
                "file_id": "demo-file-001",
                "file_name": "机器学习基础资料.pdf",
                "storage_url": "s3://demo-bucket/ml_basics.pdf"
            }]
            context_id = await demo.create_context(files)

            # 3. 创建作业
            task_prompt = "编写一份关于机器学习基础知识的教程，包括核心概念、常用算法和实践应用"
            job_id = await demo.create_job(task_prompt, context_id)

            # 4. 生成大纲
            await demo.generate_outline(job_id)

            # 5. 等待大纲完成
            outline_result = await demo.wait_for_outline(job_id)
            original_outline = outline_result["outline"]

            logger.info("📋 生成的大纲结构：")
            logger.info(f"标题：{original_outline['title']}")
            for i, node in enumerate(original_outline["nodes"], 1):
                logger.info(f"  {i}. {node['title']}")
                if node.get("content_summary"):
                    logger.info(f"     摘要：{node['content_summary']}")

            # 6. 模拟用户修改大纲
            logger.info("✏️ 模拟用户修改大纲...")
            modified_outline = {
                "title":
                "机器学习基础教程（修订版）",
                "nodes": [{
                    "id": "intro_revised",
                    "title": "机器学习导论（已优化）",
                    "content_summary": "全面介绍机器学习的定义、历史发展和应用领域",
                    "children": []
                }, {
                    "id": "algorithms_revised",
                    "title": "核心算法深度解析（已扩展）",
                    "content_summary": "详细讲解监督学习、无监督学习和强化学习的经典算法",
                    "children": []
                }, {
                    "id": "practice_revised",
                    "title": "实战项目与案例分析（新增）",
                    "content_summary": "通过真实项目案例展示机器学习的实际应用",
                    "children": []
                }, {
                    "id": "future_revised",
                    "title": "发展趋势与职业规划（新增）",
                    "content_summary": "探讨机器学习的未来发展方向和相关职业机会",
                    "children": []
                }]
            }

            # 7. 更新大纲并触发最终生成
            await demo.update_outline(job_id, modified_outline)

            logger.info("🎉 演示完成！")
            logger.info(f"📊 作业ID：{job_id}")
            logger.info("💡 在实际应用中，您可以：")
            logger.info("   - 通过SSE事件流监控文档生成进度")
            logger.info("   - 获取最终生成的文档内容")
            logger.info("   - 进行进一步的编辑和优化")

        except Exception as e:
            logger.error(f"❌ 演示过程中发生错误：{e}")


if __name__ == "__main__":
    # 配置日志
    logger.add("logs/api_demo.log", rotation="1 day", level="INFO")

    # 运行演示
    asyncio.run(run_demo())
