"""
配置模块

提供：
- settings: 应用配置
- get_logger: 日志获取
- setup_logging: 日志初始化
"""

from config.settings import settings, get_settings, validate_settings
from config.logging import get_logger, setup_logging

__all__ = [
    "settings",
    "get_settings",
    "validate_settings",
    "get_logger",
    "setup_logging",
]
