"""
اختبارات شاملة لنموذج Supplier
Comprehensive tests for Supplier model
"""

import unittest
from datetime import datetime, date
from decimal import Decimal
from src.models.supplier import Supplier, SupplierManager


class DummyResult:
    def __init__(self, rowcount=0, lastrowid=None):
        self.rowcount = rowcount
        self.lastrowid = lastrowid


class DummyDB:
    def __init__(self):
        self.calls = []
        self.fetch_one_result = None
        self.fetch_all_result = None
        self.execute_result = None

    def execute_query(self, query, params=()):
        self.calls.append(("exec", query, params))
        return self.execute_result

    def fetch_one(self, query, params=()):
        self.calls.append(("one", query, params))
        return self.fetch_one_result

    def fetch_all(self, query, params=()):
        self.calls.append(("all", query, params))
        return self.fetch_all_result


class DummyLogger:
    def __init__(self):
        self.messages = []
    def info(self, m):
        self.messages.append(("info", m))
    def warning(self, m):
        self.messages.append(("warning", m))
    def error(self, m):
        self.messages.append(("error", m))
    def debug(self, m):
        self.messages.append(("debug", m))


class TestSupplierCreation(unittest.TestCase):
    """اختبارات إنشاء المورد"""

    def test_supplier_basic_creation(self):
        """إنشاء مورد أساسي"""
        supplier = Supplier(
            name="الشركة الأولى",
            name_en="First Company"
        )
        self.assertEqual(supplier.name, "الشركة الأولى")
        self.assertEqual(supplier.name_en, "First Company")

    def test_supplier_with_contact_info(self):
        """مورد مع معلومات التواصل"""
        supplier = Supplier(
            name="الشركة الأولى",
            contact_person="أحمد",
            phone="0661234567",
            email="supplier@example.com"
        )
        self.assertEqual(supplier.contact_person, "أحمد")
        self.assertEqual(supplier.phone, "0661234567")

    def test_supplier_with_addresses(self):
        """مورد مع عناوين"""
        supplier = Supplier(
            name="الشركة الأولى",
            address="شارع النيل",
            city="الجزائر",
            country="الجزائر"
        )
        self.assertEqual(supplier.address, "شارع النيل")
        self.assertEqual(supplier.city, "الجزائر")

    def test_supplier_with_tax_info(self):
        """مورد مع معلومات ضريبية"""
        supplier = Supplier(
            name="الشركة الأولى",
            tax_number="123456789",
            commercial_register="ABC123"
        )
        self.assertEqual(supplier.tax_number, "123456789")
        self.assertEqual(supplier.commercial_register, "ABC123")

    def test_supplier_payment_terms_default(self):
        """شروط الدفع الافتراضية"""
        supplier = Supplier(name="الشركة الأولى")
        self.assertEqual(supplier.payment_terms, "نقدي")

    def test_supplier_credit_limit(self):
        """حد الائتمان للمورد"""
        supplier = Supplier(
            name="الشركة الأولى",
            credit_limit=Decimal("10000.00")
        )
        self.assertEqual(supplier.credit_limit, Decimal("10000.00"))

    def test_supplier_current_balance(self):
        """الرصيد الحالي للمورد"""
        supplier = Supplier(
            name="الشركة الأولى",
            current_balance=Decimal("5000.00")
        )
        self.assertEqual(supplier.current_balance, Decimal("5000.00"))


class TestSupplierProperties(unittest.TestCase):
    """اختبارات خصائص المورد"""

    def test_supplier_available_credit(self):
        """الائتمان المتاح"""
        supplier = Supplier(
            name="الشركة الأولى",
            credit_limit=Decimal("10000.00"),
            current_balance=Decimal("3000.00")
        )
        self.assertEqual(supplier.available_credit, Decimal("7000.00"))

    def test_supplier_is_credit_exceeded_false(self):
        """لم يتم تجاوز حد الائتمان"""
        supplier = Supplier(
            name="الشركة الأولى",
            credit_limit=Decimal("10000.00"),
            current_balance=Decimal("5000.00")
        )
        self.assertFalse(supplier.is_credit_exceeded)

    def test_supplier_is_credit_exceeded_true(self):
        """تم تجاوز حد الائتمان"""
        supplier = Supplier(
            name="الشركة الأولى",
            credit_limit=Decimal("10000.00"),
            current_balance=Decimal("15000.00")
        )
        self.assertTrue(supplier.is_credit_exceeded)

    def test_supplier_full_address(self):
        """العنوان الكامل"""
        supplier = Supplier(
            name="الشركة الأولى",
            address="شارع النيل",
            city="الجزائر",
            country="الجزائر"
        )
        self.assertIn("شارع النيل", supplier.full_address)
        self.assertIn("الجزائر", supplier.full_address)

    def test_supplier_display_name_with_contact(self):
        """الاسم للعرض مع المتصل"""
        supplier = Supplier(
            name="الشركة الأولى",
            contact_person="أحمد"
        )
        self.assertIn("الشركة الأولى", supplier.display_name)
        self.assertIn("أحمد", supplier.display_name)

    def test_supplier_display_name_without_contact(self):
        """الاسم للعرض بدون متصل"""
        supplier = Supplier(name="الشركة الأولى")
        self.assertEqual(supplier.display_name, "الشركة الأولى")


class TestSupplierSerialization(unittest.TestCase):
    """اختبارات تسلسل المورد"""

    def test_supplier_to_dict(self):
        """تحويل المورد إلى قاموس"""
        supplier = Supplier(
            id=1,
            name="الشركة الأولى",
            name_en="First Company",
            contact_person="أحمد",
            phone="0661234567",
            email="supplier@example.com",
            credit_limit=Decimal("10000.00"),
            current_balance=Decimal("5000.00")
        )
        
        data = supplier.to_dict()
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], "الشركة الأولى")
        self.assertEqual(data['contact_person'], "أحمد")


class TestSupplierPurchaseTracking(unittest.TestCase):
    """اختبارات تتبع الشراء للمورد"""

    def test_supplier_purchase_count(self):
        """عدد المشتريات"""
        supplier = Supplier(
            name="الشركة الأولى",
            purchases_count=5
        )
        self.assertEqual(supplier.purchases_count, 5)

    def test_supplier_total_purchases(self):
        """إجمالي المشتريات"""
        supplier = Supplier(
            name="الشركة الأولى",
            total_purchases=Decimal("50000.00")
        )
        self.assertEqual(supplier.total_purchases, Decimal("50000.00"))

    def test_supplier_last_purchase_date(self):
        """تاريخ آخر شراء"""
        today = date.today()
        supplier = Supplier(
            name="الشركة الأولى",
            last_purchase_date=today
        )
        self.assertEqual(supplier.last_purchase_date, today)


class TestSupplierValidation(unittest.TestCase):
    """اختبارات التحقق من صحة المورد"""

    def test_supplier_active_status(self):
        """حالة المورد النشط"""
        supplier = Supplier(
            name="الشركة الأولى",
            is_active=True
        )
        self.assertTrue(supplier.is_active)

    def test_supplier_inactive_status(self):
        """حالة المورد غير النشط"""
        supplier = Supplier(
            name="الشركة الأولى",
            is_active=False
        )
        self.assertFalse(supplier.is_active)

    def test_supplier_with_notes(self):
        """مورد مع ملاحظات"""
        supplier = Supplier(
            name="الشركة الأولى",
            notes="مورد موثوق وسريع التسليم"
        )
        self.assertIn("موثوق", supplier.notes)

    def test_supplier_decimal_conversion(self):
        """تحويل أرقام إلى Decimal"""
        supplier = Supplier(
            name="الشركة الأولى",
            credit_limit=10000,
            current_balance="5000"
        )
        self.assertIsInstance(supplier.credit_limit, Decimal)
        self.assertIsInstance(supplier.current_balance, Decimal)


class TestSupplierEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_supplier_zero_credit_limit(self):
        """مورد بدون ائتمان"""
        supplier = Supplier(
            name="الشركة الأولى",
            credit_limit=Decimal("0.00")
        )
        self.assertEqual(supplier.available_credit, Decimal("0.00"))

    def test_supplier_empty_address(self):
        """مورد بدون عنوان"""
        supplier = Supplier(
            name="الشركة الأولى",
            address=None,
            city=None,
            country=None
        )
        self.assertEqual(supplier.full_address, "")

    def test_supplier_multiple_phone_numbers(self):
        """مورد برقمي هاتف"""
        supplier = Supplier(
            name="الشركة الأولى",
            phone="0661234567",
            phone2="0671234567"
        )
        self.assertEqual(supplier.phone, "0661234567")
        self.assertEqual(supplier.phone2, "0671234567")

    def test_supplier_with_website(self):
        """مورد مع موقع ويب"""
        supplier = Supplier(
            name="الشركة الأولى",
            website="https://example.com"
        )
        self.assertIn("https://", supplier.website)


class TestSupplierManagerBasics(unittest.TestCase):
    def setUp(self):
        self.db = DummyDB()
        self.logger = DummyLogger()
        self.mgr = SupplierManager(self.db, self.logger)

    def test_add_company_filter_with_where(self):
        q, params = self.mgr._add_company_filter("SELECT * FROM s WHERE id=?", [1], company_id=9)
        self.assertIn("company_id = ?", q)
        self.assertEqual(params[-1], 9)

    def test_add_company_filter_without_where(self):
        q, params = self.mgr._add_company_filter("SELECT * FROM s", [], company_id=3)
        self.assertIn("WHERE company_id = ?", q)
        self.assertEqual(params[-1], 3)

    def test_counts_helpers(self):
        self.db.fetch_one_result = (7,)
        self.assertEqual(self.mgr.get_supplier_purchases_count(1), 7)
        self.db.fetch_one_result = None
        self.assertEqual(self.mgr.get_supplier_purchases_count(1), 0)
        self.db.fetch_one_result = (11,)
        self.assertEqual(self.mgr.get_supplier_products_count(2), 11)
        self.db.fetch_one_result = None
        self.assertEqual(self.mgr.get_supplier_products_count(2), 0)

    def test_purchases_history(self):
        self.db.fetch_all_result = [
            ("INV-1", date(2025,5,1), Decimal('100.0'), Decimal('50.0'), Decimal('50.0'), "جزئي"),
            ("INV-2", date(2025,5,2), Decimal('200.0'), Decimal('200.0'), Decimal('0.0'), "مدفوع")
        ]
        data = self.mgr.get_supplier_purchases_history(5, limit=2)
        self.assertEqual(data[0]['invoice_number'], "INV-1")
        self.assertEqual(data[1]['remaining_amount'], 0.0)

    def test_suppliers_report(self):
        self.db.fetch_one_result = (5, 4, 2, 1, Decimal('300.5'), Decimal('120.25'))
        rpt = self.mgr.get_suppliers_report()
        self.assertEqual(rpt['active_suppliers'], 4)
        self.assertEqual(rpt['total_outstanding_balance'], 300.5)

    def test_row_to_supplier_invalid_short(self):
        self.assertIsNone(self.mgr._row_to_supplier([1, "X"]))

    def test_row_to_supplier_valid(self):
        row = [
            10, "اسم", "سليم", "0555", "m@x.com", "A", "TX", 1,
            datetime.now().isoformat(), datetime.now().isoformat(),
            "0666", 100, 15, date.today().isoformat(), 500, 20
        ]
        s = self.mgr._row_to_supplier(row)
        self.assertIsNotNone(s)
        self.assertEqual(s.id, 10)
        self.assertEqual(s.credit_limit, Decimal('100'))

    def test_delete_supplier_blocks(self):
        self.mgr.get_supplier_purchases_count = lambda sid: 1
        self.assertFalse(self.mgr.delete_supplier(1))
        self.mgr.get_supplier_purchases_count = lambda sid: 0
        self.mgr.get_supplier_products_count = lambda sid: 1
        self.assertFalse(self.mgr.delete_supplier(1))

    def test_delete_supplier_soft_and_hard(self):
        self.mgr.get_supplier_purchases_count = lambda sid: 0
        self.mgr.get_supplier_products_count = lambda sid: 0
        self.db.execute_result = DummyResult(rowcount=1)
        self.assertTrue(self.mgr.delete_supplier(1, soft_delete=True))
        self.db.execute_result = DummyResult(rowcount=1)
        self.assertTrue(self.mgr.delete_supplier(2, soft_delete=False))

    def test_update_supplier_balance(self):
        self.mgr.get_supplier_by_id = lambda sid: Supplier(id=sid, current_balance=Decimal('10'))
        self.db.execute_result = DummyResult(rowcount=1)
        self.assertTrue(self.mgr.update_supplier_balance(3, Decimal('5.5')))


if __name__ == '__main__':
    unittest.main()



