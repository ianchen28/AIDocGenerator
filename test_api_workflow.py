#!/usr/bin/env python3
"""
简单的API工作流程测试脚本
演示完整的文档生成流程
"""

import asyncio
from typing import Optional

import httpx
from loguru import logger


class APIWorkflowTest:

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 服务健康状态: {data['status']}")
                return True
            else:
                logger.error(f"❌ 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 服务连接失败: {e}")
            return False

    async def create_job(self, topic: str, task_prompt: str) -> Optional[str]:
        """创建文档生成作业"""
        try:
            payload = {"topic": topic, "task_prompt": task_prompt}

            response = await self.session.post(f"{self.base_url}/api/v1/jobs",
                                               json=payload)

            if response.status_code == 201:
                data = response.json()
                job_id = data["job_id"]
                logger.success(f"✅ 作业创建成功: {job_id}")
                return job_id
            else:
                logger.error(f"❌ 作业创建失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ 创建作业异常: {e}")
            return None

    async def trigger_outline_generation(self, job_id: str) -> bool:
        """触发大纲生成"""
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v1/jobs/{job_id}/outline")

            if response.status_code == 202:
                logger.success(f"✅ 大纲生成任务已启动: {job_id}")
                return True
            else:
                logger.error(f"❌ 大纲生成启动失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 触发大纲生成异常: {e}")
            return False

    async def wait_for_outline(self,
                               job_id: str,
                               max_attempts: int = 20) -> Optional[dict]:
        """等待大纲生成完成"""
        logger.info("⏳ 等待大纲生成完成...")

        for attempt in range(max_attempts):
            try:
                response = await self.session.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}/outline")

                if response.status_code == 200:
                    data = response.json()
                    status = data["outline_status"]

                    if status == "READY":
                        logger.success("✅ 大纲生成完成！")
                        return data
                    elif status == "FAILED":
                        logger.error("❌ 大纲生成失败")
                        return None
                    else:
                        logger.info(
                            f"⏳ 大纲状态: {status}，等待中... ({attempt + 1}/{max_attempts})"
                        )
                        await asyncio.sleep(3)
                else:
                    logger.error(f"❌ 获取大纲状态失败: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"❌ 获取大纲状态异常: {e}")
                return None

        logger.error("❌ 大纲生成超时")
        return None

    async def update_outline_and_start_generation(self, job_id: str,
                                                  outline: dict) -> bool:
        """更新大纲并开始最终文档生成"""
        try:
            payload = {"outline": outline}

            response = await self.session.put(
                f"{self.base_url}/api/v1/jobs/{job_id}/outline", json=payload)

            if response.status_code == 200:
                data = response.json()
                logger.success(f"✅ {data['message']}")
                return True
            else:
                logger.error(f"❌ 大纲更新失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 更新大纲异常: {e}")
            return False

    async def check_document_status(self, job_id: str) -> Optional[str]:
        """检查文档生成状态"""
        try:
            response = await self.session.get(
                f"{self.base_url}/api/v1/jobs/{job_id}/document")

            if response.status_code == 200:
                logger.success("✅ 文档生成完成！")
                return response.text
            elif response.status_code == 202:
                logger.info("⏳ 文档仍在生成中...")
                return None
            else:
                logger.error(f"❌ 检查文档状态失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ 检查文档状态异常: {e}")
            return None

    async def run_full_workflow(self):
        """运行完整的工作流程"""
        logger.info("🚀 开始API工作流程测试")

        # 1. 健康检查
        if not await self.health_check():
            logger.error("❌ 服务不可用，退出测试")
            return

        # 2. 创建作业
        topic = "人工智能在医疗领域的应用"
        task_prompt = "请生成一份关于人工智能在医疗领域应用的详细文档，包括技术原理、应用场景、发展趋势等内容"

        job_id = await self.create_job(topic, task_prompt)
        if not job_id:
            logger.error("❌ 作业创建失败，退出测试")
            return

        # 3. 触发大纲生成
        if not await self.trigger_outline_generation(job_id):
            logger.error("❌ 大纲生成启动失败，退出测试")
            return

        # 4. 等待大纲生成完成
        outline_data = await self.wait_for_outline(job_id)
        if not outline_data:
            logger.error("❌ 大纲生成失败，退出测试")
            return

        # 5. 显示大纲内容
        outline = outline_data.get("outline")
        if outline:
            logger.info(f"📋 文档标题: {outline.get('title', 'N/A')}")
            nodes = outline.get('nodes', [])
            logger.info(f"📋 章节数量: {len(nodes)}")
            for i, node in enumerate(nodes, 1):
                logger.info(f"   {i}. {node.get('title', 'N/A')}")

        # 6. 更新大纲并开始最终生成
        updated_outline = {
            "title":
            "人工智能在医疗领域的应用（修订版）",
            "nodes": [{
                "id": "intro",
                "title": "医疗AI概述",
                "content_summary": "介绍人工智能在医疗领域的基本概念和发展历程",
                "children": []
            }, {
                "id": "tech",
                "title": "核心技术分析",
                "content_summary": "深入分析医疗AI的关键技术和算法原理",
                "children": []
            }, {
                "id": "applications",
                "title": "实际应用场景",
                "content_summary": "探讨医疗AI在诊断、治疗、药物研发等领域的应用",
                "children": []
            }, {
                "id": "future",
                "title": "发展趋势与挑战",
                "content_summary": "分析医疗AI的未来发展方向和面临的挑战",
                "children": []
            }]
        }

        if not await self.update_outline_and_start_generation(
                job_id, updated_outline):
            logger.error("❌ 大纲更新失败，退出测试")
            return

        # 7. 等待文档生成完成
        logger.info("⏳ 等待文档生成完成...")
        for attempt in range(30):  # 最多等待5分钟
            document_content = await self.check_document_status(job_id)
            if document_content:
                logger.success("🎉 完整工作流程测试成功！")
                logger.info(f"📄 生成的文档长度: {len(document_content)} 字符")
                break
            await asyncio.sleep(10)
        else:
            logger.warning("⚠️ 文档生成超时，但工作流程基本完成")

    async def close(self):
        """关闭会话"""
        await self.session.aclose()


async def main():
    """主函数"""
    test = APIWorkflowTest()
    try:
        await test.run_full_workflow()
    finally:
        await test.close()


if __name__ == "__main__":
    asyncio.run(main())
