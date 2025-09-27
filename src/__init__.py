"""
نظام إدارة المخزون والمبيعات - الإصدار المنطقي
Inventory and Sales Management System - Logical Version

نظام شامل لإدارة المخزون والمبيعات مع واجهة مستخدم عربية حديثة
A comprehensive inventory and sales management system with modern Arabic UI
"""

__version__ = "1.0.0"
__author__ = "Inventory Management Team"
__email__ = "support@inventory-system.com"
__description__ = "نظام إدارة المخزون والمبيعات - الإصدار المنطقي"

# تصدير الوحدات الرئيسية - Export main modules
from .core.database_manager import DatabaseManager
from .utils.logger import DatabaseLogger
from .core.config_manager import ConfigManager

__all__ = [
    "DatabaseManager",
    "DatabaseLogger", 
    "ConfigManager",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]