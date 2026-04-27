"""
نظام إدارة المخزون والمبيعات - الإصدار المنطقي
Inventory and Sales Management System - Logical Version

نظام شامل لإدارة المخزون والمبيعات مع واجهة مستخدم عربية حديثة
A comprehensive inventory and sales management system with modern Arabic UI
"""

__version__ = "5.2.1"
__author__ = "Inventory Management Team"
__email__ = "support@inventory-system.com"
__description__ = "نظام إدارة المخزون والمبيعات - الإصدار المنطقي"

__all__ = [
    "DatabaseManager",
    "DatabaseLogger",
    "ConfigManager",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]


def __getattr__(name):
    """Lazy exports to avoid importing heavy optional dependencies at package import time."""
    if name == "DatabaseManager":
        from .core.database_manager import DatabaseManager

        return DatabaseManager
    if name == "DatabaseLogger":
        from .utils.logger import DatabaseLogger

        return DatabaseLogger
    if name == "ConfigManager":
        from .core.config_manager import ConfigManager

        return ConfigManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
