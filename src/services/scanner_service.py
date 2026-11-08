#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الماسح الضوئي - Scanner Service
تكامل الماسحات الضوئية (باركود 1D) عبر لوحة المفاتيح (keyboard-wedge) أو المنفذ التسلسلي.

GAP-1.3 (SRS_ARCHITECTURE.md §2.4): 1D Barcode Generation & Scanner Integration.

المبدأ القياسي للـ keyboard-wedge:
    الماسح "يكتب" محارف بسرعة عالية جداً وينتهي بـ Enter داخل أي عنصر مُركّز.
    لذا هذه الخدمة تميّز ضربة الماسح عن الكتابة البشرية عبر نافذة زمنية:
    انفجار > 6 محارف خلال < 150ms = مسح؛ غير ذلك = كتابة عادية.

    Standard keyboard-wedge contract: a scanner "types" a burst of characters
    very fast and terminates with Enter into whatever widget has focus. This
    service distinguishes scanner bursts (> 6 chars within < 150 ms) from human
    typing using an injectable clock so timing is fully testable.

Modes:
- ``keyboard_wedge`` (default): الطبقة الرسومية (Qt) هي التي تُغذّي المحارف —
  في ``keyPressEvent`` استدعِ ``feed(key.text())`` وعند رجوع حدث مسح استدعِ
  ``process_scan_event(event)``. لا يوجد thread لهذا الوضع.
- ``serial``: thread خلفي (daemon) يقرأ سطوراً من منفذ تسلسلي عبر pyserial
  (استيراد كسول محمي) ويستدعي الـ callback مع المنتج المطابق.

الاعتمادات: صفر اعتمادات خارجية إلزامية (pyserial/PIL كسولة فقط).
Zero mandatory third-party dependencies (pyserial lazy, guarded).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, Optional

from src.services.barcode_service import BarcodeService
from src.utils.logger import setup_logger


class ScannerService:
    """خدمة الماسح الضوئي: تخزين مؤقت، تمييز الانفجارات، وتحويل المسح لمنتج.

    Scan-buffer engine + resolution. The buffer logic is pure and driven by an
    injectable ``clock`` callable (default ``time.monotonic``) so tests can
    advance time deterministically.

    Attributes:
        active: هل المستمع نشط حالياً؟ / whether the listener is active.
        serial_port: مسار منفذ الماسح التسلسلي (وضع serial فقط).
    """

    CONNECTION_KEYBOARD: str = "keyboard_wedge"
    CONNECTION_SERIAL: str = "serial"

    #: أقل عدد محارف يُعتبر انفجار ماسح (الشرط: > 6 ⇒ 7 فأكثر).
    MIN_SCAN_CHARS: int = 6

    def __init__(
        self,
        db_manager=None,
        logger=None,
        connection_type: str = CONNECTION_KEYBOARD,
        clock: Optional[Callable[[], float]] = None,
        window_ms: float = 150.0,
        serial_port: Optional[str] = None,
        serial_baudrate: int = 9600,
        serial_encoding: str = "utf-8",
    ):
        """تهيئة الخدمة.

        Args:
            db_manager: مدير قاعدة البيانات — اختياري؛ عند تمريره تُنشأ خدمة
                باركود داخلية لتحويل المسح إلى منتج في :meth:`on_scan`.
            logger: مسجّل اختياري / optional logger.
            connection_type: ``"keyboard_wedge"`` (افتراضي) أو ``"serial"``.
            clock: دالة زمن قابلة للحقن (افتراضي ``time.monotonic``) — للاختبار.
            window_ms: نافذة الانفجار بالمللي ثانية (افتراضي 150).
            serial_port: مسار المنفذ التسلسلي مثل ``/dev/ttyUSB0`` (وضع serial).
            serial_baudrate: معدل البود (افتراضي 9600).
            serial_encoding: ترميز قراءة السطور (افتراضي utf-8).
        """
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)
        self.connection_type = str(connection_type or self.CONNECTION_KEYBOARD).lower()
        self._clock: Callable[[], float] = clock if clock is not None else time.monotonic
        self.window_ms = float(window_ms)
        self.serial_port = serial_port
        self.serial_baudrate = int(serial_baudrate)
        self.serial_encoding = serial_encoding

        self._barcode_service: Optional[BarcodeService] = (
            BarcodeService(db_manager, self.logger) if db_manager is not None else None
        )

        # ── العازل المؤقت للمسح / scan buffer state ──
        self._buffer: str = ""
        self._buffer_start: float = 0.0
        self._last_feed: float = 0.0
        self._buffer_source: str = "keyboard"

        # ── المستمع / listener state ──
        self.active: bool = False
        self._callback: Optional[Callable[[Optional[Dict[str, Any]]], None]] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # ── الإحصاءات / statistics ──
        self._stats: Dict[str, int] = {
            "scans_detected": 0,
            "scans_resolved": 0,
            "scans_failed": 0,
        }
        self._resolution_total_ms: float = 0.0
        self._resolution_attempts: int = 0

    # ─────────────── محرك العازل / Scan-buffer engine ───────────────

    def feed(self, chunk: str, source: str = "keyboard") -> Optional[Dict[str, Any]]:
        """تغذية المحارف القادمة (من Qt keyPressEvent مثلاً) للعازل.

        Accumulates characters; when the chunk terminates with ``\\n``/``\\r``
        (Enter — scanner suffix) the buffer becomes a scan candidate. The
        candidate counts as a scanner burst only if its total length is
        > :data:`MIN_SCAN_CHARS` characters and the burst completed within
        :attr:`window_ms`; otherwise it is treated as normal typing (buffer
        cleared, None returned).

        Multi-chunk bursts are supported: ``feed("1234", t=0.0)`` then
        ``feed("5678\\n", t=0.05)`` → scan ``"12345678"``.

        Args:
            chunk: المحارف الواردة / incoming characters (may end with Enter).
            source: مصدر الإدخال (keyboard/serial) — توثيقي.

        Returns:
            Optional[Dict[str, Any]]: حدث مسح ``{"barcode", "source",
            "duration_ms", "completed_by"}`` عند اكتمال مسح صالح، أو None.
        """
        if chunk is None:
            return None
        now = self._clock()
        text = str(chunk)
        if not text:
            return None

        result: Optional[Dict[str, Any]] = None
        newline_index = max(text.rfind("\n"), text.rfind("\r"))
        if newline_index >= 0:
            # اكتمال مرشّح عند آخر Enter، وما بعده يبدأ عازلاً جديداً.
            complete_part = text[:newline_index]
            pending_part = text[newline_index + 1:]
            if not self._buffer:
                self._buffer_start = now
                self._buffer_source = source
            self._buffer += complete_part
            self._last_feed = now
            result = self._complete_candidate(now, source)
            if pending_part:
                self._buffer = pending_part
                self._buffer_start = now
                self._buffer_source = source
                self._last_feed = now
        else:
            if not self._buffer:
                self._buffer_start = now
                self._buffer_source = source
            self._buffer += text
            self._last_feed = now
        return result

    def flush(self, timeout_ms: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """إنهاء العازل يدوياً (للمسحات التي لا تنتهي بـ Enter).

        Returns the pending candidate as a scan if it was completed (last
        character received) within ``timeout_ms`` (default :attr:`window_ms`),
        otherwise treats it as typing. Either way the buffer is cleared.

        Args:
            timeout_ms: نافذة بديلة بالمللي ثانية / window override.

        Returns:
            Optional[Dict[str, Any]]: حدث المسح أو None.
        """
        now = self._clock()
        if not self._buffer:
            return None
        candidate = self._buffer.strip()
        duration_ms = (self._last_feed - self._buffer_start) * 1000.0
        source = self._buffer_source
        self._reset_buffer()
        window = self.window_ms if timeout_ms is None else float(timeout_ms)
        if len(candidate) > self.MIN_SCAN_CHARS and duration_ms <= window:
            self._stats["scans_detected"] += 1
            return self._scan_event(candidate, duration_ms, completed_by="flush", source=source)
        self.logger.debug("flush: تم اعتبار العازل كتابة بشرية وإفراغه")
        return None

    def _complete_candidate(self, now: float, source: str = "keyboard") -> Optional[Dict[str, Any]]:
        """تقييم المرشّح الحالي عند Enter / Evaluate the buffered candidate."""
        candidate = self._buffer.strip()
        duration_ms = (now - self._buffer_start) * 1000.0
        self._reset_buffer()
        if len(candidate) > self.MIN_SCAN_CHARS and duration_ms <= self.window_ms:
            self._stats["scans_detected"] += 1
            return self._scan_event(candidate, duration_ms, completed_by="newline", source=source)
        self.logger.debug(
            f"إدخال مرفوض كمسح ({len(candidate)} محرف خلال {duration_ms:.1f}ms) — كتابة بشرية"
        )
        return None

    def _reset_buffer(self) -> None:
        """إفراغ العازل / Clear the scan buffer."""
        self._buffer = ""
        self._buffer_start = 0.0
        self._last_feed = 0.0

    @staticmethod
    def _scan_event(
        barcode: str, duration_ms: float, completed_by: str, source: str = "keyboard"
    ) -> Dict[str, Any]:
        """بناء حدث مسح موحّد / Build a normalized scan event dict."""
        return {
            "barcode": barcode,
            "source": source,
            "duration_ms": round(duration_ms, 3),
            "completed_by": completed_by,
        }

    # ─────────────────── التحويل / Resolution ───────────────────

    def on_scan(self, barcode: Any) -> Optional[Dict[str, Any]]:
        """معالجة باركود ممسوح: تحويله إلى منتج وتحديث الإحصاءات.

        Resolves the scanned value through the internal
        :class:`BarcodeService` (created when a ``db_manager`` was provided)
        and returns the product dict or None. Never raises.

        Args:
            barcode: الباركود الممسوح / scanned barcode value.

        Returns:
            Optional[Dict[str, Any]]: قاموس المنتج المطابق أو None.
        """
        text = str(barcode).strip() if barcode is not None else ""
        if not text:
            return None

        started = time.perf_counter()
        product: Optional[Dict[str, Any]] = None
        if self._barcode_service is None:
            self.logger.warning(
                "on_scan بدون db_manager — لا يمكن التحويل إلى منتج (أعطِ db_manager عند الإنشاء)"
            )
        else:
            try:
                product = self._barcode_service.resolve_barcode(text)
            except Exception as exc:  # noqa: BLE001 — التحويل لا يجب أن يرفع استثناءً للواجهة
                self.logger.error(f"خطأ أثناء تحويل المسح {text!r}: {exc}")
                product = None
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self._resolution_total_ms += elapsed_ms
        self._resolution_attempts += 1

        if product is not None:
            self._stats["scans_resolved"] += 1
            self.logger.info(
                f"مسح مُحوَّل: {text} → منتج {product.get('id')} ({product.get('name')}) "
                f"خلال {elapsed_ms:.2f}ms"
            )
        else:
            self._stats["scans_failed"] += 1
            self.logger.warning(f"مسح غير معروف: {text!r}")
        return product

    def process_scan_event(
        self, event: Any
    ) -> Optional[Dict[str, Any]]:
        """تحويل حدث مسح (من feed/serial) إلى منتج + إشعار الـ callback.

        Convenience bridge for the UI layer: ``product =
        scanner.process_scan_event(event)``. Accepts a scan-event dict or a
        raw barcode string. The registered callback (if any) is invoked with
        the product dict (possibly None) and its exceptions are contained.

        Returns:
            Optional[Dict[str, Any]]: المنتج المطابق أو None.
        """
        if not event:
            return None
        barcode = event.get("barcode") if isinstance(event, dict) else event
        product = self.on_scan(barcode)
        callback = self._callback
        if callback is not None:
            try:
                callback(product)
            except Exception as exc:  # noqa: BLE001 — خطأ الـ callback لا يوقف الخدمة
                self.logger.error(f"فشل callback الماسح: {exc}")
        return product

    # ───────────────── المستمع الخلفي / Background listener ─────────────────

    def start_listening(
        self, callback: Callable[[Optional[Dict[str, Any]]], None]
    ) -> None:
        """بدء الاستماع للمسحات.

        - ``serial``: يشغّل thread خلفي (daemon) يقرأ سطوراً من المنفذ المُعدّ
          عبر pyserial (استيراد كسول محمي). عند فشل المنفذ أو غياب المكتبة:
          تحذير في السجل و ``active=False`` — بدون أي استثناء.
        - ``keyboard_wedge``: لا يوجد thread — الطبقة الرسومية (Qt) هي من
          يستدعي ``feed()`` داخل ``keyPressEvent`` ثم ``process_scan_event()``؛
          هنا فقط يُسجَّل الـ callback ويُضبط ``active=True``.

        Args:
            callback: دالة تستدعى مع قاموس المنتج (أو None لمسح غير معروف).
        """
        self._callback = callback
        if self.connection_type == self.CONNECTION_SERIAL:
            if not self.serial_port:
                self.logger.warning(
                    "ماسح تسلسلي بدون serial_port — لم يبدأ الاستماع / no serial port configured"
                )
                self.active = False
                return
            self._stop_event.clear()
            self.active = True
            self._thread = threading.Thread(
                target=self._serial_loop, name="ScannerService-serial", daemon=True
            )
            self._thread.start()
            self.logger.info(f"بدأ الاستماع على المنفذ التسلسلي {self.serial_port}")
        else:
            self.active = True
            self.logger.info(
                "وضع keyboard_wedge: الطبقة الرسومية تُغذّي feed() من keyPressEvent — "
                "لا يوجد thread خلفي"
            )

    def stop_listening(self) -> None:
        """إيقاف الاستماع وإنهاء الـ thread (مهلة انتظار ثانيتان).

        Signals the background thread to stop and joins it with a 2s timeout;
        never raises even if the thread is stuck or already dead.
        """
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
            if thread.is_alive():
                self.logger.warning("لم يتوقف thread الماسح خلال ثانيتين / scanner thread stuck")
        self._thread = None
        self.active = False

    def _serial_loop(self) -> None:
        """حلقة قراءة المنفذ التسلسلي (thread خلفي daemon).

        Reads lines from the configured serial port via a lazily imported,
        guarded pyserial and dispatches every non-empty line through
        :meth:`process_scan_event`. Any failure (missing library, absent port,
        IO error) is logged, sets ``active=False`` and exits quietly.
        """
        try:
            import serial as pyserial  # noqa: WPS433 — استيراد كسول مقصود
        except ImportError as exc:
            self.logger.warning(
                f"pyserial غير مثبت — ماسح المنفذ التسلسلي معطّل "
                f"(pip install pyserial): {exc}"
            )
            self.active = False
            return

        port = None
        try:
            port = pyserial.Serial(
                self.serial_port, self.serial_baudrate, timeout=0.5
            )
            while not self._stop_event.is_set():
                raw = port.readline()
                if not raw:
                    continue
                text = raw.decode(self.serial_encoding, errors="replace").strip()
                if text:
                    self.process_scan_event(
                        self._scan_event(text, 0.0, completed_by="serial", source="serial")
                    )
        except Exception as exc:  # noqa: BLE001 — أي فشل لا يوقف التطبيق
            self.logger.warning(f"توقف ماسح المنفذ التسلسلي: {exc}")
            self.active = False
        finally:
            if port is not None:
                try:
                    port.close()
                except Exception:  # noqa: BLE001 — الإغلاق لا يرفع
                    pass

    # ─────────────────────── الإحصاءات / Statistics ───────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        """إحصاءات المسح / Scan statistics.

        Returns:
            Dict[str, Any]: ``scans_detected`` (انفجارات صالحة)،
            ``scans_resolved`` (تحولت لمنتج)، ``scans_failed`` (لم تتحول)،
            ``avg_resolution_ms`` (متوسط زمن التحويل)، وأخرى توثيقية.
        """
        attempts = self._resolution_attempts
        avg_ms = self._resolution_total_ms / attempts if attempts else 0.0
        return {
            "scans_detected": self._stats["scans_detected"],
            "scans_resolved": self._stats["scans_resolved"],
            "scans_failed": self._stats["scans_failed"],
            "avg_resolution_ms": round(avg_ms, 3),
            "attempts": attempts,
            "active": self.active,
            "connection_type": self.connection_type,
            "buffered_chars": len(self._buffer),
        }
