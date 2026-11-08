#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESC/POS Thermal Receipt Printer Service — خدمة طابعة الإيصالات الحرارية (GAP-2.2)

Implements the ESC/POS protocol (EPSON standard) for thermal receipt printers
and cash-drawer kick pulses, per docs/SRS_ARCHITECTURE.md (GAP-2.2).

Design rules — قواعد التصميم:
1. Hardware absence NEVER crashes the app: every I/O path is guarded and the
   service degrades to ``dry_run`` mode (bytes captured in ``last_output``).
   غياب الجهاز لا يُسقط التطبيق أبداً: كل عمليات الإدخال/الإخراج محمية، وعند
   الفشل تتحول الخدمة إلى وضع dry_run مع التقاط المخرجات في last_output.
2. pyserial / pyusb are imported lazily (only when actually connecting) so the
   app runs on machines without them.
   يتم استيراد pyserial/pyusb بشكل مؤجل فقط عند محاولة الاتصال الفعلي.
3. All money uses ``Decimal`` and the receipt text is built by the pure
   module-level :func:`render_receipt_text` (no hardware involved) — the
   service only encodes + wraps it with ESC/POS commands.
   جميع المبالغ تستخدم Decimal، ونص الإيصال يُبنى بالدوال النقية أعلى الموديل.

Connection types — أنواع الاتصال:
- ``network``: TCP socket to ``ip:port`` (default 9100, the ESC/POS raw port)
- ``serial``:  pyserial to ``port`` at ``baud_rate``
- ``file``:    append bytes to a file path (perfect for testing / spooling)
- ``usb``:     pyusb direct to ``vendor_id``/``product_id`` (best-effort)

Usage — الاستخدام:
    svc = ESCPOSPrinterService(db_manager)
    svc.print_receipt(sale_dict)      # True — even in dry_run
    svc.open_cash_drawer()            # pulse pin 2
    text = svc.get_last_output_text() # inspect captured output (tests/debug)
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date, datetime
from typing import Any, Mapping

from src.utils.logger import setup_logger

# ═══════════════════════════════════════════════════════════════════
# ESC/POS command constants — ثوابت أوامر ESC/POS
# ═══════════════════════════════════════════════════════════════════
INIT = b"\x1b@"                       # ESC @  — initialize printer / تهيئة الطابعة
ALIGN_LEFT = b"\x1ba0"                # ESC a 0 — left alignment / محاذاة يسار
ALIGN_CENTER = b"\x1ba1"              # ESC a 1 — center alignment / محاذاة وسط
ALIGN_RIGHT = b"\x1ba2"               # ESC a 2 — right alignment / محاذاة يمين
BOLD_ON = b"\x1bE1"                   # ESC E 1 — emphasize on / تنشيط الخط العريض
BOLD_OFF = b"\x1bE0"                  # ESC E 0 — emphasize off / إلغاء العريض
DOUBLE_SIZE_ON = b"\x1b!\x30"         # ESC ! 0x30 — double width+height on / تكبير مضاعف
DOUBLE_SIZE_OFF = b"\x1b!\x00"        # ESC ! 0x00 — normal size / حجم عادي
FEED_LINES_PREFIX = b"\x1bd"          # ESC d n — feed n lines / تغذية n سطر
PARTIAL_CUT = b"\x1bV1"               # ESC V 1 — partial cut / قطع جزئي
FULL_CUT = b"\x1bV0"                  # ESC V 0 — full cut / قطع كامل
CASH_DRAWER_KICK = b"\x10\x14\x00\x08\x08"     # DLE DC4 — kick pin 2 / نبضة دخل 2
CASH_DRAWER_KICK_PIN5 = b"\x10\x14\x00\x10\x10"  # DLE DC4 — kick pin 5 / نبضة دخل 5
BEEP = b"\x07"                        # BEL — buzzer / جرس
STATUS_REQUEST = b"\x10\x04\x01"      # DLE EOT 1 — real-time printer status / طلب حالة


def feed_lines(n: int) -> bytes:
    """ESC d n — paper feed by n lines. تغذية الورق بمقدار n سطر."""
    try:
        n = max(0, min(255, int(n)))
    except (TypeError, ValueError):
        n = 0
    return FEED_LINES_PREFIX + bytes([n])


# ═══════════════════════════════════════════════════════════════════
# Hardware configuration model — نموذج إعدادات الجهاز
# ═══════════════════════════════════════════════════════════════════


@dataclass
class HardwareConfig:
    """Persisted hardware device configuration — إعدادات جهاز مخزنة.

    Mirrors one row of the ``hardware_config`` table (migration 009).
    تعكس صفاً واحداً من جدول hardware_config (الترحيل 009).
    """

    device_type: str                 # 'receipt_printer' | 'cash_drawer' | ...
    connection_type: str             # 'usb' | 'serial' | 'network' | 'bluetooth' | 'file'
    connection_params: dict = field(default_factory=dict)  # JSON decoded params
    device_name: str | None = None
    is_default: bool = False
    is_active: bool = True
    id: int | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "HardwareConfig":
        """Build a HardwareConfig from a DB row (dict-like).

        يبني إعدادات الجهاز من صف قاعدة البيانات، مع فك ترميز JSON
        لعمود connection_params بأمان.
        """
        raw_params = row.get("connection_params")
        if isinstance(raw_params, dict):
            params: dict = dict(raw_params)
        elif raw_params:
            try:
                parsed = json.loads(raw_params)
                params = dict(parsed) if isinstance(parsed, dict) else {}
            except (ValueError, TypeError):
                params = {}
        else:
            params = {}

        def _as_bool(value: Any, default: bool) -> bool:
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            try:
                return bool(int(value))
            except (TypeError, ValueError):
                return default

        try:
            device_id = row.get("id")
            device_id = int(device_id) if device_id is not None else None
        except (TypeError, ValueError):
            device_id = None

        return cls(
            id=device_id,
            device_type=str(row.get("device_type") or ""),
            connection_type=str(row.get("connection_type") or ""),
            connection_params=params,
            device_name=row.get("device_name"),
            is_default=_as_bool(row.get("is_default"), False),
            is_active=_as_bool(row.get("is_active"), True),
        )

    @classmethod
    def get_default(
        cls, db_manager: Any, device_type: str
    ) -> "HardwareConfig | None":
        """Return the default (or first active) config for a device type.

        يعيد الإعدادات الافتراضية لنوع الجهاز، وإلا أول جهاز نشط،
        وNone إن لم يوجد شيء أو حدث خطأ (لا يرفع استثناءات أبداً).

        Prefers ``is_default = 1`` rows, falls back to the oldest active row.
        """
        if db_manager is None or not device_type:
            return None
        try:
            row = db_manager.fetch_one(
                "SELECT * FROM hardware_config "
                "WHERE device_type = ? AND is_active = 1 "
                "ORDER BY is_default DESC, id ASC LIMIT 1",
                (device_type,),
            )
        except Exception:
            # جدول غير موجود أو خطأ قاعدة بيانات → لا أجهزة مهيأة
            return None
        if not row:
            return None
        try:
            return cls.from_row(row)
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════
# Pure text rendering (no hardware) — بناء نص الإيصال بدون أي عتاد
# ═══════════════════════════════════════════════════════════════════

RECEIPT_WIDTH = 32          # standard 80mm thermal: 32 columns / عمود قياسي
NAME_WIDTH = 16             # item name column / عرض اسم الصنف
QTY_WIDTH = 4               # quantity column / عرض الكمية
AMOUNT_WIDTH = 8            # price/total column / عرض المبلغ
LABEL_WIDTH = RECEIPT_WIDTH - AMOUNT_WIDTH  # summary label column


def _to_decimal(value: Any) -> Decimal:
    """Coerce any input (Decimal/str/int/float/None) to Decimal safely.

    تحويل آمن لأي قيمة إلى Decimal؛ القيم الفاسدة تعيد صفراً.
    """
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _fmt_money(value: Any) -> str:
    """Format money as plain 2-decimal string. تنسيق المبالغ بخانتين عشريتين."""
    amount = _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}" if amount.is_finite() else "0.00"


def _fmt_qty(value: Any) -> str:
    """Format quantity compactly (int when integral). تنسيق الكمية بشكل مضغوط."""
    try:
        amount = _to_decimal(value)
    except Exception:  # pragma: no cover — _to_decimal never raises
        return "0"
    try:
        if amount == amount.to_integral_value():
            return str(int(amount))
        return str(amount.normalize())
    except (InvalidOperation, ValueError):
        return str(amount)


def _fmt_datetime(value: Any) -> str:
    """Format a date/datetime/str for receipt display. تنسيق التاريخ للعرض."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if value:
        return str(value)
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _center(text: str, width: int = RECEIPT_WIDTH) -> str:
    """Center text within width (char-based). توسيط النص داخل العرض المعطى."""
    text = text.strip()
    if len(text) >= width:
        return text
    pad = (width - len(text)) // 2
    return " " * pad + text


def render_receipt_header(sale_dict: Mapping[str, Any]) -> str:
    """Store header block: name, store name, date, cashier/shift, invoice, customer.

    كتلة رأس الإيصال: اسم المتجر، التاريخ، الكاشير/الوردية، رقم الفاتورة، العميل.
    The service prints this block in BOLD (ESC E 1).
    """
    lines: list[str] = [
        "=" * RECEIPT_WIDTH,
        _center("Standard El-Joumla"),
        _center("ستاندرد الجملة"),
        "=" * RECEIPT_WIDTH,
        f"Date: {_fmt_datetime(sale_dict.get('sale_date'))}",
    ]
    cashier = sale_dict.get("cashier_name")
    shift = sale_dict.get("shift_number")
    if cashier and shift:
        lines.append(f"Cashier: {cashier}  Shift: #{shift}")
    elif cashier:
        lines.append(f"Cashier: {cashier}")
    elif shift:
        lines.append(f"Shift: #{shift}")
    invoice = sale_dict.get("invoice_number")
    if invoice:
        lines.append(f"Invoice: {invoice}")
    customer = sale_dict.get("customer_name")
    if customer:
        lines.append(f"Customer: {customer}")
    return "\n".join(lines) + "\n"


def render_receipt_items(sale_dict: Mapping[str, Any]) -> str:
    """Items table + subtotal/discount/tax block.

    جدول الأصناف (اسم/كمية/سعر/إجمالي بأعمدة ثابتة العرض) ثم المجموع والخصم والضريبة.
    Item line format (exact, tested):
        f"{name:<16}{qty:>4}{price:>8}{total:>8}"
    """
    lines: list[str] = [
        "-" * RECEIPT_WIDTH,
        f"{'Item':<{NAME_WIDTH}}{'Qty':>{QTY_WIDTH}}"
        f"{'Price':>{AMOUNT_WIDTH}}{'Total':>{AMOUNT_WIDTH}}",
        "-" * RECEIPT_WIDTH,
    ]
    items = sale_dict.get("items") or []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("product_name") or "")[:NAME_WIDTH]
        qty = _fmt_qty(item.get("quantity"))
        price = _fmt_money(item.get("unit_price"))
        total = _fmt_money(item.get("total_amount"))
        lines.append(f"{name:<{NAME_WIDTH}}{qty:>{QTY_WIDTH}}{price:>{AMOUNT_WIDTH}}{total:>{AMOUNT_WIDTH}}")

    lines.append("-" * RECEIPT_WIDTH)
    lines.append(f"{'Subtotal:':<{LABEL_WIDTH}}{_fmt_money(sale_dict.get('subtotal')):>{AMOUNT_WIDTH}}")
    lines.append(f"{'Discount:':<{LABEL_WIDTH}}{_fmt_money(sale_dict.get('discount_amount')):>{AMOUNT_WIDTH}}")
    lines.append(f"{'Tax:':<{LABEL_WIDTH}}{_fmt_money(sale_dict.get('tax_amount')):>{AMOUNT_WIDTH}}")
    return "\n".join(lines) + "\n"


def render_receipt_total_line(sale_dict: Mapping[str, Any]) -> str:
    """The grand TOTAL line (printed in DOUBLE SIZE by the service).

    سطر الإجمالي النهائي (تطبعه الخدمة بحجم مضاعف).
    """
    return f"{'TOTAL:':<{LABEL_WIDTH}}{_fmt_money(sale_dict.get('total')):>{AMOUNT_WIDTH}}\n"


def render_receipt_payment(sale_dict: Mapping[str, Any]) -> str:
    """Payment method / paid / change / remaining block. كتلة الدفع والباقي."""
    lines: list[str] = ["-" * RECEIPT_WIDTH]
    method = str(sale_dict.get("payment_method") or "").strip()
    paid = sale_dict.get("paid_amount")
    label = f"Payment: {method}" if method else "Payment:"
    lines.append(f"{label:<{LABEL_WIDTH}}{_fmt_money(paid):>{AMOUNT_WIDTH}}")

    total = _to_decimal(sale_dict.get("total"))
    paid_dec = _to_decimal(paid)

    remaining = sale_dict.get("remaining_amount")
    compute_change = remaining is None
    if remaining is not None:
        remaining_dec = _to_decimal(remaining)
        if remaining_dec > 0:
            # Credit sale — amount still owed / بيع بالأجل — المبلغ المتبقي
            lines.append(f"{'Remaining:':<{LABEL_WIDTH}}{_fmt_money(remaining_dec):>{AMOUNT_WIDTH}}")
        elif remaining_dec < 0:
            lines.append(f"{'Change:':<{LABEL_WIDTH}}{_fmt_money(-remaining_dec):>{AMOUNT_WIDTH}}")
        else:
            # Remaining settled in full → change (if any) comes from the payment
            # تم السداد كاملاً → الباقي يُحسب من المبلغ المدفوع إن وجد
            compute_change = True
    if compute_change and paid_dec > total:
        # Overpayment → change / دفعة زائدة → الباقي للعميل
        lines.append(f"{'Change:':<{LABEL_WIDTH}}{_fmt_money(paid_dec - total):>{AMOUNT_WIDTH}}")
    return "\n".join(lines) + "\n"


def render_receipt_footer() -> str:
    """Footer: thank-you line (centered). خاتمة الإيصال: سطر الشكر مُوسَّطاً."""
    return "\n".join([
        "=" * RECEIPT_WIDTH,
        _center("شكراً لكم / Thank you!"),
    ]) + "\n"


def render_receipt_text(sale_dict: Mapping[str, Any]) -> str:
    """Build the complete receipt text WITHOUT any hardware (pure logic).

    يبني نص الإيصال الكامل بدون أي عتاد (منطق نقي) — النواة المشتركة بين
    الخدمة والاختبارات. The service encodes this text and wraps it with
    ESC/POS commands (bold header, double-size TOTAL, feed + partial cut).

    Expected keys — المفاتيح المتوقعة:
        invoice_number, sale_date, customer_name, cashier_name, shift_number,
        items: [{product_name, quantity, unit_price, total_amount}],
        subtotal, discount_amount, tax_amount, total, paid_amount,
        payment_method, remaining_amount (optional)
    """
    return (
        render_receipt_header(sale_dict)
        + render_receipt_items(sale_dict)
        + render_receipt_total_line(sale_dict)
        + render_receipt_payment(sale_dict)
        + render_receipt_footer()
    )


def _fmt_report_label(label: str, value: str) -> str:
    """Align a report label (20) + value (12) into 32 columns.

    محاذاة سطر تقرير: تسمية بعرض 20 وقيمة بعرض 12 (مجموع 32 عموداً).
    """
    return f"{label:<20}{value:>12}"


def render_session_report_text(
    session_dict: Mapping[str, Any], report_kind: str = "x"
) -> str:
    """Build X (mid-shift) or Z (end-of-shift) report text — pure logic.

    يبني نص تقرير X (منتصف الوردية) أو Z (إغلاق الوردية) — منطق نقي بدون عتاد.

    Expected keys — المفاتيح المتوقعة:
        shift_number, opened_at, closed_at, opening_cash, cash_sales,
        card_sales, credit_sales, refunds, cash_in, cash_out,
        expected_closing, counted_cash, difference, sales_count
    """
    kind = (report_kind or "x").lower()
    if kind == "z":
        title = "تقرير Z - إغلاق الوردية"
        banner = "*** Z REPORT - SHIFT CLOSED ***"
    else:
        title = "تقرير X - منتصف الوردية"
        banner = "*** X REPORT - NO RESET ***"

    lines: list[str] = [
        "=" * RECEIPT_WIDTH,
        _center(title),
        "=" * RECEIPT_WIDTH,
        f"Shift: #{session_dict.get('shift_number') or '-'}",
        f"Opened: {_fmt_datetime(session_dict.get('opened_at'))}",
    ]
    if session_dict.get("closed_at"):
        lines.append(f"Closed: {_fmt_datetime(session_dict.get('closed_at'))}")
    lines.append("-" * RECEIPT_WIDTH)
    lines.append(_fmt_report_label("Sales Count:", str(session_dict.get("sales_count", 0) or 0)))
    lines.append(_fmt_report_label("Opening Cash:", _fmt_money(session_dict.get("opening_cash"))))
    lines.append(_fmt_report_label("Cash Sales:", _fmt_money(session_dict.get("cash_sales"))))
    lines.append(_fmt_report_label("Card Sales:", _fmt_money(session_dict.get("card_sales"))))
    lines.append(_fmt_report_label("Credit Sales:", _fmt_money(session_dict.get("credit_sales"))))
    lines.append(_fmt_report_label("Refunds:", _fmt_money(session_dict.get("refunds"))))
    lines.append(_fmt_report_label("Cash In:", _fmt_money(session_dict.get("cash_in"))))
    lines.append(_fmt_report_label("Cash Out:", _fmt_money(session_dict.get("cash_out"))))
    lines.append("-" * RECEIPT_WIDTH)

    expected = _to_decimal(session_dict.get("expected_closing"))
    counted = _to_decimal(session_dict.get("counted_cash"))
    lines.append(_fmt_report_label("Expected Closing:", _fmt_money(expected)))
    lines.append(_fmt_report_label("Counted Cash:", _fmt_money(counted)))
    difference = session_dict.get("difference")
    difference_dec = (
        _to_decimal(difference) if difference is not None else counted - expected
    )
    lines.append(_fmt_report_label("Difference:", _fmt_money(difference_dec)))
    lines.append("-" * RECEIPT_WIDTH)
    lines.append(_center(banner))
    lines.append("=" * RECEIPT_WIDTH)
    lines.append(_center("شكراً لكم / Thank you!"))
    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════════════
# Printer service — خدمة الطابعة
# ═══════════════════════════════════════════════════════════════════


class ESCPOSPrinterService:
    """ESC/POS thermal receipt printer with graceful dry-run fallback.

    خدمة طابعة الإيصالات الحرارية ببروتوكول ESC/POS مع تحول آمن إلى وضع
    dry_run عند غياب الجهاز أو فشل الاتصال — لا تسمح أبداً بإسقاط عملية البيع.
    """

    #: Arabic-compatible encodings, tried in order (cp864 = classic EPSON Arabic)
    #: ترميزات متوافقة مع العربية بالترتيب
    ENCODING_CANDIDATES: tuple[str, ...] = ("cp864", "cp1256", "cp720", "utf-8")
    CONNECT_TIMEOUT: float = 3.0    # seconds — مهلة الاتصال
    IO_TIMEOUT: float = 2.0         # seconds — مهلة الإدخال/الإخراج
    MAX_CAPTURE_BYTES: int = 1_000_000  # keep last_output bounded / حد الالتقاط

    def __init__(self, db_manager: Any, logger: Any = None) -> None:
        """Load default ``receipt_printer`` config and try to connect.

        يحمّل إعدادات الطابعة الافتراضية ويحاول الاتصال؛ عند الفشل يعمل في
        وضع dry_run بدون أي استثناء.
        """
        self.logger = logger or setup_logger(__name__)
        self._db_manager = db_manager
        self.config: HardwareConfig | None = HardwareConfig.get_default(
            db_manager, "receipt_printer"
        )
        self.connection_type: str | None = (
            self.config.connection_type.lower() if self.config else None
        )
        self.last_output: bytearray = bytearray()
        self._last_encoding: str | None = None
        self._dry_run: bool = True

        self._sock: socket.socket | None = None
        self._serial: Any = None
        self._file: Any = None
        self._usb_dev: Any = None
        self._usb_endpoint: Any = None

        try:
            self._connect()
        except Exception as exc:
            self.logger.warning(
                f"⚠️ ESC/POS: connect failed → dry_run | فشل الاتصال بالطابعة: {exc}"
            )
            self._enter_dry_run("connect failure")

    # ── properties / حالة الخدمة ─────────────────────────────────────

    @property
    def is_dry_run(self) -> bool:
        """True when output is captured instead of sent to hardware.

        True عند التقاط المخرجات بدلاً من إرسالها للعتاد.
        """
        return self._dry_run

    # ── connection lifecycle — دورة حياة الاتصال ─────────────────────

    def _connect(self) -> bool:
        """Establish the real connection per config. فتح الاتصال حسب الإعدادات.

        Raises on failure; caller (__init__) converts to dry_run.
        pyserial/pyusb are imported lazily inside this method only.
        """
        cfg = self.config
        if not cfg:
            self.logger.info(
                "🖨️ ESC/POS: no printer configured → dry_run | لا توجد طابعة مهيأة"
            )
            self._dry_run = True
            return False

        ctype = (cfg.connection_type or "").lower()
        params = cfg.connection_params or {}

        if ctype == "file":
            path = str(params.get("file") or params.get("path") or "")
            if not path:
                raise ValueError("file connection requires {'file': path} param")
            # Append mode: never truncate an existing spool / إلحاق دون إفراغ
            self._file = open(path, "ab")

        elif ctype == "network":
            host = params.get("ip") or params.get("host")
            port = int(params.get("port", 9100) or 9100)
            if not host:
                raise ValueError("network connection requires {'ip': ..., 'port': 9100}")
            timeout = float(params.get("timeout", self.CONNECT_TIMEOUT) or self.CONNECT_TIMEOUT)
            self._sock = socket.create_connection((str(host), port), timeout=timeout)
            self._sock.settimeout(
                float(params.get("io_timeout", self.IO_TIMEOUT) or self.IO_TIMEOUT)
            )

        elif ctype == "serial":
            import serial as pyserial  # lazy — قد لا تكون مثبتة على الجهاز

            self._serial = pyserial.Serial(
                port=str(params.get("port") or params.get("device") or ""),
                baudrate=int(params.get("baud_rate", 9600) or 9600),
                bytesize=8,
                parity=pyserial.PARITY_NONE,
                stopbits=1,
                timeout=self.IO_TIMEOUT,
                write_timeout=self.IO_TIMEOUT,
            )

        elif ctype == "usb":
            import usb.core  # lazy — قد لا تكون مثبتة على الجهاز
            import usb.util

            vendor_id = int(params.get("vendor_id", 0) or 0)
            product_id = int(params.get("product_id", 0) or 0)
            dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
            if dev is None:
                raise OSError(f"USB printer {vendor_id:#06x}:{product_id:#06x} not found")
            try:
                dev.set_configuration()
            except Exception:
                pass  # already configured / مهيأ مسبقاً
            self._usb_dev = dev
            endpoint = None
            try:
                cfg_obj = dev.get_active_configuration()
                for intf in cfg_obj:
                    for ep in intf:
                        # OUT endpoint: direction bit (0x80) not set / نقطة نهاية للإخراج
                        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                            endpoint = ep
                            break
                    if endpoint is not None:
                        break
            except Exception:
                endpoint = None
            self._usb_endpoint = endpoint.bEndpointAddress if endpoint is not None else 0x01

        elif ctype == "bluetooth":
            # Not yet supported — degrade safely / غير مدعوم بعد — تحول آمن
            raise ValueError("bluetooth printers are not supported yet")

        else:
            raise ValueError(f"unsupported connection_type: {ctype!r}")

        self._dry_run = False
        self.logger.info(
            f"✅ ESC/POS: connected via {ctype} | تم الاتصال بالطابعة عبر {ctype} "
            f"({cfg.device_name or 'unnamed'})"
        )
        return True

    def _enter_dry_run(self, reason: str) -> None:
        """Switch to dry-run capture mode. التحويل إلى وضع الالتقاط الآمن."""
        self._dry_run = True
        self._cleanup_handles()
        self.logger.warning(
            f"⚠️ ESC/POS: degraded to dry_run ({reason}) — output captured only | "
            f"تم التحويل لوضع الالتقاط بسبب: {reason}"
        )

    def _cleanup_handles(self) -> None:
        """Close every hardware handle silently. إغلاق كل المقابض بصمت."""
        for handle in (self._sock, self._serial, self._file):
            try:
                if handle is not None:
                    handle.close()
            except Exception:
                pass
        self._sock = None
        self._serial = None
        self._file = None
        self._usb_dev = None
        self._usb_endpoint = None

    def _disconnect(self) -> None:
        """Close the connection (idempotent). إغلاق الاتصال (آمن للتكرار)."""
        self._cleanup_handles()

    def close(self) -> None:
        """Public cleanup — flush and disconnect. تنظيف عام للموارد."""
        self._disconnect()

    # ── low-level write — الكتابة منخفضة المستوى ─────────────────────

    def _write(self, data: bytes) -> bool:
        """Write raw bytes to the device (or capture in dry-run).

        يكتب البايتات للجهاز أو يلتقطها في وضع dry_run؛ يعيد True دائماً
        حتى عند التدهور — فشل الطابعة لا يُسقط عملية البيع.
        """
        if not data:
            return True
        # Mirror every byte into last_output (debug + tests + spool recovery)
        self.last_output.extend(data)
        if len(self.last_output) > self.MAX_CAPTURE_BYTES:
            del self.last_output[: len(self.last_output) - self.MAX_CAPTURE_BYTES]

        if self._dry_run:
            return True
        try:
            if self._sock is not None:
                self._sock.sendall(data)
            elif self._serial is not None:
                self._serial.write(data)
                try:
                    self._serial.flush()
                except Exception:
                    pass
            elif self._file is not None:
                self._file.write(data)
                self._file.flush()
            elif self._usb_dev is not None:
                self._usb_dev.write(self._usb_endpoint, data)
            return True
        except Exception as exc:
            self.logger.warning(
                f"⚠️ ESC/POS: write failed → dry_run | فشل الكتابة للطابعة: {exc}"
            )
            self._enter_dry_run("write failure")
            return True

    # ── encoding — الترميز ───────────────────────────────────────────

    def _pick_encoding(self, text: str) -> str:
        """Pick the first Arabic-compatible encoding that can encode text.

        يختار أول ترميز متوافق مع العربية يستطيع ترميز النص كاملاً،
        بالترتيب: cp864 ثم cp1256 ثم cp720 ثم utf-8.
        """
        for encoding in self.ENCODING_CANDIDATES:
            try:
                text.encode(encoding)
                return encoding
            except (UnicodeEncodeError, LookupError):
                continue
        return "utf-8"

    def _encode_text(self, text: str) -> bytes:
        """Encode receipt text for the printer (remembers chosen encoding).

        يرمّز نص الإيصال للطابعة ويتذكر الترميز المختار ليستخدمه
        get_last_output_text لفك الترميز بدقة أثناء الاختبار.
        """
        encoding = self._pick_encoding(text)
        self._last_encoding = encoding
        try:
            return text.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            return text.encode("utf-8", errors="replace")

    def get_last_output_text(self) -> str:
        """Decode the captured raw output for tests/debugging.

        يفك ترميز المخرجات الملتقطة للعرض/الاختبار؛ يحاول الترميز المعروف
        أولاً ثم cp864/cp1256 ثم utf-8 مع تجاهل البايتات التالفة.
        """
        data = bytes(self.last_output)
        for encoding in (self._last_encoding, "cp864", "cp1256"):
            if not encoding:
                continue
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return data.decode("utf-8", errors="replace")

    # ── receipt composition — تركيب الإيصال ──────────────────────────

    def _write_sections(
        self,
        sections: list[tuple[str, str]],
        tail: bytes,
    ) -> bool:
        """Encode styled text sections into one ESC/POS payload and write it.

        يرمّز أقسام النص (عريض/مضاعف/عادي) في حمولة واحدة ويكتبها؛
        ترميز واحد لكل الإيصال لضمان تناسق صفحة الأحرف على الطابعة.
        """
        full_text = "".join(text for _, text in sections)
        encoding = self._pick_encoding(full_text)
        self._last_encoding = encoding

        payload = bytearray(INIT)
        for style, text in sections:
            if style == "bold":
                payload += BOLD_ON
            elif style == "double":
                payload += DOUBLE_SIZE_ON
            payload += text.encode(encoding, errors="replace")
            if style == "bold":
                payload += BOLD_OFF
            elif style == "double":
                payload += DOUBLE_SIZE_OFF
        payload += tail
        return self._write(bytes(payload))

    def print_receipt(self, sale_dict: Mapping[str, Any]) -> bool:
        """Print a full sale receipt. طباعة إيصال بيع كامل.

        ``sale_dict`` is a plain dict (decoupled from the Sale model) —
        see :func:`render_receipt_text` for expected keys.
        Returns True even in dry_run; False only if the dict is unusable.
        """
        try:
            sections: list[tuple[str, str]] = [
                ("bold", render_receipt_header(sale_dict)),
                ("normal", render_receipt_items(sale_dict)),
                ("double", render_receipt_total_line(sale_dict)),
                ("normal", render_receipt_payment(sale_dict)),
                ("normal", render_receipt_footer()),
            ]
        except Exception as exc:
            self.logger.error(
                f"❌ ESC/POS: receipt render failed | فشل بناء الإيصال: {exc}"
            )
            return False
        self._write_sections(sections, tail=feed_lines(3) + PARTIAL_CUT)
        return True

    def print_x_report(self, session_dict: Mapping[str, Any]) -> bool:
        """Print X-report (mid-shift summary, no reset). طباعة تقرير X."""
        return self._print_session_report(session_dict, "x")

    def print_z_report(self, session_dict: Mapping[str, Any]) -> bool:
        """Print Z-report (end-of-shift summary, reset totals). طباعة تقرير Z."""
        return self._print_session_report(session_dict, "z")

    def _print_session_report(
        self, session_dict: Mapping[str, Any], report_kind: str
    ) -> bool:
        try:
            text = render_session_report_text(session_dict, report_kind)
        except Exception as exc:
            self.logger.error(
                f"❌ ESC/POS: {report_kind.upper()}-report render failed | "
                f"فشل بناء التقرير: {exc}"
            )
            return False
        sections = [("normal", text)]
        self._write_sections(sections, tail=feed_lines(3) + FULL_CUT)
        return True

    # ── hardware actions — عمليات العتاد ─────────────────────────────

    def open_cash_drawer(self) -> bool:
        """Send the cash-drawer kick pulse (pin 2). إرسال نبضة فتح درج النقدية."""
        self._write(CASH_DRAWER_KICK)
        return True

    def cut_paper(self, partial: bool = True) -> bool:
        """Feed 2 lines then cut. تغذية سطرين ثم القطع (جزئي أو كامل)."""
        cut = PARTIAL_CUT if partial else FULL_CUT
        self._write(feed_lines(2) + cut)
        return True

    def beep(self) -> bool:
        """Sound the printer buzzer (attention signal). تشغيل جرس الطابعة."""
        self._write(BEEP)
        return True

    def read_status(self, timeout: float = 2.0) -> bytes | None:
        """Best-effort DLE EOT 1 status read (network/serial only).

        قراءة حالة الطابعة (أفضل جهد) عبر طلب DLE EOT 1 — للاتصالات
        network/serial فقط، وبمهلة قصوى لا تتجاوز timeout ثانية؛ يعيد
        None عند الفشل أو في وضع dry_run بدون أي استثناء خارجي.
        """
        if self._dry_run:
            return None
        if self.connection_type not in ("network", "serial"):
            return None
        try:
            if self._sock is not None:
                previous_timeout = self._sock.gettimeout()
                self._sock.settimeout(max(0.1, float(timeout)))
                try:
                    self._sock.sendall(STATUS_REQUEST)
                    data = self._sock.recv(1)
                    return data if data else None
                finally:
                    try:
                        self._sock.settimeout(previous_timeout)
                    except Exception:
                        pass
            if self._serial is not None:
                self._serial.write_timeout = max(0.1, float(timeout))
                self._serial.timeout = max(0.1, float(timeout))
                self._serial.write(STATUS_REQUEST)
                data = self._serial.read(1)
                return data if data else None
        except Exception as exc:
            self.logger.warning(
                f"⚠️ ESC/POS: status read failed | فشل قراءة حالة الطابعة: {exc}"
            )
        return None
