#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبارات سير عمل مرتجع المشتريات (GAP-3.2) — قاعدة بيانات SQLite حقيقية مؤقتة.

Purchase Return Workflow tests (GAP-3.2) against a real temp SQLite DB:

1. إنشاء مسودة → رقم المرتجع + الحالة + البنود
2. فرض الكمية القابلة للإرجاع (المشترى − المرتجع)
3. الموافقة تعين الدفعات الأحدث انتهاءً أولاً + رفض عند نقص المخزون
4. الإتمام (إشعار دائن): خصم الدفعة/المخزون + حركة out/purchase_return
   + قيد مدين 2100 / دائن 4100 + تسوية المورد
5. الإتمام (استرداد نقدي): القيد دائن الصندوق + تسوية المورد
6. الذرية: فشل منتصف التدفق → لا تغييرات (rollback)
7. الإلغاء: مسودة/معتمد → ملغى بدون أثر؛ المكتمل → خطأ
8. حساب الكمية القابلة للإرجاع عبر عدة مشتريات
9. التقسيم عبر دفعات متعددة (30 + 70 → إرجاع 50)
"""

import os
import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database_manager import DatabaseManager
from src.models.product import Product, ProductManager
from src.services.purchase_return_service import (
    PurchaseReturnError,
    PurchaseReturnService,
    PurchaseReturnStatus,
)


# ═══════════════════════════════════════════════════════════════════
# Fixture: real temp SQLite DB (نفس نمط test_business_gaps.py)
# ═══════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════
# Seed helpers — بذور البيانات
# ═══════════════════════════════════════════════════════════════════

_accounting_ready = False


def _ensure_accounting_schema(db):
    """ضمان جداول المحاسبة + الحسابات المستخدمة (idempotent).

    المخططات من migrations/003_create_accounting_system.sql — نفس البنية.
    Ensures the accounting tables (same DDL as migration 003) and seeds
    the accounts the purchase-return JE needs: 1000 cash, 2100 A/P,
    4100 inventory.
    """
    global _accounting_ready
    if _accounting_ready:
        return
    db.execute_non_query("""
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT UNIQUE NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            sub_type TEXT,
            description TEXT,
            normal_side TEXT DEFAULT 'DEBIT',
            is_header BOOLEAN DEFAULT 0,
            parent_account_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            is_locked BOOLEAN DEFAULT 0,
            opening_balance DECIMAL(15,2) DEFAULT 0.00,
            current_balance DECIMAL(15,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute_non_query("""
        CREATE TABLE IF NOT EXISTS general_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_number TEXT UNIQUE NOT NULL,
            entry_date TIMESTAMP NOT NULL,
            reference_type TEXT,
            reference_id INTEGER,
            description TEXT,
            notes TEXT,
            is_posted BOOLEAN DEFAULT 0,
            posted_date TIMESTAMP,
            posted_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute_non_query("""
        CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            account_code TEXT,
            account_name TEXT,
            debit_amount DECIMAL(15,2) DEFAULT 0.00,
            credit_amount DECIMAL(15,2) DEFAULT 0.00,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (journal_id) REFERENCES general_journal(id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id)
        )
    """)
    for code, name, atype, side in (
        ("1000", "الصندوق", "Asset", "DEBIT"),          # cash
        ("1100", "الصندوق البديل", "Asset", "DEBIT"),   # cash fallback
        ("2100", "حسابات الموردين", "Liability", "CREDIT"),  # A/P
        ("4100", "المخزون", "Asset", "DEBIT"),          # inventory
    ):
        db.execute_non_query(
            """
            INSERT OR IGNORE INTO chart_of_accounts
                (account_code, account_name, account_type, normal_side, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (code, name, atype, side),
        )
    _accounting_ready = True


_counter = {"n": 0}


def _add_product(db, name, stock=1000.0, cost="10.00", price="15.00") -> int:
    """إضافة منتج حقيقي عبر ProductManager — add a real product"""
    _counter["n"] += 1
    pm = ProductManager(db)
    product = Product(
        name=f"{name}-{_counter['n']}", unit="حبة",
        cost_price=Decimal(cost), selling_price=Decimal(price),
        current_stock=stock,
    )
    pid = pm.create_product(product)
    assert pid, "فشل إنشاء المنتج"
    return pid


def _add_supplier(db, name, balance="500") -> int:
    """إضافة مورد مباشرة (current_balance موجود عبر _upgrade_existing_schema)"""
    _counter["n"] += 1
    sid = db.execute_insert(
        "INSERT INTO suppliers (name, current_balance) VALUES (?, ?)",
        (f"{name}-{_counter['n']}", float(Decimal(balance))),
    )
    assert sid, "فشل إنشاء المورد"
    return sid


def _add_batch(db, product_id, batch_number, quantity, cost="10.00",
               expiry=None, supplier_id=None) -> int:
    """إضافة دفعة مباشرة إلى جدول batches — insert a batch directly"""
    bid = db.execute_insert(
        """
        INSERT INTO batches (product_id, batch_number, quantity, cost_price,
                             expiry_date, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (product_id, batch_number, quantity, cost, expiry, supplier_id),
    )
    assert bid, "فشل إنشاء الدفعة"
    return bid


def _add_purchase(db, supplier_id, product_qty_cost_list,
                  paid="0", invoice_suffix=None) -> int:
    """إضافة فاتورة شراء + بنودها — insert purchase + purchase_items"""
    _counter["n"] += 1
    total = sum(q * Decimal(c) for q, _, c in product_qty_cost_list)
    suffix = invoice_suffix or _counter["n"]
    pid = db.execute_insert(
        """
        INSERT INTO purchases (invoice_number, supplier_id, total_amount,
                               final_amount, purchase_date, status,
                               paid_amount, payment_status)
        VALUES (?, ?, ?, ?, date('now'), 'received', ?, 'partial')
        """,
        (f"PINV-TEST-{suffix}", supplier_id, float(total), float(total),
         float(Decimal(paid))),
    )
    assert pid, "فشل إنشاء فاتورة الشراء"
    for qty, prod_id, cost in product_qty_cost_list:
        db.execute_insert(
            """
            INSERT INTO purchase_items (purchase_id, product_id, quantity,
                                        unit_cost, total_cost)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pid, prod_id, qty, cost, float(qty * Decimal(cost))),
        )
    return pid


def _batch_qty(db, batch_id: int) -> Decimal:
    row = db.fetch_one("SELECT quantity FROM batches WHERE id = ?", (batch_id,))
    return Decimal(str(row.get("quantity", 0) or 0))


def _stock_of(db, product_id: int) -> Decimal:
    row = db.fetch_one(
        "SELECT current_stock FROM products WHERE id = ?", (product_id,)
    )
    return Decimal(str(row.get("current_stock", 0) or 0))


def _supplier_balance(db, supplier_id: int) -> Decimal:
    row = db.fetch_one(
        "SELECT current_balance FROM suppliers WHERE id = ?", (supplier_id,)
    )
    return Decimal(str(row.get("current_balance", 0) or 0))


@pytest.fixture()
def svc(db):
    """خدمة مرتجعات المشتريات على قاعدة الاختبار"""
    _ensure_accounting_schema(db)
    return PurchaseReturnService(db)


# ═══════════════════════════════════════════════════════════════════
# 1) إنشاء مسودة — Draft creation happy path
# ═══════════════════════════════════════════════════════════════════

class TestDraftCreation:
    def test_create_draft_happy_path(self, db, svc):
        """مسودة سليمة → رقم PR-YYYYMMDD-XXXX + حالة draft + بنود محفوظة"""
        sid = _add_supplier(db, "مورد مسودة")
        pid = _add_product(db, "منتج مسودة")
        purchase_id = _add_purchase(db, sid, [(100, pid, "10.00")])

        return_id = svc.create_return(
            supplier_id=sid,
            items=[{"product_id": pid, "quantity": 5}],
            purchase_id=purchase_id,
            reason="تالف",
            notes="اختبار",
            user_id=1,
        )
        assert return_id

        ret = svc.get_return(return_id)
        assert ret is not None
        # صيغة الرقم PR-YYYYMMDD-XXXX
        assert re.fullmatch(r"PR-\d{8}-\d{4}", ret["return_number"])
        assert ret["status"] == PurchaseReturnStatus.DRAFT.value
        assert ret["supplier_id"] == sid
        assert ret["purchase_id"] == purchase_id
        assert len(ret["items"]) == 1
        assert Decimal(str(ret["items"][0]["quantity"])) == Decimal("5")
        assert Decimal(str(ret["items"][0]["product_id"])) == pid
        # الكمية لم تُخصم بعد (مسودة)
        assert _stock_of(db, pid) == Decimal("1000")
        # list_returns filter يعمل
        rows = svc.list_returns(supplier_id=sid, status="draft")
        assert any(r["id"] == return_id for r in rows)

    def test_create_validations(self, db, svc):
        """رفض: مورد غير موجود / بند فارغ / كمية صفرية / منتج غير موجود"""
        sid = _add_supplier(db, "مورد تحقق")
        pid = _add_product(db, "منتج تحقق")
        _add_purchase(db, sid, [(10, pid, "10.00")])

        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=999999,
                              items=[{"product_id": pid, "quantity": 1}])
        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=sid, items=[])
        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=sid,
                              items=[{"product_id": pid, "quantity": 0}])
        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=sid,
                              items=[{"product_id": 999999, "quantity": 1}])


# ═══════════════════════════════════════════════════════════════════
# 2) فرض الكمية القابلة للإرجاع — Returnable quantity enforcement
# ═══════════════════════════════════════════════════════════════════

class TestReturnableQuantity:
    def test_over_return_rejected_exact_fit_allowed(self, db, svc):
        """شراء 100: إرجاع 60 ✓ → 50 إضافية ✗ (60+50>100) → 40 إضافية ✓"""
        sid = _add_supplier(db, "مورد حق الإرجاع")
        pid = _add_product(db, "منتج حق الإرجاع")
        purchase_id = _add_purchase(db, sid, [(100, pid, "10.00")])

        r1 = svc.create_return(supplier_id=sid,
                               items=[{"product_id": pid, "quantity": 60}],
                               purchase_id=purchase_id)
        assert r1

        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=sid,
                              items=[{"product_id": pid, "quantity": 50}],
                              purchase_id=purchase_id)

        r2 = svc.create_return(supplier_id=sid,
                               items=[{"product_id": pid, "quantity": 40}],
                               purchase_id=purchase_id)
        assert r2

    def test_cancelled_return_frees_quota(self, db, svc):
        """إلغاء مرتجع يحرر الكمية (غير الملغى فقط يحتسب)"""
        sid = _add_supplier(db, "مورد إلغاء الحق")
        pid = _add_product(db, "منتج إلغاء الحق")
        purchase_id = _add_purchase(db, sid, [(10, pid, "10.00")])

        r1 = svc.create_return(supplier_id=sid,
                               items=[{"product_id": pid, "quantity": 10}],
                               purchase_id=purchase_id)
        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=sid,
                              items=[{"product_id": pid, "quantity": 1}],
                              purchase_id=purchase_id)
        assert svc.cancel_return(r1) is True
        r2 = svc.create_return(supplier_id=sid,
                               items=[{"product_id": pid, "quantity": 10}],
                               purchase_id=purchase_id)
        assert r2


# ═══════════════════════════════════════════════════════════════════
# 3) الموافقة — Approval (FEFO-reverse batch assignment)
# ═══════════════════════════════════════════════════════════════════

class TestApproval:
    def test_approve_picks_latest_expiry_batch(self, db, svc):
        """الموافقة تعين الدفعة الأحدث انتهاءً (أقصى تاريخ صلاحية) ولم تخصم بعد"""
        sid = _add_supplier(db, "مورد موافقة")
        pid = _add_product(db, "منتج موافقة", stock=200)
        _add_purchase(db, sid, [(100, pid, "10.00")])
        old_batch = _add_batch(db, pid, "B-OLD", 100, cost="10.00",
                               expiry="2025-01-01", supplier_id=sid)
        new_batch = _add_batch(db, pid, "B-NEW", 100, cost="12.00",
                               expiry="2026-06-01", supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 10}],
        )
        assert svc.approve_return(return_id, approver_id=1) is True

        ret = svc.get_return(return_id)
        assert ret["status"] == PurchaseReturnStatus.APPROVED.value
        assert ret["approved_by"] == 1
        assert ret["approved_at"]
        assert ret["items"][0]["batch_id"] == new_batch  # الأحدث انتهاءً
        # لا خصم قبل الإتمام
        assert _batch_qty(db, new_batch) == Decimal("100")
        assert _batch_qty(db, old_batch) == Decimal("100")
        assert _stock_of(db, pid) == Decimal("200")

    def test_approve_requires_draft(self, db, svc):
        """الموافقة على معتمد مرة أخرى → خطأ انتقال حالة"""
        sid = _add_supplier(db, "مورد موافقة مزدوجة")
        pid = _add_product(db, "منتج موافقة مزدوجة")
        _add_purchase(db, sid, [(10, pid, "10.00")])
        _add_batch(db, pid, "B-D", 10, cost="10.00", expiry="2026-01-01",
                   supplier_id=sid)
        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 2}])
        assert svc.approve_return(return_id, approver_id=1) is True
        with pytest.raises(PurchaseReturnError):
            svc.approve_return(return_id, approver_id=1)

    def test_approve_rejects_insufficient_stock(self, db, svc):
        """مخزون الدفعات غير كافٍ → PurchaseReturnError + بقاء الحالة draft"""
        sid = _add_supplier(db, "مورد نقص")
        pid = _add_product(db, "منتج نقص")
        _add_purchase(db, sid, [(10, pid, "10.00")])
        _add_batch(db, pid, "B-TINY", 3, cost="10.00", expiry="2026-01-01",
                   supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 10}])
        with pytest.raises(PurchaseReturnError):
            svc.approve_return(return_id, approver_id=1)
        # التراجع: الحالة تبقى مسودة
        ret = svc.get_return(return_id)
        assert ret["status"] == PurchaseReturnStatus.DRAFT.value


# ═══════════════════════════════════════════════════════════════════
# 4) الإتمام (إشعار دائن) — Complete with credit_note
# ═══════════════════════════════════════════════════════════════════

class TestCompleteCreditNote:
    def test_complete_credit_note_full_flow(self, db, svc):
        """إتمام كامل: دفعة/مخزون/حركة/قيد/تسوية/credit_note_amount"""
        sid = _add_supplier(db, "مورد إتمام", balance="500")
        pid = _add_product(db, "منتج إتمام", stock=100)
        purchase_id = _add_purchase(db, sid, [(50, pid, "10.00")],
                                    paid="500")  # مدفوعة جزئياً 500/500
        batch_id = _add_batch(db, pid, "B-COMP", 50, cost="10.00",
                              expiry="2026-09-01", supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 10}],
            purchase_id=purchase_id)
        assert svc.approve_return(return_id, approver_id=1) is True
        assert svc.complete_return(return_id, user_id=2) is True

        ret = svc.get_return(return_id)
        assert ret["status"] == PurchaseReturnStatus.COMPLETED.value
        assert ret["completed_at"]
        assert Decimal(str(ret["credit_note_amount"])) == Decimal("100.00")

        # الدفعة والمخزون
        assert _batch_qty(db, batch_id) == Decimal("40")
        assert _stock_of(db, pid) == Decimal("90")

        # حركة المخزون out/purchase_return
        mv = db.fetch_one(
            "SELECT * FROM stock_movements WHERE reference_type='purchase_return' "
            "AND reference_id = ? ORDER BY id DESC LIMIT 1", (return_id,))
        assert mv, "حركة المرتجع غير مسجلة"
        assert mv["movement_type"] == "out"
        assert int(mv["quantity"]) == 10
        assert mv["batch_id"] == batch_id
        assert mv["product_id"] == pid

        # القيد المحاسبي: مدين 2100 / دائن 4100 بمبلغ 100
        je = db.fetch_one(
            "SELECT id FROM general_journal WHERE reference_type='purchase_return' "
            "AND reference_id = ? ORDER BY id DESC LIMIT 1", (return_id,))
        assert je, "القيد المحاسبي غير موجود"
        lines = db.fetch_all(
            "SELECT * FROM journal_lines WHERE journal_id = ?", (je["id"],))
        assert len(lines) >= 2
        debit_ap = [l for l in lines
                    if l["account_code"] == "2100" and float(l["debit_amount"] or 0) > 0]
        credit_inv = [l for l in lines
                      if l["account_code"] == "4100" and float(l["credit_amount"] or 0) > 0]
        assert debit_ap and credit_inv, "أسطر القيد 2100/4100 مفقودة"
        assert abs(float(debit_ap[0]["debit_amount"]) - 100.0) < 0.01
        assert abs(float(credit_inv[0]["credit_amount"]) - 100.0) < 0.01

        # تسوية المورد: الرصيد 500 → 400
        assert _supplier_balance(db, sid) == Decimal("400")
        # paid_amount: 500 → 400 (إشعار دائن يخفض المسدد — floor 0)
        prow = db.fetch_one("SELECT paid_amount, payment_status, remaining_amount "
                            "FROM purchases WHERE id = ?", (purchase_id,))
        assert float(prow["paid_amount"]) == 400.0
        assert prow["payment_status"] == "partial"
        assert float(prow["remaining_amount"]) == 100.0

    def test_complete_requires_approval(self, db, svc):
        """مسودة لا يمكن إتمامها"""
        sid = _add_supplier(db, "مورد بدون موافقة")
        pid = _add_product(db, "منتج بدون موافقة")
        _add_purchase(db, sid, [(10, pid, "10.00")])
        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 2}])
        with pytest.raises(PurchaseReturnError):
            svc.complete_return(return_id)


# ═══════════════════════════════════════════════════════════════════
# 5) الإتمام (استرداد نقدي) — Complete with cash_refund
# ═══════════════════════════════════════════════════════════════════

class TestCompleteCashRefund:
    def test_complete_cash_refund_credits_cash(self, db, svc):
        """استرداد نقدي → القيد دائن الصندوق + تسوية المورد"""
        sid = _add_supplier(db, "مورد نقدي", balance="300")
        pid = _add_product(db, "منتج نقدي", stock=80)
        _add_purchase(db, sid, [(20, pid, "5.00")])
        batch_id = _add_batch(db, pid, "B-CASH", 20, cost="5.00",
                              expiry="2026-08-01", supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 8}])
        assert svc.approve_return(return_id, approver_id=1) is True
        assert svc.complete_return(return_id, user_id=3,
                                   refund_method="cash_refund") is True

        # القيد: مدين 2100 / دائن الصندوق (1000)
        je = db.fetch_one(
            "SELECT id FROM general_journal WHERE reference_type='purchase_return' "
            "AND reference_id = ? ORDER BY id DESC LIMIT 1", (return_id,))
        assert je, "القيد النقدي غير موجود"
        lines = db.fetch_all(
            "SELECT * FROM journal_lines WHERE journal_id = ?", (je["id"],))
        credit_cash = [l for l in lines
                       if l["account_code"] == "1000" and float(l["credit_amount"] or 0) > 0]
        assert credit_cash, "لا يوجد سطر دائن للصندوق 1000"
        assert abs(float(credit_cash[0]["credit_amount"]) - 40.0) < 0.01  # 8 × 5

        # المخزون والدفعة والرصيد
        assert _batch_qty(db, batch_id) == Decimal("12")
        assert _stock_of(db, pid) == Decimal("72")
        assert _supplier_balance(db, sid) == Decimal("260")


# ═══════════════════════════════════════════════════════════════════
# 6) الذرية — Atomicity (mid-flow failure → full rollback)
# ═══════════════════════════════════════════════════════════════════

class TestAtomicity:
    def test_mid_flow_failure_rolls_back_everything(self, db, svc, monkeypatch):
        """فشل حركة المخزون للبند الثاني → كل شيء يعود كما كان"""
        sid = _add_supplier(db, "مورد ذرية", balance="200")
        pid1 = _add_product(db, "منتج ذرية 1", stock=50)
        pid2 = _add_product(db, "منتج ذرية 2", stock=50)
        _add_purchase(db, sid, [(10, pid1, "10.00"), (10, pid2, "20.00")])
        b1 = _add_batch(db, pid1, "B-A1", 10, cost="10.00", expiry="2026-05-01",
                        supplier_id=sid)
        b2 = _add_batch(db, pid2, "B-A2", 10, cost="20.00", expiry="2026-06-01",
                        supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid,
            items=[{"product_id": pid1, "quantity": 4},
                   {"product_id": pid2, "quantity": 6}])
        assert svc.approve_return(return_id, approver_id=1) is True

        original = svc._insert_stock_movement
        calls = {"n": 0}

        def flaky(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] >= 2:  # فشل عند حركة البند الثاني
                raise RuntimeError("محاكاة فشل منتصف التدفق")
            return original(*args, **kwargs)

        monkeypatch.setattr(svc, "_insert_stock_movement", flaky)

        with pytest.raises(RuntimeError):
            svc.complete_return(return_id, user_id=1)

        # لا تغييرات: الدفعات والمخزون والرصيد والحالة
        assert _batch_qty(db, b1) == Decimal("10")
        assert _batch_qty(db, b2) == Decimal("10")
        assert _stock_of(db, pid1) == Decimal("50")
        assert _stock_of(db, pid2) == Decimal("50")
        assert _supplier_balance(db, sid) == Decimal("200")
        ret = svc.get_return(return_id)
        assert ret["status"] == PurchaseReturnStatus.APPROVED.value
        assert Decimal(str(ret["credit_note_amount"] or 0)) == Decimal("0")
        # لا حركات ولا قيود مسجلة
        mv_rows = db.fetch_all(
            "SELECT id FROM stock_movements WHERE reference_type='purchase_return' "
            "AND reference_id = ?", (return_id,))
        assert mv_rows == []
        je_rows = db.fetch_all(
            "SELECT id FROM general_journal WHERE reference_type='purchase_return' "
            "AND reference_id = ?", (return_id,))
        assert je_rows == []

    def test_complete_succeeds_after_rollback(self, db, svc, monkeypatch):
        """بعد فشل التراجع يمكن الإتمام مجدداً بنجاح"""
        sid = _add_supplier(db, "مورد ذرية ثانية", balance="100")
        pid = _add_product(db, "منتج ذرية ثانية", stock=30)
        _add_purchase(db, sid, [(10, pid, "10.00")])
        _add_batch(db, pid, "B-R", 10, cost="10.00", expiry="2026-04-01",
                   supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 5}])
        svc.approve_return(return_id, approver_id=1)

        monkeypatch.setattr(
            svc, "_insert_stock_movement",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("فشل أول")),
        )
        with pytest.raises(RuntimeError):
            svc.complete_return(return_id)
        assert _batch_qty(db, _batch_id_of(db, pid)) == Decimal("10")

        # إعادة المحاولة بدون التدخل → نجاح
        monkeypatch.undo()
        assert svc.complete_return(return_id) is True
        assert _batch_qty(db, _batch_id_of(db, pid)) == Decimal("5")
        assert _stock_of(db, pid) == Decimal("25")


def _batch_id_of(db, product_id: int) -> int:
    row = db.fetch_one("SELECT id FROM batches WHERE product_id = ? "
                       "ORDER BY id DESC LIMIT 1", (product_id,))
    return int(row["id"])


# ═══════════════════════════════════════════════════════════════════
# 7) الإلغاء — Cancel
# ═══════════════════════════════════════════════════════════════════

class TestCancel:
    def test_cancel_draft_no_stock_change(self, db, svc):
        """إلغاء مسودة → ملغاة بدون أي أثر على المخزون"""
        sid = _add_supplier(db, "مورد إلغاء")
        pid = _add_product(db, "منتج إلغاء", stock=100)
        _add_purchase(db, sid, [(20, pid, "10.00")])
        batch_id = _add_batch(db, pid, "B-X", 20, cost="10.00",
                              expiry="2026-07-01", supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 5}])
        assert svc.cancel_return(return_id, user_id=1) is True

        ret = svc.get_return(return_id)
        assert ret["status"] == PurchaseReturnStatus.CANCELLED.value
        assert _batch_qty(db, batch_id) == Decimal("20")
        assert _stock_of(db, pid) == Decimal("100")

    def test_cancel_approved_releases_nothing(self, db, svc):
        """إلغاء معتمد → الدفعات لم تُخصم أصلاً (الموافقة تعيين فقط)"""
        sid = _add_supplier(db, "مورد إلغاء معتمد")
        pid = _add_product(db, "منتج إلغاء معتمد", stock=100)
        _add_purchase(db, sid, [(20, pid, "10.00")])
        batch_id = _add_batch(db, pid, "B-Y", 20, cost="10.00",
                              expiry="2026-07-01", supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 5}])
        svc.approve_return(return_id, approver_id=1)
        assert svc.cancel_return(return_id) is True
        assert _batch_qty(db, batch_id) == Decimal("20")  # لم تُخصم
        assert _stock_of(db, pid) == Decimal("100")

    def test_cancel_completed_raises(self, db, svc):
        """إلغاء مرتجع مكتمل → PurchaseReturnError"""
        sid = _add_supplier(db, "مورد إلغاء مكتمل")
        pid = _add_product(db, "منتج إلغاء مكتمل", stock=100)
        _add_purchase(db, sid, [(20, pid, "10.00")])
        _add_batch(db, pid, "B-Z", 20, cost="10.00", expiry="2026-07-01",
                   supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 5}])
        svc.approve_return(return_id, approver_id=1)
        assert svc.complete_return(return_id) is True
        with pytest.raises(PurchaseReturnError):
            svc.cancel_return(return_id)


# ═══════════════════════════════════════════════════════════════════
# 8) الكمية القابلة للإرجاع عبر عدة مشتريات — get_returnable_quantity
# ═══════════════════════════════════════════════════════════════════

class TestGetReturnableQuantity:
    def test_across_multiple_purchases(self, db, svc):
        """30 + 70 من مشتريين → قابل للإرجاع 100 → بعد مرتجع 30 يبقى 70"""
        sid = _add_supplier(db, "مورد متعدد")
        pid = _add_product(db, "منتج متعدد")
        p1 = _add_purchase(db, sid, [(30, pid, "10.00")], invoice_suffix="M1")
        p2 = _add_purchase(db, sid, [(70, pid, "10.00")], invoice_suffix="M2")

        assert svc.get_returnable_quantity(sid, pid) == Decimal("100")
        assert svc.get_returnable_quantity(sid, pid, purchase_id=p1) == Decimal("30")

        r1 = svc.create_return(supplier_id=sid,
                               items=[{"product_id": pid, "quantity": 30}])
        assert svc.get_returnable_quantity(sid, pid) == Decimal("70")
        # فحص مرتبط بفاتورة معينة: المشترى محدود بالفاتورة، والمرتجع على مستوى المورد
        assert svc.get_returnable_quantity(sid, pid, purchase_id=p1) == Decimal("0")
        assert svc.get_returnable_quantity(sid, pid, purchase_id=p2) == Decimal("40")

        # منتج آخر لم يُشترِه المورد → صفر
        other = _add_product(db, "منتج غير مشترى")
        assert svc.get_returnable_quantity(sid, other) == Decimal("0")

        # زائد عن الحق مرفوض
        with pytest.raises(PurchaseReturnError):
            svc.create_return(supplier_id=sid,
                              items=[{"product_id": pid, "quantity": 71}])


# ═══════════════════════════════════════════════════════════════════
# 9) التقسيم عبر دفعات متعددة — Multi-batch split (30 + 70 → return 50)
# ═══════════════════════════════════════════════════════════════════

class TestMultiBatchSplit:
    def test_return_50_splits_across_two_batches(self, db, svc):
        """دفعات 30 (أحدث) + 70 (أقدم) → إرجاع 50: 30 من الأحدث + 20 من الأقدم"""
        sid = _add_supplier(db, "مورد تقسيم", balance="1000")
        pid = _add_product(db, "منتج تقسيم", stock=100)
        _add_purchase(db, sid, [(100, pid, "10.00")])
        newest = _add_batch(db, pid, "B-N30", 30, cost="10.00",
                            expiry="2026-12-01", supplier_id=sid)
        older = _add_batch(db, pid, "B-O70", 70, cost="9.00",
                           expiry="2025-03-01", supplier_id=sid)

        return_id = svc.create_return(
            supplier_id=sid, items=[{"product_id": pid, "quantity": 50}])
        svc.approve_return(return_id, approver_id=1)

        items = svc.get_return(return_id)["items"]
        assert len(items) == 2  # تقسيم على دفعتين
        qty_by_batch = {i["batch_id"]: Decimal(str(i["quantity"])) for i in items}
        assert qty_by_batch[newest] == Decimal("30")  # الأحدث أولاً
        assert qty_by_batch[older] == Decimal("20")
        assert sum(qty_by_batch.values()) == Decimal("50")

        # الإتمام: حركتان مجموعهما 50 + خصم الدفعات
        assert svc.complete_return(return_id) is True
        assert _batch_qty(db, newest) == Decimal("0")
        assert _batch_qty(db, older) == Decimal("50")
        assert _stock_of(db, pid) == Decimal("50")

        moves = db.fetch_all(
            "SELECT * FROM stock_movements WHERE reference_type='purchase_return' "
            "AND reference_id = ?", (return_id,))
        assert len(moves) == 2
        move_total = sum(int(m["quantity"]) for m in moves)
        assert move_total == 50
        move_by_batch = {m["batch_id"]: int(m["quantity"]) for m in moves}
        assert move_by_batch[newest] == 30
        assert move_by_batch[older] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])
