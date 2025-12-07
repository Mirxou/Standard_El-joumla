"""
Unit Tests for ExceptionHandler
اختبارات وحدة ExceptionHandler
"""

import pytest
from src.core.exception_handler import (
    GlobalExceptionHandler,
    LogicalVersionError,
    DatabaseError,
    ValidationError,
    BusinessLogicError,
    ExceptionType
)


class TestExceptionTypes:
    """اختبارات أنواع الاستثناءات"""
    
    def test_logical_version_error(self):
        """اختبار استثناء عام"""
        error = LogicalVersionError("Test error")
        
        assert str(error) == "Test error"
        assert error.error_type == ExceptionType.GENERAL
        assert error.recoverable is True
    
    def test_database_error(self):
        """اختبار استثناء قاعدة البيانات"""
        error = DatabaseError("Database error", query="SELECT * FROM test")
        
        assert error.error_type == ExceptionType.DATABASE_QUERY
        assert 'query' in error.details
    
    def test_validation_error(self):
        """اختبار استثناء التحقق"""
        error = ValidationError("Validation error", field="name", value="")
        
        assert error.error_type == ExceptionType.VALIDATION
        assert error.details['field'] == "name"
    
    def test_business_logic_error(self):
        """اختبار استثناء منطق الأعمال"""
        error = BusinessLogicError("Business logic error")
        
        assert error.error_type == ExceptionType.BUSINESS_LOGIC


class TestGlobalExceptionHandler:
    """اختبارات معالج الأخطاء العام"""
    
    @pytest.fixture
    def exception_handler(self):
        """إنشاء معالج أخطاء"""
        return GlobalExceptionHandler()
    
    def test_init(self, exception_handler):
        """اختبار التهيئة"""
        assert exception_handler is not None
    
    def test_handle_exception(self, exception_handler):
        """اختبار معالجة استثناء"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            # يجب ألا يرفع استثناء
            # handle_exception يحتاج 3 معاملات: exc_type, exc_value, exc_traceback
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            # قد يرفع SystemExit في بعض الحالات، لكن يجب ألا يرفع استثناءات أخرى
            try:
                exception_handler.handle_exception(exc_type, exc_value, exc_traceback)
            except SystemExit:
                # SystemExit مقبول في معالجة الأخطاء
                pass
    
    def test_handle_logical_version_error(self, exception_handler):
        """اختبار معالجة LogicalVersionError"""
        try:
            raise LogicalVersionError("Test error")
        except Exception as e:
            # يجب ألا يرفع استثناء
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exception_handler.handle_exception(exc_type, exc_value, exc_traceback)

