"""
اختبارات شاملة لنموذج Account
Comprehensive tests for Account model
"""

import unittest
from datetime import datetime
from decimal import Decimal

from src.models.account import Account


class TestAccountCreation(unittest.TestCase):
    """اختبارات إنشاء حساب"""

    def test_account_creation_valid(self):
        """إنشاء حساب صحيح"""
        account = Account(account_code="1001", account_name="النقد بالصندوق", account_type="Asset")
        self.assertEqual(account.account_code, "1001")
        self.assertEqual(account.account_name, "النقد بالصندوق")
        self.assertEqual(account.account_type, "Asset")
        self.assertEqual(account.normal_side, "DEBIT")
        self.assertTrue(account.is_active)
        self.assertFalse(account.is_locked)

    def test_account_creation_missing_code(self):
        """إنشاء حساب بدون رمز"""
        with self.assertRaises(ValueError) as ctx:
            Account(account_code="", account_name="اختبار", account_type="Asset")
        self.assertIn("رمز الحساب", str(ctx.exception))

    def test_account_creation_missing_name(self):
        """إنشاء حساب بدون اسم"""
        with self.assertRaises(ValueError) as ctx:
            Account(account_code="1001", account_name="", account_type="Asset")
        self.assertIn("اسم الحساب", str(ctx.exception))

    def test_account_creation_invalid_type(self):
        """إنشاء حساب بنوع غير صحيح"""
        with self.assertRaises(ValueError) as ctx:
            Account(account_code="1001", account_name="حساب", account_type="InvalidType")
        self.assertIn("نوع حساب غير صحيح", str(ctx.exception))

    def test_account_creation_all_types(self):
        """إنشاء حسابات لكل الأنواع"""
        types = ["Asset", "Liability", "Equity", "Revenue", "Expense"]
        for acc_type in types:
            account = Account(account_code="1000", account_name="اختبار", account_type=acc_type)
            self.assertEqual(account.account_type, acc_type)


class TestAccountProperties(unittest.TestCase):
    """اختبارات خصائص الحساب"""

    def test_get_display_code(self):
        """الحصول على رمز الحساب المنسق"""
        account = Account(account_code="2001", account_name="حسابات دائنة", account_type="Asset")
        expected = "2001 - حسابات دائنة"
        self.assertEqual(account.get_display_code(), expected)

    def test_is_debit_account_true(self):
        """فحص حساب مدين"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            normal_side="DEBIT",
        )
        self.assertTrue(account.is_debit_account())
        self.assertFalse(account.is_credit_account())

    def test_is_credit_account_true(self):
        """فحص حساب دائن"""
        account = Account(
            account_code="2001",
            account_name="دائنون",
            account_type="Liability",
            normal_side="CREDIT",
        )
        self.assertTrue(account.is_credit_account())
        self.assertFalse(account.is_debit_account())

    def test_is_asset_account(self):
        """فحص حساب أصول"""
        account = Account(account_code="1001", account_name="نقد", account_type="Asset")
        self.assertTrue(account.is_asset_account())
        self.assertFalse(account.is_liability_account())

    def test_is_liability_account(self):
        """فحص حساب التزامات"""
        account = Account(account_code="2001", account_name="دائنون", account_type="Liability")
        self.assertTrue(account.is_liability_account())
        self.assertFalse(account.is_asset_account())

    def test_is_equity_account(self):
        """فحص حساب حقوق الملكية"""
        account = Account(account_code="3001", account_name="رأس المال", account_type="Equity")
        self.assertTrue(account.is_equity_account())

    def test_is_revenue_account(self):
        """فحص حساب الإيرادات"""
        account = Account(account_code="4001", account_name="مبيعات", account_type="Revenue")
        self.assertTrue(account.is_revenue_account())

    def test_is_expense_account(self):
        """فحص حساب المصروفات"""
        account = Account(account_code="5001", account_name="مصروفات الكهرباء", account_type="Expense")
        self.assertTrue(account.is_expense_account())


class TestAccountBalance(unittest.TestCase):
    """اختبارات رصيد الحساب"""

    def test_balance_initialization(self):
        """تهيئة الرصيد"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            opening_balance=Decimal("1000.00"),
            current_balance=Decimal("1500.00"),
        )
        self.assertEqual(account.opening_balance, Decimal("1000.00"))
        self.assertEqual(account.current_balance, Decimal("1500.00"))

    def test_balance_zero(self):
        """رصيد صفر"""
        account = Account(account_code="1001", account_name="نقد", account_type="Asset")
        self.assertEqual(account.opening_balance, Decimal("0.00"))
        self.assertEqual(account.current_balance, Decimal("0.00"))

    def test_balance_string_conversion(self):
        """تحويل الرصيد من string"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            opening_balance=Decimal("5000.50"),
            current_balance=Decimal("6000.75"),
        )
        self.assertEqual(account.opening_balance, Decimal("5000.50"))
        self.assertEqual(account.current_balance, Decimal("6000.75"))

    def test_balance_negative(self):
        """رصيد سالب (محتمل في بعض الحسابات)"""
        account = Account(
            account_code="2001",
            account_name="دائنون",
            account_type="Liability",
            current_balance=Decimal("-500.00"),
        )
        self.assertEqual(account.current_balance, Decimal("-500.00"))


class TestAccountState(unittest.TestCase):
    """اختبارات حالة الحساب"""

    def test_account_active(self):
        """حساب نشط"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            is_active=True,
        )
        self.assertTrue(account.is_active)
        self.assertFalse(account.is_locked)

    def test_account_inactive(self):
        """حساب غير نشط"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            is_active=False,
        )
        self.assertFalse(account.is_active)

    def test_account_locked(self):
        """حساب مقفل"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            is_locked=True,
        )
        self.assertTrue(account.is_locked)

    def test_account_header(self):
        """حساب رئيسي"""
        account = Account(
            account_code="1000",
            account_name="الأصول",
            account_type="Asset",
            is_header=True,
        )
        self.assertTrue(account.is_header)

    def test_account_with_parent(self):
        """حساب فرعي مع حساب أب"""
        account = Account(
            account_code="1001",
            account_name="نقد بالصندوق",
            account_type="Asset",
            parent_account_id=1000,
        )
        self.assertEqual(account.parent_account_id, 1000)


class TestAccountHierarchy(unittest.TestCase):
    """اختبارات التسلسل الهرمي للحسابات"""

    def test_main_account_no_parent(self):
        """حساب رئيسي بدون حساب أب"""
        account = Account(
            account_code="1000",
            account_name="الأصول",
            account_type="Asset",
            is_header=True,
            parent_account_id=None,
        )
        self.assertIsNone(account.parent_account_id)

    def test_sub_account_with_parent(self):
        """حساب فرعي مع حساب أب"""
        account = Account(
            account_code="1001",
            account_name="نقد بالصندوق",
            account_type="Asset",
            parent_account_id=1000,
        )
        self.assertIsNotNone(account.parent_account_id)
        self.assertEqual(account.parent_account_id, 1000)


class TestAccountTimestamps(unittest.TestCase):
    """اختبارات الطوابع الزمنية"""

    def test_timestamps_none(self):
        """الطوابع الزمنية None"""
        account = Account(account_code="1001", account_name="نقد", account_type="Asset")
        self.assertIsNone(account.created_at)
        self.assertIsNone(account.updated_at)

    def test_timestamps_set(self):
        """الطوابع الزمنية محددة"""
        now = datetime.now()
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            created_at=now,
            updated_at=now,
        )
        self.assertEqual(account.created_at, now)
        self.assertEqual(account.updated_at, now)


class TestAccountAttributes(unittest.TestCase):
    """اختبارات السمات الأخرى"""

    def test_account_with_description(self):
        """حساب مع وصف"""
        description = "حساب النقد في الصندوق الرئيسي"
        account = Account(
            account_code="1001",
            account_name="النقد بالصندوق",
            account_type="Asset",
            description=description,
        )
        self.assertEqual(account.description, description)

    def test_account_with_subtype(self):
        """حساب مع نوع فرعي"""
        account = Account(
            account_code="1001",
            account_name="النقد بالصندوق",
            account_type="Asset",
            sub_type="Current Asset",
        )
        self.assertEqual(account.sub_type, "Current Asset")

    def test_account_with_id(self):
        """حساب مع معرف"""
        account = Account(
            id=123,
            account_code="1001",
            account_name="النقد بالصندوق",
            account_type="Asset",
        )
        self.assertEqual(account.id, 123)


class TestAccountEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_account_very_large_balance(self):
        """حساب برصيد كبير جداً"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            current_balance=Decimal("999999999999.99"),
        )
        self.assertGreater(account.current_balance, Decimal("0"))

    def test_account_decimal_precision(self):
        """دقة Decimal للأرصدة"""
        account = Account(
            account_code="1001",
            account_name="نقد",
            account_type="Asset",
            current_balance=Decimal("1234.5678"),
        )
        self.assertEqual(account.current_balance, Decimal("1234.5678"))

    def test_account_code_special_chars(self):
        """رمز حساب برموز خاصة"""
        account = Account(account_code="1001-A", account_name="نقد", account_type="Asset")
        self.assertEqual(account.account_code, "1001-A")

    def test_account_name_long(self):
        """اسم حساب طويل"""
        long_name = "حساب النقد والعملات بأنواعها المختلفة في الفرع الرئيسي"
        account = Account(account_code="1001", account_name=long_name, account_type="Asset")
        self.assertEqual(account.account_name, long_name)


if __name__ == "__main__":
    unittest.main()
