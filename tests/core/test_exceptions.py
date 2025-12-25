"""
اختبارات شاملة لنظام الاستثناءات
Comprehensive tests for Exceptions system
"""

import unittest
from datetime import datetime
from src.core.exceptions import (
    ErrorSeverity,
    ErrorCategory,
    BaseInventoryException,
    DatabaseException,
    ValidationException,
    AuthenticationException,
    InsufficientPermissionsException,
    ProductNotFoundException,
    DuplicateValueException,
    BusinessLogicException,
)


class TestErrorEnums(unittest.TestCase):
    """اختبارات Enums الأخطاء"""

    def test_error_severity_values(self):
        """فحص قيم مستويات الخطورة"""
        self.assertEqual(ErrorSeverity.LOW.value, "low")
        self.assertEqual(ErrorSeverity.MEDIUM.value, "medium")
        self.assertEqual(ErrorSeverity.HIGH.value, "high")
        self.assertEqual(ErrorSeverity.CRITICAL.value, "critical")

    def test_error_category_values(self):
        """فحص قيم فئات الأخطاء"""
        self.assertEqual(ErrorCategory.DATABASE.value, "database")
        self.assertEqual(ErrorCategory.AUTHENTICATION.value, "authentication")
        self.assertEqual(ErrorCategory.VALIDATION.value, "validation")
        self.assertEqual(ErrorCategory.BUSINESS_LOGIC.value, "business_logic")
        self.assertEqual(ErrorCategory.UI.value, "ui")
        self.assertEqual(ErrorCategory.NETWORK.value, "network")
        self.assertEqual(ErrorCategory.FILE_SYSTEM.value, "file_system")
        self.assertEqual(ErrorCategory.SYSTEM.value, "system")


class TestBaseInventoryException(unittest.TestCase):
    """اختبارات الاستثناء الأساسي"""

    def test_basic_exception_creation(self):
        """إنشاء استثناء أساسي"""
        exc = BaseInventoryException("Test error")
        self.assertEqual(exc.message, "Test error")
        self.assertEqual(exc.error_code, "BaseInventoryException")
        self.assertEqual(exc.category, ErrorCategory.SYSTEM)
        self.assertEqual(exc.severity, ErrorSeverity.MEDIUM)

    def test_exception_with_all_params(self):
        """إنشاء استثناء بكل المعاملات"""
        exc = BaseInventoryException(
            message="Custom error",
            error_code="ERR001",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details={"user_id": 123, "action": "delete"}
        )
        self.assertEqual(exc.message, "Custom error")
        self.assertEqual(exc.error_code, "ERR001")
        self.assertEqual(exc.category, ErrorCategory.DATABASE)
        self.assertEqual(exc.severity, ErrorSeverity.HIGH)
        self.assertEqual(exc.details["user_id"], 123)
        self.assertEqual(exc.details["action"], "delete")

    def test_exception_timestamp(self):
        """فحص timestamp الاستثناء"""
        exc = BaseInventoryException("Test")
        self.assertIsInstance(exc.timestamp, datetime)
        self.assertLessEqual((datetime.now() - exc.timestamp).total_seconds(), 1)

    def test_exception_to_dict(self):
        """تحويل الاستثناء إلى dict"""
        exc = BaseInventoryException(
            message="Test error",
            error_code="TEST001",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details={"field": "email"}
        )
        result = exc.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["error_code"], "TEST001")
        self.assertEqual(result["message"], "Test error")
        self.assertEqual(result["category"], "validation")
        self.assertEqual(result["severity"], "low")
        self.assertEqual(result["details"]["field"], "email")
        self.assertIn("timestamp", result)


class TestDatabaseException(unittest.TestCase):
    """اختبارات استثناءات قاعدة البيانات"""

    def test_database_exception_creation(self):
        """إنشاء استثناء قاعدة بيانات"""
        exc = DatabaseException("Connection failed")
        self.assertEqual(exc.message, "Connection failed")
        self.assertEqual(exc.category, ErrorCategory.DATABASE)

    def test_database_exception_with_details(self):
        """استثناء قاعدة بيانات مع تفاصيل"""
        exc = DatabaseException(
            "Query failed",
            details={"query": "SELECT * FROM users", "error": "timeout"}
        )
        self.assertEqual(exc.details["query"], "SELECT * FROM users")
        self.assertEqual(exc.details["error"], "timeout")


class TestValidationException(unittest.TestCase):
    """اختبارات استثناءات التحقق"""

    def test_validation_exception_creation(self):
        """إنشاء استثناء تحقق"""
        exc = ValidationException("Invalid email format")
        self.assertEqual(exc.message, "Invalid email format")
        self.assertEqual(exc.category, ErrorCategory.VALIDATION)

    def test_validation_exception_with_field(self):
        """استثناء تحقق مع اسم الحقل"""
        exc = ValidationException(
            "Field is required",
            details={"field": "username", "value": None}
        )
        self.assertEqual(exc.details["field"], "username")
        self.assertIsNone(exc.details["value"])


class TestAuthenticationException(unittest.TestCase):
    """اختبارات استثناءات المصادقة"""

    def test_authentication_exception_creation(self):
        """إنشاء استثناء مصادقة"""
        exc = AuthenticationException("Invalid credentials")
        self.assertEqual(exc.message, "Invalid credentials")
        self.assertEqual(exc.category, ErrorCategory.AUTHENTICATION)


class TestInsufficientPermissionsException(unittest.TestCase):
    """اختبارات استثناءات رفض الصلاحية"""

    def test_permission_denied_creation(self):
        """إنشاء استثناء رفض صلاحية"""
        exc = InsufficientPermissionsException("Access denied")
        self.assertEqual(exc.message, "Access denied")
        self.assertEqual(exc.category, ErrorCategory.AUTHENTICATION)

    def test_permission_denied_with_resource(self):
        """استثناء رفض صلاحية مع المورد"""
        exc = InsufficientPermissionsException(
            "Cannot delete user",
            details={"resource": "user", "action": "delete", "user_id": 5}
        )
        self.assertEqual(exc.details["resource"], "user")
        self.assertEqual(exc.details["action"], "delete")


class TestProductNotFoundException(unittest.TestCase):
    """اختبارات استثناءات المنتج غير موجود"""

    def test_resource_not_found_creation(self):
        """إنشاء استثناء منتج غير موجود"""
        exc = ProductNotFoundException("Product not found")
        self.assertEqual(exc.message, "Product not found")

    def test_resource_not_found_with_id(self):
        """استثناء منتج غير موجود مع المعرف"""
        exc = ProductNotFoundException(
            "Product 999 not found",
            details={"resource_type": "product", "id": 999}
        )
        self.assertEqual(exc.details["resource_type"], "product")
        self.assertEqual(exc.details["id"], 999)


class TestDuplicateValueException(unittest.TestCase):
    """اختبارات استثناءات القيمة المكررة"""

    def test_duplicate_resource_creation(self):
        """إنشاء استثناء قيمة مكررة"""
        exc = DuplicateValueException("Email already exists")
        self.assertEqual(exc.message, "Email already exists")

    def test_duplicate_resource_with_value(self):
        """استثناء قيمة مكررة مع التفاصيل"""
        exc = DuplicateValueException(
            "Barcode already exists",
            details={"field": "barcode", "value": "ABC123"}
        )
        self.assertEqual(exc.details["field"], "barcode")
        self.assertEqual(exc.details["value"], "ABC123")


class TestBusinessLogicException(unittest.TestCase):
    """اختبارات استثناءات منطق العمل"""

    def test_business_rule_violation_creation(self):
        """إنشاء استثناء منطق عمل"""
        exc = BusinessLogicException("Insufficient stock")
        self.assertEqual(exc.message, "Insufficient stock")
        self.assertEqual(exc.category, ErrorCategory.BUSINESS_LOGIC)

    def test_business_rule_violation_with_rule(self):
        """استثناء منطق عمل مع التفاصيل"""
        exc = BusinessLogicException(
            "Cannot sell below cost",
            details={
                "rule": "MIN_SELLING_PRICE",
                "cost": 100,
                "selling_price": 80
            }
        )
        self.assertEqual(exc.details["rule"], "MIN_SELLING_PRICE")
        self.assertEqual(exc.details["cost"], 100)
        self.assertEqual(exc.details["selling_price"], 80)


class TestExceptionInheritance(unittest.TestCase):
    """اختبارات التوارث بين الاستثناءات"""

    def test_all_inherit_from_base(self):
        """جميع الاستثناءات ترث من BaseInventoryException"""
        exceptions = [
            DatabaseException("test"),
            ValidationException("test"),
            AuthenticationException("test"),
            InsufficientPermissionsException("test"),
            ProductNotFoundException("test"),
            DuplicateValueException("test"),
            BusinessLogicException("test"),
        ]
        
        for exc in exceptions:
            self.assertIsInstance(exc, BaseInventoryException)
            self.assertIsInstance(exc, Exception)

    def test_exception_can_be_raised(self):
        """يمكن رفع جميع الاستثناءات"""
        with self.assertRaises(DatabaseException):
            raise DatabaseException("DB Error")
        
        with self.assertRaises(ValidationException):
            raise ValidationException("Validation Error")
        
        with self.assertRaises(BaseInventoryException):
            raise AuthenticationException("Auth Error")


if __name__ == '__main__':
    unittest.main()
