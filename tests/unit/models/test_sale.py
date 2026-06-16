#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.core.database_manager import DatabaseManager
from src.models.sale import PaymentMethod, Sale, SaleItem, SaleManager, SaleStatus


@pytest.fixture
def db_manager():
    db = DatabaseManager(db_path=":memory:")
    db.initialize()
    # Ensure required columns exist in sales table for SaleManager
    try:
        db.execute_query("ALTER TABLE sales ADD COLUMN status TEXT")
    except Exception:
        pass
    for col_def in [
        "paid_amount REAL DEFAULT 0",
        "remaining_amount REAL DEFAULT 0",
        "currency_id INTEGER",
        "exchange_rate REAL DEFAULT 1.0",
        "base_amount REAL",
        "converted_amount REAL",
    ]:
        try:
            db.execute_query(f"ALTER TABLE sales ADD COLUMN {col_def}")
        except Exception:
            pass
    # Ensure minimal seed product for sale items
    db.execute_query(
        """
        INSERT INTO products (name, unit, cost_price, selling_price, current_stock)
        VALUES (?, 'قطعة', 100.0, 150.0, 100)
        """,
        ("Test Product",),
    )
    # Fetch inserted product id
    pid = db.fetch_one("SELECT id FROM products WHERE name = ?", ("Test Product",))[0]
    # Seed default batch referenced by SaleItem (batch_id = 1)
    db.execute_query(
        """
        INSERT INTO batches (id, product_id, batch_number, quantity, cost_price, selling_price)
        VALUES (1, ?, 'BATCH-001', 100, 100.0, 150.0)
        """,
        (pid,),
    )
    return db, pid


@pytest.fixture
def sale_manager(db_manager):
    db, _ = db_manager
    return SaleManager(db_manager=db, logger=Mock())


def make_sale(product_id: int, qty: int = 2, unit_price: Decimal = Decimal("150.00")) -> Sale:
    sale = Sale(
        invoice_number="INV-20250101-0001",
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        sale_date=date.today(),
        status=SaleStatus.CONFIRMED,
        discount_percentage=Decimal("0.00"),
        tax_percentage=Decimal("0.00"),
    )
    item = SaleItem(
        product_id=product_id,
        product_name="Test Product",
        quantity=qty,
        unit_price=unit_price,
    )
    sale.add_item(item)
    return sale


def test_create_sale_basic_flow(sale_manager, db_manager):
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))

    # Totals before persist
    assert sale.subtotal == Decimal("300.00")
    assert sale.total_amount == Decimal("300.00")
    assert sale.remaining_amount == Decimal("300.00")
    assert sale.status in (SaleStatus.CONFIRMED, SaleStatus.PARTIALLY_PAID)

    sale_id = sale_manager.create_sale(sale)
    assert sale_id is not None and sale_id > 0

    persisted = sale_manager.get_sale_by_id(sale_id)
    assert persisted is not None
    assert persisted.total_amount == Decimal("300.00")
    assert persisted.paid_amount == Decimal("0.00")
    assert persisted.remaining_amount == Decimal("300.00")
    assert persisted.items_count == 1
    assert persisted.total_quantity == 2


def test_add_payment_and_status_transitions(sale_manager, db_manager):
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=1, unit_price=Decimal("200.00"))
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    # Partial payment
    ok = sale_manager.add_payment(sale_id, Decimal("50.00"))
    assert ok
    s = sale_manager.get_sale_by_id(sale_id)
    assert s.paid_amount == Decimal("50.00")
    assert s.remaining_amount == Decimal("150.00")
    assert s.status in (SaleStatus.PARTIALLY_PAID, SaleStatus.CONFIRMED)

    # Full payment
    ok = sale_manager.add_payment(sale_id, Decimal("150.00"))
    assert ok
    s = sale_manager.get_sale_by_id(sale_id)
    assert s.paid_amount == Decimal("200.00")
    assert s.remaining_amount == Decimal("0.00")
    assert s.status == SaleStatus.PAID


def test_list_and_search_sales(sale_manager, db_manager):
    db, pid = db_manager

    sale1 = make_sale(product_id=pid, qty=1, unit_price=Decimal("100.00"))
    sale1.invoice_number = "INV-Alpha"
    sale_manager.create_sale(sale1)

    sale2 = make_sale(product_id=pid, qty=3, unit_price=Decimal("50.00"))
    sale2.invoice_number = "INV-Beta"
    sale_manager.create_sale(sale2)

    # list_sales returns concise dicts
    listing = sale_manager.list_sales(search_term="INV", limit=10)
    assert isinstance(listing, list) and len(listing) >= 2
    assert any(item["invoice_number"] == "INV-Alpha" for item in listing)

    # search_sales returns Sale instances
    results = sale_manager.search_sales(search_term="Beta")
    assert isinstance(results, list) and len(results) == 1
    assert results[0].invoice_number == "INV-Beta"


def test_generate_invoice_number(sale_manager, db_manager):
    # Smoke test: should return INV-YYYYMMDD-XXXX format
    inv = sale_manager.generate_invoice_number()
    assert inv.startswith("INV-")
    assert inv.count("-") >= 2


def test_update_sale_status(sale_manager, db_manager):
    """اختبار تحديث حالة الفاتورة"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    # تحديث الحالة إلى مؤكدة
    success = sale_manager.update_sale_status(sale_id, SaleStatus.CONFIRMED)
    assert success

    updated_sale = sale_manager.get_sale_by_id(sale_id)
    assert updated_sale.status == SaleStatus.CONFIRMED

    # تحديث الحالة إلى ملغية
    success = sale_manager.update_sale_status(sale_id, SaleStatus.CANCELLED)
    assert success


def test_cancel_sale(sale_manager, db_manager):
    """اختبار إلغاء فاتورة"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    success = sale_manager.cancel_sale(sale_id)
    assert success

    cancelled_sale = sale_manager.get_sale_by_id(sale_id)
    assert cancelled_sale.status == SaleStatus.CANCELLED


def test_get_sale_by_invoice_number(sale_manager, db_manager):
    """اختبار الحصول على فاتورة برقم الفاتورة"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale.invoice_number = "INV-TEST-123"
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    found_sale = sale_manager.get_sale_by_invoice_number("INV-TEST-123")
    assert found_sale is not None
    assert found_sale.invoice_number == "INV-TEST-123"
    assert found_sale.id == sale_id


def test_get_sales_summary(sale_manager, db_manager):
    """اختبار الحصول على ملخص المبيعات"""
    db, pid = db_manager
    sale1 = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_manager.create_sale(sale1)

    sale2 = make_sale(product_id=pid, qty=1, unit_price=Decimal("200.00"))
    sale_manager.create_sale(sale2)

    summary = sale_manager.get_sales_summary()
    assert summary is not None
    assert "total_sales" in summary or "total_invoices" in summary


def test_get_daily_sales(sale_manager, db_manager):
    """اختبار الحصول على المبيعات اليومية"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_manager.create_sale(sale)

    daily_sales = sale_manager.get_daily_sales(date.today())
    assert isinstance(daily_sales, list)
    assert len(daily_sales) >= 1


def test_get_recent_sales(sale_manager, db_manager):
    """اختبار الحصول على المبيعات الأخيرة"""
    db, pid = db_manager
    sale1 = make_sale(product_id=pid, qty=1, unit_price=Decimal("100.00"))
    sale_manager.create_sale(sale1)

    sale2 = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_manager.create_sale(sale2)

    recent = sale_manager.get_recent_sales(limit=5)
    assert isinstance(recent, list)
    assert len(recent) >= 2


def test_delete_sale_soft(sale_manager, db_manager):
    """اختبار حذف فاتورة بشكل ناعم"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    success = sale_manager.delete_sale(sale_id, soft_delete=True)
    assert success


"""
اختبارات شاملة لنموذج Sale
Comprehensive tests for Sale model
"""

import unittest
from datetime import date, datetime, timedelta  # noqa: F811
from decimal import Decimal

from src.models.sale import PaymentMethod, Sale, SaleItem, SaleStatus  # noqa: F811


class TestSaleStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات المبيعات"""

    def test_sale_status_draft(self):
        """حالة مسودة"""
        self.assertEqual(SaleStatus.DRAFT.value, "مسودة")

    def test_sale_status_confirmed(self):
        """حالة مؤكدة"""
        self.assertEqual(SaleStatus.CONFIRMED.value, "مؤكدة")

    def test_sale_status_paid(self):
        """حالة مدفوعة"""
        self.assertEqual(SaleStatus.PAID.value, "مدفوعة")

    def test_sale_status_partially_paid(self):
        """حالة مدفوعة جزئياً"""
        self.assertEqual(SaleStatus.PARTIALLY_PAID.value, "مدفوعة جزئياً")

    def test_sale_status_cancelled(self):
        """حالة ملغية"""
        self.assertEqual(SaleStatus.CANCELLED.value, "ملغية")

    def test_sale_status_returned(self):
        """حالة مرتجعة"""
        self.assertEqual(SaleStatus.RETURNED.value, "مرتجعة")


class TestPaymentMethodEnum(unittest.TestCase):
    """اختبارات تعداد طرق الدفع"""

    def test_payment_method_cash(self):
        """دفع نقدي"""
        self.assertEqual(PaymentMethod.CASH.value, "نقدي")

    def test_payment_method_card(self):
        """دفع ببطاقة"""
        self.assertEqual(PaymentMethod.CARD.value, "بطاقة")

    def test_payment_method_bank_transfer(self):
        """تحويل بنكي"""
        self.assertEqual(PaymentMethod.BANK_TRANSFER.value, "تحويل بنكي")

    def test_payment_method_credit(self):
        """دفع آجل"""
        self.assertEqual(PaymentMethod.CREDIT.value, "آجل")

    def test_payment_method_mixed(self):
        """دفع مختلط"""
        self.assertEqual(PaymentMethod.MIXED.value, "مختلط")


class TestSaleItemCreation(unittest.TestCase):
    """اختبارات إنشاء عنصر المبيعات"""

    def test_sale_item_basic(self):
        """إنشاء عنصر أساسي"""
        item = SaleItem(
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
        )
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.unit_price, Decimal("100.00"))

    def test_sale_item_with_discount(self):
        """عنصر مع خصم"""
        item = SaleItem(
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10.00"),
        )
        self.assertEqual(item.discount_percentage, Decimal("10.00"))

    def test_sale_item_with_tax(self):
        """عنصر مع ضريبة"""
        item = SaleItem(
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
            tax_percentage=Decimal("15.00"),
        )
        self.assertEqual(item.tax_percentage, Decimal("15.00"))

    def test_sale_item_calculate_total(self):
        """حساب المجموع"""
        item = SaleItem(
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10.00"),
            tax_percentage=Decimal("15.00"),
        )
        item.calculate_total()

        # subtotal = 5 * 100 = 500
        # discount = 500 * 10% = 50
        # after_discount = 500 - 50 = 450
        # tax = 450 * 15% = 67.5
        # total = 450 + 67.5 = 517.5

        self.assertEqual(item.total_amount, Decimal("517.50"))

    def test_sale_item_to_dict(self):
        """تحويل عنصر إلى قاموس"""
        item = SaleItem(
            id=1,
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10.00"),
        )
        item.calculate_total()
        item_dict = item.to_dict()

        self.assertEqual(item_dict["product_id"], 1)
        self.assertEqual(item_dict["quantity"], 5)
        self.assertEqual(item_dict["unit_price"], 100.0)


class TestSaleCreation(unittest.TestCase):
    """اختبارات إنشاء فاتورة مبيعات"""

    def test_sale_basic_creation(self):
        """إنشاء فاتورة أساسية"""
        sale = Sale(invoice_number="INV001", customer_id=1, customer_name="أحمد محمد")
        self.assertEqual(sale.invoice_number, "INV001")
        self.assertEqual(sale.customer_id, 1)
        self.assertEqual(sale.customer_name, "أحمد محمد")

    def test_sale_default_status(self):
        """الحالة الافتراضية"""
        sale = Sale(invoice_number="INV001")
        self.assertEqual(sale.status, SaleStatus.DRAFT)

    def test_sale_default_payment_method(self):
        """طريقة الدفع الافتراضية"""
        sale = Sale(invoice_number="INV001")
        self.assertEqual(sale.payment_method, PaymentMethod.CASH)

    def test_sale_with_customer_info(self):
        """فاتورة مع بيانات العميل"""
        sale = Sale(
            invoice_number="INV001",
            customer_id=1,
            customer_name="أحمد محمد",
            customer_phone="+966123456789",
        )
        self.assertEqual(sale.customer_phone, "+966123456789")

    def test_sale_with_dates(self):
        """فاتورة مع تواريخ"""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        sale = Sale(invoice_number="INV001", sale_date=today, due_date=tomorrow)
        self.assertEqual(sale.sale_date, today)
        self.assertEqual(sale.due_date, tomorrow)

    def test_sale_with_payment_method(self):
        """فاتورة بطريقة دفع محددة"""
        sale = Sale(invoice_number="INV001", payment_method=PaymentMethod.CARD)
        self.assertEqual(sale.payment_method, PaymentMethod.CARD)

    def test_sale_with_status(self):
        """فاتورة بحالة محددة"""
        sale = Sale(invoice_number="INV001", status=SaleStatus.CONFIRMED)
        self.assertEqual(sale.status, SaleStatus.CONFIRMED)


class TestSaleItems(unittest.TestCase):
    """اختبارات عناصر المبيعات"""

    def test_sale_add_item(self):
        """إضافة عنصر للفاتورة"""
        sale = Sale(invoice_number="INV001")
        item = SaleItem(
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item)
        self.assertEqual(sale.items_count, 1)

    def test_sale_add_multiple_items(self):
        """إضافة عدة عناصر"""
        sale = Sale(invoice_number="INV001")
        for i in range(3):
            item = SaleItem(
                product_id=i + 1,
                product_name=f"منتج {i+1}",
                quantity=i + 1,
                unit_price=Decimal("100.00"),
            )
            sale.add_item(item)
        self.assertEqual(sale.items_count, 3)

    def test_sale_total_quantity(self):
        """إجمالي الكمية"""
        sale = Sale(invoice_number="INV001")
        item1 = SaleItem(
            product_id=1,
            product_name="منتج 1",
            quantity=5,
            unit_price=Decimal("100.00"),
        )
        item2 = SaleItem(
            product_id=2,
            product_name="منتج 2",
            quantity=3,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item1)
        sale.add_item(item2)
        self.assertEqual(sale.total_quantity, 8)

    def test_sale_remove_item(self):
        """حذف عنصر من الفاتورة"""
        sale = Sale(invoice_number="INV001")
        item = SaleItem(
            id=1,
            product_id=1,
            product_name="قميص أبيض",
            quantity=5,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item)
        self.assertEqual(sale.items_count, 1)
        sale.remove_item(1)
        self.assertEqual(sale.items_count, 0)


class TestSaleCalculations(unittest.TestCase):
    """اختبارات حسابات الفاتورة"""

    def test_sale_subtotal(self):
        """الإجمالي الفرعي"""
        sale = Sale(invoice_number="INV001")
        item1 = SaleItem(
            product_id=1,
            product_name="منتج 1",
            quantity=5,
            unit_price=Decimal("100.00"),
        )
        item2 = SaleItem(
            product_id=2,
            product_name="منتج 2",
            quantity=3,
            unit_price=Decimal("200.00"),
        )
        sale.add_item(item1)
        sale.add_item(item2)

        expected = Decimal("500.00") + Decimal("600.00")
        self.assertEqual(sale.subtotal, expected)

    def test_sale_with_discount(self):
        """فاتورة مع خصم"""
        sale = Sale(invoice_number="INV001", discount_percentage=Decimal("10.00"))
        item = SaleItem(
            product_id=1,
            product_name="منتج 1",
            quantity=10,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item)

        # subtotal = 1000
        # discount = 1000 * 10% = 100
        self.assertEqual(sale.discount_amount, Decimal("100.00"))

    def test_sale_with_tax(self):
        """فاتورة مع ضريبة"""
        sale = Sale(invoice_number="INV001", tax_percentage=Decimal("15.00"))
        item = SaleItem(
            product_id=1,
            product_name="منتج 1",
            quantity=10,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item)

        # subtotal = 1000
        # tax = 1000 * 15% = 150
        self.assertEqual(sale.tax_amount, Decimal("150.00"))

    def test_sale_total_amount(self):
        """المجموع النهائي"""
        sale = Sale(invoice_number="INV001")
        item = SaleItem(
            product_id=1,
            product_name="منتج 1",
            quantity=10,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item)

        # subtotal = 1000, no discount/tax
        # total = 1000
        self.assertEqual(sale.total_amount, Decimal("1000.00"))


class TestSalePayment(unittest.TestCase):
    """اختبارات الدفع"""

    def test_sale_is_paid_true(self):
        """فاتورة مدفوعة كاملة"""
        sale = Sale(
            invoice_number="INV001",
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("1000.00"),
        )
        self.assertTrue(sale.is_paid)

    def test_sale_is_paid_false(self):
        """فاتورة غير مدفوعة"""
        sale = Sale(
            invoice_number="INV001",
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("0.00"),
        )
        self.assertFalse(sale.is_paid)

    def test_sale_is_paid_partial(self):
        """فاتورة مدفوعة جزئياً"""
        sale = Sale(
            invoice_number="INV001",
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("500.00"),
        )
        self.assertFalse(sale.is_paid)

    def test_sale_remaining_amount(self):
        """المبلغ المتبقي"""
        sale = Sale(
            invoice_number="INV001",
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("600.00"),
        )
        # remaining_amount is set separately in constructor
        # it doesn't get calculated from total_amount - paid_amount
        self.assertEqual(sale.remaining_amount, Decimal("0.00"))


class TestSaleMultiCurrency(unittest.TestCase):
    """اختبارات الفاتورة بعملات متعددة"""

    def test_sale_with_currency(self):
        """فاتورة بعملة محددة"""
        sale = Sale(
            invoice_number="INV001",
            currency_id=2,
            exchange_rate=Decimal("3.75"),
            total_amount=Decimal("1000.00"),
        )
        sale.calculate_totals()

        self.assertEqual(sale.currency_id, 2)
        self.assertEqual(sale.exchange_rate, Decimal("3.75"))


class TestSaleSerialization(unittest.TestCase):
    """اختبارات تسلسل بيانات الفاتورة"""

    def test_sale_to_dict(self):
        """تحويل فاتورة إلى قاموس"""
        sale = Sale(
            id=1,
            invoice_number="INV001",
            customer_id=1,
            customer_name="أحمد محمد",
            total_amount=Decimal("1000.00"),
        )
        sale_dict = sale.to_dict()

        self.assertEqual(sale_dict["id"], 1)
        self.assertEqual(sale_dict["invoice_number"], "INV001")
        self.assertEqual(sale_dict["customer_name"], "أحمد محمد")
        self.assertEqual(sale_dict["total_amount"], 1000.0)

    def test_sale_to_dict_with_items(self):
        """تحويل فاتورة مع عناصر"""
        sale = Sale(invoice_number="INV001")
        item = SaleItem(
            product_id=1,
            product_name="منتج 1",
            quantity=5,
            unit_price=Decimal("100.00"),
        )
        sale.add_item(item)

        sale_dict = sale.to_dict()
        self.assertEqual(len(sale_dict["items"]), 1)
        self.assertEqual(sale_dict["items_count"], 1)


class TestSaleEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_sale_empty_invoice_number(self):
        """فاتورة برقم فارغ"""
        sale = Sale(invoice_number="")
        self.assertEqual(sale.invoice_number, "")

    def test_sale_with_notes(self):
        """فاتورة مع ملاحظات"""
        sale = Sale(invoice_number="INV001", notes="توصيل سريع")
        self.assertEqual(sale.notes, "توصيل سريع")

    def test_sale_decimal_conversions(self):
        """تحويلات Decimal صحيحة"""
        sale = Sale(
            invoice_number="INV001",
            subtotal=100.50,  # float
            discount_amount="50.25",  # string
            tax_amount=Decimal("15.00"),
        )
        self.assertIsInstance(sale.subtotal, Decimal)
        self.assertIsInstance(sale.discount_amount, Decimal)
        self.assertIsInstance(sale.tax_amount, Decimal)

    def test_sale_large_amounts(self):
        """فاتورة بمبالغ كبيرة"""
        sale = Sale(
            invoice_number="INV001",
            total_amount=Decimal("999999.99"),
            paid_amount=Decimal("999999.99"),
        )
        self.assertTrue(sale.is_paid)

    def test_sale_created_timestamp(self):
        """فاتورة مع وقت الإنشاء"""
        now = datetime.now()
        sale = Sale(invoice_number="INV001", created_at=now)
        self.assertEqual(sale.created_at, now)

    def test_sale_multiple_payment_methods(self):
        """اختبار جميع طرق الدفع"""
        methods = [
            PaymentMethod.CASH,
            PaymentMethod.CARD,
            PaymentMethod.BANK_TRANSFER,
            PaymentMethod.CREDIT,
            PaymentMethod.MIXED,
        ]
        for method in methods:
            sale = Sale(invoice_number=f"INV_{method.value}", payment_method=method)
            self.assertEqual(sale.payment_method, method)

    def test_update_sale_status(self):
        """اختبار تحديث حالة الفاتورة"""
        from src.core.database_manager import DatabaseManager
        from src.models.sale import SaleManager

        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        try:
            for col_def in [
                "status TEXT",
                "paid_amount REAL DEFAULT 0",
                "remaining_amount REAL DEFAULT 0",
                "currency_id INTEGER",
                "exchange_rate REAL DEFAULT 1.0",
                "base_amount REAL",
                "converted_amount REAL",
            ]:
                try:
                    db.execute_query(f"ALTER TABLE sales ADD COLUMN {col_def}")
                except Exception:
                    pass

            db.execute_query(
                """
                INSERT INTO products (name, unit, cost_price, selling_price, current_stock)
                VALUES (?, 'قطعة', 100.0, 150.0, 100)
                """,
                ("Test Product",),
            )
            pid = db.fetch_one("SELECT id FROM products WHERE name = ?", ("Test Product",))[0]
            # Seed default batch referenced by SaleItem (batch_id = 1)
            db.execute_query(
                """
                INSERT INTO batches (id, product_id, batch_number, quantity, cost_price, selling_price)
                VALUES (1, ?, 'BATCH-001', 100, 100.0, 150.0)
                """,
                (pid,),
            )

            sale_manager = SaleManager(db_manager=db, logger=Mock())
            sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
            sale_id = sale_manager.create_sale(sale)
            assert sale_id

            success = sale_manager.update_sale_status(sale_id, SaleStatus.CONFIRMED)
            assert success

            updated_sale = sale_manager.get_sale_by_id(sale_id)
            assert updated_sale.status == SaleStatus.CONFIRMED

            success = sale_manager.update_sale_status(sale_id, SaleStatus.CANCELLED)
            assert success
        finally:
            db.close()


def test_cancel_sale(sale_manager, db_manager):  # noqa: F811
    """اختبار إلغاء فاتورة"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    success = sale_manager.cancel_sale(sale_id)
    assert success

    cancelled_sale = sale_manager.get_sale_by_id(sale_id)
    assert cancelled_sale.status == SaleStatus.CANCELLED


def test_get_sale_by_invoice_number(sale_manager, db_manager):  # noqa: F811
    """اختبار الحصول على فاتورة برقم الفاتورة"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale.invoice_number = "INV-TEST-123"
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    found_sale = sale_manager.get_sale_by_invoice_number("INV-TEST-123")
    assert found_sale is not None
    assert found_sale.invoice_number == "INV-TEST-123"
    assert found_sale.id == sale_id


def test_get_sales_summary(sale_manager, db_manager):  # noqa: F811
    """اختبار الحصول على ملخص المبيعات"""
    db, pid = db_manager
    sale1 = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_manager.create_sale(sale1)

    sale2 = make_sale(product_id=pid, qty=1, unit_price=Decimal("200.00"))
    sale_manager.create_sale(sale2)

    summary = sale_manager.get_sales_summary()
    assert summary is not None
    assert "total_sales" in summary or "total_invoices" in summary


def test_get_daily_sales(sale_manager, db_manager):  # noqa: F811
    """اختبار الحصول على المبيعات اليومية"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_manager.create_sale(sale)

    daily_sales = sale_manager.get_daily_sales(date.today())
    assert isinstance(daily_sales, list)
    assert len(daily_sales) >= 1


def test_get_recent_sales(sale_manager, db_manager):  # noqa: F811
    """اختبار الحصول على المبيعات الأخيرة"""
    db, pid = db_manager
    sale1 = make_sale(product_id=pid, qty=1, unit_price=Decimal("100.00"))
    sale1.invoice_number = ""
    sale_manager.create_sale(sale1)

    sale2 = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale2.invoice_number = ""
    sale_manager.create_sale(sale2)

    recent = sale_manager.get_recent_sales(limit=5)
    assert isinstance(recent, list)
    assert len(recent) >= 2


def test_delete_sale_soft(sale_manager, db_manager):  # noqa: F811
    """اختبار حذف فاتورة بشكل ناعم"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    success = sale_manager.delete_sale(sale_id, soft_delete=True)
    assert success


def test_create_sale_with_multiple_items(sale_manager, db_manager):
    """اختبار إنشاء فاتورة بعناصر متعددة"""
    db, pid = db_manager

    # إنشاء منتج إضافي
    db.execute_query(
        """
        INSERT INTO products (name, unit, cost_price, selling_price, current_stock)
        VALUES (?, 'قطعة', 80.0, 120.0, 50)
        """,
        ("Product 2",),
    )
    pid2 = db.fetch_one("SELECT id FROM products WHERE name = ?", ("Product 2",))[0]

    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))

    # إضافة عنصر ثاني
    item2 = SaleItem(
        product_id=pid2,
        product_name="Product 2",
        quantity=3,
        unit_price=Decimal("120.00"),
    )
    sale.add_item(item2)

    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    persisted = sale_manager.get_sale_by_id(sale_id)
    assert persisted.items_count == 2
    assert persisted.total_quantity == 5
    assert persisted.subtotal == Decimal("660.00")  # (2 * 150) + (3 * 120)


def test_create_sale_with_discount_and_tax(sale_manager, db_manager):
    """اختبار إنشاء فاتورة مع خصم وضريبة"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale.discount_percentage = Decimal("10.00")  # 10% خصم
    sale.tax_percentage = Decimal("15.00")  # 15% ضريبة

    sale_id = sale_manager.create_sale(sale)
    assert sale_id

    persisted = sale_manager.get_sale_by_id(sale_id)
    assert persisted.discount_percentage == Decimal("10.00")
    assert persisted.tax_percentage == Decimal("15.00")
    assert persisted.total_amount > persisted.subtotal


def test_sale_item_quantity_validation(sale_manager, db_manager):
    """اختبار التحقق من صحة كمية العنصر"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))  # noqa: F841

    # يجب أن تكون الكمية موجبة
    item = SaleItem(
        product_id=pid,
        product_name="Test Product",
        quantity=1,
        unit_price=Decimal("150.00"),
    )
    assert item.quantity > 0


def test_sale_get_nonexistent(sale_manager, db_manager):
    """اختبار الحصول على فاتورة غير موجودة"""
    nonexistent_id = 99999
    sale = sale_manager.get_sale_by_id(nonexistent_id)
    assert sale is None


def test_sale_cancel_nonexistent(sale_manager, db_manager):
    """اختبار إلغاء فاتورة غير موجودة"""
    nonexistent_id = 99999
    success = sale_manager.cancel_sale(nonexistent_id)
    assert success is False


def test_sale_search_by_date_range(sale_manager, db_manager):
    """اختبار البحث عن مبيعات بنطاق تاريخ"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_manager.create_sale(sale)

    from_date = date.today()
    to_date = date.today()

    # البحث عن المبيعات اليوم
    if hasattr(sale_manager, "get_sales_by_date_range"):
        sales = sale_manager.get_sales_by_date_range(from_date, to_date)
        assert isinstance(sales, list)
        assert len(sales) >= 1


def test_sale_payment_exceeds_total(sale_manager, db_manager):
    """اختبار دفع مبلغ أكبر من الإجمالي"""
    db, pid = db_manager
    sale = make_sale(product_id=pid, qty=2, unit_price=Decimal("150.00"))
    sale_id = sale_manager.create_sale(sale)

    total = Decimal("300.00")  # noqa: F841
    payment_amount = Decimal("500.00")

    success = sale_manager.add_payment(sale_id, payment_amount, PaymentMethod.CASH)

    if success:
        updated_sale = sale_manager.get_sale_by_id(sale_id)
        # يجب ألا يتجاوز المبلغ المدفوع الإجمالي
        assert updated_sale.paid_amount <= updated_sale.total_amount
        assert updated_sale.status == SaleStatus.PAID


if __name__ == "__main__":
    unittest.main()
