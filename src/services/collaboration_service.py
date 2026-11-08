#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التحرير التعاوني — Collaboration Service (GAP-5.3)

تنفيذ SRS docs/SRS_ARCHITECTURE.md (Area 5, سطور ~1370-1462):
- أقفال تحرير تشاؤمية (pessimistic record locks) على الجدول `record_locks`
- سجل تعارضات المزامنة على الجدول `sync_conflicts` (مخطط GAP-5.3)
- بث إشعارات التحرير/القفل الحية عبر WebSocketManager

Collaborative editing service per SRS Area 5:
- Pessimistic per-record edit locks (record_locks) with TTL expiry,
  idempotent re-acquire/refresh, heartbeat extension and admin force release.
- Sync conflict ledger (sync_conflicts — GAP-5.3 schema: table_name/record_id/
  local_data/remote_data/resolution/merged_data) with version divergence
  detection and final-data resolution output.
- Live edit / lock-change notifications through the real WebSocketManager
  (async `broadcast`) with an injectable sync `broadcast_callback` fallback.

ملاحظة معمارية (Architecture note — جدول التعارضات):
الجدول `sync_conflicts` موجود مسبقًا بمخطط آخر من ترحيل المزامنة السحابية
(`migrations/026_add_cloud_sync_support.sql`: sync_settings_id NOT NULL مع
مفتاح خارجي إلى cloud_sync_settings + قيد فريد ثلاثي + status/...). إعادة
استخدام هذا الجدول لصفوف GAP-5.3 مستحيلة سلميًا (FK/UNIQUE) وتعديله يخترق
ملكية ميزة المزامنة السحابية. لذلك يتخذ `_ensure_schema()` قرارًا واعيًا
بشكل الجدول: قاعدة بيانات جديدة بلا ترحيل 026 ⇒ ينشئ `sync_conflicts` بمخطط
SRS حرفيًا؛ وجود المخطط القديم ⇒ ينشئ جدولًا مخصصًا موازيًا
`collab_sync_conflicts` بنفس مخطط SRS ولا يلمس الجدول القديم إطلاقًا.
الجدول الفعلي مكشوف كـ `service.conflicts_table` للمستدعين.
(يُوصى بترحيل مستقبلي يوحّد الاسمين في جدول واحد للسجل الموحد.)

توقيت الخدمة (Clock): `clock` قابل للحقن (افتراضي time.time) لاختبار انتهاء
الصلاحية دون انتظار حقيقي. كل الأزمنة مخزّنة كنص ISO موحد العرض
("YYYY-MM-DD HH:MM:SS.ffffff") حتى تكون المقارنات المعجمية في SQL صحيحة.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.core.database_lock_handler import is_lock_error
from src.utils.logger import setup_logger

__all__ = [
    "CollaborationService",
    "ConflictResolutionError",
    "RESOLUTION_LOCAL_WINS",
    "RESOLUTION_REMOTE_WINS",
    "RESOLUTION_MERGED",
    "VALID_RESOLUTIONS",
    "MAX_LOCK_TTL",
]

# ── قيم الحلول المسموحة — Valid resolution values (SRS) ──────────────────────
RESOLUTION_LOCAL_WINS = "local_wins"
RESOLUTION_REMOTE_WINS = "remote_wins"
RESOLUTION_MERGED = "merged"
VALID_RESOLUTIONS = (RESOLUTION_LOCAL_WINS, RESOLUTION_REMOTE_WINS, RESOLUTION_MERGED)

# ── ثوابت الأقفال — Lock constants ───────────────────────────────────────────
DEFAULT_LOCK_TTL = 300          # 5 دقائق — default sliding TTL (seconds)
MAX_LOCK_TTL = 86400            # سقف عمر القفل بدون انتهاء صلاحية (24 ساعة)
_RETRY_ATTEMPTS = 3             # محاولات عند تعارض قفل قاعدة البيانات
_RETRY_DELAY = 0.05             # 50ms بين المحاولات (اصطلاح database_lock_handler)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

T = TypeVar("T")


class ConflictResolutionError(Exception):
    """خطأ في حل التعارض — Conflict resolution error (bilingual)."""

    def __init__(self, message: str):
        super().__init__(message)


class CollaborationService:
    """خدمة التحرير التعاوني — Collaborative editing service (GAP-5.3).

    Args:
        db_manager: مدير قاعدة البيانات (DatabaseManager أو متوافق).
        websocket_manager: مدير WebSocket الحقيقي (اختياري) — يستخدم
            `broadcast(message: Dict)` غير المتزامن مع حماية كاملة من الفشل.
        logger: مسجل مخصص (اختياري).
        clock: دالة زمن قابلة للحقن (افتراضي time.time) لاختبارات الانتهاء.
        broadcast_callback: بديل متزامن للبث إذا كانت واجهة المدير غير مناسبة،
            توقيعه `callback(payload: dict) -> int | None`.
    """

    def __init__(
        self,
        db_manager,
        websocket_manager: Any | None = None,
        logger=None,
        clock: Callable[[], float] | None = None,
        broadcast_callback: Callable[[Dict[str, Any]], Any] | None = None,
    ):
        self.db_manager = db_manager
        self.db = db_manager  # اسم مختصر متاح للراحة — short alias
        self.conflicts_table: str = "sync_conflicts"  # يُحسم في _ensure_schema
        # حماية مؤشر الاتصال المشترك — shared-connection cursor guard:
        # Python sqlite3 cursors ليست آمنة خيطيًا؛ عند مشاركة اتصال واحد بين
        # خيوط (pool disabled) يجب تسلسل الأقسام الحرجة على مستوى التطبيق.
        # ذرية عبر الاتصالات/العمليات تبقى بضمانة BEGIN IMMEDIATE.
        self._db_mutex = threading.RLock()
        self._websocket_manager = websocket_manager
        self._broadcast_callback = broadcast_callback
        self.logger = logger or setup_logger(__name__)
        self._clock: Callable[[], float] = clock or time.time
        self._ensure_schema()

    # ────────────────────────── الزمن — Time helpers ──────────────────────────

    def _now(self) -> float:
        """الزمن الحالي كعدد عائم — Current time as float seconds."""
        return float(self._clock())

    def _iso(self, ts: float) -> str:
        """تنسيق موحد قابل للمقارنة المعجمية في SQLite.

        Uniform, lexicographically-sortable ISO timestamp for TEXT columns.
        """
        return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="microseconds")

    # ────────────────────────── المخطط — Schema ───────────────────────────────

    def _ensure_schema(self) -> None:
        """إنشاء جداول GAP-5.3 بشكل أيديميُّ (SRS DDL مُكيَّف لـ SQLite).

        Idempotent creation of `record_locks` + `sync_conflicts` and the
        expiry index, exactly as specified in the SRS (adapted to SQLite).
        """
        self.db.execute_non_query("""
            CREATE TABLE IF NOT EXISTS record_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                locked_by INTEGER NOT NULL,
                locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                session_id TEXT,
                UNIQUE(table_name, record_id)
            )
        """)
        self.db.execute_non_query(
            "CREATE INDEX IF NOT EXISTS idx_record_locks_expiry ON record_locks(expires_at)"
        )
        self._resolve_conflicts_table()

    _SRS_SYNC_CONFLICTS_DDL = """
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            local_data TEXT NOT NULL,     -- JSON
            remote_data TEXT NOT NULL,    -- JSON
            resolution TEXT,              -- 'local_wins','remote_wins','merged'
            resolved_by INTEGER,
            resolved_at TEXT,
            merged_data TEXT,             -- JSON
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """

    def _resolve_conflicts_table(self) -> None:
        """حسم جدول التعارضات حسب شكل القاعدة — Shape-aware conflicts table.

        - قاعدة جديدة بلا جدول ⇒ إنشاء `sync_conflicts` بمخطط SRS حرفيًا.
        - جدول موجود بمخطط GAP-5.3 (أُنشئ سابقًا بواسطتنا) ⇒ إعادة استخدامه.
        - جدول موجود بمخطط ترحيل 026 القديم (sync_settings_id FK + UNIQUE
          ثلاثي) ⇒ إنشاء `collab_sync_conflicts` موازٍ بنفس مخطط SRS دون
          أي تعديل على جدول ميزة المزامنة السحابية (عزل ملكية كامل).
        """
        try:
            rows = self.db.fetch_all("PRAGMA table_info(sync_conflicts)")
        except Exception as exc:  # noqa: BLE001 — دفاعي
            self.logger.warning(f"تعذر قراءة أعمدة sync_conflicts: {exc}")
            rows = []
        existing = {r["name"] for r in rows or [] if isinstance(r, dict)}

        if not existing:
            # قاعدة جديدة — مخطط SRS حرفي على sync_conflicts
            self.db.execute_non_query(self._SRS_SYNC_CONFLICTS_DDL.format(table="sync_conflicts"))
            self.conflicts_table = "sync_conflicts"
        elif "sync_settings_id" in existing:
            # مخطط ترحيل 026 القديم — جدول موازٍ مخصص لعزل تام بلا ALTER
            self.db.execute_non_query(self._SRS_SYNC_CONFLICTS_DDL.format(table="collab_sync_conflicts"))
            self.conflicts_table = "collab_sync_conflicts"
        else:
            # مخطط GAP-5.3 موجود مسبقًا (أو قريب منه) — إعادة استخدام
            self.conflicts_table = "sync_conflicts"
        self.logger.info(
            f"جدول تعارضات GAP-5.3: {self.conflicts_table} — conflicts table resolved"
        )

    def _conflict_insert(
        self,
        table_name: str,
        record_id: int,
        local_json: str,
        remote_json: str,
    ) -> Optional[int]:
        """إدراج تعارض في جدول GAP-5.3 المحسوم — Insert into resolved table."""
        query = (
            f"INSERT INTO {self.conflicts_table} "
            "(table_name, record_id, local_data, remote_data) VALUES (?, ?, ?, ?)"
        )
        return self.db.execute_insert(query, (table_name, record_id, local_json, remote_json))

    # ─────────────────── إعادة المحاولة — Retry helper ────────────────────────

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """هل الخطأ قابل لإعادة المحاولة؟ — Retryable DB-lock/txn race?

        يغطي اصطلاحات database_lock_handler + سباق المعاملات على الاتصال
        المشترك ("cannot start a transaction within a transaction").
        """
        if is_lock_error(exc):
            return True
        msg = str(exc).lower()
        return "cannot start a transaction within a transaction" in msg

    def _run_with_retry(self, op_name: str, fn: Callable[[], T]) -> T:
        """تنفيذ عملية قاعدة بيانات مع إعادة محاولة محدودة (3 × 50ms).

        Run a DB operation with bounded retry on lock/txn races, mirroring
        the project's database_lock_handler conventions (WARNING logs only).
        """
        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001 — مُصنَّف أدناه
                if self._is_retryable(exc) and attempt < _RETRY_ATTEMPTS:
                    last_exc = exc
                    self.logger.warning(
                        f"تعارض قفل قاعدة البيانات في {op_name} "
                        f"(المحاولة {attempt}/{_RETRY_ATTEMPTS}) — إعادة المحاولة بعد "
                        f"{_RETRY_DELAY * 1000:.0f}ms: {exc}"
                    )
                    time.sleep(_RETRY_DELAY)
                    continue
                raise
        if last_exc is not None:  # دفاعي — لا يُفترض الوصول هنا
            raise last_exc
        raise RuntimeError(f"{op_name} failed without a specific error")

    # ─────────────────── JSON helpers ─────────────────────────────────────────

    @staticmethod
    def _json_dumps(data: Any) -> str:
        """تسلسل JSON آمن (Decimal → str) — JSON-safe dump (money=Decimal)."""
        return json.dumps(data if data is not None else {}, ensure_ascii=False, default=str)

    @staticmethod
    def _json_loads(raw: Any) -> Any:
        """فك تسلسل JSON مع حماية — Defensive JSON parse."""
        if raw is None:
            return None
        if isinstance(raw, (dict, list)):
            return raw
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _jsonable(value: Any) -> Any:
        """تحويل قيمة الحقل لشيء قابل للبث — Make payload value broadcast-safe."""
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime,)):
            return value.isoformat()
        return value

    # ═══════════════════════ الأقفال — Record locks ═══════════════════════════

    def acquire_lock(
        self,
        table_name: str,
        record_id: int,
        user_id: int,
        ttl: int = DEFAULT_LOCK_TTL,
        session_id: str | None = None,
    ) -> Dict[str, Any]:
        """الحصول على قفل تحرير على سجل — Acquire a pessimistic edit lock.

        ذرّية داخل BEGIN IMMEDIATE + تسلسل بمزامنة الخدمة: تنظيف المنتهي،
        ثم إعادة التفعيل الانسيابي (sliding refresh) لنفس المستخدم، أو الإدراج،
        أو الرفض مع معلومات مالك القفل الحالي. إعادة الحصول من نفس المستخدم
        آمنة تكراريًا.

        Returns:
            {"acquired": bool, "locked_by": int|None, "expires_at": str|None,
             ...معلومات المالك عند الرفض}
        """
        ttl = max(1, min(int(ttl), MAX_LOCK_TTL))

        def _attempt() -> Dict[str, Any]:
            with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
                now = self._now()
                now_iso = self._iso(now)
                expires_iso = self._iso(now + ttl)
                null_guard_cutoff = self._iso(now - MAX_LOCK_TTL)

                with self.db_manager.transaction():
                    # 1) تنظيف انتهازي رخيص للمنتهي عالميًا (مفهرس على expires_at)
                    self.db_manager.execute_non_query(
                        "DELETE FROM record_locks WHERE expires_at IS NOT NULL AND expires_at < ?",
                        (now_iso,),
                    )
                    # 2) حارس الأقفال بدون انتهاء صلاحية القديمة جدًا
                    self.db_manager.execute_non_query(
                        "DELETE FROM record_locks WHERE expires_at IS NULL AND locked_at < ?",
                        (null_guard_cutoff,),
                    )
                    # 3) فحص القفل الحالي لهذا السجل تحديدًا
                    row = self.db_manager.fetch_one(
                        "SELECT * FROM record_locks WHERE table_name = ? AND record_id = ?",
                        (table_name, record_id),
                    )
                    if row is None:
                        self.db_manager.execute_insert(
                            """
                            INSERT INTO record_locks
                                (table_name, record_id, locked_by, locked_at, expires_at, session_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (table_name, record_id, user_id, now_iso, expires_iso, session_id),
                        )
                        return {
                            "acquired": True,
                            "locked_by": user_id,
                            "expires_at": expires_iso,
                            "session_id": session_id,
                        }
                    if int(row.get("locked_by") or 0) == int(user_id):
                        # إعادة الحصول = تجديد انسيابي (idempotent re-acquire)
                        self.db_manager.execute_non_query(
                            """
                            UPDATE record_locks
                               SET expires_at = ?, locked_at = ?,
                                   session_id = COALESCE(?, session_id)
                             WHERE table_name = ? AND record_id = ?
                            """,
                            (expires_iso, now_iso, session_id, table_name, record_id),
                        )
                        return {
                            "acquired": True,
                            "locked_by": user_id,
                            "expires_at": expires_iso,
                            "refreshed": True,
                        }
                    # قفل مستخدم آخر — رفض مع معلومات "من/متى"
                    return {
                        "acquired": False,
                        "locked_by": row.get("locked_by"),
                        "expires_at": row.get("expires_at"),
                        "locked_at": row.get("locked_at"),
                        "session_id": row.get("session_id"),
                    }

        return self._run_with_retry("acquire_lock", _attempt)

    def release_lock(
        self,
        table_name: str,
        record_id: int,
        user_id: int,
        force: bool = False,
    ) -> bool:
        """تحرير قفل — Release lock (owner only; `force=True` for admin override).

        صارم: المالك فقط يحرر قفله. `force=True` مخصص لتجاوز المشرف ويُترك
        للطبقة العليا للتحقق من صلاحيات المشرف قبل تمريره.
        """
        def _attempt() -> bool:
            with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
                if force:
                    rowcount = self.db_manager.execute_non_query(
                        "DELETE FROM record_locks WHERE table_name = ? AND record_id = ?",
                        (table_name, record_id),
                    )
                else:
                    rowcount = self.db_manager.execute_non_query(
                        "DELETE FROM record_locks WHERE table_name = ? AND record_id = ? AND locked_by = ?",
                        (table_name, record_id, user_id),
                    )
                return bool(rowcount and int(rowcount) > 0)

        return self._run_with_retry("release_lock", _attempt)

    def get_lock(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """قراءة القفل الحالي بعد تطهير المنتهي — Current lock (purges expired first)."""
        with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
            now = self._now()
            now_iso = self._iso(now)
            null_guard_cutoff = self._iso(now - MAX_LOCK_TTL)
            self.db_manager.execute_non_query(
                """
                DELETE FROM record_locks
                 WHERE table_name = ? AND record_id = ?
                   AND ((expires_at IS NOT NULL AND expires_at < ?)
                        OR (expires_at IS NULL AND locked_at < ?))
                """,
                (table_name, record_id, now_iso, null_guard_cutoff),
            )
            row = self.db_manager.fetch_one(
                "SELECT * FROM record_locks WHERE table_name = ? AND record_id = ?",
                (table_name, record_id),
            )
        return dict(row) if row else None

    def heartbeat_lock(
        self,
        table_name: str,
        record_id: int,
        user_id: int,
        ttl: int = DEFAULT_LOCK_TTL,
    ) -> bool:
        """تمديد صلاحية القفل من قبل مالكه — Sliding-heartbeat extension.

        ينجح فقط إذا كان المستخدم هو المالك والقفل لم ينتهِ بعد.
        """
        ttl = max(1, min(int(ttl), MAX_LOCK_TTL))

        def _attempt() -> bool:
            with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
                now = self._now()
                now_iso = self._iso(now)
                new_expiry = self._iso(now + ttl)
                rowcount = self.db_manager.execute_non_query(
                    """
                    UPDATE record_locks
                       SET expires_at = ?, locked_at = ?
                     WHERE table_name = ? AND record_id = ? AND locked_by = ?
                       AND (expires_at IS NULL OR expires_at >= ?)
                    """,
                    (new_expiry, now_iso, table_name, record_id, user_id, now_iso),
                )
                return bool(rowcount and int(rowcount) > 0)

        return self._run_with_retry("heartbeat_lock", _attempt)

    def purge_expired_locks(self) -> int:
        """تنظيف عالمي للأقفال المنتهية — Global sweep; returns purged count."""
        with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
            now = self._now()
            now_iso = self._iso(now)
            null_guard_cutoff = self._iso(now - MAX_LOCK_TTL)
            rowcount = self.db_manager.execute_non_query(
                """
                DELETE FROM record_locks
                 WHERE (expires_at IS NOT NULL AND expires_at < ?)
                    OR (expires_at IS NULL AND locked_at < ?)
                """,
                (now_iso, null_guard_cutoff),
            )
        purged = int(rowcount or 0)
        if purged:
            self.logger.info(f"تم تطهير {purged} قفل منتهي — Purged {purged} expired record locks")
        return purged

    # ═══════════ الإشعارات الحية — Live WebSocket notifications ═══════════════

    def notify_edit(
        self,
        table_name: str,
        record_id: int,
        field: str,
        value: Any,
        user_id: int,
        broadcast_callback: Callable[[Dict[str, Any]], Any] | None = None,
    ) -> Dict[str, Any]:
        """بث تحرير حقل عبر WebSocket — Broadcast a live field edit.

        الحمولة (payload): {"type": "record_edit", "table", "record_id",
        "field", "value", "user_id", "ts"}. البث محمي بالكامل: أي فشل يُسجَّل
        كـ WARNING ولا يُرفع أبدًا حتى لا يُعطّل مسار الحفظ الأساسي.
        """
        payload: Dict[str, Any] = {
            "type": "record_edit",
            "table": table_name,
            "record_id": record_id,
            "field": field,
            "value": self._jsonable(value),
            "user_id": user_id,
            "ts": self._iso(self._now()),
        }
        callback = broadcast_callback if broadcast_callback is not None else self._broadcast_callback
        return self._broadcast_payload(payload, callback, context=f"{table_name}#{record_id}.{field}")

    def notify_lock_change(
        self,
        table_name: str,
        record_id: int,
        action: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """بث تغيّر حالة القفل — Broadcast lock_change (acquired/released/denied)."""
        payload: Dict[str, Any] = {
            "type": "lock_change",
            "action": str(action),
            "table": table_name,
            "record_id": record_id,
            "user_id": user_id,
            "ts": self._iso(self._now()),
        }
        return self._broadcast_payload(payload, self._broadcast_callback, context=f"lock:{action}")

    def _broadcast_payload(
        self,
        payload: Dict[str, Any],
        callback: Callable[[Dict[str, Any]], Any] | None,
        context: str = "",
    ) -> Dict[str, Any]:
        """بث محمي — Guarded broadcast (never raises; WARNING on failure).

        الأولوية: callback متزامن صريح ← مدير WebSocket الحقيقي (`broadcast`
        غير المتزامن مع دعم حلقة أحداث جارية أو جديدة) ← لا شيء.
        """
        try:
            # 1) بديل متزامن صريح (fallback broadcast_callback)
            if callback is not None:
                result = callback(payload)
                recipients: Optional[int] = None
                if isinstance(result, (int, float)) and not isinstance(result, bool):
                    recipients = int(result)
                return {"notified": True, "recipients": recipients}

            manager = self._websocket_manager
            if manager is None:
                return {"notified": False, "recipients": None}

            recipients = self._count_recipients(manager)
            broadcast = getattr(manager, "broadcast", None)
            if broadcast is None:
                self.logger.warning(
                    f"مدير WebSocket بلا دالة broadcast — تخطي البث ({context})"
                )
                return {"notified": False, "recipients": recipients}

            self._invoke_broadcast(broadcast, payload)
            self.logger.info(
                f"تم بث إشعار تعاوني ({payload.get('type')}) لـ {context} — "
                f"recipients={recipients}"
            )
            return {"notified": True, "recipients": recipients}
        except Exception as exc:  # noqa: BLE001 — البث لا يُعطّل مسار الحفظ
            self.logger.warning(f"فشل بث الإشعار التعاوني ({context}) — broadcast failed: {exc}")
            return {"notified": False, "recipients": None}

    @staticmethod
    def _count_recipients(manager: Any) -> Optional[int]:
        """عدّ المستلمين المحتملين — Count connections if introspectable."""
        try:
            conns = getattr(manager, "active_connections", None)
            if isinstance(conns, dict):
                total = 0
                for room in conns.values():
                    try:
                        total += len(room)
                    except TypeError:
                        continue
                return total
        except Exception:  # noqa: BLE001 — العد دفاعي فقط
            pass
        return None

    def _invoke_broadcast(self, broadcast: Callable, payload: Dict[str, Any]) -> None:
        """استدعاء دالة البث متزامنة أو غير متزامنة — Sync/async tolerant call.

        داخل حلقة جارية: fire-and-forget عبر create_task؛ خارجه: حلقة مؤقتة.
        """
        coro = None
        if asyncio.iscoroutinefunction(broadcast):
            coro = broadcast(payload)
        else:
            result = broadcast(payload)
            if asyncio.iscoroutine(result):
                coro = result
            else:
                return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)  # fire-and-forget داخل السياق غير المتزامن
            return
        except RuntimeError:
            pass
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    # ═══════════ التعارضات — Conflict detection & resolution ══════════════════

    def detect_conflict(
        self,
        table_name: str,
        record_id: int,
        local_version: int,
        remote_version: int,
        local_data: Dict[str, Any] | None = None,
        remote_data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """كشف تعارض الإصدارات وتسجيله — Detect & log a version conflict.

        إذا تساوى الإصداران فلا تعارض. عند الاختلاف تُسجَّل سطر في
        `sync_conflicts` (مخطط GAP-5.3) وتُعاد قائمة الحقول المتباعدة
        (حقول بقيم مختلفة في الطرفين + حقول موجودة في طرف واحد فقط).
        """
        try:
            lv = int(local_version)
            rv = int(remote_version)
        except (TypeError, ValueError):
            lv = rv = 0  # إصدارات غير صالحة → تُعامل كمتعادلة (لا تعارض خيالي)

        if lv == rv:
            return {
                "conflict": False,
                "conflict_id": None,
                "local_version": lv,
                "remote_version": rv,
                "diverged_fields": [],
            }

        diverged_fields = self._diff_fields(local_data, remote_data)
        with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
            conflict_id = self._conflict_insert(
                table_name,
                record_id,
                self._json_dumps(local_data),
                self._json_dumps(remote_data),
            )
        self.logger.info(
            f"تعارض مزامنة على {table_name}#{record_id} "
            f"(local={lv} vs remote={rv}) — conflict_id={conflict_id}"
        )
        return {
            "conflict": True,
            "conflict_id": int(conflict_id) if conflict_id is not None else None,
            "local_version": lv,
            "remote_version": rv,
            "diverged_fields": diverged_fields,
        }

    @staticmethod
    def _diff_fields(
        local_data: Dict[str, Any] | None,
        remote_data: Dict[str, Any] | None,
    ) -> List[str]:
        """مقارنة الحقول: مختلف القيمة أو موجود بطرف واحد — Field-wise diff."""
        if local_data is None or remote_data is None:
            return []
        if not isinstance(local_data, dict) or not isinstance(remote_data, dict):
            return []
        diverged: List[str] = []
        for key in sorted(set(local_data) | set(remote_data)):
            if key not in local_data or key not in remote_data:
                diverged.append(key)
                continue
            if not CollaborationService._values_equal(local_data[key], remote_data[key]):
                diverged.append(key)
        return diverged

    @staticmethod
    def _values_equal(a: Any, b: Any) -> bool:
        """مقارنة متسامحة (Decimal/float) — Tolerant value equality."""
        try:
            if a == b:
                return True
        except Exception:  # noqa: BLE001 — أنواع غريبة
            return str(a) == str(b)
        return str(a) == str(b)

    def resolve_conflict(
        self,
        conflict_id: int,
        resolution: str,
        merged_data: Dict[str, Any] | None = None,
        resolved_by: int | None = None,
    ) -> Dict[str, Any]:
        """حل تعارض مسجل — Resolve a recorded conflict.

        resolution ∈ {'local_wins','remote_wins','merged'}؛ الخيار 'merged'
        يتطلب merged_data وإلا يُرفع ConflictResolutionError. يُحدَّث السجل
        (resolution/resolved_by/resolved_at/merged_data) ويُعاد سجل البيانات
        النهائي حسب الحل (local_data / remote_data / merged_data).
        """
        res = str(resolution or "").strip().lower()
        if res not in VALID_RESOLUTIONS:
            raise ConflictResolutionError(
                f"حل غير صالح: '{resolution}' — المسموح: {', '.join(VALID_RESOLUTIONS)} / "
                f"Invalid resolution '{resolution}'; expected one of {list(VALID_RESOLUTIONS)}"
            )
        if res == RESOLUTION_MERGED and merged_data is None:
            raise ConflictResolutionError(
                "حل 'merged' يتطلب merged_data — 'merged' resolution requires merged_data"
            )

        with self._db_mutex:  # قراءة+تحديث ذرّية — atomic read-modify-write
            row = self.db_manager.fetch_one(
                f"SELECT * FROM {self.conflicts_table} WHERE id = ?", (int(conflict_id),)
            )
            if not row:
                raise ConflictResolutionError(
                    f"التعارض #{conflict_id} غير موجود — Conflict #{conflict_id} not found"
                )

            if res == RESOLUTION_LOCAL_WINS:
                final_data = self._json_loads(row.get("local_data")) or {}
            elif res == RESOLUTION_REMOTE_WINS:
                final_data = self._json_loads(row.get("remote_data")) or {}
            else:
                final_data = dict(merged_data or {})

            now_iso = self._iso(self._now())
            merged_col = self._json_dumps(merged_data) if res == RESOLUTION_MERGED else None
            self.db_manager.execute_non_query(
                f"""
                UPDATE {self.conflicts_table}
                   SET resolution = ?, resolved_by = ?, resolved_at = ?, merged_data = ?
                 WHERE id = ?
                """,
                (res, resolved_by, now_iso, merged_col, int(conflict_id)),
            )
        self.logger.info(
            f"تم حل التعارض #{conflict_id} ({res}) بواسطة {resolved_by} — "
            f"Conflict #{conflict_id} resolved ({res})"
        )
        return final_data

    def list_unresolved_conflicts(
        self,
        table_name: str | None = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """سرد التعارضات غير المحلولة — List unresolved conflicts (JSON parsed)."""
        limit = max(1, int(limit))
        table = self.conflicts_table
        with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
            if table_name:
                rows = self.db_manager.fetch_all(
                    f"""
                    SELECT * FROM {table}
                     WHERE table_name = ? AND resolution IS NULL
                     ORDER BY created_at DESC, id DESC
                     LIMIT ?
                    """,
                    (table_name, limit),
                )
            else:
                rows = self.db_manager.fetch_all(
                    f"""
                    SELECT * FROM {table}
                     WHERE resolution IS NULL
                     ORDER BY created_at DESC, id DESC
                     LIMIT ?
                    """,
                    (limit,),
                )
        return [self._parse_conflict_row(r) for r in rows or []]

    def get_conflict(self, conflict_id: int) -> Optional[Dict[str, Any]]:
        """قراءة تعارض بفكّ JSON — Get one conflict with parsed JSON fields."""
        with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
            row = self.db_manager.fetch_one(
                f"SELECT * FROM {self.conflicts_table} WHERE id = ?", (int(conflict_id),)
            )
        if not row:
            return None
        return self._parse_conflict_row(row)

    def _parse_conflict_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """فك حقول JSON في صف التعارض — Parse JSON columns of a conflict row."""
        parsed = dict(row)
        parsed["local_data"] = self._json_loads(parsed.get("local_data"))
        parsed["remote_data"] = self._json_loads(parsed.get("remote_data"))
        parsed["merged_data"] = self._json_loads(parsed.get("merged_data"))
        return parsed

    # ═══════════ إصدار السجل — Record version awareness ═══════════════════════

    def get_record_version(
        self,
        table_name: str,
        record_id: int,
        version_column: str = "updated_at",
    ) -> Optional[int]:
        """قراءة مؤشر إصدار السجل — Read the record's version marker as int.

        الاستراتيجية:
        1. عمود رقمي باسم `version` إن وُجد (عبر PRAGMA) → قيمته مباشرة.
        2. وإلا عمود `version_column` (افتراضي updated_at) → بصمة رقمية:
           int(sha256(str(value))[:12], 16) — تتغير مع كل تحديث للسجل.
        جدول مجهول أو سجل مفقود → None (دفاعي، يستخدمه المستدعون لتغذية
        detect_conflict).
        """
        table = self._safe_identifier(table_name)
        column = self._safe_identifier(version_column)
        if not table or not column or record_id is None:
            return None

        try:
            with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
                cols = self.db_manager.fetch_all(f"PRAGMA table_info({table})")
        except Exception as exc:  # noqa: BLE001 — جدول تالف/غير متاح
            self.logger.warning(f"تعذر قراءة أعمدة الجدول {table}: {exc}")
            return None
        if not cols:
            return None  # جدول مجهول
        col_names = {c.get("name") for c in cols if isinstance(c, dict)}

        with self._db_mutex:  # تسلسل مؤشر الاتصال المشترك — serialize shared conn
            if "version" in col_names:
                row = self.db_manager.fetch_one(
                    f"SELECT version FROM {table} WHERE id = ?", (record_id,)
                )
                if row is None:
                    return None
                if row.get("version") is not None:
                    try:
                        return int(row["version"])
                    except (TypeError, ValueError):
                        pass  # عمود version غير رقمي → تابع للبديل

            if column in col_names:
                row = self.db_manager.fetch_one(
                    f"SELECT {column} AS version_marker FROM {table} WHERE id = ?",
                    (record_id,),
                )
                if row is None or row.get("version_marker") is None:
                    return None
                marker = str(row["version_marker"])
                return int(hashlib.sha256(marker.encode("utf-8")).hexdigest()[:12], 16)

        return None

    @staticmethod
    def _safe_identifier(name: Any) -> Optional[str]:
        """تحقق من صلاحية المعرّف SQL — Validate SQL identifier (anti-injection)."""
        if not isinstance(name, str) or not _IDENTIFIER_RE.fullmatch(name):
            return None
        return name
