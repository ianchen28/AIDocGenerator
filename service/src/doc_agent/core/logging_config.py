#!/usr/bin/env python3
"""
集中式日志配置模块
使用 loguru 库提供强大的日志功能
"""

import os
import sys
from typing import Any
from pathlib import Path

from loguru import logger

from .config import AppSettings


def safe_format(record):
    """安全格式化函数，处理run_id不存在的情况"""
    # 确保extra中有run_id，如果不存在则添加默认值
    if 'run_id' not in record['extra']:
        record['extra']['run_id'] = 'N/A'
    return record


def setup_logging(config: AppSettings) -> None:
    """
    设置统一的日志配置
    
    Args:
        config: 应用配置对象
    """
    from loguru import logger

    # 移除所有现有的处理器，但保留默认的stderr处理器
    logger.remove()
    # 重新添加默认的stderr处理器
    logger.add(sys.stderr, level="WARNING")

    # 确保日志目录存在 - 使用根目录的相对路径
    # 从当前文件位置找到项目根目录
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent.parent  # 多一个.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    # 统一日志文件路径：使用根目录的logs/app.log
    log_file_path = log_dir / "app.log"

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        level=config.logging.level,
        format=
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        colorize=True,  # 启用颜色
        backtrace=True,
        diagnose=True,
        enqueue=False,  # 同步写入，确保实时输出
    )

    # 添加文件处理器
    logger.add(
        log_file_path,
        level=config.logging.level,
        format=
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=config.logging.rotation,  # 日志轮转
        retention=config.logging.retention,  # 日志保留
        compression="zip",  # 压缩旧日志文件
        enqueue=False,  # 同步写入，确保实时输出
        serialize=False,  # 不使用序列化，保持可读格式
        backtrace=True,
        diagnose=True,
    )

    # 拦截标准库的logging
    import logging

    class InterceptHandler(logging.Handler):

        def emit(self, record):
            # 获取对应的loguru级别
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # 找到调用者
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth,
                       exception=record.exc_info).log(level,
                                                      record.getMessage())

    # 配置logging使用loguru，但不强制覆盖
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=False)

    # 不移除任何现有的handlers，让FastAPI保持原有的日志配置

    logger.info("日志系统已成功配置")
    logger.info(f"统一日志文件路径: {log_file_path}")
    logger.info(f"日志轮转: {config.logging.rotation}")
    logger.info(f"日志保留: {config.logging.retention}")
    logger.info("日志将同时输出到控制台和文件")


def get_logger(name: str = None) -> Any:
    """
    获取配置好的 logger 实例
    Args:
        name: 日志器名称，默认为 None（使用根日志器）
    Returns:
        loguru.logger: 配置好的日志器实例
    """
    if name:
        return logger.bind(name=name)
    return logger
