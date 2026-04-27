"""
اختبارات شاملة لنموذج Purchase
Comprehensive tests for Purchase model
"""

import unittest
from datetime import datetime, date, timedelta
from decimal import Decimal

import pytest

from src.models.purchase import (
    Purchase,
    PurchaseItem,
    PurchaseManager,
    PurchaseStatus,
    PaymentStatus,
)


class DummyResult:
    def __init__(self, lastrowid=1, rowcount=1):
        self.lastrowid = lastrowid
        self.rowcount = rowcount


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
        self.one_row = None
        self.rows = []
        self.last_query = None
        self.last_params = None
        self.item_inserts = []
        self.next_lastrowid = 1
        self.rowcount = 1

    def execute_query(self, query, params=()):
        self.last_query = query
        self.last_params = params
        if "INSERT INTO purchase_items" in query:
            self.item_inserts.append(params)
        return DummyResult(lastrowid=self.next_lastrowid, rowcount=self.rowcount)

    def execute_non_query(self, query, params=()):
        self.last_query = query
        self.last_params = params
        return self.rowcount

    def fetch_one(self, query, params=()):
        self.last_query = query
        self.last_params = params
        return self.one_row

    def fetch_all(self, query, params=()):
        self.last_query = query
        self.last_params = params
        return list(self.rows)


class TestPurchaseItemCreation(unittest.TestCase):
    """اختبارات إنشاء عنصر المشترى"""

    def test_purchase_item_basic(self):
        """إنشاء عنصر شراء أساسي"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00")
        )
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "المنتج الأول")
        self.assertEqual(item.quantity_ordered, Decimal("10"))
        self.assertEqual(item.tax_percent, Decimal("15.00"))  # Default tax

    def test_purchase_item_with_discount(self):
        """عنصر شراء مع خصم"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00"),
            discount_percent=Decimal("10.00")
        )
        self.assertEqual(item.discount_percent, Decimal("10.00"))

    def test_purchase_item_with_tax(self):
        """عنصر شراء مع ضريبة"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00"),
            tax_percent=Decimal("15.00")
        )
        self.assertEqual(item.tax_percent, Decimal("15.00"))

    def test_purchase_item_with_batch(self):
        """عنصر شراء مع رقم دفعة"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00"),
            batch_number="BATCH001"
        )
        self.assertEqual(item.batch_number, "BATCH001")

    def test_purchase_item_with_expiry(self):
        """عنصر شراء مع تاريخ انتهاء"""
        expiry = date.today() + timedelta(days=365)
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00"),
            expiry_date=expiry
        )
        self.assertEqual(item.expiry_date, expiry)


class TestPurchaseItemProperties(unittest.TestCase):
    """اختبارات خصائص عنصر المشترى"""

    def test_purchase_item_subtotal(self):
        """الإجمالي الفرعي لعنصر الشراء"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00")
        )
        self.assertEqual(item.subtotal, Decimal("1000.00"))

    def test_purchase_item_pending_quantity(self):
        """الكمية المعلقة"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            quantity_received=Decimal("6"),
            unit_cost=Decimal("100.00")
        )
        self.assertEqual(item.pending_quantity, Decimal("4"))

    def test_purchase_item_is_fully_received_true(self):
        """تم استلام العنصر كاملاً"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            quantity_received=Decimal("10"),
            unit_cost=Decimal("100.00")
        )
        self.assertTrue(item.is_fully_received)

    def test_purchase_item_is_fully_received_false(self):
        """لم يتم استلام العنصر كاملاً"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            quantity_received=Decimal("5"),
            unit_cost=Decimal("100.00")
        )
        self.assertFalse(item.is_fully_received)


class TestPurchaseItemCalculations(unittest.TestCase):
    """اختبارات حسابات عنصر الشراء"""

    def test_purchase_item_calculate_totals(self):
        """حساب مجاميع عنصر الشراء"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00"),
            discount_percent=Decimal("10.00"),
            tax_percent=Decimal("15.00")
        )
        item.calculate_totals()
        
        # subtotal = 10 * 100 = 1000
        # discount = 1000 * 10% = 100
        # net = 1000 - 100 = 900
        # tax = 900 * 15% = 135
        # total = 900 + 135 = 1035
        
        self.assertEqual(item.subtotal, Decimal("1000.00"))
        self.assertEqual(item.discount_amount, Decimal("100.00"))
        self.assertEqual(item.tax_amount, Decimal("135.00"))
        self.assertEqual(item.total_amount, Decimal("1035.00"))


class TestPurchaseCreation(unittest.TestCase):
    """اختبارات إنشاء فاتورة الشراء"""

    def test_purchase_basic_creation(self):
        """إنشاء فاتورة شراء أساسية"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول"
        )
        self.assertEqual(purchase.invoice_number, "INV001")
        self.assertEqual(purchase.supplier_id, 1)
        self.assertEqual(purchase.supplier_name, "المورد الأول")

    def test_purchase_with_items(self):
        """فاتورة شراء مع عناصر"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                unit_cost=Decimal("100.00")
            ),
            PurchaseItem(
                product_id=2,
                product_name="المنتج الثاني",
                quantity_ordered=Decimal("5"),
                unit_cost=Decimal("200.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertEqual(purchase.items_count, 2)
        self.assertEqual(len(purchase.items), 2)

    def test_purchase_with_date(self):
        """فاتورة شراء مع تاريخ"""
        today = date.today()
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            purchase_date=today
        )
        self.assertEqual(purchase.purchase_date, today)

    def test_purchase_default_status(self):
        """الحالة الافتراضية للفاتورة"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول"
        )
        self.assertEqual(purchase.status, PurchaseStatus.PENDING.value)

    def test_purchase_status_received(self):
        """فاتورة شراء مستلمة"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            status=PurchaseStatus.RECEIVED.value
        )
        self.assertEqual(purchase.status, PurchaseStatus.RECEIVED.value)

    def test_purchase_payment_status_unpaid(self):
        """فاتورة شراء غير مدفوعة"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            payment_status=PaymentStatus.UNPAID.value
        )
        self.assertEqual(purchase.payment_status, PaymentStatus.UNPAID.value)

    def test_purchase_payment_status_paid(self):
        """فاتورة شراء مدفوعة"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            payment_status=PaymentStatus.PAID.value
        )
        self.assertEqual(purchase.payment_status, PaymentStatus.PAID.value)


class TestPurchaseProperties(unittest.TestCase):
    """اختبارات خصائص فاتورة الشراء"""

    def test_purchase_items_count(self):
        """عدد الأصناف في الفاتورة"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                unit_cost=Decimal("100.00")
            ),
            PurchaseItem(
                product_id=2,
                product_name="المنتج الثاني",
                quantity_ordered=Decimal("5"),
                unit_cost=Decimal("200.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertEqual(purchase.items_count, 2)

    def test_purchase_total_quantity_ordered(self):
        """إجمالي الكمية المطلوبة"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                unit_cost=Decimal("100.00")
            ),
            PurchaseItem(
                product_id=2,
                product_name="المنتج الثاني",
                quantity_ordered=Decimal("5"),
                unit_cost=Decimal("200.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertEqual(purchase.total_quantity_ordered, Decimal("15"))

    def test_purchase_total_quantity_received(self):
        """إجمالي الكمية المستلمة"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                quantity_received=Decimal("8"),
                unit_cost=Decimal("100.00")
            ),
            PurchaseItem(
                product_id=2,
                product_name="المنتج الثاني",
                quantity_ordered=Decimal("5"),
                quantity_received=Decimal("3"),
                unit_cost=Decimal("200.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertEqual(purchase.total_quantity_received, Decimal("11"))

    def test_purchase_is_fully_received_true(self):
        """تم استلام الفاتورة كاملة"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                quantity_received=Decimal("10"),
                unit_cost=Decimal("100.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertTrue(purchase.is_fully_received)

    def test_purchase_is_fully_received_false(self):
        """لم يتم استلام الفاتورة كاملة"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                quantity_received=Decimal("5"),
                unit_cost=Decimal("100.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertFalse(purchase.is_fully_received)

    def test_purchase_is_partially_received(self):
        """تم استلام جزء من الفاتورة"""
        items = [
            PurchaseItem(
                product_id=1,
                product_name="المنتج الأول",
                quantity_ordered=Decimal("10"),
                quantity_received=Decimal("5"),
                unit_cost=Decimal("100.00")
            )
        ]
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=items
        )
        self.assertTrue(purchase.is_partially_received)


class TestPurchasePricing(unittest.TestCase):
    """اختبارات أسعار الشراء"""

    def test_purchase_with_amounts(self):
        """فاتورة شراء مع مبالغ"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            subtotal_amount=Decimal("1000.00"),
            discount_amount=Decimal("100.00"),
            tax_amount=Decimal("135.00"),
            shipping_cost=Decimal("50.00"),
            total_amount=Decimal("1085.00")
        )
        self.assertEqual(purchase.subtotal_amount, Decimal("1000.00"))
        self.assertEqual(purchase.total_amount, Decimal("1085.00"))

    def test_purchase_payment_tracking(self):
        """تتبع الدفع"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("600.00"),
            remaining_amount=Decimal("400.00")
        )
        self.assertEqual(purchase.paid_amount, Decimal("600.00"))
        self.assertEqual(purchase.remaining_amount, Decimal("400.00"))

    def test_purchase_overdue_check(self):
        """فحص تأخر الفاتورة"""
        yesterday = date.today() - timedelta(days=1)
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            expected_delivery_date=yesterday,
            payment_status=PaymentStatus.UNPAID.value
        )
        self.assertTrue(purchase.is_overdue)


class TestPurchaseMultiCurrency(unittest.TestCase):
    """اختبارات الفاتورة بعملات متعددة"""

    def test_purchase_with_currency(self):
        """فاتورة بعملة محددة"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            currency_id=2,
            exchange_rate=Decimal("1.5"),
            base_amount=Decimal("1000.00"),
            converted_amount=Decimal("1500.00")
        )
        self.assertEqual(purchase.currency_id, 2)
        self.assertEqual(purchase.exchange_rate, Decimal("1.5"))


class TestPurchaseEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_purchase_empty_items(self):
        """فاتورة بدون عناصر"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول"
        )
        self.assertEqual(purchase.items_count, 0)
        self.assertFalse(purchase.is_fully_received)

    def test_purchase_with_notes(self):
        """فاتورة مع ملاحظات"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            notes="تسليم سريع"
        )
        self.assertEqual(purchase.notes, "تسليم سريع")

    def test_purchase_large_quantity(self):
        """فاتورة بكمية كبيرة"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("999999"),
            unit_cost=Decimal("100.00")
        )
        self.assertEqual(item.quantity_ordered, Decimal("999999"))
        self.assertEqual(item.subtotal, Decimal("99999900.00"))

    def test_purchase_add_item(self):
        """إضافة عنصر للفاتورة"""
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول"
        )
        item = PurchaseItem(
            id=1,
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00")
        )
        purchase.add_item(item)
        self.assertEqual(purchase.items_count, 1)

    def test_purchase_remove_item(self):
        """حذف عنصر من الفاتورة"""
        item = PurchaseItem(
            id=1,
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00")
        )
        purchase = Purchase(
            invoice_number="INV001",
            supplier_id=1,
            supplier_name="المورد الأول",
            items=[item]
        )
        self.assertTrue(purchase.remove_item(1))
        self.assertEqual(purchase.items_count, 0)

    def test_purchase_item_to_dict(self):
        """تحويل عنصر إلى قاموس"""
        item = PurchaseItem(
            product_id=1,
            product_name="المنتج الأول",
            quantity_ordered=Decimal("10"),
            unit_cost=Decimal("100.00")
        )
        item_dict = item.to_dict()
        self.assertEqual(item_dict['product_id'], 1)
        self.assertEqual(item_dict['product_name'], "المنتج الأول")
        self.assertEqual(item_dict['quantity_ordered'], 10.0)


# --- تغطية موسعة لإدارة المشتريات ---


def test_purchase_item_calculations_and_dict():
    item = PurchaseItem(
        product_id=1,
        product_name="Prod",
        quantity_ordered=2,
        quantity_received=1,
        unit_cost=Decimal("50"),
        discount_percent=Decimal("10"),
        tax_percent=Decimal("15"),
    )

    item.calculate_totals()

    assert item.subtotal == Decimal("100")
    assert item.discount_amount == Decimal("10")
    assert item.tax_amount == Decimal("13.5")
    assert item.total_amount == Decimal("103.5")
    assert item.pending_quantity == Decimal("1")
    assert item.is_fully_received is False

    d = item.to_dict()
    assert d["net_amount"] == 90.0
    assert d["pending_quantity"] == 1.0
    assert d["is_fully_received"] is False


def test_purchase_totals_and_payment_status_overdue():
    today = date.today()
    overdue_date = today - timedelta(days=2)

    item = PurchaseItem(quantity_ordered=1, quantity_received=0, unit_cost=Decimal("100"))
    purchase = Purchase(expected_delivery_date=overdue_date, items=[item])

    purchase.calculate_totals()
    assert purchase.total_amount == Decimal("115")
    assert purchase.payment_status == PaymentStatus.OVERDUE.value
    assert purchase.is_overdue is True
    assert purchase.is_fully_received is False
    assert purchase.is_partially_received is False

    purchase.paid_amount = purchase.total_amount
    purchase.calculate_totals()
    assert purchase.payment_status == PaymentStatus.PAID.value


def test_purchase_generate_invoice_and_create_inserts_items(monkeypatch):
    db = DummyDB()
    logger = DummyLogger()
    mgr = PurchaseManager(db, logger)

    db.one_row = (9,)
    item1 = PurchaseItem(product_id=10, quantity_ordered=2, unit_cost=5)
    item2 = PurchaseItem(product_id=11, quantity_ordered=1, unit_cost=3)
    purchase = Purchase(supplier_id=7, items=[item1, item2])
    db.next_lastrowid = 42

    purchase_id = mgr.create_purchase(purchase)
    assert purchase_id == 42
    assert purchase.invoice_number.startswith("PUR")
    assert len(db.item_inserts) == 2
    assert purchase.total_amount > 0


def test_row_to_purchase_and_item_and_dict_conversion():
    mgr = PurchaseManager(DummyDB())
    ts = datetime(2024, 5, 1, 12, 0, 0).isoformat()
    row = (
        5,
        "PUR000123",
        "SUP-1",
        3,
        "2024-05-01",
        "2024-05-05",
        "2024-05-06",
        PurchaseStatus.PENDING.value,
        PaymentStatus.UNPAID.value,
        "نقدي",
        "100.5",
        "1.5",
        "2.5",
        "3.5",
        "107.5",
        "10.0",
        "97.5",
        1,
        "1.1",
        "90.0",
        "107.5",
        "Notes",
        9,
        ts,
        ts,
        "المورد",
    )

    purchase = mgr._row_to_purchase(row)
    assert purchase.id == 5
    assert purchase.invoice_number == "PUR000123"
    assert purchase.exchange_rate == Decimal("1.1")
    assert purchase.converted_amount == Decimal("107.5")
    assert purchase.supplier_name == "المورد"

    item_row = (
        1,
        5,
        10,
        "2",
        "1",
        "5",
        "0",
        "0",
        "15",
        "5.75",
        "20.75",
        "2024-12-31",
        "B1",
        "note",
        "Prod",
        "BRC",
    )
    item = mgr._row_to_purchase_item(item_row)
    assert item.purchase_id == 5
    assert item.product_name == "Prod"
    assert item.tax_amount == Decimal("5.75")

    dict_row = (
        99,
        "PUR000777",
        "المورد",
        datetime(2024, 6, 1, 8, 0, 0),
        Decimal("50"),
        Decimal("20"),
        Decimal("30"),
        PurchaseStatus.PENDING.value,
        PaymentStatus.UNPAID.value,
    )
    brief = mgr._row_to_purchase_dict(dict_row)
    assert brief["invoice_number"] == "PUR000777"
    assert brief["purchase_date"] == "2024-06-01"
    assert brief["remaining_amount"] == 30.0


def test_get_purchases_summary_and_list_purchases():
    db = DummyDB()
    mgr = PurchaseManager(db)

    db.one_row = (2, Decimal("100"), Decimal("70"), Decimal("30"))
    summary = mgr.get_purchases_summary()
    assert summary["total_purchases"] == 2
    assert summary["total_amount"] == 100.0
    assert summary["avg_purchase_value"] == 50.0

    db.rows = [
        (1, "PUR1", "Supplier", date(2024, 1, 1), Decimal("10"), Decimal("5"), Decimal("5"), "معلقة", "غير مدفوعة"),
    ]
    listing = mgr.list_purchases(limit=1)
    assert listing[0]["invoice_number"] == "PUR1"
    assert listing[0]["total_amount"] == 10.0


def test_receive_purchase_items_updates_status_and_stock(monkeypatch):
    db = DummyDB()
    mgr = PurchaseManager(db)

    purchase = Purchase(id=7)
    item = PurchaseItem(id=1, product_id=99, quantity_ordered=Decimal("5"), quantity_received=Decimal("0"), unit_cost=Decimal("2"))
    purchase.items = [item]

    monkeypatch.setattr(mgr, "get_purchase_by_id", lambda pid: purchase)

    updated = {}
    monkeypatch.setattr(mgr, "update_purchase", lambda p: updated.setdefault("called", True) or True)

    stock_updates = {}
    monkeypatch.setattr(
        mgr,
        "_update_product_stock",
        lambda product_id, quantity, unit_cost, expiry_date=None, batch_number=None: stock_updates.setdefault(product_id, float(quantity)),
    )

    ok = mgr.receive_purchase_items(7, [{"item_id": 1, "quantity_received": 5}])
    assert ok is True
    assert purchase.status == PurchaseStatus.RECEIVED.value
    assert updated.get("called") is True
    assert stock_updates[99] == 5.0


def test_cancel_purchase_behaviour(monkeypatch):
    db = DummyDB()
    mgr = PurchaseManager(db)

    received_purchase = Purchase(id=1, status=PurchaseStatus.RECEIVED.value)
    monkeypatch.setattr(mgr, "get_purchase_by_id", lambda pid: received_purchase)
    assert mgr.cancel_purchase(1) is False

    pending_purchase = Purchase(id=2, status=PurchaseStatus.PENDING.value, notes="old")
    monkeypatch.setattr(mgr, "get_purchase_by_id", lambda pid: pending_purchase)
    monkeypatch.setattr(mgr, "update_purchase", lambda p: True)
    assert mgr.cancel_purchase(2, reason="out of stock") is True
    assert "out of stock" in pending_purchase.notes


if __name__ == '__main__':
    unittest.main()



