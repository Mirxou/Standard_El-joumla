#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التفريغ التلقائي لطابور المزامنة (GAP-5.2) — Sync Queue Flush Service
==========================================================================

الغرض / Purpose:
    عند استعادة الاتصال (انتقال offline → online)، تُفرَّغ طابور المزامنة
    المحلي (sync_queue) تلقائيًا بدل انتظار مزامنة يدوية، حتى لا تبقى
    عمليات البيع/الجرد المعلقة بلا حدود.

    When connectivity returns (offline → online transition), automatically
    flush the local ``sync_queue`` instead of waiting for a manual sync, so
    offline sales/stock operations are never stranded indefinitely.

المطابقة مع SRS / SRS Reference:
    docs/SRS_ARCHITECTURE.md → Area 5 → GAP-5.2 (Automatic Offline Queue
    Flush) — يغطي: ربط مراقب الاتصال، التهدئة (debounce)، إحصائيات المحاولات،
    وقراءة عمق الطابور من المخطط الحقيقي.

ما تم اكتشافه في المصدر الفعلي / What was discovered in the real codebase:
    * مراقب الاتصال ``ConnectivityMonitor`` (src/core/connectivity_monitor.py)
      هو QObject مع إشارات Qt: ``connected``, ``disconnected``,
      ``status_changed(bool)`` — لا يوجد سجل استدعاءات عادي، لذا أضيفت
      إضافة طفيفة ``on_state_change(callback)`` تناسب معماره.
    * مخطط ``sync_queue`` الحقيقي (src/api/api_client.py):
      ``id, entity_type, entity_id, operation, created_at, synced BOOLEAN``
      — عمود الحالة هو ``synced`` (0 = معلّق).
    * صيغة ثانية لـ sync_queue في src/core/local_database_manager.py:
      ``id, table_name, record_id, operation, data, retry_count, ...``
      بلا عمود حالة (الصفوف كلها معلّقة حتى معالجتها).
    * أسماء طرق التفريغ الحقيقية في مكدس المزامنة:
      ``sync_pending_changes()`` (api_client، تعيد Dict[str,int]),
      ``sync_now()`` / ``sync_ultimate_flow()`` (sync_service),
      بينما ``full_sync(settings_id)`` تحتاج معاملات فتُستبعد تلقائيًا.

مبدأ صارم / Strictness principle:
    لا يوجد "نجاح مزيّف" — إذا لم يوجد مُنفّذ تفريغ حقيقي (لا cloud_sync_service
    بطريقة مناسبة ولا flush_callback)، يفشل flush_now صراحةً (success=False
    مع رسالة خطأ) ولا يُعلَّم أي صف كـ flushed أبدًا.
    No fake success: if no real flusher exists, ``flush_now`` returns
    ``success=False`` with an explicit error — queue rows are NEVER marked
    as flushed by this service itself.
"""

from __future__ import annotations

import inspect
import time
from typing import Any, Callable, Dict, Optional

from src.utils.logger import setup_logger

# أسماء طرق التفريغ المرشحة بالترتيب — مرتبة على المكدس الفعلي للمشروع
_FLUSHER_METHOD_CANDIDATES: tuple[str, ...] = (
    "flush_pending",
    "flush_queue",
    "process_queue",
    "push_pending",
    "sync_pending_changes",  # api_client.py — الطريقة الحقيقية لتفريغ sync_queue
    "sync_pending",
    "sync_now",              # sync_service.py
    "sync_ultimate_flow",    # sync_service.py
)

_STATE_ONLINE = "online"
_STATE_OFFLINE = "offline"
_ONLINE_ALIASES = frozenset({"online", "connected", "up", "true", "1", "yes"})
_OFFLINE_ALIASES = frozenset({"offline", "disconnected", "down", "false", "0", "no"})


class SyncQueueFlushService:
    """تفريغ تلقائي لطابور المزامنة عند استعادة الاتصال — Auto flush of sync_queue on reconnect.

    المدخلات:
        * ``cloud_sync_service``: يُفحَص انعكاسيًا (hasattr + توقيع بدون معاملات)
          لاختيار طريقة تفريغ حقيقية (مثل ``sync_pending_changes``).
        * ``flush_callback``: بديل صريح يعيد int (عدد المفرَّغ) أو bool.
        * ``connectivity_monitor``: يُربَط عبر ``attach_to_monitor`` بإطاره المتاح
          (إشارة Qt أو ``on_state_change``).
        * ``min_flush_interval_s``: فترة تهدئة بين عمليات التفريغ (افتراضي 20 ثانية).
        * ``clock``: ساعة monotonic قابلة للحقن للاختبارات (افتراضي time.monotonic).
    """

    def __init__(
        self,
        db_manager=None,
        connectivity_monitor=None,
        cloud_sync_service=None,
        logger=None,
        flush_callback: Callable[[], Any] | None = None,
        min_flush_interval_s: float = 20.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """التهيئة — Constructor.

        Args:
            db_manager: مدير قاعدة البيانات لقراءة عمق الطابور (اختياري).
            connectivity_monitor: مراقب الاتصال (يُربط تلقائيًا إن أمكن).
            cloud_sync_service: خدمة مزامنة تُفحص انعكاسيًا بحثًا عن طريقة تفريغ.
            logger: مسجّل مخصص (اختياري).
            flush_callback: دالة تفريغ صريحة تعيد int أو bool (اختيارية).
            min_flush_interval_s: الحد الأدنى للفاصل بين التفريغات (تهدئة).
            clock: ساعة قابلة للحقن (monotonic) لأغراض الاختبار.
        """
        self.db_manager = db_manager
        self.logger = logger or setup_logger(self.__class__.__name__)
        self._flush_callback = flush_callback
        self.min_flush_interval_s = max(0.0, float(min_flush_interval_s))
        self._clock = clock or time.monotonic

        # اختيار المُنفّذ: طريقة من cloud_sync_service أولاً ثم flush_callback
        self._cloud_flusher: Optional[Callable[[], Any]] = None
        self._cloud_flusher_name: Optional[str] = None
        if cloud_sync_service is not None:
            self._cloud_flusher, self._cloud_flusher_name = self._resolve_flusher_method(
                cloud_sync_service
            )
            if self._cloud_flusher is None:
                self.logger.warning(
                    "cloud_sync_service لا يعرض طريقة تفريغ مناسبة بدون معاملات — "
                    "سيُعتمد flush_callback إن وُجد"
                )
        self._flusher = self._cloud_flusher or self._flush_callback
        self._flusher_source: Optional[str] = (
            self._cloud_flusher_name if self._cloud_flusher else (
                "flush_callback" if self._flush_callback else None
            )
        )

        # حالة الاتصال الأخيرة لمنطق الانتقال — last known state for transition logic
        self._last_state: Optional[str] = None
        self._monitor_attached = False

        # حالة التهدئة — cooldown state
        self._last_flush_time: Optional[float] = None

        # الإحصائيات — statistics
        self._stats: Dict[str, Any] = {
            "total_flush_attempts": 0,
            "successful": 0,
            "failed": 0,
            "last_flush_at": None,        # وقت الجدار wall-clock لآخر محاولة
            "last_flushed_count": 0,
            "last_error": None,
            "skipped_flushes": 0,         # إضافي: عدد التفريغات المُتجاهلة بالتهدئة
            "last_flush_reason": None,
            "flusher_source": self._flusher_source,
        }

        if connectivity_monitor is not None:
            self.attach_to_monitor(connectivity_monitor)

    # ------------------------------------------------------------------ #
    # اكتشاف طريقة التفريغ / Flusher introspection
    # ------------------------------------------------------------------ #
    @staticmethod
    def _resolve_flusher_method(service: Any) -> tuple[Optional[Callable[[], Any]], Optional[str]]:
        """فحص انعكاسي لطريقة تفريغ صفرية المعاملات — Find a zero-arg flusher method.

        يتخطى الطرق التي تتطلب معاملات (مثل ``full_sync(settings_id)``).
        Skips methods that require arguments (e.g. ``full_sync(settings_id)``).
        """
        if service is None:
            return None, None
        for name in _FLUSHER_METHOD_CANDIDATES:
            method = getattr(service, name, None)
            if method is None or not callable(method):
                continue
            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):
                # builtins/objects بلا توقيع — نفترض قابلية الاستدعاء
                return method, name
            try:
                signature.bind()
            except TypeError:
                continue  # تحتاج معاملات — requires args
            return method, name
        return None, None

    @staticmethod
    def _normalize_flushed_count(raw: Any) -> int:
        """تطبيع ناتج المُنفّذ إلى int — Normalize flusher result to a flushed count.

        يدعم: int / bool / None / dict مثل ``{"synced": n, "failed": m, "pending": k}``
        (صيغة api_client.sync_pending_changes الحقيقية).
        """
        if raw is None:
            return 0
        if isinstance(raw, bool):
            return 1 if raw else 0
        if isinstance(raw, int):
            return max(0, raw)
        if isinstance(raw, dict):
            for key in ("flushed", "synced", "pushed", "processed", "count"):
                value = raw.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    return max(0, int(value))
            return 0
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return 0

    # ------------------------------------------------------------------ #
    # التفريغ الفوري / Immediate flush
    # ------------------------------------------------------------------ #
    def flush_now(self, reason: str = "manual") -> dict:
        """محاولة تفريغ فورية مع تهدئة وحماية كاملة — Immediate flush attempt with cooldown; never raises.

        Args:
            reason: سبب التفريغ ("manual" | "reconnect" | ...).

        Returns:
            {success: bool, flushed: int, error: str|None, duration_ms: int,
             reason: str, skipped: bool}
        """
        started = time.perf_counter()
        result: Dict[str, Any] = {
            "success": False,
            "flushed": 0,
            "error": None,
            "duration_ms": 0,
            "reason": reason,
            "skipped": False,
        }

        # بوابة التهدئة / cooldown gate
        now = self._clock()
        if (
            self._last_flush_time is not None
            and (now - self._last_flush_time) < self.min_flush_interval_s
        ):
            result["skipped"] = True
            result["success"] = True  # تجاهل مقصود وليس فشل — intentional skip, not failure
            self._stats["skipped_flushes"] += 1
            self.logger.debug(
                f"تجاهل التفريغ (ضمن فترة التهدئة {self.min_flush_interval_s} ثانية) — السبب: {reason}"
            )
            return result

        self._last_flush_time = self._clock()
        self._stats["total_flush_attempts"] += 1
        self._stats["last_flush_at"] = time.time()
        self._stats["last_flush_reason"] = reason

        if self._flusher is None:
            result["error"] = (
                "لا يوجد مُنفّذ تفريغ حقيقي: مرّر cloud_sync_service بطريقة مناسبة "
                "(مثل sync_pending_changes) أو flush_callback"
            )
            result["duration_ms"] = int((time.perf_counter() - started) * 1000)
            self._stats["failed"] += 1
            self._stats["last_error"] = result["error"]
            # مُسجّل كتحذير: شرط إعدادي متوقع وليس عطلاً داخلياً (اتفاقية المشروع)
            self.logger.warning(result["error"])
            return result

        try:
            raw = self._flusher()
            result["flushed"] = self._normalize_flushed_count(raw)
            result["success"] = True
            self._stats["successful"] += 1
            self._stats["last_flushed_count"] = result["flushed"]
            self._stats["last_error"] = None
            self.logger.info(
                f"تفريغ طابور المزامنة ({reason}) عبر {self._flusher_source}: "
                f"{result['flushed']} عملية في {result['duration_ms']} مللي ثانية"
            )
        except Exception as exc:  # لا نرفع نحو الخارج — never raise outward
            result["error"] = f"فشل التفريغ: {exc}"
            self._stats["failed"] += 1
            self._stats["last_error"] = result["error"]
            # شرط مُلتقط ومُعالج — warning لا error (اتفاقية المشروع)
            self.logger.warning(result["error"])

        result["duration_ms"] = int((time.perf_counter() - started) * 1000)
        return result

    # ------------------------------------------------------------------ #
    # منطق الانتقال / Connectivity transition logic
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalize_state(state: Any) -> str:
        """تطبيع حالة الاتصال — Normalize a state value to 'online'/'offline'."""
        text = str(state if state is not None else "").strip().lower()
        if text in _ONLINE_ALIASES:
            return _STATE_ONLINE
        if text in _OFFLINE_ALIASES:
            return _STATE_OFFLINE
        return text

    def handle_state_change(self, new_state: Any) -> dict:
        """معالجة تغيّر حالة الاتصال — Handle a connectivity state change.

        يُطلق التفريغ فقط عند الانتقال offline → online. الاستدعاء الأول
        (بلا حالة سابقة) لا يفرّغ؛ والعودة إلى offline لا تفرّغ أيضًا.

        Args:
            new_state: الحالة الجديدة ("online"/"offline" أو bool أو مقاديلها).

        Returns:
            {flushed: bool, skipped: bool, reason: str, result: dict|None}
        """
        normalized = self._normalize_state(new_state)
        if normalized not in (_STATE_ONLINE, _STATE_OFFLINE):
            return {
                "flushed": False,
                "skipped": True,
                "reason": f"حالة غير معروفة: {new_state!r}",
                "result": None,
            }

        previous = self._last_state
        self._last_state = normalized

        if normalized == _STATE_ONLINE and previous == _STATE_OFFLINE:
            self.logger.info("استعادة الاتصال — بدء التفريغ التلقائي لطابور المزامنة")
            flush_result = self.flush_now(reason="reconnect")
            return {
                "flushed": True,
                "skipped": bool(flush_result.get("skipped")),
                "reason": "offline→online transition",
                "result": flush_result,
            }

        return {
            "flushed": False,
            "skipped": True,
            "reason": f"لا يوجد انتقال offline→online (السابقة={previous}, الجديدة={normalized})",
            "result": None,
        }

    # ------------------------------------------------------------------ #
    # الربط بمراقب الاتصال / Monitor attachment (defensive introspection)
    # ------------------------------------------------------------------ #
    def _on_monitor_state(self, is_connected: bool) -> None:
        """مقبض إشارة/استدعاء المراقب — Handler for monitor state callbacks/signals."""
        try:
            self.handle_state_change(bool(is_connected))
        except Exception as exc:  # pragma: no cover — حماية نهائية
            self.logger.warning(f"فشل معالجة تغيّر حالة الاتصال: {exc}")

    def attach_to_monitor(self, connectivity_monitor: Any) -> bool:
        """ربط الخدمة بمراقب الاتصال دفاعيًا — Defensively attach to a connectivity monitor.

        استراتيجيات الربط بالترتيب (المكتشف في الكود الفعلي):
        1. ``on_state_change(callback)`` — الخطاف البسيط المضاف إلى ConnectivityMonitor.
        2. إشارة Qt ``status_changed(bool)`` (تُطلق مع كل فحص).
        3. إشارة Qt ``connected()`` (تُطلق عند الانتقال فقط).

        Returns:
            True عند نجاح الربط، False إذا لم يُتعرف على واجهة المراقب (بدون أي استثناء).
        """
        if connectivity_monitor is None:
            self.logger.warning("attach_to_monitor: مراقب الاتصال غير موجود")
            return False

        # 1) خطاف الاستدعاءات البسيط / plain callback hook
        hook = getattr(connectivity_monitor, "on_state_change", None)
        if callable(hook):
            try:
                hook(self._on_monitor_state)
                self._monitor_attached = True
                self.logger.info("تم ربط خدمة التفريغ بمراقب الاتصال عبر on_state_change")
                return True
            except Exception as exc:
                self.logger.warning(f"فشل الربط عبر on_state_change: {exc}")

        # 2) إشارة Qt status_changed(bool) / Qt signal
        signal = getattr(connectivity_monitor, "status_changed", None)
        if signal is not None and hasattr(signal, "connect") and callable(signal.connect):
            try:
                signal.connect(self._on_monitor_state)
                self._monitor_attached = True
                self.logger.info("تم ربط خدمة التفريغ بإشارة status_changed(bool)")
                return True
            except Exception as exc:
                self.logger.warning(f"فشل الربط بإشارة status_changed: {exc}")

        # 3) إشارة Qt connected() — تُطلق عند الانتقال offline→online فقط
        connected_signal = getattr(connectivity_monitor, "connected", None)
        if connected_signal is not None and hasattr(connected_signal, "connect"):
            try:
                def _on_connected() -> None:
                    self._last_state = _STATE_ONLINE
                    self.flush_now(reason="reconnect")

                connected_signal.connect(_on_connected)
                self._monitor_attached = True
                self.logger.info("تم ربط خدمة التفريغ بإشارة connected()")
                return True
            except Exception as exc:
                self.logger.warning(f"فشل الربط بإشارة connected: {exc}")

        self.logger.warning(
            "لم يتم التعرف على واجهة مراقب الاتصال (لا on_state_change ولا إشارات Qt) — تخطي الربط"
        )
        return False

    @property
    def is_monitor_attached(self) -> bool:
        """هل تم الربط بمراقب ناجح؟ — Whether a monitor was attached successfully."""
        return self._monitor_attached

    # ------------------------------------------------------------------ #
    # الإحصائيات وعمق الطابور / Stats and queue depth
    # ------------------------------------------------------------------ #
    def get_stats(self) -> dict:
        """إحصائيات المحاولات — Flush attempt statistics (copy)."""
        stats = dict(self._stats)
        return stats

    def get_queue_depth(self) -> dict:
        """عمق طابور المزامنة من المخطط الحقيقي — Queue depth read from the real sync_queue schema.

        يكتشف أعمدة الجدول عبر PRAGMA ويتكيف مع الصيغتين الحقيقيتين:
        * صيغة api_client (عمود ``synced``): pending = synced=0.
        * صيغة local_database_manager (بلا عمود حالة): الصفوف كلها معلّقة.
        * صيغة عامة بعمود ``status``: pending/failed حسب القيم.

        Returns:
            {pending: int, failed: int, total: int, table_exists: bool}
        """
        base = {"pending": 0, "failed": 0, "total": 0, "table_exists": False}
        if self.db_manager is None:
            return base
        try:
            columns_rows = self.db_manager.fetch_all("PRAGMA table_info(sync_queue)")
            if not columns_rows:
                return base  # الجدول غير موجود — table absent
            base["table_exists"] = True
            column_names = [str(row.get("name")) for row in columns_rows if row.get("name")]

            total_row = self.db_manager.fetch_one("SELECT COUNT(*) AS c FROM sync_queue")
            total = int((total_row or {}).get("c") or 0)
            base["total"] = total

            if "status" in column_names:
                pending_row = self.db_manager.fetch_one(
                    "SELECT COUNT(*) AS c FROM sync_queue WHERE status = 'pending'"
                )
                failed_row = self.db_manager.fetch_one(
                    "SELECT COUNT(*) AS c FROM sync_queue WHERE status = 'failed'"
                )
                base["pending"] = int((pending_row or {}).get("c") or 0)
                base["failed"] = int((failed_row or {}).get("c") or 0)
            elif "synced" in column_names:
                # المخطط الحقيقي في api_client.py: synced BOOLEAN DEFAULT 0
                pending_row = self.db_manager.fetch_one(
                    "SELECT COUNT(*) AS c FROM sync_queue WHERE synced = 0 OR synced IS NULL"
                )
                base["pending"] = int((pending_row or {}).get("c") or 0)
                # لا يوجد مؤشر فشل في هذا المخطط — no failure marker in this schema
                base["failed"] = 0
            else:
                # صيغة local_database_manager: الصفوف كلها معلّقة حتى معالجتها
                base["pending"] = total
                base["failed"] = 0
            return base
        except Exception as exc:
            # قراءة عمق الطابور شرط مُلتقط ومُعالج (يُعاد result افتراضي) — warning
            self.logger.warning(f"فشل قراءة عمق طابور المزامنة: {exc}")
            base["error"] = str(exc)
            return base
