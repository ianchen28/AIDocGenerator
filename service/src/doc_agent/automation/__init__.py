"""
AI文档生成系统自动化操作模块

提供优雅标准的自动操作实现方式，包括：
- 自动化任务调度
- 批量文档生成
- 智能监控和告警
- 结果管理和归档
"""

from .scheduler import AutomationScheduler
from .monitor import AutomationMonitor
from .executor import AutomationExecutor
from .manager import AutomationManager

__all__ = [
    "AutomationScheduler", "AutomationMonitor", "AutomationExecutor",
    "AutomationManager"
]
