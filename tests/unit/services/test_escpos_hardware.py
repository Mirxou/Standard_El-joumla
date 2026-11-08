#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات GAP-2.2: طابعة الإيصالات الحرارية ESC/POS ودرج النقدية — قاعدة بيانات حقيقية:

- Migration 009: جدول hardware_config (إنشاء + idempotent + فهرس)
- HardwareConfig: البحث عن الجهاز الافتراضي وتحليل JSON
- render_receipt_text: بناء نص الإيصال النقي (أعمدة ثابتة، عربية، DECIMAL)
- ESCPOSPrinterService: وضع الملف الحقيقي + وضع dry_run + تقارير X/Z
- CashDrawerService: الفتح عبر الطابعة + حالة الدرج + التدقيق
"""

import importlib
import json
import os
import sys
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database_manager import DatabaseManager
from src.services.cash_drawer_service import CashDrawerService, DrawerStatus
from src.services.escpos_printer_service import (
    CASH_DRAWER_KICK,
    DOUBLE_SIZE_OFF,
    DOUBLE_SIZE_ON,
    FULL_CUT,
    INIT,
    PARTIAL_CUT,
    ESCPOSPrinterService,
    HardwareConfig,
    feed_lines,
    render_receipt_text,
)

# تحميل الترحيل 009 (اسم الموديل يبدأ برقم — يُستورد عبر importlib)
MIGRATION_009 = importlib.import_module(
    "src.core.local_migrations.migrations.009_add_hardware_config"
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures — التهيئة
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
    # تطبيق ترحيل 009 لضمان وجود جدول hardware_config
    MIGRATION_009.upgrade(manager)
    assert manager.fetch_one(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'hardware_config'"
    ) is not None

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


def _clear_hardware_config(db) -> None:
    """تفريغ جدول الأجهزة لعزل كل اختبار"""
    db.execute_non_query("DELETE FROM hardware_config")


def _insert_device(db, device_type: str, connection_type: str,
                   params: dict, is_default: int = 1) -> int:
    """إدراج جهاز في جدول hardware_config وإرجاع معرفه"""
    db.execute_non_query(
        "INSERT INTO hardware_config "
        "(device_type, connection_type, connection_params, device_name, is_default, is_active) "
        "VALUES (?, ?, ?, ?, ?, 1)",
        (device_type, connection_type, json.dumps(params), f"Test {device_type}", is_default),
    )
    row = db.fetch_one(
        "SELECT id FROM hardware_config WHERE device_type = ? ORDER BY id DESC LIMIT 1",
        (device_type,),
    )
    return int(row["id"])


def _sample_sale() -> dict:
    """فاتورة بيع نموذجية للمطبوعات — 55.00 - 3.00 + 8.25 = 60.25"""
    return {
        "invoice_number": "INV-2025-0001",
        "sale_date": datetime(2025, 7, 9, 14, 30),
        "customer_name": "عميل نقدي",
        "cashier_name": "Ahmed",
        "shift_number": 12,
        "items": [
            {
                "product_name": "Product A",
                "quantity": 2,
                "unit_price": Decimal("15.00"),
                "total_amount": Decimal("30.00"),
            },
            {
                "product_name": "Product B",
                "quantity": 1,
                "unit_price": Decimal("25.00"),
                "total_amount": Decimal("25.00"),
            },
        ],
        "subtotal": Decimal("55.00"),
        "discount_amount": Decimal("3.00"),
        "tax_amount": Decimal("8.25"),
        "total": Decimal("60.25"),
        "paid_amount": Decimal("70.00"),
        "payment_method": "Cash",
        "remaining_amount": Decimal("0.00"),
    }


def _sample_session() -> dict:
    """وردية نموذجية لتقارير X/Z"""
    return {
        "shift_number": 12,
        "opened_at": datetime(2025, 7, 9, 8, 0),
        "closed_at": datetime(2025, 7, 9, 16, 0),
        "opening_cash": Decimal("500.00"),
        "cash_sales": Decimal("1200.00"),
        "card_sales": Decimal("300.00"),
        "credit_sales": Decimal("150.00"),
        "refunds": Decimal("50.00"),
        "cash_in": Decimal("100.00"),
        "cash_out": Decimal("80.00"),
        "expected_closing": Decimal("1870.00"),
        "counted_cash": Decimal("1860.00"),
        "difference": Decimal("-10.00"),
        "sales_count": 45,
    }


def _tmp_output_file() -> str:
    """إنشاء ملف مخرجات مؤقت للطباعة الوهمية عبر وضع file"""
    tmp = tempfile.NamedTemporaryFile(suffix=".out", delete=False)
    tmp.close()
    return tmp.name


# ═══════════════════════════════════════════════════════════════════
# Migration 009 — جدول إعدادات الأجهزة
# ═══════════════════════════════════════════════════════════════════


class TestMigration009:
    def test_table_exists_with_expected_columns(self, db):
        """الجدول موجود بكل الأعمدة المتوقعة"""
        columns = {row["name"] for row in
                   db.execute_query("PRAGMA table_info(hardware_config)")}
        assert columns == {
            "id", "device_type", "connection_type", "connection_params",
            "device_name", "is_default", "is_active", "created_at",
        }

    def test_idempotent_apply_twice(self, db):
        """التطبيق مرتين متتاليتين آمن (CREATE IF NOT EXISTS)"""
        MIGRATION_009.upgrade(db)  # مطبق مسبقاً في الـ fixture — لا يرفع استثناء
        MIGRATION_009.upgrade(db)
        columns = {row["name"] for row in
                   db.execute_query("PRAGMA table_info(hardware_config)")}
        assert "device_type" in columns

    def test_index_on_device_type_exists(self, db):
        """فهرس device_type موجود بعد الترحيل"""
        row = db.fetch_one(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'index' AND name = 'idx_hardware_config_device_type'"
        )
        assert row is not None

    def test_downgrade_and_reupgrade(self, db):
        """التراجع يحذف الجدول وإعادة التطبيق تنشئه من جديد"""
        MIGRATION_009.downgrade(db)
        row = db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'hardware_config'"
        )
        assert row is None
        MIGRATION_009.upgrade(db)
        columns = {row["name"] for row in
                   db.execute_query("PRAGMA table_info(hardware_config)")}
        assert "connection_params" in columns


# ═══════════════════════════════════════════════════════════════════
# HardwareConfig — البحث عن الأجهزة
# ═══════════════════════════════════════════════════════════════════


class TestHardwareConfig:
    def test_get_default_returns_is_default_row(self, db):
        """get_default يعيد الصف المعلّم is_default ويحلل JSON"""
        _clear_hardware_config(db)
        _insert_device(db, "receipt_printer", "file", {"file": "/tmp/x.out"}, is_default=1)
        _insert_device(db, "receipt_printer", "network", {"ip": "10.0.0.5"}, is_default=0)

        cfg = HardwareConfig.get_default(db, "receipt_printer")
        assert cfg is not None
        assert cfg.connection_type == "file"
        assert cfg.connection_params == {"file": "/tmp/x.out"}
        assert cfg.is_default is True
        assert cfg.is_active is True
        assert cfg.device_type == "receipt_printer"

    def test_get_default_none_for_unknown_type(self, db):
        """نوع غير معروف يعيد None بدون استثناء"""
        _clear_hardware_config(db)
        _insert_device(db, "receipt_printer", "file", {"file": "/tmp/x.out"})
        assert HardwareConfig.get_default(db, "label_printer") is None
        assert HardwareConfig.get_default(db, "cash_drawer") is None

    def test_get_default_none_without_db(self, db):
        """بدون مدير قاعدة بيانات يعيد None بأمان"""
        assert HardwareConfig.get_default(None, "receipt_printer") is None

    def test_from_row_parses_json_and_coerces_flags(self, db):
        """from_row يحلل JSON و يحول 0/1 إلى bool ويقاوم JSON الفاسد"""
        row = {
            "id": 7,
            "device_type": "cash_drawer",
            "connection_type": "network",
            "connection_params": json.dumps({"ip": "192.168.1.100", "port": 9100}),
            "device_name": "Front drawer",
            "is_default": 1,
            "is_active": 0,
        }
        cfg = HardwareConfig.from_row(row)
        assert cfg.id == 7
        assert cfg.connection_params == {"ip": "192.168.1.100", "port": 9100}
        assert cfg.is_default is True
        assert cfg.is_active is False

        bad = HardwareConfig.from_row({**row, "connection_params": "not-json{{{"})
        assert bad.connection_params == {}
        dict_row = HardwareConfig.from_row({**row, "connection_params": {"port": 1}})
        assert dict_row.connection_params == {"port": 1}


# ═══════════════════════════════════════════════════════════════════
# render_receipt_text — بناء النص النقي
# ═══════════════════════════════════════════════════════════════════


class TestReceiptRendering:
    def test_receipt_contains_core_content(self):
        """النص يحتوي رقم الفاتورة، الأصناف، TOTAL، والخاتمة العربية"""
        sale = _sample_sale()
        text = render_receipt_text(sale)

        assert "INV-2025-0001" in text
        assert "Product A" in text and "Product B" in text
        assert "Standard El-Joumla" in text
        assert "ستاندرد الجملة" in text
        assert "Date: 2025-07-09 14:30" in text
        assert "Cashier: Ahmed  Shift: #12" in text
        assert "شكراً" in text
        assert "=" * 32 in text and "-" * 32 in text

    def test_total_line_correct_decimal_sum(self):
        """سطر TOTAL بقيمة Decimal صحيحة (المجموع الناقص الخصم زائد الضريبة)"""
        sale = _sample_sale()
        items_sum = sum(
            (Decimal(str(i["total_amount"])) for i in sale["items"]), Decimal("0")
        )
        assert items_sum == sale["subtotal"]                       # مجموع الأصناف
        assert sale["total"] == sale["subtotal"] - sale["discount_amount"] + sale["tax_amount"]

        text = render_receipt_text(sale)
        expected_total_line = f"{'TOTAL:':<24}{'60.25':>8}"
        assert expected_total_line in text
        assert f"{'Subtotal:':<24}{'55.00':>8}" in text
        assert f"{'Discount:':<24}{'3.00':>8}" in text
        assert f"{'Tax:':<24}{'8.25':>8}" in text

    def test_exact_item_line_column_alignment(self):
        """سطر الصنف يطابق الأعمدة الثابتة حرفياً: اسم16 كمية4 سعر8 إجمالي8"""
        sale = _sample_sale()
        text = render_receipt_text(sale)
        expected = f"{'Product A':<16}{'2':>4}{'15.00':>8}{'30.00':>8}"
        assert expected in text

    def test_payment_and_change_lines(self):
        """سطر الدفع والباقي (70.00 مدفوع مقابل 60.25 → 9.75 باقي)"""
        text = render_receipt_text(_sample_sale())
        assert f"{'Payment: Cash':<24}{'70.00':>8}" in text
        assert f"{'Change:':<24}{'9.75':>8}" in text

    def test_long_item_name_truncated_to_16(self):
        """اسم أطول من 16 حرفاً يُقص إلى 16"""
        sale = _sample_sale()
        long_name = "Super Long Product Name X"
        sale["items"] = [{
            "product_name": long_name,
            "quantity": 1,
            "unit_price": Decimal("10.00"),
            "total_amount": Decimal("10.00"),
        }]
        text = render_receipt_text(sale)
        expected = f"{long_name[:16]:<16}{'1':>4}{'10.00':>8}{'10.00':>8}"
        assert expected in text
        assert long_name not in text  # لم يتسرب الاسم الكامل

    def test_zero_quantity_still_renders(self):
        """صنف بكمية 0 يظهر في الإيصال"""
        sale = _sample_sale()
        sale["items"] = [{
            "product_name": "Zero Qty Item",
            "quantity": 0,
            "unit_price": Decimal("5.00"),
            "total_amount": Decimal("0.00"),
        }]
        text = render_receipt_text(sale)
        expected = f"{'Zero Qty Item':<16}{'0':>4}{'5.00':>8}{'0.00':>8}"
        assert expected in text

    def test_huge_total_fits_line(self):
        """إجمالي كبير (1234567.89) يظهر كاملاً في سطر TOTAL"""
        sale = _sample_sale()
        sale["total"] = Decimal("1234567.89")
        text = render_receipt_text(sale)
        total_line = next(
            line for line in text.splitlines() if line.startswith("TOTAL:")
        )
        assert "1234567.89" in total_line

    def test_remaining_amount_credit_line(self):
        """المبلغ المتبقي للبيع بالأجل يظهر كسطر Remaining"""
        sale = _sample_sale()
        sale["paid_amount"] = Decimal("40.00")
        sale["remaining_amount"] = Decimal("20.25")
        text = render_receipt_text(sale)
        assert f"{'Remaining:':<24}{'20.25':>8}" in text


# ═══════════════════════════════════════════════════════════════════
# ESCPOSPrinterService — وضع الملف الحقيقي
# ═══════════════════════════════════════════════════════════════════


class TestPrinterFileConnection:
    def test_print_receipt_writes_bytes_to_file(self, db):
        """طباعة إيصال عبر اتصال file: البايتات تُكتب فعلياً في الملف"""
        _clear_hardware_config(db)
        out_file = _tmp_output_file()
        try:
            _insert_device(db, "receipt_printer", "file", {"file": out_file}, is_default=1)
            svc = ESCPOSPrinterService(db)
            assert svc.is_dry_run is False
            assert svc.config is not None
            assert svc.connection_type == "file"

            assert svc.print_receipt(_sample_sale()) is True

            raw = Path(out_file).read_bytes()
            assert raw.startswith(INIT)
            assert b"TOTAL:" in raw
            assert raw.endswith(feed_lines(3) + PARTIAL_CUT)

            text = svc.get_last_output_text()
            assert "INV-2025-0001" in text
            assert "Product A" in text
            assert "60.25" in text
            assert "شكراً" in text
            svc.close()
        finally:
            _clear_hardware_config(db)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_cut_paper_writes_cut_command(self, db):
        """cut_paper يكتب أمر القطع الجزئي في نهاية الملف"""
        _clear_hardware_config(db)
        out_file = _tmp_output_file()
        try:
            _insert_device(db, "receipt_printer", "file", {"file": out_file})
            svc = ESCPOSPrinterService(db)
            assert svc.is_dry_run is False
            assert svc.cut_paper(partial=True) is True
            assert Path(out_file).read_bytes().endswith(PARTIAL_CUT)

            assert svc.cut_paper(partial=False) is True
            assert Path(out_file).read_bytes().endswith(FULL_CUT)
            svc.close()
        finally:
            _clear_hardware_config(db)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_bold_and_double_size_markers_present(self, db):
        """الرأس بين BOLD_ON/OFF وسطر TOTAL بين DOUBLE_SIZE_ON/OFF"""
        _clear_hardware_config(db)
        out_file = _tmp_output_file()
        try:
            _insert_device(db, "receipt_printer", "file", {"file": out_file})
            svc = ESCPOSPrinterService(db)
            assert svc.print_receipt(_sample_sale()) is True
            raw = Path(out_file).read_bytes()
            assert b"\x1bE1" in raw and b"\x1bE0" in raw
            assert DOUBLE_SIZE_ON in raw and DOUBLE_SIZE_OFF in raw
            svc.close()
        finally:
            _clear_hardware_config(db)
            if os.path.exists(out_file):
                os.unlink(out_file)


# ═══════════════════════════════════════════════════════════════════
# ESCPOSPrinterService — وضع dry_run
# ═══════════════════════════════════════════════════════════════════


class TestPrinterDryRun:
    def test_no_config_defaults_to_dry_run(self, db):
        """بدون أي إعدادات → dry_run ونجاح مع التقاط المخرجات"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)
        assert svc.config is None
        assert svc.is_dry_run is True

        assert svc.print_receipt(_sample_sale()) is True
        assert len(svc.last_output) > 0
        assert svc.last_output.startswith(INIT)
        text = svc.get_last_output_text()
        assert "INV-2025-0001" in text
        assert "شكراً" in text

    def test_bad_file_path_degrades_to_dry_run(self, db):
        """مسار ملف غير صالح (مجلد غير موجود) → تدهور آمن إلى dry_run"""
        _clear_hardware_config(db)
        _insert_device(db, "receipt_printer", "file",
                       {"file": "/nonexistent_dir_1234/nope.out"})
        svc = ESCPOSPrinterService(db)
        assert svc.is_dry_run is True
        assert svc.print_receipt(_sample_sale()) is True  # لا استثناء
        assert len(svc.last_output) > 0

    def test_open_cash_drawer_and_beep_capture(self, db):
        """النبضة والجرس تُلتقط في last_output بوضع dry_run"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)
        assert svc.open_cash_drawer() is True
        assert svc.last_output.endswith(CASH_DRAWER_KICK)
        assert svc.beep() is True
        assert svc.last_output.endswith(b"\x07")


# ═══════════════════════════════════════════════════════════════════
# تقارير X / Z
# ═══════════════════════════════════════════════════════════════════


class TestSessionReports:
    def test_x_report_content_and_full_cut(self, db):
        """تقرير X: رقم الوردية والمبالغ المتوقعة ويُنهى بقطع كامل"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)  # dry_run
        assert svc.is_dry_run is True

        assert svc.print_x_report(_sample_session()) is True
        text = svc.get_last_output_text()
        assert "تقرير X" in text
        assert "Shift: #12" in text
        assert "Expected Closing:" in text and "1870.00" in text
        assert "Counted Cash:" in text and "1860.00" in text
        assert "Difference:" in text and "-10.00" in text
        assert "Sales Count:" in text and "45" in text
        assert svc.last_output.endswith(feed_lines(3) + FULL_CUT)

    def test_z_report_content_and_full_cut(self, db):
        """تقرير Z: عنوان الإغلاق ووقت الإقفال ويُنهى بقطع كامل"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)

        assert svc.print_z_report(_sample_session()) is True
        text = svc.get_last_output_text()
        assert "تقرير Z" in text
        assert "Shift: #12" in text
        assert "Closed: 2025-07-09 16:00" in text
        assert "Counted Cash:" in text and "1860.00" in text
        assert svc.last_output.endswith(feed_lines(3) + FULL_CUT)

    def test_difference_computed_when_missing(self, db):
        """الفرق يُحسب تلقائياً من المحصَّل المتوقع عند غيابه"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)
        session = _sample_session()
        session.pop("difference")
        assert svc.print_z_report(session) is True
        text = svc.get_last_output_text()
        assert "Difference:" in text
        assert "-10.00" in text  # 1860.00 - 1870.00


# ═══════════════════════════════════════════════════════════════════
# CashDrawerService — درج النقدية
# ═══════════════════════════════════════════════════════════════════


class TestCashDrawerService:
    def test_open_dry_run_kick_captured(self, db):
        """dry_run: الفتح يعيد True ويلتقط نبضة دخل 2 في النهاية"""
        _clear_hardware_config(db)
        drawer = CashDrawerService(db)
        assert drawer.is_dry_run is True
        assert drawer.open() is True
        assert drawer.last_output.endswith(CASH_DRAWER_KICK)
        # الطابعة المفوَّض إليها التقطت النبضة أيضاً
        assert drawer.printer_service.last_output.endswith(CASH_DRAWER_KICK)

    def test_check_status_unknown_in_dry_run(self, db):
        """dry_run: حالة الدرج UNKNOWN فوراً بدون حجب"""
        _clear_hardware_config(db)
        drawer = CashDrawerService(db)
        assert drawer.check_status() is DrawerStatus.UNKNOWN

    def test_open_and_log_records_reason(self, db):
        """open_and_log يعيد True ويسجل السبب في السجل بدون استثناء"""
        _clear_hardware_config(db)
        drawer = CashDrawerService(db)
        assert drawer.open_and_log("اختبار فتح الدرج") is True
        assert drawer.open_and_log() is True
        assert drawer.last_output.endswith(CASH_DRAWER_KICK)

    def test_delegates_to_file_printer(self, db):
        """بدون إعدادات درج: الفتح يتم عبر طابعة file حقيقية وتبت النبضة في الملف"""
        _clear_hardware_config(db)
        out_file = _tmp_output_file()
        try:
            _insert_device(db, "receipt_printer", "file", {"file": out_file})
            drawer = CashDrawerService(db)
            assert drawer.is_dry_run is False  # طابعة حقيقية (وضع ملف)
            assert drawer.open() is True
            raw = Path(out_file).read_bytes()
            assert raw.endswith(CASH_DRAWER_KICK)
            assert drawer.last_output.endswith(CASH_DRAWER_KICK)
            drawer.close()
        finally:
            _clear_hardware_config(db)
            if os.path.exists(out_file):
                os.unlink(out_file)

    def test_drawer_enum_values(self):
        """قيم enum الحالة الثلاث"""
        assert {s.value for s in DrawerStatus} == {"open", "closed", "unknown"}


# ═══════════════════════════════════════════════════════════════════
# الترميز — cp864 / cp1256 / utf-8
# ═══════════════════════════════════════════════════════════════════


class TestEncoding:
    def test_encode_text_arabic_round_trip(self, db):
        """ترميز النص العربي يرتد بدقة عبر الترميز المختار"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)
        for sample in ("شكراً لكم / Thank you!", "ستاندرد الجملة",
                       "تقرير X - منتصف الوردية", "TOTAL: 60.25"):
            encoded = svc._encode_text(sample)
            assert isinstance(encoded, bytes)
            assert encoded.decode(svc._last_encoding) == sample

    def test_encoding_candidates_order(self, db):
        """ترتيب الترميزات: cp864 ثم cp1256 ثم cp720 ثم utf-8"""
        assert ESCPOSPrinterService.ENCODING_CANDIDATES == (
            "cp864", "cp1256", "cp720", "utf-8",
        )

    def test_get_last_output_text_empty(self, db):
        """نص مخرجات فارغة يعيد سلسلة فارغة بدون استثناء"""
        _clear_hardware_config(db)
        svc = ESCPOSPrinterService(db)
        assert svc.get_last_output_text() == ""
