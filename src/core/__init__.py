"""
Core Module - المكونات الأساسية
المكونات الأساسية للتطبيق
"""

__all__ = [
    'ConfigManager',
    'DatabaseManager',
    'get_db_manager',
    'DatabaseException',
    'signals',
    'AppSignals',
    'EncryptionManager',
    'GlobalExceptionHandler',
]


def __getattr__(name):
    """Lazy exports to keep package imports lightweight."""
    if name == 'ConfigManager':
        from .config_manager import ConfigManager
        return ConfigManager
    if name == 'DatabaseManager' or name == 'get_db_manager':
        from .database_manager import DatabaseManager, get_db_manager
        return DatabaseManager if name == 'DatabaseManager' else get_db_manager
    if name == 'DatabaseException':
        from .exceptions import DatabaseException
        return DatabaseException
    if name == 'signals' or name == 'AppSignals':
        from .signals import signals, AppSignals
        return signals if name == 'signals' else AppSignals
    if name == 'EncryptionManager':
        from .encryption_manager import EncryptionManager
        return EncryptionManager
    if name == 'GlobalExceptionHandler':
        from .exception_handler import GlobalExceptionHandler
        return GlobalExceptionHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

