#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات فجوات الأعمال المتبقية (Gaps 5-8) — قاعدة بيانات حقيقية:

- Gap 5: تحويل الوحدات في تدفق البيع + رفع CreditLimitError + تطبيع الـ enum
- Gap 6: complete_return الذري (مخزون + حركات + قيد محاسبي)
- Gap 7: تخصيص دفعات الموردين FIFO على الفواتير الأقدم
- Gap 8: خدمة المصاريف (CRUD + موافقة بقيد + متكررة catch-up)
"""

import os
import sys
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database_manager import DatabaseManager
from src.models.customer import Customer, CustomerManager
from src.models.product import Product, ProductManager
from src.models.return_invoice import (
    RefundMethod,
    ReturnInvoice,
    ReturnItem,
    ReturnReason,
    ReturnType,
)
from src.models.sale import PaymentMethod, Sale, SaleItem
from src.services.business_rules_service import CreditLimitError, UnitConversionService
from src.services.expense_service import ExpenseService
from src.services.payment_service import PaymentService
from src.services.return_service import ReturnService
from src.services.sales_service import SalesService


@pytest.fixture(scope="module")
def db():
    """قاعدة بيانات SQLite حقيقية مؤقتة للمجموعة كاملة"""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)

    manager = DatabaseManager(db_path=tmp.name, pool_options={"enabled": False})
    assert manager.initialize() is True

    yield manager

    try:
        if manager.connection:
            manager.connection.close()
    except Exception:
        pass
    for path in (tmp.name, tmp.name + "-wal", tmp.name + "-shm"):
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass


def _add_product(db, name="منتج اختبار", unit="حبة", stock=1000.0,
                 cost="10.00", price="15.00") -> int:
    pm = ProductManager(db)
    product = Product(
        name=name, unit=unit,
        cost_price=Decimal(cost), selling_price=Decimal(price),
        current_stock=stock,
    )
    pid = pm.create_product(product)
    assert pid, "فشل إنشاء المنتج"
    return pid


def _add_customer(db, name="عميل اختبار", credit_limit="0",
                  balance="0") -> int:
    cm = CustomerManager(db)
    customer = Customer(
        name=name,
        credit_limit=Decimal(credit_limit),
        current_balance=Decimal(balance),
    )
    cid = cm.create_customer(customer)
    assert cid, "فشل إنشاء العميل"
    return cid


def _stock_of(db, product_id: int) -> float:
    row = db.fetch_one("SELECT current_stock FROM products WHERE id = ?", (product_id,))
    return float(row.get("current_stock", 0) or 0)


# ═══════════════════════════════════════════════════════════════════
# Gap 5: تحويل الوحدات
# ═══════════════════════════════════════════════════════════════════

class TestGap5UnitConversion:
    def test_normalize_converts_quantity_and_price(self, db):
        """2 كرتونة (24 حبة/كرتونة) → 48 حبة + سعر الوحدة من unit_prices"""
        pid = _add_product(db, name="منتج وحدات", unit="حبة", stock=1000)
        ucs = UnitConversionService(db)
        assert ucs.set_conversion(pid, "كرتونة", "حبة", Decimal("24"))
        assert ucs.set_unit_price(
            pid, "كرتونة", Decimal("360.00"), Decimal("240.00")
        )

        service = SalesService(db)
        sale = Sale(total_amount=Decimal("0"))
        item = SaleItem(product_id=pid, quantity=2,
                        unit_price=Decimal("0"), sale_unit="كرتونة")
        sale.add_item(item)

        converted = service._normalize_sale_units(sale)
        assert converted is True
        assert item.quantity == 48.0                       # 2 × 24
        assert item.unit_price == Decimal("360.00")        # من unit_prices
        assert item.total_amount == Decimal("17280.00")    # 48 × 360

    def test_create_sale_with_unit_deducts_base_stock(self, db):
        """بيع 2 كرتونة يخصم 48 حبة من المخزون الأساسي (FEFO/خصم ذري)"""
        pid = _add_product(db, name="منتج بيع كرتونة", unit="حبة", stock=100)
        ucs = UnitConversionService(db)
        assert ucs.set_conversion(pid, "كرتونة", "حبة", Decimal("24"))

        service = SalesService(db)
        sale = Sale(total_amount=Decimal("0"))
        sale.add_item(SaleItem(product_id=pid, quantity=2,
                               unit_price=Decimal("360"), sale_unit="كرتونة"))
        sale_id = service.create_sale(sale, user_id=None)
        assert sale_id, "فشل إنشاء البيع المحول"

        assert _stock_of(db, pid) == 52.0  # 100 − 48

    def test_same_unit_no_conversion(self, db):
        """وحدة البيع = الأساسية → لا تحويل"""
        pid = _add_product(db, name="منتج حبة", unit="حبة", stock=100)
        service = SalesService(db)
        sale = Sale(total_amount=Decimal("0"))
        sale.add_item(SaleItem(product_id=pid, quantity=5,
                               unit_price=Decimal("15"), sale_unit="حبة"))
        assert service._normalize_sale_units(sale) is False
        assert item_qty(sale) == 5.0

    def test_unknown_unit_falls_back(self, db):
        """وحدة بلا تحويل مسجّل → الكمية تبقى كما هي (سلوك آمن)"""
        pid = _add_product(db, name="منتج بلا تحويل", unit="حبة", stock=100)
        service = SalesService(db)
        sale = Sale(total_amount=Decimal("0"))
        sale.add_item(SaleItem(product_id=pid, quantity=3,
                               unit_price=Decimal("15"), sale_unit="باليت"))
        service._normalize_sale_units(sale)
        assert item_qty(sale) == 3.0


def item_qty(sale: Sale) -> float:
    return float(sale.items[0].quantity)


# ═══════════════════════════════════════════════════════════════════
# Gap 5: السقف الائتماني — رفع الاستثناء + تطبيع الـ enum
# ═══════════════════════════════════════════════════════════════════

class TestGap5CreditLimit:
    def test_credit_exceeded_raises(self, db):
        """بيع آجل يتجاوز السقف → CreditLimitError يُرفع (لا None صامتة)"""
        pid = _add_product(db, name="منتج ائتمان", unit="حبة", stock=100)
        cid = _add_customer(db, name="عميل سقف 100", credit_limit="100")

        service = SalesService(db)
        sale = Sale(
            customer_id=cid,
            payment_method=PaymentMethod.CREDIT,  # enum — اختبار تطبيع الـ enum
            total_amount=Decimal("500"),
        )
        sale.add_item(SaleItem(product_id=pid, quantity=10,
                               unit_price=Decimal("50")))

        with pytest.raises(CreditLimitError):
            service.create_sale(sale)

    def test_credit_within_limit_updates_balance(self, db):
        """بيع آجل داخل السقف → ينشأ + رصيد العميل يزيد"""
        pid = _add_product(db, name="منتج ائتمان 2", unit="حبة", stock=100)
        cid = _add_customer(db, name="عميل سقف 500", credit_limit="500")

        service = SalesService(db)
        sale = Sale(
            customer_id=cid,
            payment_method=PaymentMethod.CREDIT,
            total_amount=Decimal("150"),
            final_amount=Decimal("150"),
        )
        sale.add_item(SaleItem(product_id=pid, quantity=10,
                               unit_price=Decimal("15")))
        sale_id = service.create_sale(sale)
        assert sale_id

        row = db.fetch_one(
            "SELECT current_balance FROM customers WHERE id = ?", (cid,)
        )
        assert Decimal(str(row.get("current_balance", 0))) == Decimal("150")

    def test_cash_sale_skips_credit_check(self, db):
        """بيع نقدي لا يفحص السقف حتى لو الرصيد كبير"""
        pid = _add_product(db, name="منتج نقدي", unit="حبة", stock=100)
        cid = _add_customer(db, name="عميل سقف ضيق", credit_limit="10")

        service = SalesService(db)
        sale = Sale(
            customer_id=cid,
            payment_method=PaymentMethod.CASH,
            total_amount=Decimal("1000"),
            final_amount=Decimal("1000"),
        )
        sale.add_item(SaleItem(product_id=pid, quantity=50,
                               unit_price=Decimal("20")))
        assert service.create_sale(sale)


# ═══════════════════════════════════════════════════════════════════
# Gap 6: الإرجاع الذري
# ═══════════════════════════════════════════════════════════════════

class TestGap6AtomicReturn:
    def _make_approved_return(self, db, pid, qty=5, unit_price="15"):
        svc = ReturnService(db)
        invoice = ReturnInvoice(
            return_type=ReturnType.SALE_RETURN,
            return_reason=ReturnReason.DAMAGED,
            refund_method=RefundMethod.CREDIT_NOTE,
        )
        invoice.add_item(ReturnItem(
            product_id=pid, quantity_returned=Decimal(str(qty)),
            unit_price=Decimal(unit_price),
        ))
        return_id = svc.create_return(invoice)
        assert return_id
        assert svc.approve_return(return_id, approved_by=1)
        return svc, return_id

    def test_complete_restores_stock_and_records_movement(self, db):
        """إتمام المرتجع → المخزون يعود + حركة in/return تُسجل + قيد محاسبي"""
        pid = _add_product(db, name="منتج مرتجع", unit="حبة", stock=100)
        svc, return_id = self._make_approved_return(db, pid, qty=5)

        assert svc.complete_return(return_id) is True
        assert _stock_of(db, pid) == 105.0  # 100 + 5

        mv = db.fetch_one(
            "SELECT * FROM stock_movements WHERE reference_type='return' "
            "AND product_id = ? ORDER BY id DESC LIMIT 1",
            (pid,),
        )
        assert mv, "حركة المرتجع غير مسجلة"
        assert int(mv["quantity"]) == 5
        assert mv["movement_type"] == "in"

        # حالة المرتجع = COMPLETED
        row = db.fetch_one("SELECT status FROM return_invoices WHERE id = ?",
                           (return_id,))
        assert row["status"] == "COMPLETED"

    def test_complete_requires_approval(self, db):
        """مرتجع معلق (غير موافق عليه) → رفض الإتمام"""
        pid = _add_product(db, name="منتج مرتجع معلق", unit="حبة", stock=50)
        svc = ReturnService(db)
        invoice = ReturnInvoice(
            return_type=ReturnType.SALE_RETURN,
            return_reason=ReturnReason.DAMAGED,
        )
        invoice.add_item(ReturnItem(product_id=pid,
                                    quantity_returned=Decimal("3"),
                                    unit_price=Decimal("10")))
        return_id = svc.create_return(invoice)
        assert svc.complete_return(return_id) is False
        assert _stock_of(db, pid) == 50.0  # لم يتغير

    def test_get_return_maps_db_columns(self, db):
        """قراءة المرتجع تحاكي أعمدة DB → quantity_returned صحيحة"""
        pid = _add_product(db, name="منتج قراءة", unit="حبة", stock=80)
        svc, return_id = self._make_approved_return(db, pid, qty=7)
        invoice = svc.get_return(return_id)
        assert invoice is not None
        assert len(invoice.items) == 1
        assert Decimal(str(invoice.items[0].quantity_returned)) == Decimal("7")


# ═══════════════════════════════════════════════════════════════════
# Gap 7: دفعات الموردين FIFO
# ═══════════════════════════════════════════════════════════════════

class TestGap7SupplierFifo:
    def _make_supplier_with_purchases(self, db, supplier_name="مورد FIFO"):
        row = db.fetch_one(
            "SELECT id FROM suppliers WHERE name = ?", (supplier_name,)
        )
        if row:
            sid = int(row["id"])
        else:
            sid = db.execute_insert(
                "INSERT INTO suppliers (name, current_balance) VALUES (?, 0)",
                (supplier_name,),
            )

        # نظف مشتريات سابقة لنفس المورد + تخصيصاتها (معزولة للاختبار)
        db.execute_non_query(
            "DELETE FROM payment_allocations WHERE purchase_id IN "
            "(SELECT id FROM purchases WHERE supplier_id = ?)",
            (sid,),
        )
        db.execute_non_query("DELETE FROM purchases WHERE supplier_id = ?", (sid,))

        # فاتورة أقدم (1000) ثم أحدث (500)
        p1 = db.execute_insert(
            """
            INSERT INTO purchases (invoice_number, supplier_id, total_amount,
                                   final_amount, purchase_date)
            VALUES ('INV-OLD-1', ?, 1000, 1000, date('now', '-10 day'))
            """,
            (sid,),
        )
        p2 = db.execute_insert(
            """
            INSERT INTO purchases (invoice_number, supplier_id, total_amount,
                                   final_amount, purchase_date)
            VALUES ('INV-NEW-1', ?, 500, 500, date('now'))
            """,
            (sid,),
        )
        return sid, p1, p2

    def _insert_payment(self, db, supplier_id: int, amount: float) -> int:
        """إنشاء صف دفعة حقيقي (FK يتطلب payment_id موجوداً)"""
        return db.execute_insert(
            """
            INSERT INTO payments (
                payment_number, payment_type, payment_method, status,
                amount, currency, payment_date, supplier_id, entity_id,
                created_at, updated_at
            ) VALUES (?, 'supplier_payment', 'cash', 'completed',
                      ?, 'DZD', date('now'), ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (f"PAY-FIFO-{supplier_id}-{amount}", amount, supplier_id, supplier_id),
        )

    def test_fifo_allocates_oldest_first(self, db):
        """دفعة 800 → 800 للأقدم (جزئية) + صفر للأحدث"""
        db_svc = PaymentService(db)
        sid, p1, p2 = self._make_supplier_with_purchases(db)
        pay_id = self._insert_payment(db, sid, 800.0)

        allocs = db_svc._allocate_supplier_payment_fifo(
            payment_id=pay_id, supplier_id=sid, amount=Decimal("800")
        )
        assert len(allocs) == 1
        assert allocs[0]["purchase_id"] == p1
        assert allocs[0]["purchase_status"] == "partial"
        assert allocs[0]["purchase_paid"] == 800.0

        row = db.fetch_one("SELECT paid_amount, payment_status FROM purchases WHERE id = ?", (p1,))
        assert float(row["paid_amount"]) == 800.0
        assert row["payment_status"] == "partial"

    def test_fifo_spills_to_next_invoice(self, db):
        """دفعة 1200 → تسدد الأقدم (1000) + 200 للأحدث (جزئية)"""
        db_svc = PaymentService(db)
        sid, p1, p2 = self._make_supplier_with_purchases(db)
        pay_id = self._insert_payment(db, sid, 1200.0)

        allocs = db_svc._allocate_supplier_payment_fifo(
            payment_id=pay_id, supplier_id=sid, amount=Decimal("1200")
        )
        assert len(allocs) == 2
        assert allocs[0]["purchase_id"] == p1
        assert allocs[0]["purchase_status"] == "paid"
        assert allocs[1]["purchase_id"] == p2
        assert allocs[1]["allocated_amount"] == 200.0

        r1 = db.fetch_one("SELECT payment_status FROM purchases WHERE id = ?", (p1,))
        r2 = db.fetch_one("SELECT paid_amount FROM purchases WHERE id = ?", (p2,))
        assert r1["payment_status"] == "paid"
        assert float(r2["paid_amount"]) == 200.0

    def test_get_payment_allocations(self, db):
        """قراءة التخصيصات من payment_allocations"""
        db_svc = PaymentService(db)
        sid, p1, _ = self._make_supplier_with_purchases(db)
        pay_id = self._insert_payment(db, sid, 300.0)
        db_svc._allocate_supplier_payment_fifo(
            payment_id=pay_id, supplier_id=sid, amount=Decimal("300")
        )
        rows = db_svc.get_payment_allocations(pay_id)
        assert len(rows) == 1
        assert rows[0]["purchase_id"] == p1
        assert float(rows[0]["allocated_amount"]) == 300.0


# ═══════════════════════════════════════════════════════════════════
# Gap 8: المصاريف
# ═══════════════════════════════════════════════════════════════════

class TestGap8Expenses:
    def test_create_expense_pending(self, db):
        svc = ExpenseService(db)
        eid = svc.create_expense(
            description="مصروف كهرباء", amount=Decimal("2500"),
            category_id=None, expense_date=date.today(),
        )
        assert eid
        exp = svc.get_expense(eid)
        assert exp["status"] == "pending"
        assert exp["expense_number"].startswith("EXP-")

    def test_reject_invalid_amount(self, db):
        svc = ExpenseService(db)
        assert svc.create_expense(description="صفر", amount=Decimal("0")) is None
        assert svc.create_expense(description="", amount=Decimal("10")) is None

    def test_approve_creates_journal_entry(self, db):
        svc = ExpenseService(db)
        eid = svc.create_expense(
            description="إيجار محل", amount=Decimal("50000"),
            expense_date=date.today(),
        )
        assert svc.approve_expense(eid, approved_by=1) is True

        exp = svc.get_expense(eid)
        assert exp["status"] == "approved"
        assert exp["journal_id"] is not None

        # القيد: مدين المصروف / دائن الصندوق
        lines = db.fetch_all(
            "SELECT debit_amount, credit_amount FROM journal_lines "
            "WHERE journal_id = ?", (exp["journal_id"],),
        )
        if lines:
            debits = sum(float(l["debit_amount"] or 0) for l in lines)
            credits = sum(float(l["credit_amount"] or 0) for l in lines)
            assert abs(debits - 50000) < 0.01
            assert abs(credits - 50000) < 0.01

    def test_double_approve_blocked(self, db):
        svc = ExpenseService(db)
        eid = svc.create_expense(description="صيانة", amount=Decimal("100"))
        assert svc.approve_expense(eid) is True
        assert svc.approve_expense(eid) is False  # موافقة مزدوجة ممنوعة

    def test_approved_expense_cannot_be_deleted(self, db):
        svc = ExpenseService(db)
        eid = svc.create_expense(description="مصروف محاسبي", amount=Decimal("300"))
        svc.approve_expense(eid)
        assert svc.delete_expense(eid) is False
        pending = svc.create_expense(description="مصروف معلق", amount=Decimal("30"))
        assert svc.delete_expense(pending) is True

    def test_recurring_monthly_catchup(self, db):
        """قالب شهري متأخر 3 أشهر → توليد 3 مصاريف + تقديم الاستحقاق"""
        svc = ExpenseService(db)
        overdue = date.today() - timedelta(days=95)  # ~3 أشهر
        rid = svc.create_recurring(
            name="إيجار مستودع", amount=Decimal("20000"),
            frequency="monthly", next_due_date=overdue, auto_approve=True,
        )
        assert rid

        generated = svc.generate_due_expenses()
        mine = [g for g in generated if g["recurring_id"] == rid]
        assert len(mine) == 4  # 95 يوم ≈ 4 دورات شهرية متقاطعة

        # كل المصاريف المولدة موافق عليها (auto_approve)
        for g in mine:
            exp = svc.get_expense(g["expense_id"])
            assert exp["status"] == "approved"

        # الاستحقاق التالي في المستقبل
        tpl = [t for t in svc.get_recurring() if t["id"] == rid][0]
        assert date.fromisoformat(str(tpl["next_due_date"])) > date.today()

    def test_expense_statistics(self, db):
        svc = ExpenseService(db)
        stats = svc.get_expense_statistics()
        assert stats["total"] > 0
        assert stats["count"] > 0
        assert len(stats["by_category"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])
