import sys
from datetime import datetime, date
from decimal import Decimal

import pytest

from src.models.customer import Customer, CustomerManager


class DummyLogger:
    def __init__(self):
        self.logs = []

    def info(self, msg):
        self.logs.append(("info", msg))

    def debug(self, msg):
        self.logs.append(("debug", msg))

    def warning(self, msg):
        self.logs.append(("warning", msg))

    def error(self, msg):
        self.logs.append(("error", msg))


class DummyDB:
    def __init__(self):
        self.columns = [
            'id', 'name', 'name_en', 'phone', 'phone2', 'email', 'address',
            'city', 'country', 'tax_number', 'credit_limit', 'current_balance',
            'notes', 'is_active', 'created_at', 'updated_at'
        ]
        self.next_id = 1
        self.last_insert_query = None
        self.last_insert_params = None
        self.last_update_query = None
        self.last_update_params = None
        self.one_row = None
        self.rows = []
        self.sales_data = {}
        self.non_query_result = 1

    def fetch_all(self, query, params=()):
        if isinstance(query, str) and query.strip().upper().startswith("PRAGMA TABLE_INFO(CUSTOMERS)"):
            # Return list of tuples, index 1 must be column name
            return [(i, name) for i, name in enumerate(self.columns)]
        # For generic SELECTs used in searches/lists
        return list(self.rows)

    def fetch_one(self, query, params=()):
        if isinstance(query, str) and "FROM sales" in query:
            # params expected: (customer_id,)
            cid = params[0]
            return self.sales_data.get(cid, (None, 0, 0))
        return self.one_row

    def execute_insert(self, query, params=()):
        self.last_insert_query = query
        self.last_insert_params = params
        return self.next_id

    def execute_non_query(self, query, params=()):
        self.last_update_query = query
        self.last_update_params = params
        return self.non_query_result


def test_customer_dataclass_properties_and_to_dict():
    now = datetime(2024, 5, 20, 12, 30, 0)
    cust = Customer(
        id=10,
        name="عميل تجريبي",
        name_en="Demo Customer",
        phone="0555000000",
        phone2="0666000000",
        email="demo@example.com",
        address="شارع 1",
        city="الجزائر",
        country="الجزائر",
        tax_number="TAX-123",
        credit_limit=1000,  # int -> Decimal via post_init
        current_balance="250.5",  # str -> Decimal
        notes="عميل نشط",
        is_active=True,
        created_at=now,
        updated_at=now,
        last_purchase_date=date(2024, 5, 1),
        total_purchases=200.75,  # float -> Decimal
        purchases_count=5,
    )

    # Computed props
    assert cust.available_credit == Decimal('749.5')
    assert cust.is_credit_exceeded is False
    assert cust.full_address == "شارع 1, الجزائر, الجزائر"

    d = cust.to_dict()
    assert d["id"] == 10
    assert d["name_en"] == "Demo Customer"
    assert d["phone2"] == "0666000000"
    assert d["credit_limit"] == 1000.0
    assert d["current_balance"] == 250.5
    assert d["total_purchases"] == 200.75
    assert d["available_credit"] == 749.5
    assert d["is_credit_exceeded"] is False
    assert d["full_address"] == "شارع 1, الجزائر, الجزائر"
    assert d["created_at"].startswith("2024-05-20T12:30:00")
    assert d["last_purchase_date"] == "2024-05-01"


def test_get_available_columns_cached():
    db = DummyDB()
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    cols_first = mgr._get_available_columns()
    assert set(cols_first) == set(db.columns)

    # Mutate DB columns to ensure caching works; manager should still return old set
    db.columns = ['id', 'name']
    cols_second = mgr._get_available_columns()
    assert set(cols_second) != set(db.columns)
    assert set(cols_second)  # not empty


def test_create_customer_with_optional_columns_and_webhook_ignored_on_import_error(monkeypatch):
    db = DummyDB()
    db.next_id = 42
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    # Force import error for webhook service to exercise try/except path
    def fake_import(*args, **kwargs):
        raise ImportError("no webhook service")

    # Ensure the module path used inside create_customer fails to import
    if 'src.services.webhook_service' in sys.modules:
        del sys.modules['src.services.webhook_service']

    cust = Customer(name="Zed", phone="123", email="z@x", address="A1", credit_limit=200, current_balance=50)
    new_id = mgr.create_customer(cust)
    assert new_id == 42

    # Base columns (9) + all 6 optionals present in DummyDB.columns => 15 params
    assert db.last_insert_params is not None
    assert len(db.last_insert_params) == 15


def test_create_customer_when_pragma_fails_uses_base_columns(monkeypatch):
    db = DummyDB()
    logger = DummyLogger()

    # Make PRAGMA fail
    def fail_fetch_all(query, params=()):
        if isinstance(query, str) and query.strip().upper().startswith("PRAGMA TABLE_INFO(CUSTOMERS)"):
            raise RuntimeError("pragma failed")
        return []

    db.fetch_all = fail_fetch_all  # type: ignore
    db.next_id = 7
    mgr = CustomerManager(db, logger)

    cust = Customer(name="BaseOnly", phone="000", email="b@x", address="B", credit_limit=100, current_balance=0)
    new_id = mgr.create_customer(cust)
    assert new_id == 7
    # Only base 9 params expected
    assert db.last_insert_params is not None
    assert len(db.last_insert_params) == 9


def test_get_customer_by_id_with_sales_enrichment():
    db = DummyDB()
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    # Available columns include a subset; manager will select those
    db.columns = ['id', 'name', 'phone', 'email', 'address', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']

    # Row returned for the SELECT (order must match selected columns)
    created_at = datetime(2024, 1, 2, 10, 0, 0)
    db.one_row = (
        5, "عميل أ", "0555", "a@ex", "Z St",
        500.0, 125.0, 1, created_at, created_at
    )

    # Sales enrichment for customer_id 5
    db.sales_data[5] = ("2024-12-30", 1000.5, 3)

    cust = mgr.get_customer_by_id(5)
    assert isinstance(cust, Customer)
    assert cust.id == 5
    assert cust.name == "عميل أ"
    assert cust.available_credit == Decimal('375.0')
    assert cust.last_purchase_date == date(2024, 12, 30)
    assert cust.total_purchases == Decimal('1000.5')
    assert cust.purchases_count == 3


def test_get_customer_by_phone_with_and_without_phone2():
    db = DummyDB()
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    # Case 1: phone2 present
    db.columns = ['id', 'name', 'phone', 'phone2', 'email', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']
    db.one_row = (7, 'عميل هاتف', '0555', '0666', 'p@e', 100.0, 10.0, 1, datetime.now(), datetime.now())
    cust = mgr.get_customer_by_phone('0666')
    assert cust is not None and cust.id == 7

    # Case 2: phone2 absent
    db.columns = ['id', 'name', 'phone', 'email', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']
    db.one_row = (8, 'عميل هاتف 2', '0999', 'q@e', 200.0, 0.0, 1, datetime.now(), datetime.now())
    cust2 = mgr.get_customer_by_phone('0999')
    assert cust2 is not None and cust2.id == 8


def test_update_and_delete_customer():
    db = DummyDB()
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    # update with optionals present
    db.columns = ['id', 'name', 'name_en', 'phone', 'phone2', 'email', 'address', 'city', 'country', 'tax_number', 'credit_limit', 'current_balance', 'notes', 'is_active', 'created_at', 'updated_at']
    c = Customer(id=11, name='X', phone='1', email='e', address='a', credit_limit=300, current_balance=10,
                 name_en='XE', phone2='2', city='c', country='dz', tax_number='tx', notes='n', is_active=True)
    db.non_query_result = 1
    ok = mgr.update_customer(c)
    assert ok is True
    assert db.last_update_params is not None
    # ends with id
    assert db.last_update_params[-1] == 11

    # delete (soft)
    db.non_query_result = 1
    deleted = mgr.delete_customer(11)
    assert deleted is True


def test_get_customers_report():
    db = DummyDB()
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    # Return a single row for aggregate report
    db.one_row = (20, 18, 4, 2, 1234.5, 250.0)
    report = mgr.get_customers_report()
    assert report == {
        'total_customers': 20,
        'active_customers': 18,
        'customers_with_balance': 4,
        'customers_over_limit': 2,
        'total_outstanding_balance': 1234.5,
        'avg_credit_limit': 250.0,
    }


def test_add_company_filter_handles_existing_and_missing_where(monkeypatch):
    db = DummyDB()
    mgr = CustomerManager(db)

    # Explicit company_id with existing WHERE
    q1, p1 = mgr._add_company_filter("SELECT * FROM t WHERE is_active = 1", ["x"], company_id=5)
    assert "company_id = ?" in q1
    assert p1[-1] == 5

    # Implicit company_id via _get_company_id when no WHERE exists
    monkeypatch.setattr(mgr, "_get_company_id", lambda: 9)
    q2, p2 = mgr._add_company_filter("SELECT * FROM t", [])
    assert "WHERE company_id = ?" in q2
    assert p2 == [9]


def test_get_select_columns_respects_available_order():
    db = DummyDB()
    db.columns = ['id', 'name', 'phone', 'email', 'credit_limit', 'current_balance', 'is_active', 'updated_at']
    mgr = CustomerManager(db)

    cols = mgr._get_select_columns()
    assert cols == ['id', 'name', 'phone', 'email', 'credit_limit', 'current_balance', 'is_active', 'updated_at']


def test_search_customers_returns_customers_with_defaults():
    db = DummyDB()
    logger = DummyLogger()
    mgr = CustomerManager(db, logger)

    db.columns = ['id', 'name', 'phone', 'email', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']
    created = datetime(2024, 5, 1, 10, 0, 0)
    db.rows = [
        (1, 'بحث 1', '0100', 'a@e', 100.0, 20.0, 1, created, created),
        (2, 'بحث 2', '0200', 'b@e', 200.0, 0.0, 1, created, created),
    ]

    customers = mgr.search_customers(active_only=False)
    assert len(customers) == 2
    assert customers[0].id == 1
    assert customers[0].last_purchase_date is None
    assert customers[0].total_purchases == Decimal('0')
    assert customers[1].purchases_count == 0


def test_get_all_customers_delegates_to_search(monkeypatch):
    db = DummyDB()
    mgr = CustomerManager(db)

    called = {}

    def fake_search(active_only=True):
        called['active_only'] = active_only
        return ['sentinel']

    monkeypatch.setattr(mgr, 'search_customers', fake_search)

    result = mgr.get_all_customers(active_only=False)
    assert result == ['sentinel']
    assert called['active_only'] is False


def test_get_customers_with_balance_maps_rows():
    db = DummyDB()
    mgr = CustomerManager(db)
    db.columns = ['id', 'name', 'phone', 'email', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']
    when = datetime(2024, 3, 3, 3, 3, 3)
    db.rows = [(3, 'مدين', '0300', 'c@e', 300.0, 120.0, 1, when, when)]

    customers = mgr.get_customers_with_balance()
    assert len(customers) == 1
    assert customers[0].available_credit == Decimal('180.0')
    assert customers[0].is_active is True


def test_get_top_customers_enriches_and_sorts():
    db = DummyDB()
    mgr = CustomerManager(db)
    db.columns = ['id', 'name', 'phone', 'email', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']
    ts = datetime(2024, 4, 4, 4, 4, 4)
    db.rows = [
        (1, 'TopA', '0111', 'a@e', 500.0, 50.0, 1, ts, ts),
        (2, 'TopB', '0222', 'b@e', 600.0, 10.0, 1, ts, ts),
    ]
    db.sales_data[1] = (date(2024, 1, 1), 1000.0, 5)
    db.sales_data[2] = (date(2024, 1, 2), 500.0, 2)

    customers = mgr.get_top_customers(limit=2)
    assert [c.id for c in customers] == [1, 2]
    assert customers[0].total_purchases == Decimal('1000.0')
    assert customers[1].total_purchases == Decimal('500.0')


def test_map_row_to_dict_fills_missing_keys():
    db = DummyDB()
    mgr = CustomerManager(db)
    row_dict = {'id': 10, 'name': 'Partial'}

    mapped = mgr._map_row_to_dict(row_dict)
    assert mapped['id'] == 10
    assert mapped['name'] == 'Partial'
    # Missing fields should be present with None
    assert 'phone2' in mapped and mapped['phone2'] is None
    assert 'updated_at' in mapped


def test_dict_to_object_and_row_to_customer_parsing():
    db = DummyDB()
    mgr = CustomerManager(db)
    data = {
        'id': 21,
        'name': 'Parser',
        'credit_limit': '150.5',
        'current_balance': '10.5',
        'is_active': 1,
        'created_at': '2024-05-01T12:00:00',
        'updated_at': '2024-05-02T12:00:00',
        'last_purchase_date': '2024-05-03',
        'total_purchases': '75.25',
        'purchases_count': '4'
    }

    obj = mgr._dict_to_object(data)
    assert obj.id == 21
    assert obj.created_at == datetime(2024, 5, 1, 12, 0, 0)
    assert obj.last_purchase_date == date(2024, 5, 3)
    assert obj.credit_limit == Decimal('150.5')
    assert obj.total_purchases == Decimal('75.25')

    # Tuple input for _row_to_customer should map by DB_COLUMNS
    ts = datetime(2024, 6, 1, 1, 1, 1)
    row = (4, 'Row Cust', None, '010', None, 'row@e', 'addr', 'cty', 'dz', 'tx', 100.0, 20.0, None, 1, ts, ts)
    obj2 = mgr._row_to_customer(row)
    assert obj2.id == 4
    assert obj2.phone == '010'
    assert obj2.credit_limit == Decimal('100.0')


def test_enrich_with_sales_data_handles_errors(monkeypatch):
    db = DummyDB()
    mgr = CustomerManager(db)

    def fail_fetch_one(query, params=()):
        raise RuntimeError("db down")

    monkeypatch.setattr(db, 'fetch_one', fail_fetch_one)

    data = {}
    mgr._enrich_with_sales_data(99, data)
    assert data['last_purchase_date'] is None
    assert data['total_purchases'] == 0
    assert data['purchases_count'] == 0
"""
اختبارات شاملة لنموذج Customer
Comprehensive tests for Customer model
"""

import unittest
from decimal import Decimal
from datetime import datetime, date
from src.models.customer import Customer


class TestCustomerDataclass(unittest.TestCase):
    """اختبارات Customer dataclass"""

    def test_customer_creation_default(self):
        """إنشاء عميل بقيم افتراضية"""
        customer = Customer()
        self.assertIsNone(customer.id)
        self.assertEqual(customer.name, "")
        self.assertEqual(customer.country, "الجزائر")
        self.assertEqual(customer.credit_limit, Decimal('0.00'))
        self.assertEqual(customer.current_balance, Decimal('0.00'))
        self.assertTrue(customer.is_active)

    def test_customer_creation_with_values(self):
        """إنشاء عميل بقيم محددة"""
        customer = Customer(
            id=1,
            name="أحمد محمد",
            phone="0123456789",
            email="ahmed@example.com",
            credit_limit=Decimal('10000.00'),
            current_balance=Decimal('5000.00')
        )
        self.assertEqual(customer.id, 1)
        self.assertEqual(customer.name, "أحمد محمد")
        self.assertEqual(customer.phone, "0123456789")
        self.assertEqual(customer.email, "ahmed@example.com")
        self.assertEqual(customer.credit_limit, Decimal('10000.00'))
        self.assertEqual(customer.current_balance, Decimal('5000.00'))

    def test_credit_limit_conversion(self):
        """تحويل حد الائتمان إلى Decimal"""
        customer = Customer(credit_limit=5000, current_balance=2500)
        self.assertIsInstance(customer.credit_limit, Decimal)
        self.assertIsInstance(customer.current_balance, Decimal)
        self.assertEqual(customer.credit_limit, Decimal('5000'))
        self.assertEqual(customer.current_balance, Decimal('2500'))

    def test_total_purchases_conversion(self):
        """تحويل إجمالي المشتريات"""
        customer = Customer(
            total_purchases=15000.50,
            purchases_count=5
        )
        self.assertIsInstance(customer.total_purchases, Decimal)
        self.assertEqual(customer.total_purchases, Decimal('15000.50'))
        self.assertEqual(customer.purchases_count, 5)


class TestCustomerProperties(unittest.TestCase):
    """اختبارات خصائص العميل المحسوبة"""

    def test_available_credit_normal(self):
        """حساب الائتمان المتاح - حالة عادية"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('3000')
        )
        self.assertEqual(customer.available_credit, Decimal('7000'))

    def test_available_credit_zero(self):
        """حساب الائتمان المتاح - صفر"""
        customer = Customer(
            credit_limit=Decimal('5000'),
            current_balance=Decimal('5000')
        )
        self.assertEqual(customer.available_credit, Decimal('0'))

    def test_available_credit_negative(self):
        """حساب الائتمان المتاح - سالب"""
        customer = Customer(
            credit_limit=Decimal('5000'),
            current_balance=Decimal('6000')
        )
        self.assertEqual(customer.available_credit, Decimal('-1000'))

    def test_is_credit_exceeded_false(self):
        """فحص تجاوز الائتمان - false"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('5000')
        )
        self.assertFalse(customer.is_credit_exceeded)

    def test_is_credit_exceeded_true(self):
        """فحص تجاوز الائتمان - true"""
        customer = Customer(
            credit_limit=Decimal('5000'),
            current_balance=Decimal('6000')
        )
        self.assertTrue(customer.is_credit_exceeded)

    def test_is_credit_exceeded_equal(self):
        """فحص تجاوز الائتمان - متساوي"""
        customer = Customer(
            credit_limit=Decimal('5000'),
            current_balance=Decimal('5000')
        )
        self.assertFalse(customer.is_credit_exceeded)

    def test_full_address_all_parts(self):
        """العنوان الكامل - مع جميع الأجزاء"""
        customer = Customer(
            address="شارع النيل 123",
            city="الجزائر العاصمة",
            country="الجزائر"
        )
        expected = "شارع النيل 123, الجزائر العاصمة, الجزائر"
        self.assertEqual(customer.full_address, expected)

    def test_full_address_partial(self):
        """العنوان الكامل - أجزاء ناقصة"""
        customer = Customer(
            address="شارع النيل 123",
            city="الجزائر العاصمة",
            country=None
        )
        expected = "شارع النيل 123, الجزائر العاصمة"
        self.assertEqual(customer.full_address, expected)

    def test_full_address_empty(self):
        """العنوان الكامل - فارغ"""
        customer = Customer()
        self.assertEqual(customer.full_address, "الجزائر")

    def test_full_address_none_all(self):
        """العنوان الكامل - جميع القيم None"""
        customer = Customer(
            address=None,
            city=None,
            country=None
        )
        self.assertEqual(customer.full_address, "")


class TestCustomerToDict(unittest.TestCase):
    """اختبارات تحويل العميل إلى dict"""

    def test_to_dict_basic(self):
        """تحويل عميل أساسي إلى dict"""
        customer = Customer(
            id=1,
            name="محمد علي",
            phone="0123456789"
        )
        result = customer.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "محمد علي")
        self.assertEqual(result['phone'], "0123456789")

    def test_to_dict_all_fields(self):
        """تحويل عميل كامل إلى dict"""
        now = datetime.now()
        last_purchase = date.today()
        customer = Customer(
            id=5,
            name="فاطمة محمد",
            name_en="Fatima Mohamed",
            phone="0987654321",
            phone2="0111111111",
            email="fatima@example.com",
            address="شارع 5",
            city="وهران",
            country="الجزائر",
            tax_number="TAX123",
            credit_limit=Decimal('20000'),
            current_balance=Decimal('8000'),
            notes="عميل VIP",
            is_active=True,
            created_at=now,
            updated_at=now,
            last_purchase_date=last_purchase,
            total_purchases=Decimal('150000'),
            purchases_count=20
        )
        result = customer.to_dict()
        
        self.assertEqual(result['id'], 5)
        self.assertEqual(result['name'], "فاطمة محمد")
        self.assertEqual(result['name_en'], "Fatima Mohamed")
        self.assertEqual(result['phone'], "0987654321")
        self.assertEqual(result['phone2'], "0111111111")
        self.assertEqual(result['email'], "fatima@example.com")
        self.assertEqual(result['credit_limit'], 20000.0)
        self.assertEqual(result['current_balance'], 8000.0)
        self.assertTrue(result['is_active'])

    def test_to_dict_computed_properties(self):
        """فحص الخصائص المحسوبة في dict"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('4000'),
            purchases_count=15,
            total_purchases=Decimal('85000'),
            last_purchase_date=date.today()
        )
        result = customer.to_dict()
        
        self.assertEqual(result['available_credit'], 6000.0)
        self.assertFalse(result['is_credit_exceeded'])
        self.assertEqual(result['total_purchases'], 85000.0)
        self.assertEqual(result['purchases_count'], 15)


class TestCustomerEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_customer_with_empty_name(self):
        """عميل باسم فارغ"""
        customer = Customer(name="")
        self.assertEqual(customer.name, "")
        self.assertEqual(customer.full_address, "الجزائر")

    def test_customer_with_unicode_names(self):
        """أسماء بالعربية والإنجليزية"""
        customer = Customer(
            name="محمد علي",
            name_en="Mohamed Ali",
            address="شارع 123"
        )
        self.assertEqual(customer.name, "محمد علي")
        self.assertEqual(customer.name_en, "Mohamed Ali")

    def test_customer_with_large_credit(self):
        """ائتمان كبير جداً"""
        customer = Customer(
            credit_limit=Decimal('999999999.99'),
            current_balance=Decimal('100000.00')
        )
        self.assertEqual(
            customer.available_credit,
            Decimal('999899999.99')
        )
        self.assertFalse(customer.is_credit_exceeded)

    def test_customer_with_multiple_phones(self):
        """عميل بهاتفين"""
        customer = Customer(
            phone="0123456789",
            phone2="0987654321"
        )
        self.assertEqual(customer.phone, "0123456789")
        self.assertEqual(customer.phone2, "0987654321")

    def test_customer_inactive(self):
        """عميل غير مفعل"""
        customer = Customer(
            name="عميل غير مفعل",
            is_active=False
        )
        self.assertFalse(customer.is_active)

    def test_customer_with_tax_number(self):
        """عميل برقم ضريبي"""
        customer = Customer(
            tax_number="TN0123456789"
        )
        self.assertEqual(customer.tax_number, "TN0123456789")

    def test_customer_negative_purchases_count(self):
        """عميل برقم مشتريات سالب (حالة حدية)"""
        customer = Customer(purchases_count=-5)
        self.assertEqual(customer.purchases_count, -5)

    def test_customer_with_future_date(self):
        """عميل بتاريخ مستقبلي"""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=30)
        customer = Customer(last_purchase_date=future_date)
        self.assertEqual(customer.last_purchase_date, future_date)


class TestCustomerCredit(unittest.TestCase):
    """اختبارات إدارة الائتمان"""

    def test_credit_utilization_zero(self):
        """استخدام ائتمان صفر"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('0')
        )
        self.assertEqual(customer.available_credit, Decimal('10000'))
        self.assertFalse(customer.is_credit_exceeded)

    def test_credit_utilization_half(self):
        """استخدام نصف الائتمان"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('5000')
        )
        self.assertEqual(customer.available_credit, Decimal('5000'))
        self.assertFalse(customer.is_credit_exceeded)

    def test_credit_utilization_full(self):
        """استخدام كامل الائتمان"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('10000')
        )
        self.assertEqual(customer.available_credit, Decimal('0'))
        self.assertFalse(customer.is_credit_exceeded)

    def test_credit_exceeded_small_amount(self):
        """تجاوز ائتمان صغير"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('10001')
        )
        self.assertTrue(customer.is_credit_exceeded)
        self.assertEqual(customer.available_credit, Decimal('-1'))

    def test_credit_exceeded_large_amount(self):
        """تجاوز ائتمان كبير"""
        customer = Customer(
            credit_limit=Decimal('10000'),
            current_balance=Decimal('15000')
        )
        self.assertTrue(customer.is_credit_exceeded)
        self.assertEqual(customer.available_credit, Decimal('-5000'))


if __name__ == '__main__':
    unittest.main()
