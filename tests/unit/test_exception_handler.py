"""
Unit Tests for ExceptionHandler
اختبارات وحدة ExceptionHandler
"""

import sys

import pytest

from src.core.exception_handler import (
    BusinessLogicError,
    DatabaseError,
    ExceptionType,
    GlobalExceptionHandler,
    StandardElJoumlaError,
    ValidationError,
)


class TestExceptionTypes:
    """اختبارات أنواع الاستثناءات"""

    def test_logical_version_error(self):
        """اختبار استثناء عام"""
        error = StandardElJoumlaError("Test error")

        assert str(error) == "Test error"
        assert error.error_type == ExceptionType.GENERAL
        assert error.recoverable is True

    def test_database_error(self):
        """اختبار استثناء قاعدة البيانات"""
        error = DatabaseError("Database error", query="SELECT * FROM test")

        assert error.error_type == ExceptionType.DATABASE_QUERY
        assert error.details.get("query") == "SELECT * FROM test"

    def test_validation_error(self):
        """اختبار استثناء التحقق"""
        error = ValidationError("Validation error", field="name", value="invalid")

        assert error.error_type == ExceptionType.VALIDATION
        assert error.details.get("field") == "name"
        assert error.details.get("value") == "invalid"

    def test_business_logic_error(self):
        """اختبار استثناء منطق الأعمال"""
        error = BusinessLogicError("Business logic error")

        assert error.error_type == ExceptionType.BUSINESS_LOGIC


class TestGlobalExceptionHandler:
    """اختبارات معالج الأخطاء العام"""

    @pytest.fixture
    def exception_handler(self):
        """إنشاء معالج أخطاء"""
        # نستخدم نسخة لا تظهر حوارات عند الأعطال لتجنب تعليق الاختبارات
        return GlobalExceptionHandler(enable_crash_dialog=False)

    def test_init(self, exception_handler):
        """اختبار التهيئة"""
        assert exception_handler is not None
        assert exception_handler.enable_crash_dialog is False

    def test_handle_exception_system_exit(self, exception_handler):
        """اختبار معالجة استثناء يسبب الخروج"""
        try:
            raise ValueError("Fatal error")
        except ValueError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            # نتوقع خروج النظام لأن recoverable هو False افتراضياً للاستثناءات غير المعروفة
            with pytest.raises(SystemExit):
                exception_handler.handle_exception(exc_type, exc_value, exc_traceback)

    def test_handle_recoverable_error(self, exception_handler):
        """اختبار معالجة خطأ يمكن تجاوزه"""
        try:
            raise StandardElJoumlaError("Recoverable error", recoverable=True)
        except StandardElJoumlaError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            # لا يجب أن يخرج النظام
            exception_handler.handle_exception(exc_type, exc_value, exc_traceback)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
