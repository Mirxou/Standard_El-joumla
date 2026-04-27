"""
Unit Tests for LoggingService
اختبارات وحدة LoggingService
"""

import pytest
from unittest.mock import Mock, patch
from src.core.logging_service import AdvancedLoggingService, LogLevel, StructuredFormatter, ColoredFormatter


class TestStructuredFormatter:
    """اختبارات StructuredFormatter"""
    
    @pytest.fixture
    def formatter(self):
        """إنشاء formatter"""
        return StructuredFormatter()
    
    def test_format(self, formatter):
        """اختبار تنسيق السجل"""
        import logging
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert isinstance(formatted, str)
        assert "Test message" in formatted


class TestColoredFormatter:
    """اختبارات ColoredFormatter"""
    
    @pytest.fixture
    def formatter(self):
        """إنشاء formatter"""
        return ColoredFormatter()
    
    def test_format(self, formatter):
        """اختبار تنسيق السجل مع ألوان"""
        import logging
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert isinstance(formatted, str)
        assert "Test message" in formatted


class TestAdvancedLoggingService:
    """اختبارات خدمة السجلات المتقدمة"""
    
    @pytest.fixture
    def logging_service(self):
        """إنشاء خدمة سجلات"""
        return AdvancedLoggingService(
            log_dir="logs",
            app_name="test_app"
        )
    
    def test_init(self, logging_service):
        """اختبار التهيئة"""
        assert logging_service is not None
        assert logging_service.app_name == "test_app"
    
    def test_get_logger(self, logging_service):
        """اختبار الحصول على logger"""
        logger = logging_service.get_logger("test_module")
        
        assert logger is not None
        # قد يكون اسم الـ logger مسبوقاً باسم التطبيق
        assert "test_module" in logger.name or logger.name == "test_module"
    
    def test_log_info(self, logging_service):
        """اختبار تسجيل معلومات"""
        logger = logging_service.get_logger("test_module")
        
        # يجب ألا يرفع استثناء
        logger.info("Test info message")
    
    def test_log_error(self, logging_service):
        """اختبار تسجيل خطأ"""
        logger = logging_service.get_logger("test_module")
        
        # يجب ألا يرفع استثناء
        logger.error("Test error message")
    
    def test_log_exception(self, logging_service):
        """اختبار تسجيل استثناء"""
        logger = logging_service.get_logger("test_module")
        
        try:
            raise ValueError("Test exception")
        except Exception:
            # يجب ألا يرفع استثناء
            logger.exception("Test exception message")



