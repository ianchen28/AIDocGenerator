"""
任务ID生成器

用于生成唯一的任务ID，确保每个任务都有唯一的标识符。
"""

import time
import uuid
from typing import Union

from doc_agent.core.logger import logger


class TaskIdGenerator:
    """任务ID生成器"""

    def __init__(self):
        """初始化任务ID生成器"""
        self.counter = 0
        logger.info("任务ID生成器初始化完成")

    def generate_task_id(self) -> str:
        """
        生成唯一的任务ID
        
        Returns:
            str: 唯一的任务ID，全数字格式
        """
        # 使用时间戳和随机数生成唯一ID，全数字格式
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        random_part = uuid.uuid4().int % 1000000  # 6位随机数
        task_id = f"{timestamp}{random_part:06d}"

        logger.debug(f"生成任务ID: {task_id}")
        return task_id


# 全局任务ID生成器实例
task_id_generator = TaskIdGenerator()


def generate_task_id() -> str:
    """
    生成唯一的任务ID
    
    Returns:
        str: 唯一的任务ID
    """
    return task_id_generator.generate_task_id()
