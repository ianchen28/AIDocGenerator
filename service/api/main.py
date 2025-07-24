from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from .endpoints import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("FastAPI应用正在启动...")
    yield
    # 关闭
    logger.info("FastAPI应用正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(title="AI文档生成器API",
              description="AI驱动的文档生成服务API",
              version="1.0.0",
              lifespan=lifespan)

# 包含API路由器，设置prefix为/api/v1
app.include_router(router, prefix="/api/v1", tags=["API v1"])


@app.get("/")
async def root():
    """根端点 - 健康检查"""
    logger.info("根端点被访问")
    return {"message": "AI文档生成器API服务", "status": "运行中", "version": "1.0.0"}
