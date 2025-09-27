"""
نظام معالجة الأخطاء والاستثناءات الشامل
Comprehensive Error and Exception Handling System

يحتوي على جميع أنواع الاستثناءات المخصصة ومعالجات الأخطاء
Contains all custom exceptions and error handlers
"""

from typing import Optional, Dict, Any
from enum import Enum
import traceback
import logging
from datetime import datetime


class ErrorSeverity(Enum):
    """مستويات خطورة الأخطاء - Error Severity Levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """فئات الأخطاء - Error Categories"""
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    UI = "ui"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    SYSTEM = "system"


class BaseInventoryException(Exception):
    """الاستثناء الأساسي لنظام إدارة المخزون - Base Inventory System Exception"""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل الاستثناء إلى قاموس - Convert exception to dictionary"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback
        }


# استثناءات الإعدادات - Configuration Exceptions
class ConfigurationException(BaseInventoryException):
    """استثناء الإعدادات العام - General Configuration Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ConfigFileNotFoundException(ConfigurationException):
    """استثناء ملف الإعدادات غير موجود - Config File Not Found Exception"""
    pass


class InvalidConfigFormatException(ConfigurationException):
    """استثناء تنسيق إعدادات غير صحيح - Invalid Config Format Exception"""
    pass


# استثناءات قاعدة البيانات - Database Exceptions
class DatabaseException(BaseInventoryException):
    """استثناء قاعدة البيانات العام - General Database Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class DatabaseConnectionException(DatabaseException):
    """استثناء اتصال قاعدة البيانات - Database Connection Exception"""
    pass


class DatabaseQueryException(DatabaseException):
    """استثناء استعلام قاعدة البيانات - Database Query Exception"""
    pass


class DatabaseIntegrityException(DatabaseException):
    """استثناء تكامل قاعدة البيانات - Database Integrity Exception"""
    pass


# استثناءات المصادقة والأمان - Authentication & Security Exceptions
class AuthenticationException(BaseInventoryException):
    """استثناء المصادقة العام - General Authentication Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class InvalidCredentialsException(AuthenticationException):
    """استثناء بيانات اعتماد غير صحيحة - Invalid Credentials Exception"""
    pass


class SessionExpiredException(AuthenticationException):
    """استثناء انتهاء الجلسة - Session Expired Exception"""
    pass


class InsufficientPermissionsException(AuthenticationException):
    """استثناء صلاحيات غير كافية - Insufficient Permissions Exception"""
    pass


class AccountLockedException(AuthenticationException):
    """استثناء حساب مقفل - Account Locked Exception"""
    pass


# استثناءات التحقق من صحة البيانات - Validation Exceptions
class ValidationException(BaseInventoryException):
    """استثناء التحقق من صحة البيانات العام - General Validation Exception"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.field = field


class RequiredFieldException(ValidationException):
    """استثناء حقل مطلوب - Required Field Exception"""
    pass


class InvalidFormatException(ValidationException):
    """استثناء تنسيق غير صحيح - Invalid Format Exception"""
    pass


class ValueOutOfRangeException(ValidationException):
    """استثناء قيمة خارج النطاق - Value Out of Range Exception"""
    pass


class DuplicateValueException(ValidationException):
    """استثناء قيمة مكررة - Duplicate Value Exception"""
    pass


# استثناءات منطق الأعمال - Business Logic Exceptions
class BusinessLogicException(BaseInventoryException):
    """استثناء منطق الأعمال العام - General Business Logic Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class InsufficientStockException(BusinessLogicException):
    """استثناء مخزون غير كافي - Insufficient Stock Exception"""
    pass


class ProductNotFoundException(BusinessLogicException):
    """استثناء منتج غير موجود - Product Not Found Exception"""
    pass


class CustomerNotFoundException(BusinessLogicException):
    """استثناء عميل غير موجود - Customer Not Found Exception"""
    pass


class SupplierNotFoundException(BusinessLogicException):
    """استثناء مورد غير موجود - Supplier Not Found Exception"""
    pass


class InvalidPriceException(BusinessLogicException):
    """استثناء سعر غير صحيح - Invalid Price Exception"""
    pass


class SaleAlreadyCompletedException(BusinessLogicException):
    """استثناء بيع مكتمل بالفعل - Sale Already Completed Exception"""
    pass


class PurchaseAlreadyReceivedException(BusinessLogicException):
    """استثناء شراء مستلم بالفعل - Purchase Already Received Exception"""
    pass


# استثناءات واجهة المستخدم - UI Exceptions
class UIException(BaseInventoryException):
    """استثناء واجهة المستخدم العام - General UI Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.UI,
            severity=ErrorSeverity.LOW,
            **kwargs
        )


class DialogException(UIException):
    """استثناء نافذة الحوار - Dialog Exception"""
    pass


class WindowException(UIException):
    """استثناء النافذة - Window Exception"""
    pass


# استثناءات الشبكة - Network Exceptions
class NetworkException(BaseInventoryException):
    """استثناء الشبكة العام - General Network Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ConnectionTimeoutException(NetworkException):
    """استثناء انتهاء مهلة الاتصال - Connection Timeout Exception"""
    pass


class APIException(NetworkException):
    """استثناء واجهة برمجة التطبيقات - API Exception"""
    pass


# استثناءات نظام الملفات - File System Exceptions
class FileSystemException(BaseInventoryException):
    """استثناء نظام الملفات العام - General File System Exception"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class FileNotFoundException(FileSystemException):
    """استثناء ملف غير موجود - File Not Found Exception"""
    pass


class FilePermissionException(FileSystemException):
    """استثناء صلاحية الملف - File Permission Exception"""
    pass


class ExportException(FileSystemException):
    """استثناء التصدير - Export Exception"""
    pass


class ImportException(FileSystemException):
    """استثناء الاستيراد - Import Exception"""
    pass


# معالج الأخطاء العام - Global Error Handler
class ErrorHandler:
    """معالج الأخطاء العام - Global Error Handler"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
    
    def handle_exception(
        self,
        exception: Exception,
        context: str = None,
        user_message: str = None,
        show_to_user: bool = True
    ) -> Dict[str, Any]:
        """
        معالجة الاستثناء وتسجيله
        Handle exception and log it
        """
        # تحديد نوع الاستثناء
        if isinstance(exception, BaseInventoryException):
            error_info = exception.to_dict()
        else:
            error_info = {
                "error_code": exception.__class__.__name__,
                "message": str(exception),
                "category": ErrorCategory.SYSTEM.value,
                "severity": ErrorSeverity.MEDIUM.value,
                "details": {},
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc()
            }
        
        # إضافة السياق
        if context:
            error_info["context"] = context
        
        # تسجيل الخطأ
        self._log_error(error_info)
        
        # تحديث إحصائيات الأخطاء
        self._update_error_stats(error_info["error_code"])
        
        # إعداد رسالة المستخدم
        if user_message:
            error_info["user_message"] = user_message
        elif show_to_user:
            error_info["user_message"] = self._get_user_friendly_message(exception)
        
        return error_info
    
    def _log_error(self, error_info: Dict[str, Any]):
        """تسجيل الخطأ - Log error"""
        severity = error_info.get("severity", "medium")
        message = f"[{error_info['error_code']}] {error_info['message']}"
        
        if severity == "critical":
            self.logger.critical(message, extra=error_info)
        elif severity == "high":
            self.logger.error(message, extra=error_info)
        elif severity == "medium":
            self.logger.warning(message, extra=error_info)
        else:
            self.logger.info(message, extra=error_info)
    
    def _update_error_stats(self, error_code: str):
        """تحديث إحصائيات الأخطاء - Update error statistics"""
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
    
    def _get_user_friendly_message(self, exception: Exception) -> str:
        """الحصول على رسالة مفهومة للمستخدم - Get user-friendly message"""
        if isinstance(exception, DatabaseConnectionException):
            return "خطأ في الاتصال بقاعدة البيانات. يرجى المحاولة مرة أخرى."
        elif isinstance(exception, InvalidCredentialsException):
            return "بيانات تسجيل الدخول غير صحيحة. يرجى التحقق من اسم المستخدم وكلمة المرور."
        elif isinstance(exception, InsufficientStockException):
            return "الكمية المطلوبة غير متوفرة في المخزون."
        elif isinstance(exception, ValidationException):
            return f"خطأ في البيانات المدخلة: {exception.message}"
        elif isinstance(exception, FileNotFoundException):
            return "الملف المطلوب غير موجود."
        elif isinstance(exception, NetworkException):
            return "خطأ في الاتصال بالشبكة. يرجى التحقق من الاتصال."
        else:
            return "حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى أو الاتصال بالدعم الفني."
    
    def get_error_statistics(self) -> Dict[str, int]:
        """الحصول على إحصائيات الأخطاء - Get error statistics"""
        return self.error_counts.copy()
    
    def reset_error_statistics(self):
        """إعادة تعيين إحصائيات الأخطاء - Reset error statistics"""
        self.error_counts.clear()


# مثيل معالج الأخطاء العام - Global error handler instance
global_error_handler = ErrorHandler()


def handle_exception(exception: Exception, context: str = None, **kwargs) -> Dict[str, Any]:
    """دالة مساعدة لمعالجة الاستثناءات - Helper function for handling exceptions"""
    return global_error_handler.handle_exception(exception, context, **kwargs)


def log_error(message: str, error_code: str = None, **kwargs):
    """دالة مساعدة لتسجيل الأخطاء - Helper function for logging errors"""
    exception = BaseInventoryException(message, error_code=error_code, **kwargs)
    return global_error_handler.handle_exception(exception, show_to_user=False)