# service/src/doc_agent/utils/decorators.py
"""
装饰器工具模块
包含各种通用的装饰器函数
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from loguru import logger


def timer(func: Optional[Callable] = None, *, log_level: str = "info"):
    """
    计算函数执行时间的装饰器
    
    Args:
        func: 被装饰的函数
        log_level: 日志级别 ("debug", "info", "warning", "error")
    
    Examples:
        @timer
        def sync_function():
            pass
            
        @timer(log_level="debug")
        async def async_function():
            pass
    """

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            log_func = getattr(logger, log_level)
            log_func(f"函数 {func.__name__} 执行耗时: {elapsed_time:.4f} 秒")
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            log_func = getattr(logger, log_level)
            log_func(f"异步函数 {func.__name__} 执行耗时: {elapsed_time:.4f} 秒")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    if func is None:
        return decorator
    return decorator(func)


def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
    
    Examples:
        @retry(max_attempts=3, delay=2.0)
        def unreliable_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(f"函数 {func.__name__} 第 {attempt} 次执行失败: {e}, {delay}秒后重试")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 执行失败，已重试 {max_attempts} 次: {e}")
                        raise last_exception
            
            return None
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(f"异步函数 {func.__name__} 第 {attempt} 次执行失败: {e}, {delay}秒后重试")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"异步函数 {func.__name__} 执行失败，已重试 {max_attempts} 次: {e}")
                        raise last_exception
            
            return None
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def cache_result(ttl: int = 300):
    """
    缓存结果装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
    
    Examples:
        @cache_result(ttl=600)
        def expensive_function():
            pass
    """
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 创建缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            current_time = time.time()
            
            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl:
                    logger.debug(f"函数 {func.__name__} 使用缓存结果")
                    return result
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            logger.debug(f"函数 {func.__name__} 结果已缓存")
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 创建缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            current_time = time.time()
            
            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl:
                    logger.debug(f"异步函数 {func.__name__} 使用缓存结果")
                    return result
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            logger.debug(f"异步函数 {func.__name__} 结果已缓存")
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_function_call(log_args: bool = True, log_result: bool = False):
    """
    记录函数调用的装饰器
    
    Args:
        log_args: 是否记录参数
        log_result: 是否记录返回值
    
    Examples:
        @log_function_call(log_args=True, log_result=False)
        def important_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if log_args:
                logger.debug(f"调用函数 {func.__name__}，参数: args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"调用函数 {func.__name__}")
            
            result = func(*args, **kwargs)
            
            if log_result:
                logger.debug(f"函数 {func.__name__} 返回值: {result}")
            
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if log_args:
                logger.debug(f"调用异步函数 {func.__name__}，参数: args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"调用异步函数 {func.__name__}")
            
            result = await func(*args, **kwargs)
            
            if log_result:
                logger.debug(f"异步函数 {func.__name__} 返回值: {result}")
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def validate_input(*validators: Callable):
    """
    输入验证装饰器
    
    Args:
        *validators: 验证函数列表
    
    Examples:
        @validate_input(lambda x: x > 0, lambda x: x < 100)
        def process_number(x):
            pass
    """
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 验证参数
            for validator in validators:
                for arg in args:
                    if not validator(arg):
                        raise ValueError(f"参数 {arg} 未通过验证: {validator.__name__}")
            
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 验证参数
            for validator in validators:
                for arg in args:
                    if not validator(arg):
                        raise ValueError(f"参数 {arg} 未通过验证: {validator.__name__}")
            
            return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# 导出所有装饰器
__all__ = [
    'timer',
    'retry', 
    'cache_result',
    'log_function_call',
    'validate_input'
] 