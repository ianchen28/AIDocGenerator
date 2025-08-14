#!/usr/bin/env python3
"""
固定配置的负载均衡器
支持可配置的 worker 数量
"""

import asyncio
import json
import logging
import random
import time
from typing import List, Dict, Any
from urllib.parse import urlparse

import aiohttp
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 负载均衡器配置
class LoadBalancerConfig(BaseModel):
    workers: List[str]  # worker 地址列表
    health_check_interval: int = 30  # 健康检查间隔（秒）
    timeout: int = 30  # 请求超时时间（秒）


class SimpleLoadBalancer:

    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.workers = config.workers.copy()
        self.healthy_workers = self.workers.copy()
        self.current_index = 0
        self.session = None

    async def start(self):
        """启动负载均衡器"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(
            total=self.config.timeout))

        # 启动健康检查
        asyncio.create_task(self._health_check_loop())

        logger.info(f"负载均衡器启动，worker 数量: {len(self.workers)}")
        logger.info(f"Worker 列表: {self.workers}")

    async def stop(self):
        """停止负载均衡器"""
        if self.session:
            await self.session.close()

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._check_worker_health()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"健康检查出错: {e}")

    async def _check_worker_health(self):
        """检查所有 worker 的健康状态"""
        healthy_workers = []

        for worker in self.workers:
            try:
                async with self.session.get(f"{worker}/",
                                            timeout=5) as response:
                    if response.status == 200:
                        healthy_workers.append(worker)
                        logger.debug(f"Worker {worker} 健康")
                    else:
                        logger.warning(
                            f"Worker {worker} 响应异常: {response.status}")
            except Exception as e:
                logger.warning(f"Worker {worker} 健康检查失败: {e}")

        self.healthy_workers = healthy_workers
        logger.info(
            f"健康 worker 数量: {len(self.healthy_workers)}/{len(self.workers)}")

    def _get_next_worker(self) -> str:
        """获取下一个可用的 worker（轮询算法）"""
        if not self.healthy_workers:
            raise HTTPException(status_code=503, detail="没有可用的 worker")

        worker = self.healthy_workers[self.current_index %
                                      len(self.healthy_workers)]
        self.current_index += 1
        return worker

    def _get_random_worker(self) -> str:
        """获取随机 worker"""
        if not self.healthy_workers:
            raise HTTPException(status_code=503, detail="没有可用的 worker")

        return random.choice(self.healthy_workers)

    async def forward_request(self, request: Request,
                              path: str) -> JSONResponse:
        """转发请求到 worker"""
        if not self.healthy_workers:
            raise HTTPException(status_code=503, detail="没有可用的 worker")

        # 选择 worker（这里使用轮询算法）
        worker = self._get_next_worker()

        # 构建目标 URL
        target_url = f"{worker}{path}"
        if request.query_params:
            target_url += f"?{request.query_params}"

        # 准备请求头
        headers = dict(request.headers)
        # 移除一些不应该转发的头
        headers.pop("host", None)
        headers.pop("content-length", None)

        # 读取请求体
        body = await request.body()

        try:
            # 转发请求
            async with self.session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=body,
                    timeout=self.config.timeout) as response:
                # 读取响应内容
                content = await response.read()

                # 构建响应头
                response_headers = dict(response.headers)
                response_headers.pop("content-length", None)  # 让 FastAPI 重新计算

                # 直接返回原始响应
                from fastapi.responses import Response
                return Response(content=content,
                                status_code=response.status,
                                headers=response_headers)

        except asyncio.TimeoutError:
            logger.error(f"请求超时: {target_url}")
            raise HTTPException(status_code=504, detail="请求超时")
        except Exception as e:
            logger.error(f"转发请求失败: {e}")
            raise HTTPException(status_code=502, detail=f"转发请求失败: {str(e)}")


# 创建 FastAPI 应用
app = FastAPI(title="AI文档生成器负载均衡器", version="1.0.0")

# 全局负载均衡器实例
load_balancer = None


def create_load_balancer_config(base_port: int = 8000,
                                num_workers: int = 2) -> LoadBalancerConfig:
    """创建负载均衡器配置"""
    workers = []
    for i in range(num_workers):
        port = base_port + i
        workers.append(f"http://127.0.0.1:{port}")

    return LoadBalancerConfig(workers=workers,
                              health_check_interval=30,
                              timeout=30)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global load_balancer

    # 从环境变量或默认值获取配置
    import os
    base_port = int(os.getenv("LB_BASE_PORT", "8000"))
    num_workers = int(os.getenv("LB_NUM_WORKERS", "2"))

    # 创建配置
    config = create_load_balancer_config(base_port, num_workers)

    load_balancer = SimpleLoadBalancer(config)
    await load_balancer.start()

    logger.info(
        f"负载均衡器启动完成，配置: {num_workers} 个 worker，端口范围: {base_port}-{base_port + num_workers - 1}"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global load_balancer
    if load_balancer:
        await load_balancer.stop()
    logger.info("负载均衡器已关闭")


@app.get("/")
async def root():
    """根路径 - 显示负载均衡器状态"""
    global load_balancer

    return {
        "message":
        "AI文档生成器负载均衡器",
        "status":
        "运行中",
        "total_workers":
        len(load_balancer.workers) if load_balancer else 0,
        "healthy_workers":
        len(load_balancer.healthy_workers) if load_balancer else 0,
        "workers":
        load_balancer.workers if load_balancer else [],
        "healthy_workers_list":
        load_balancer.healthy_workers if load_balancer else []
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    global load_balancer

    if not load_balancer or not load_balancer.healthy_workers:
        raise HTTPException(status_code=503, detail="没有可用的 worker")

    return {
        "status": "healthy",
        "healthy_workers": len(load_balancer.healthy_workers)
    }


@app.api_route("/{path:path}",
               methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """代理所有其他请求到 worker"""
    global load_balancer

    if not load_balancer:
        raise HTTPException(status_code=503, detail="负载均衡器未初始化")

    return await load_balancer.forward_request(request, f"/{path}")


if __name__ == "__main__":
    # 启动负载均衡器
    import os
    lb_port = int(os.getenv("LB_PORT", "8081"))

    uvicorn.run("load_balancer:app",
                host="0.0.0.0",
                port=lb_port,
                reload=False,
                log_level="info")
