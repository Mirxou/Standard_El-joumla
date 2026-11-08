#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات GAP-1.3: توليد الباركود وتكامل الماسح الضوئي — قاعدة بيانات SQLite حقيقية.

- EAN-13: توليد حتمي + رقم تحقق صحيح (متجه معروف: 4006381333931)
- ربط الباركود بالمنتجات + التعارض UNIQUE + الخريطة العكسية
- الماسح: منطق العازل الزمني (ساعة وهمية)، on_scan، الإحصاءات
- Code128: الترميز الخالص + توليد الصورة (PIL متوفر في هذه البيئة)
- ملصقات: بناء النص 30x20mm / 50x25mm + الطباعة (dry-run و file)

GAP-1.3 tests: barcode generation, scanner buffer timing, Code128, labels.
"""

import json
import os
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
from src.services.barcode_service import (
    BarcodeCollisionError,
    BarcodeService,
    CODE128_PATTERNS,
    code128_encode,
    code128_bitstream,
    ean13_check_digit,
    is_valid_ean13,
)
from src.services.scanner_service import ScannerService


# ═══════════════════════════ أدوات مساعدة / Helpers ═══════════════════════════

class FakeClock:
    """ساعة وهمية حتمية لاختبار نوافذ التوقيت / Deterministic fake clock."""

    def __init__(self, start: float = 0.0):
        self.t = float(start)

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += float(seconds)


@pytest.fixture(scope="module")
def db():
    """قاعدة بيانات SQLite حقيقية مؤقتة للمجموعة كاملة / Temp real SQLite DB."""
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


@pytest.fixture()
def barcode_service(db):
    """خدمة باركود مرتبطة بقاعدة الاختبار / BarcodeService bound to test DB."""
    return BarcodeService(db)


def _add_product(db, name="منتج باركود", unit="حبة", cost="10.50", price="15.50") -> int:
    """إنشاء منتج بدون باركود وإنشاء معرّفه / Create a product, return its id."""
    pm = ProductManager(db)
    product = Product(
        name=name,
        unit=unit,
        cost_price=Decimal(cost),
        selling_price=Decimal(price),
        current_stock=250,
    )
    pid = pm.create_product(product)
    assert pid, "فشل إنشاء المنتج"
    return pid


def _set_barcode(db, product_id: int, barcode: str) -> None:
    """تعيين باركود مباشرة بـ SQL (لتهيئة سيناريوهات التعارض)."""
    db.execute_non_query(
        "UPDATE products SET barcode = ? WHERE id = ?", (barcode, product_id)
    )


def _independent_check_digit(body_12: str) -> int:
    """حساب مستقل تماماً لرقم التحقق (يُحاكي المواصفة الرسمية)."""
    assert len(body_12) == 12
    total = sum(
        int(d) * (3 if i % 2 else 1) for i, d in enumerate(body_12)
    )
    return (10 - total % 10) % 10


# ═══════════════════════ EAN-13: التوليد والتحقق ═══════════════════════

class TestEan13Generation:
    def test_known_vector_stabilo_pen_is_valid(self, barcode_service):
        """متجه معروف: 4006381333931 صالح و 4006381333930 غير صالح."""
        assert barcode_service.validate_ean13("4006381333931") is True
        assert barcode_service.validate_ean13("4006381333930") is False

    def test_generate_ean13_for_product_1_layout_and_check(self, barcode_service):
        """معرف 1 → جسم يبدأ بـ "200" + 00000001 + خانة البديل، ورقم تحقق مستقل."""
        barcode = barcode_service.generate_ean13(1)
        assert len(barcode) == 13 and barcode.isdigit()
        assert barcode.startswith("200"), "يجب استخدام بادئة النطاق الداخلي GS1"
        assert barcode[3:11] == "00000001", "الخانات 4-11 تشفّر معرف المنتج"
        body = barcode[:12]
        assert barcode[12] == str(_independent_check_digit(body))
        assert barcode_service.validate_ean13(barcode) is True

    def test_pure_check_digit_matches_known_vectors(self):
        """دالة رقم التحقق الخالصة على متجهات موثوقة."""
        assert ean13_check_digit("400638133393") == 1  # Stabilo pen
        assert ean13_check_digit("200000000010") == _independent_check_digit("200000000010")

    def test_determinism_same_product_same_barcode(self, barcode_service):
        """نفس المعرف مرتين (وحتى عبر خدمة جديدة) ⇒ نفس الباركود."""
        first = barcode_service.generate_ean13(1234)
        second = barcode_service.generate_ean13(1234)
        again = BarcodeService(barcode_service.db).generate_ean13(1234)
        assert first == second == again

    def test_large_product_id_hash_fallback(self, barcode_service):
        """معرفات فوق 99,999,999 تستخدم hash fallback حتمي وتنتج EAN-13 صالح."""
        huge = 123_456_789_012
        bc1 = barcode_service.generate_ean13(huge)
        bc2 = barcode_service.generate_ean13(huge)
        assert bc1 == bc2
        assert len(bc1) == 13 and bc1.startswith("200")
        assert barcode_service.validate_ean13(bc1) is True

    def test_validate_ean13_negatives(self, barcode_service):
        """حالات رفض صريحة: رقم تحقق خاطئ / نص / طول خاطئ / None."""
        assert barcode_service.validate_ean13("4006381333930") is False  # bad check
        assert barcode_service.validate_ean13("abc") is False
        assert barcode_service.validate_ean13("400638133393") is False   # 12 digits
        assert barcode_service.validate_ean13("40063813339312") is False  # 14 digits
        assert barcode_service.validate_ean13("") is False
        assert barcode_service.validate_ean13(None) is False
        assert barcode_service.validate_ean13(4006381333931) is False    # non-str

    def test_is_valid_ean13_module_function(self):
        """النسخة الخالصة على مستوى الوحدة تعمل بنفس المنطق."""
        assert is_valid_ean13("4006381333931") is True
        assert is_valid_ean13("4006381333930") is False


# ═══════════════════ ربط الباركود والتحويل / Assign & resolve ═══════════════════

class TestAssignAndResolve:
    def test_assign_persists_and_resolves_back(self, db, barcode_service):
        """الربط يخزَّن في products.barcode ويُقرأ مرة أخرى عبر resolve_barcode."""
        pid = _add_product(db, name="منتج ربط", price="25.00", cost="12.00")
        barcode = barcode_service.assign_barcode_to_product(pid)

        stored = db.fetch_one("SELECT barcode FROM products WHERE id = ?", (pid,))
        assert stored["barcode"] == barcode
        assert barcode_service.validate_ean13(barcode) is True

        product = barcode_service.resolve_barcode(barcode)
        assert product is not None
        assert product["id"] == pid
        assert product["name"] == "منتج ربط"
        assert product["barcode"] == barcode
        assert product["selling_price"] == Decimal("25.00")
        assert product["cost_price"] == Decimal("12.00")

    def test_assign_explicit_barcode(self, db, barcode_service):
        """ربط باركود خارجي صريح يُخزَّن كما هو ويُحوَّل بدقة."""
        pid = _add_product(db, name="منتج خارجي")
        result = barcode_service.assign_barcode_to_product(pid, "4006381333931")
        assert result == "4006381333931"
        assert barcode_service.resolve_barcode("4006381333931")["id"] == pid

    def test_assign_to_missing_product_raises(self, barcode_service):
        """منتج غير موجود ⇒ ValueError (لا تخمين صامت)."""
        with pytest.raises(ValueError):
            barcode_service.assign_barcode_to_product(987654321)

    def test_collision_variants_and_no_overwrite(self, db, barcode_service):
        """منتج آخر يحمل مسبقاً الباركود المتوقع ⇒ بديل ناجح أو CollisionError،
        ويُمنع الكتم/الكتابة فوق باركود المنتج الآخر."""
        target = _add_product(db, name="هدف التعارض")
        hoarder = _add_product(db, name="حاجز الباركود")
        expected = barcode_service.generate_ean13(target)
        _set_barcode(db, hoarder, expected)  # احتكار الباركود المتوقع مسبقاً

        try:
            final = barcode_service.assign_barcode_to_product(target)
        except BarcodeCollisionError:
            final = None  # مسار مقبول أيضاً حسب المواصفة

        assert final is None or final != expected
        if final is not None:
            assert barcode_service.validate_ean13(final) is True
            resolved = barcode_service.resolve_barcode(final)
            assert resolved is not None and resolved["id"] == target

        # المنتج الآخر لم يُمس: باركوده كما هو ويظل محوَّلاً إليه.
        assert db.fetch_one(
            "SELECT barcode FROM products WHERE id = ?", (hoarder,)
        )["barcode"] == expected
        assert barcode_service.resolve_barcode(expected)["id"] == hoarder

    def test_resolve_unknown_and_empty(self, db, barcode_service):
        """باركود غير موجود/فارغ/None ⇒ None بأمان."""
        assert barcode_service.resolve_barcode("9999999999999") is None
        assert barcode_service.resolve_barcode("") is None
        assert barcode_service.resolve_barcode("   ") is None
        assert barcode_service.resolve_barcode(None) is None

    def test_resolve_malformed_thirteen_digits(self, db, barcode_service):
        """13 خانة برقم تحقق خاطئ ولا تطابق مخزوناً ⇒ None."""
        # جسم داخلي صالح مع رقم تحقق مكسور عمداً.
        body = barcode_service._ean13_body(77_777_777, variant=0)
        bad = body + str((ean13_check_digit(body) + 1) % 10)
        assert is_valid_ean13(bad) is False
        assert barcode_service.resolve_barcode(bad) is None

    def test_reverse_map_stale_scan_guard(self, db, barcode_service):
        """الخريطة العكسية ترفض باركوداً داخلياً صالحاً لا يطابق المخزَّن (stale)."""
        pid = _add_product(db, name="حارس الراكد")
        stale = barcode_service.generate_ean13_variant(pid, variant=1)  # غير المخزَّن
        _set_barcode(db, pid, barcode_service.generate_ean13_variant(pid, variant=0))

        assert barcode_service.validate_ean13(stale) is True
        assert stale.startswith("200")
        # id المضمّن صحيح لكن الباركود المخزَّن مختلف ⇒ رفض (حماية الراكد).
        assert barcode_service.resolve_barcode(stale) is None
        # المخزَّن الفعلي يتحول طبيعياً.
        assert barcode_service.resolve_barcode(
            barcode_service.generate_ean13_variant(pid, variant=0)
        )["id"] == pid


# ═══════════════════ الماسح: منطق العازل الزمني / Scanner timing ═══════════════════

class TestScannerTiming:
    def test_fast_burst_completes_scan(self):
        """انفجار سريع متعدد الأجزاء خلال 50ms ⇒ مسح "12345678"."""
        clock = FakeClock()
        scanner = ScannerService(clock=clock)

        assert scanner.feed("1234") is None  # بلا Enter — لا مسح بعد
        clock.advance(0.05)
        event = scanner.feed("5678\n")

        assert event is not None
        assert event["barcode"] == "12345678"
        assert event["completed_by"] == "newline"
        assert event["duration_ms"] == pytest.approx(50.0, abs=0.001)
        assert scanner.get_statistics()["scans_detected"] == 1

    def test_slow_feeds_are_typing(self):
        """تغذيتان تفصل بينهما 300ms ⇒ كتابة بشرية (None) وإفراغ العازل."""
        clock = FakeClock()
        scanner = ScannerService(clock=clock)

        assert scanner.feed("1234") is None
        clock.advance(0.30)
        assert scanner.feed("5678\n") is None
        assert scanner.get_statistics()["scans_detected"] == 0
        # العازل أُفرغ: دفعة جديدة لا تجمع القديم.
        assert scanner.feed("1234567\n") is not None  # مسح جديد مستقل

    def test_short_burst_rejected(self):
        """انفجار من 5 محارف فقط ⇒ None (أقصر من عتبة الماسح)."""
        clock = FakeClock()
        scanner = ScannerService(clock=clock)
        assert scanner.feed("12345\n") is None
        assert scanner.get_statistics()["scans_detected"] == 0

    def test_flush_returns_pending_candidate(self):
        """مسح بلا Enter ثم flush() ⇒ يعيد المرشّح المكتمَل داخل النافذة."""
        clock = FakeClock()
        scanner = ScannerService(clock=clock)

        assert scanner.feed("12345678") is None  # لم يصل Enter بعد
        clock.advance(0.05)
        event = scanner.flush()

        assert event is not None
        assert event["barcode"] == "12345678"
        assert event["completed_by"] == "flush"
        # flush على عازل فارغ ⇒ None.
        assert scanner.flush() is None

    def test_flush_older_than_window_is_typing(self):
        """كتابة بطيئة (2 ثانية) ثم flush ⇒ None (خارج نافذة 150ms)."""
        clock = FakeClock()
        scanner = ScannerService(clock=clock)
        scanner.feed("1")
        clock.advance(1.0)
        scanner.feed("2345678")
        assert scanner.flush() is None

    def test_empty_and_none_chunks(self):
        """تغذية فارغة/None لا تكسر العازل."""
        clock = FakeClock()
        scanner = ScannerService(clock=clock)
        assert scanner.feed("") is None
        assert scanner.feed(None) is None
        assert scanner.flush() is None


# ═══════════════════ الماسح: التحويل والإحصاءات / on_scan & stats ═══════════════════

class TestScannerOnScan:
    def test_on_scan_resolves_product_end_to_end(self, db):
        """مسح باركود منتج حقيقي ⇒ قاموس المنتج + إحصاءات صحيحة."""
        pid = _add_product(db, name="منتج ماسح", price="33.00", cost="20.00")
        svc = BarcodeService(db)
        barcode = svc.assign_barcode_to_product(pid)

        scanner = ScannerService(db)
        product = scanner.on_scan(barcode)

        assert product is not None
        assert product["id"] == pid
        assert product["name"] == "منتج ماسح"
        assert product["selling_price"] == Decimal("33.00")

        stats = scanner.get_statistics()
        assert stats["scans_resolved"] == 1
        assert stats["scans_failed"] == 0
        assert stats["avg_resolution_ms"] >= 0.0

    def test_on_scan_unknown_returns_none(self, db):
        """مسح غير معروف ⇒ None ويُحسب failed."""
        scanner = ScannerService(db)
        assert scanner.on_scan("nosuchbarcode123") is None
        assert scanner.on_scan(None) is None
        stats = scanner.get_statistics()
        assert stats["scans_failed"] == 1  # None الفارغ لا يُحسب
        assert stats["scans_resolved"] == 0

    def test_feed_then_process_scan_event_with_callback(self, db):
        """السلك الكامل: feed() → حدث → process_scan_event() → callback بالمنتج."""
        pid = _add_product(db, name="منتج سيل")
        barcode = BarcodeService(db).assign_barcode_to_product(pid)

        scanner = ScannerService(db)
        received = []
        scanner.start_listening(received.append)  # keyboard_wedge: تسجيل فقط
        assert scanner.active is True

        # 13 محرفاً دفعة واحدة مع Enter = انفجار ماسح نموذجي.
        event = scanner.feed(barcode + "\n")
        assert event is not None
        product = scanner.process_scan_event(event)

        assert product is not None and product["id"] == pid
        assert received and received[-1]["id"] == pid

        stats = scanner.get_statistics()
        assert stats["scans_detected"] == 1
        assert stats["scans_resolved"] == 1
        scanner.stop_listening()
        assert scanner.active is False

    def test_keyboard_wedge_documented_no_thread(self, db):
        """وضع keyboard_wedge لا يفتح thread خلفياً (الواجهة تُغذّي feed)."""
        scanner = ScannerService(db)
        scanner.start_listening(lambda product: None)
        assert scanner.active is True
        assert scanner._thread is None
        scanner.stop_listening()


# ═══════════════════ الماسح التسلسلي / Serial listener ═══════════════════

class TestSerialListener:
    def test_missing_serial_port_never_raises(self, db):
        """serial بدون منفذ مُعدّ ⇒ تحذير و active=False بدون استثناء."""
        scanner = ScannerService(db, connection_type="serial")
        scanner.start_listening(lambda product: None)  # يجب ألا يرفع
        assert scanner.active is False
        scanner.stop_listening()

    def test_missing_pyserial_fails_gracefully(self, db):
        """غياب pyserial ⇒ الـ thread يموت بهدوء و active=False (لا استثناء)."""
        pytest.importorskip("threading")  # حرفيّة لتوثيق الاعتماد على threading فقط
        scanner = ScannerService(
            db, connection_type="serial", serial_port="/dev/ttyUSB0-does-not-exist"
        )
        scanner.start_listening(lambda product: None)  # لا استثناء رغم غياب pyserial
        scanner.stop_listening()  # join بمهلة ثانيتين
        assert scanner.active is False


# ═══════════════════════ Code128: الترميز والصورة ═══════════════════════

class TestCode128Encoding:
    def test_table_structure(self):
        """جدول الأنماط: 107 مدخلاً، start-B و stop بالأنماط الرسمية."""
        assert len(CODE128_PATTERNS) == 107
        assert CODE128_PATTERNS[104] == "11010010000"  # Start B
        assert CODE128_PATTERNS[106] == "1100011101011"  # Stop + termination bar
        assert all(len(p) == 11 for p in CODE128_PATTERNS[:106])

    def test_encode_single_a(self):
        """'A' → [START_B, 33, checksum, STOP]؛ checksum = (104 + 1×33) % 103 = 34."""
        symbols = code128_encode("A")
        assert symbols[0] == 104  # Start B
        assert symbols[1] == ord("A") - 32 == 33
        assert symbols[2] == 34   # (104 + 33) % 103 — يطابق التطبيقات المرجعية
        assert symbols[-1] == 106
        assert len(symbols) == 4

    def test_encode_multi_char_checksum_weighted(self):
        """المجموع مرجّح بالموضع: 'AB' → (104 + 1×33 + 2×34) % 103 = 102."""
        assert code128_encode("AB") == [104, 33, 34, 102, 106]

    def test_encode_reference_vector_from_verified_table(self):
        """متجه مرجعي كامل للسلسلة 'STJ-2025-001' (تم التحقق منه مستقلاً)."""
        assert code128_encode("STJ-2025-001") == [
            104, 51, 52, 42, 13, 18, 16, 18, 21, 13, 16, 16, 17, 29, 106,
        ]

    def test_bitstream_prefix_suffix(self):
        """سلسلة البتات تبدأ بـ Start-B وتنتهي بـ Stop."""
        bits = code128_bitstream("STJ-2025-001")
        assert bits.startswith("11010010000")
        assert bits.endswith("1100011101011")
        assert len(bits) == 11 * (len(code128_encode("STJ-2025-001")) - 1) + 13

    def test_encode_rejects_invalid(self):
        """رفض النص الفارغ/None والمحارف خارج 32..126."""
        with pytest.raises(ValueError):
            code128_encode("")
        with pytest.raises(ValueError):
            code128_encode(None)
        with pytest.raises(ValueError):
            code128_encode("نعم")  # محارف خارج ASCII 32..126


class TestCode128Image:
    def test_generate_image_size_and_content(self):
        """الصورة بالمقاس المطلوب وغير فارغة (قيمتا أبيض/أسود على الأقل)."""
        pytest.importorskip("PIL")
        from src.services.barcode_service import BarcodeService as _BS  # noqa: F401

        service = BarcodeService.__new__(BarcodeService)  # لا يحتاج db للصور
        image = service.generate_code128_image("STJ-2025-001", width=400, height=120)
        assert image.size == (400, 120)
        extrema = image.getextrema()
        assert len(extrema) == 2 and extrema[0] < extrema[1]  # أسود + أبيض

    def test_generate_image_custom_size(self):
        """مقاس مخصص (200×60) يعمل ويحترم الأبعاد."""
        pytest.importorskip("PIL")
        service = BarcodeService.__new__(BarcodeService)
        image = service.generate_code128_image("A", width=200, height=60)
        assert image.size == (200, 60)

    def test_generate_image_invalid_inputs(self):
        """قيمة فارغة أو محارف غير مدعومة ⇒ ValueError (لا صورة)."""
        pytest.importorskip("PIL")
        service = BarcodeService.__new__(BarcodeService)
        with pytest.raises(ValueError):
            service.generate_code128_image("")
        with pytest.raises(ValueError):
            service.generate_code128_image("نعم")

    def test_generate_image_too_narrow(self):
        """عرض أصغر من عدد الوحدات المطلوب ⇒ ValueError."""
        pytest.importorskip("PIL")
        service = BarcodeService.__new__(BarcodeService)
        with pytest.raises(ValueError):
            service.generate_code128_image("STJ-2025-001", width=20, height=50)


# ═══════════════════════ الملصقات / Labels ═══════════════════════

def _label_product(name: str) -> dict:
    """قاموس منتج لاختبارات الملصقات / Product dict for label tests."""
    return {
        "id": 1,
        "name": name,
        "barcode": "2000000000105",
        "selling_price": Decimal("15.50"),
        "cost_price": Decimal("8.00"),
        "unit": "حبة",
        "current_stock": 10.0,
    }


class TestLabelText:
    def test_formats_differ_and_truncate(self, barcode_service):
        """30x20 ≠ 50x25، والاسم الطويل يُقتطع حسب حدود المقاس."""
        long_name = "منتج تجريبي بطول كبير جداً للاختبار ABCDEFGH"
        product = _label_product(long_name)

        label_30 = barcode_service.build_label_text(product, "30x20mm")
        label_50 = barcode_service.build_label_text(product, "50x25mm")

        assert label_30 != label_50
        lines_30 = label_30.splitlines()
        lines_50 = label_50.splitlines()
        assert len(lines_30) == 4 and len(lines_50) == 4

        # السطر الأول يعرّف المقاس، الثاني الاسم المقتطع، ثم السعر ثم الباركود.
        assert lines_30[0] == "=== 30x20mm ==="
        assert lines_50[0] == "=== 50x25mm ==="
        assert lines_30[1] == long_name[:20]
        assert len(lines_30[1]) == 20
        assert lines_50[1] == long_name[:34]
        assert "15.50" in lines_30[2] and "15.50" in lines_50[2]
        assert lines_30[3] == "2000000000105"

    def test_unknown_format_raises(self, barcode_service):
        """مقاس غير مدعوم ⇒ ValueError يسرد المدعوم."""
        with pytest.raises(ValueError):
            barcode_service.build_label_text(_label_product("x"), "99x99mm")

    def test_decimal_money_in_price_line(self, barcode_service):
        """السعر يُنسّق من Decimal بخانتين عشريتين."""
        label = barcode_service.build_label_text(_label_product("منتج"), "30x20mm")
        assert "السعر/Price: 15.50" in label


class TestPrintLabel:
    def test_print_existing_product_dry_run(self, db):
        """طابعة غير مهيأة ⇒ dry-run: True + last_output يحوي الملصق."""
        service = BarcodeService(db)
        pid = _add_product(db, name="منتج طباعة", price="42.00")
        _set_barcode(db, pid, service.generate_ean13(pid))

        assert service.print_barcode_label(pid) is True
        assert service.last_output is not None
        assert "منتج طباعة" in service.last_output
        assert "42.00" in service.last_output
        assert service.generate_ean13(pid) in service.last_output

    def test_print_auto_assigns_missing_barcode(self, db):
        """منتج بلا باركود ⇒ يُولَّد ويُخزَّن ثم يُطبع."""
        service = BarcodeService(db)
        pid = _add_product(db, name="منتج بلا باركود")
        stored_before = db.fetch_one(
            "SELECT barcode FROM products WHERE id = ?", (pid,)
        )["barcode"]
        assert not stored_before  # بلا باركود مبدئياً

        assert service.print_barcode_label(pid, "50x25mm") is True
        stored_after = db.fetch_one(
            "SELECT barcode FROM products WHERE id = ?", (pid,)
        )["barcode"]
        assert stored_after and service.validate_ean13(stored_after)
        assert stored_after in service.last_output

    def test_print_missing_product_returns_false(self, db):
        """منتج غير موجود ⇒ False بدون استثناء."""
        assert BarcodeService(db).print_barcode_label(987654321) is False

    def test_print_to_file_connection(self, db, tmp_path):
        """connection_type='file' في hardware_config ⇒ كتابة فعلية للملف."""
        label_file = tmp_path / "labels" / "label.txt"
        db.execute_non_query(
            """
            CREATE TABLE IF NOT EXISTS hardware_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_type VARCHAR(50) NOT NULL,
                connection_type VARCHAR(20) NOT NULL,
                connection_params TEXT,
                device_name VARCHAR(100),
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute_insert(
            """
            INSERT INTO hardware_config
                (device_type, connection_type, connection_params, device_name, is_default, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "label_printer",
                "file",
                json.dumps({"path": str(label_file)}),
                "ملصقات الاختبار",
                1,
                1,
            ),
        )
        try:
            service = BarcodeService(db)
            pid = _add_product(db, name="منتج ملف", price="7.25")
            _set_barcode(db, pid, service.generate_ean13(pid))

            assert service.print_barcode_label(pid) is True
            assert label_file.exists()
            content = label_file.read_text(encoding="utf-8")
            assert "منتج ملف" in content and "7.25" in content
        finally:
            db.execute_non_query("DELETE FROM hardware_config WHERE device_type = 'label_printer'")
