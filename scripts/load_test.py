#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI文档生成服务压测脚本
支持配置并发请求数、请求间隔、测试时长等功能
"""

import asyncio
import aiohttp
import time
import json
import argparse
import random
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics
from loguru import logger


@dataclass
class LoadTestConfig:
    """压测配置"""
    url: str = "http://10.215.58.199:8081/api/v1/jobs/document-from-outline"
    concurrent_users: int = 10
    duration_seconds: int = 1
    request_interval: float = 0.5
    timeout: int = 30
    max_requests: Optional[int] = None
    log_level: str = "INFO"


@dataclass
class TestResult:
    """测试结果"""
    request_id: str
    start_time: float
    end_time: float
    status_code: int
    response_time: float
    success: bool
    error_message: str = ""


class LoadTester:
    """压测器"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.request_count = 0
        self.session_id_counter = 0

        # 设置日志
        logger.remove()
        logger.add(
            f"logs/load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            level=config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="100 MB")
        logger.add(lambda msg: print(msg, end=""),
                   level=config.log_level,
                   format="{time:HH:mm:ss} | {level} | {message}")

    def generate_session_id(self) -> str:
        """生成会话ID"""
        self.session_id_counter += 1
        timestamp = int(time.time() * 1000)
        return f"{timestamp}_{self.session_id_counter}"

    def generate_request_data(self) -> Dict:
        """生成请求数据"""
        # 写死的主题和字数选项
        themes = [
            "人工智能的发展与应用", "环境保护与可持续发展", "数字化转型与企业发展", "健康生活方式的重要性",
            "教育创新与未来学习", "科技创新与社会进步", "文化传承与现代发展", "经济发展与民生改善", "互联网技术与现代生活",
            "医疗健康与生活质量"
        ]
        word_counts = [2000, 3000, 4000, 5000, 6000, 8000, 10000]

        theme = random.choice(themes)
        word_count = random.choice(word_counts)

        return {
            "outline": "ef9eff70e4dc524ec03d0f614517bda5",
            "isOnline": False,
            "sessionId": self.generate_session_id(),
            "taskPrompt": f"帮我写一篇【主题】{theme}的文章，篇幅大概在【字数】{word_count}字左右"
        }

    async def make_request(self, session: aiohttp.ClientSession,
                           request_id: str) -> TestResult:
        """发送单个请求"""
        start_time = time.time()
        data = self.generate_request_data()

        try:
            async with session.post(
                    self.config.url,
                    json=data,
                    timeout=aiohttp.ClientTimeout(
                        total=self.config.timeout)) as response:
                end_time = time.time()
                response_time = end_time - start_time

                success = 200 <= response.status < 300
                error_message = "" if success else f"HTTP {response.status}"

                result = TestResult(request_id=request_id,
                                    start_time=start_time,
                                    end_time=end_time,
                                    status_code=response.status,
                                    response_time=response_time,
                                    success=success,
                                    error_message=error_message)

                # 获取响应内容
                try:
                    response_text = await response.text()
                    logger.info(
                        f"请求 {request_id}: 状态码={response.status}, 响应时间={response_time:.2f}s"
                    )
                    # 限制响应内容显示长度，避免日志过长
                    if len(response_text) > 500:
                        logger.info(f"响应内容 (前500字符): {response_text[:500]}...")
                    else:
                        logger.info(f"响应内容: {response_text}")
                except Exception as e:
                    logger.info(
                        f"请求 {request_id}: 状态码={response.status}, 响应时间={response_time:.2f}s"
                    )
                    logger.warning(f"无法读取响应内容: {e}")
                return result

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            result = TestResult(request_id=request_id,
                                start_time=start_time,
                                end_time=end_time,
                                status_code=0,
                                response_time=response_time,
                                success=False,
                                error_message=str(e))

            logger.error(f"请求 {request_id} 失败: {e}")
            return result

    async def worker(self, worker_id: int, session: aiohttp.ClientSession):
        """工作协程"""
        logger.info(f"工作协程 {worker_id} 启动")

        # 计算每个工作协程应该发送的请求数
        if self.config.max_requests:
            requests_per_worker = self.config.max_requests // self.config.concurrent_users
            if worker_id < self.config.max_requests % self.config.concurrent_users:
                requests_per_worker += 1
        else:
            # 基于时间计算预期请求数
            requests_per_worker = int(self.config.duration_seconds /
                                      self.config.request_interval) + 1

        logger.info(f"工作协程 {worker_id} 计划发送 {requests_per_worker} 个请求")

        for request_num in range(requests_per_worker):
            # 检查是否达到总请求数限制
            if self.config.max_requests and self.request_count >= self.config.max_requests:
                break

            request_id = f"worker_{worker_id}_req_{request_num + 1}"
            self.request_count += 1

            result = await self.make_request(session, request_id)
            self.results.append(result)

            # 如果不是最后一个请求，则等待间隔时间
            if request_num < requests_per_worker - 1 and self.config.request_interval > 0:
                await asyncio.sleep(self.config.request_interval)

        logger.info(f"工作协程 {worker_id} 完成，发送了 {requests_per_worker} 个请求")

    async def run_load_test(self):
        """运行压测"""
        logger.info("开始压测...")
        logger.info(f"配置: {self.config}")

        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            # 创建多个工作协程
            workers = []
            for i in range(self.config.concurrent_users):
                worker = asyncio.create_task(self.worker(i, session))
                workers.append(worker)

            # 等待指定时间或达到最大请求数
            try:
                if self.config.max_requests:
                    while self.request_count < self.config.max_requests:
                        await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(self.config.duration_seconds)
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在停止...")

            # 取消所有工作协程
            for worker in workers:
                worker.cancel()

            # 等待所有协程完成
            await asyncio.gather(*workers, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        logger.info(f"压测完成，总耗时: {total_time:.2f}s")
        self.print_results(total_time)

    def print_results(self, total_time: float):
        """打印测试结果"""
        if not self.results:
            logger.warning("没有测试结果")
            return

        successful_requests = [r for r in self.results if r.success]
        failed_requests = [r for r in self.results if not r.success]

        total_requests = len(self.results)
        success_count = len(successful_requests)
        failure_count = len(failed_requests)

        response_times = [r.response_time for r in successful_requests]

        logger.info("=" * 60)
        logger.info("压测结果汇总")
        logger.info("=" * 60)
        logger.info(f"总请求数: {total_requests}")
        logger.info(f"成功请求: {success_count}")
        logger.info(f"失败请求: {failure_count}")
        logger.info(f"成功率: {success_count/total_requests*100:.2f}%")
        logger.info(f"总耗时: {total_time:.2f}s")
        logger.info(f"平均RPS: {total_requests/total_time:.2f}")

        if response_times:
            logger.info(f"平均响应时间: {statistics.mean(response_times):.2f}s")
            logger.info(f"最小响应时间: {min(response_times):.2f}s")
            logger.info(f"最大响应时间: {max(response_times):.2f}s")
            logger.info(f"响应时间中位数: {statistics.median(response_times):.2f}s")
            logger.info(f"响应时间标准差: {statistics.stdev(response_times):.2f}s")

        if failed_requests:
            logger.info("\n失败请求详情:")
            for req in failed_requests[:10]:  # 只显示前10个失败请求
                logger.error(f"  请求 {req.request_id}: {req.error_message}")
            if len(failed_requests) > 10:
                logger.error(f"  ... 还有 {len(failed_requests) - 10} 个失败请求")

        # 保存详细结果到文件
        self.save_detailed_results()

    def save_detailed_results(self):
        """保存详细结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/load_test_results_{timestamp}.json"

        results_data = []
        for result in self.results:
            results_data.append({
                "request_id": result.request_id,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "status_code": result.status_code,
                "response_time": result.response_time,
                "success": result.success,
                "error_message": result.error_message
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        logger.info(f"详细结果已保存到: {filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI文档生成服务压测脚本")
    parser.add_argument(
        "--url",
        default="http://10.215.58.199:8081/api/v1/jobs/document-from-outline",
        help="API端点URL")
    # parser.add_argument(
    #     "--url",
    #     default="http://10.215.58.199:8081/api/v1/jobs/outline",
    #     help="API端点URL")
    parser.add_argument("--concurrent",
                        "-c",
                        type=int,
                        default=50,
                        help="并发用户数")
    parser.add_argument("--duration",
                        "-d",
                        type=int,
                        default=1,
                        help="测试持续时间(秒)")
    parser.add_argument("--interval",
                        "-i",
                        type=float,
                        default=0.5,
                        help="请求间隔(秒)")
    parser.add_argument("--timeout",
                        "-t",
                        type=int,
                        default=30,
                        help="请求超时时间(秒)")
    parser.add_argument("--max-requests", "-m", type=int, help="最大请求数(可选)")
    parser.add_argument("--log-level",
                        default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="日志级别")

    args = parser.parse_args()

    config = LoadTestConfig(url=args.url,
                            concurrent_users=args.concurrent,
                            duration_seconds=args.duration,
                            request_interval=args.interval,
                            timeout=args.timeout,
                            max_requests=args.max_requests,
                            log_level=args.log_level)

    # 确保logs目录存在
    import os
    os.makedirs("logs", exist_ok=True)

    # 运行压测
    tester = LoadTester(config)
    asyncio.run(tester.run_load_test())


if __name__ == "__main__":
    main()
