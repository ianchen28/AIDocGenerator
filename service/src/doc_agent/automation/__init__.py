"""
AI文档生成系统自动化操作模块

提供优雅标准的自动操作实现方式，包括：
- 自动化任务调度
- 批量文档生成
- 智能监控和告警
- 结果管理和归档
"""

from doc_agent.automation.executor import AutomationExecutor
from doc_agent.automation.manager import AutomationManager
from doc_agent.automation.monitor import AutomationMonitor
from doc_agent.automation.scheduler import AutomationScheduler

__all__ = [
    "AutomationScheduler",
    "AutomationMonitor",
    "AutomationExecutor",
    "AutomationManager",
]
