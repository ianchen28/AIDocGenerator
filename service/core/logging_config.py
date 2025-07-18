#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集中式日志配置模块
使用 loguru 库提供强大的日志功能
"""

import sys
import os
from loguru import logger
from typing import Any
from .config import AppSettings


def setup_logging(config: AppSettings) -> None:
    """
    设置集中式日志配置
    
    Args:
        config: 应用配置对象，包含日志配置信息
    """
    # 1. 移除所有默认处理器，确保清洁的设置
    logger.remove()

    # 2. 配置控制台处理器
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>")

    logger.add(sink=sys.stderr,
               level=config.logging.level,
               format=console_format,
               colorize=True,
               backtrace=True,
               diagnose=True)

    # 3. 配置文件处理器
    # 确保日志目录存在
    log_dir = os.path.dirname(config.logging.file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 文件格式（非彩色，结构化）
    file_format = ("{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                   "{level: <8} | "
                   "{name}:{function}:{line} | "
                   "{message}")

    logger.add(
        sink=config.logging.file_path,
        level="DEBUG",  # 文件记录所有级别的日志
        format=file_format,
        rotation=config.logging.rotation,  # 日志轮转
        retention=config.logging.retention,  # 日志保留
        compression="zip",  # 压缩旧日志文件
        enqueue=True,  # 非阻塞日志
        serialize=False,  # 不使用序列化，保持可读格式
        backtrace=True,
        diagnose=True)

    # 4. 记录日志配置成功信息
    logger.info(f"日志系统已成功配置")
    logger.info(f"控制台日志级别: {config.logging.level}")
    logger.info(f"文件日志路径: {config.logging.file_path}")
    logger.info(f"日志轮转: {config.logging.rotation}")
    logger.info(f"日志保留: {config.logging.retention}")


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
