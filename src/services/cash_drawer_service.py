#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cash Drawer Service — خدمة درج النقدية (GAP-2.2)

Controls a cash drawer wired to the ESC/POS receipt printer kick port (RJ11,
the standard wiring) or, optionally, a direct serial-attached drawer.

يتحكم في درج النقدية الموصول بمنفذ نبضة طابعة الإيصالات ESC/POS (الأسلاك
القياسية) أو، اختيارياً، درج موصول مباشرة عبر المنفذ التسلسلي.

Design rules — قواعد التصميم:
1. Hardware absence NEVER crashes the app — everything is guarded and the
   service falls back to dry_run semantics identical to the printer service.
   غياب العتاد لا يُسقط التطبيق أبداً — كل شيء محمي والخدمة تعمل بنمط
   dry_run المطابق لخدمة الطابعة.
2. If no dedicated ``cash_drawer`` hardware_config row exists, the service
   delegates to :class:`ESCPOSPrinterService` (kick through the printer) —
   this is the standard wiring in real POS installations.
   عند غياب إعدادات خاصة بالدرج، تُفوَّض المهمة لخدمة الطابعة (نبضة عبر
   الطابعة) وهي الطريقة القياسية في أنظمة نقاط البيع.
3. pyserial is imported lazily inside the connect attempt only.
   يتم استيراد pyserial مؤجلاً داخل محاولة الاتصال فقط.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from src.services.escpos_printer_service import (
    CASH_DRAWER_KICK,
    ESCPOSPrinterService,
    HardwareConfig,
)
from src.utils.logger import setup_logger


class DrawerStatus(Enum):
    """Cash drawer physical state — الحالة الفعلية لدرج النقدية."""

    OPEN = "open"          # الدرج مفتوح
    CLOSED = "closed"      # الدرج مغلق
    UNKNOWN = "unknown"    # لا يمكن التحقق (لا يوجد عتاد قراءة)


class CashDrawerService:
    """Cash drawer control with printer-kick delegation and dry-run fallback.

    خدمة التحكم في درج النقدية مع التفويض إلى نبضة الطابعة وتحول آمن إلى
    وضع dry_run — فتح الدرج لا يُسقط عملية البيع أبداً.
    """

    #: DLE EOT 1 — printer real-time status (includes drawer kick pin 3 bit)
    STATUS_REQUEST: bytes = b"\x10\x04\x01"
    STATUS_READ_TIMEOUT: float = 2.0  # seconds — never block longer / أقصى مهلة

    def __init__(self, db_manager: Any, logger: Any = None) -> None:
        """Load default ``cash_drawer`` config and prepare the delegate printer.

        يحمّل إعدادات الدرج الافتراضية ويجهز الطابعة المفوَّض إليها؛ عند عدم
        وجود إعدادات يعمل عبر الطابعة في وضع dry_run بأمان.
        """
        self.logger = logger or setup_logger(__name__)
        self._db_manager = db_manager
        self.config: HardwareConfig | None = HardwareConfig.get_default(
            db_manager, "cash_drawer"
        )
        self.last_output: bytearray = bytearray()

        # Delegate printer — the standard kick wiring (RJ11 through printer)
        # الطابعة المفوَّض إليها — الأسلاك القياسية عبر منفذ الطابعة
        self.printer_service = ESCPOSPrinterService(db_manager, logger=logger)

        # Optional direct serial drawer (rare hardware) — درج تسلسلي مباشر (نادر)
        self._direct_serial: Any = None
        if self.config is not None and (self.config.connection_type or "").lower() == "serial":
            self._connect_direct_serial()

    # ── connection — الاتصال ─────────────────────────────────────────

    def _connect_direct_serial(self) -> bool:
        """Best-effort direct serial connection to a standalone drawer.

        محاولة اتصال تسلسلي مباشر بالدرج (أفضل جهد)؛ الفشل يُسجل ويعيد
        التفويض للطابعة بدون أي استثناء.
        """
        params = (self.config.connection_params or {}) if self.config else {}
        try:
            import serial as pyserial  # lazy — قد لا تكون مثبتة

            self._direct_serial = pyserial.Serial(
                port=str(params.get("port") or params.get("device") or ""),
                baudrate=int(params.get("baud_rate", 9600) or 9600),
                bytesize=8,
                parity=pyserial.PARITY_NONE,
                stopbits=1,
                timeout=self.STATUS_READ_TIMEOUT,
                write_timeout=self.STATUS_READ_TIMEOUT,
            )
            self.logger.info(
                f"✅ Cash drawer: direct serial on {self._direct_serial.port} | "
                f"اتصال مباشر بالدرج عبر {self._direct_serial.port}"
            )
            return True
        except Exception as exc:
            self._direct_serial = None
            self.logger.warning(
                f"⚠️ Cash drawer: direct serial failed → printer kick | "
                f"فشل الاتصال المباشر بالدرج، سيتم التفويض للطابعة: {exc}"
            )
            return False

    @property
    def is_dry_run(self) -> bool:
        """True when no real hardware path exists (output captured only).

        True عندما لا يوجد مسار عتاد حقيقي (تُلتقط المخرجات فقط):
        لا درج تسلسلي مباشر والطابعة المفوَّض إليها في وضع dry_run.
        """
        if self._direct_serial is not None:
            return False
        return self.printer_service.is_dry_run

    # ── actions — العمليات ───────────────────────────────────────────

    def open(self) -> bool:
        """Send the drawer kick pulse (pin 2). إرسال نبضة فتح الدرج (دخل 2).

        Direct serial drawer first; otherwise delegate to the printer kick.
        Returns True even in dry_run — a missing drawer never blocks a sale.
        """
        try:
            if self._direct_serial is not None:
                try:
                    self._direct_serial.write(CASH_DRAWER_KICK)
                    try:
                        self._direct_serial.flush()
                    except Exception:
                        pass
                    self.last_output.extend(CASH_DRAWER_KICK)
                    return True
                except Exception as exc:
                    self.logger.warning(
                        f"⚠️ Cash drawer: direct write failed → printer kick | "
                        f"فشل الكتابة المباشرة، التفويض للطابعة: {exc}"
                    )
                    try:
                        self._direct_serial.close()
                    except Exception:
                        pass
                    self._direct_serial = None

            result = self.printer_service.open_cash_drawer()
            # Mirror the delegated pulse so callers can inspect what was sent
            # عكس النبضة المرسلة عبر الطابعة لأغراض الفحص والاختبار
            self.last_output.extend(CASH_DRAWER_KICK)
            return result
        except Exception as exc:
            # Absolute last resort — log, record, succeed: sale must continue
            # الملاذ الأخير — تسجيل والتقاط والنجاح: البيع يجب أن يستمر
            self.logger.warning(
                f"⚠️ Cash drawer: open failed entirely | فشل فتح الدرج كلياً: {exc}"
            )
            self.last_output.extend(CASH_DRAWER_KICK)
            return True

    def open_and_log(self, reason: str = "") -> bool:
        """Open the drawer and record an audit note in the logger.

        يفتح الدرج ويسجل ملاحظة تدقيق في السجل (بدون أي اعتماد على جدول
        التدقيق) — لكل فتح درج يجب أن يكون له سبب موثق.
        """
        result = self.open()
        self.logger.info(
            f"💰 Cash drawer opened | تم فتح درج النقدية — "
            f"reason/السبب: {reason or 'manual'}, dry_run={self.is_dry_run}, "
            f"success={result}"
        )
        return result

    def check_status(self) -> DrawerStatus:
        """Check drawer open/closed state (best-effort, max ~2s).

        فحص حالة الدرج (أفضل جهد) — عبر طلب حالة الطابعة DLE EOT 1 إذا كان
        الاتصال network/serial؛ يعيد UNKNOWN فوراً في dry_run أو عند الفشل،
        ولا ينتظر أبداً أكثر من مهلة قصيرة.

        Bit interpretation — تفسير البت:
            DLE EOT 1 bit 2 (0x04) reflects drawer kick-out pin 3; the
            ON/OFF→open/closed mapping is device-dependent, this default
            treats pin-3-high as OPEN (documented best-effort behaviour).
        """
        if self.is_dry_run:
            return DrawerStatus.UNKNOWN
        try:
            data = self.printer_service.read_status(
                timeout=self.STATUS_READ_TIMEOUT
            )
        except Exception as exc:
            self.logger.warning(
                f"⚠️ Cash drawer: status read exception | استثناء قراءة الحالة: {exc}"
            )
            return DrawerStatus.UNKNOWN
        if not data:
            return DrawerStatus.UNKNOWN
        try:
            status_byte = data[0]
        except (TypeError, IndexError):
            return DrawerStatus.UNKNOWN
        return DrawerStatus.OPEN if (status_byte & 0x04) else DrawerStatus.CLOSED

    # ── cleanup — التنظيف ────────────────────────────────────────────

    def close(self) -> None:
        """Release hardware handles (idempotent). تحرير المقابض (آمن للتكرار)."""
        try:
            if self._direct_serial is not None:
                self._direct_serial.close()
        except Exception:
            pass
        self._direct_serial = None
        try:
            self.printer_service.close()
        except Exception:
            pass
