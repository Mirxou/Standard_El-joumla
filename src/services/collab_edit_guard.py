#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حارس التحرير التعاوني — Collaborative Edit Guard (GAP-5.3)

أداة رقيقة قابلة لإعادة الاستخدام تغلّف CollaborationService بأقفال تشاؤمية:
سطر واحد يحمي أي تعديل سجل، ويضمن تحرير القفل دائمًا حتى عند حدوث استثناء
داخل كتلة `with` (منع تسريب الأقفال المعلّقة).

A thin reusable guard around CollaborationService locking. `guarded_edit()`
acquires the record lock on entry (raising RecordLockedError with who/when
details if another user holds it) and ALWAYS releases on exit — including on
exception — so a crashed editor can never leak a stale lock. Live
lock-change notifications (acquired/denied/released) are emitted through the
service's guarded WebSocket broadcast when configured.

Usage / الاستخدام:
    guard = CollabEditGuard(collab_service)
    with guard.guarded_edit("products", product_id, user_id=7, ttl=300) as g:
        # g.lock_info["acquired"] is True — القفل محتجز من قبلنا هنا
        ...apply the edit...
    # الخروج (حتى مع استثناء) حرّر القفل — lock released on any exit path
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

__all__ = ["CollabEditGuard", "RecordLockedError"]


class RecordLockedError(Exception):
    """السجل مقفل حاليًا من مستخدم آخر — Record is locked by another user.

    يحمل تفاصيل "من قفل ومتى وحتى متى" لتعرضها الواجهة / carries lock
    ownership details (locked_by/locked_at/expires_at) for UI display.
    """

    def __init__(
        self,
        table_name: str,
        record_id: int,
        locked_by: int | None = None,
        locked_at: str | None = None,
        expires_at: str | None = None,
        message: str | None = None,
    ):
        self.table_name = table_name
        self.record_id = record_id
        self.locked_by = locked_by
        self.locked_at = locked_at
        self.expires_at = expires_at
        if message is None:
            owner = f"#{locked_by}" if locked_by is not None else "مستخدم آخر / another user"
            message = (
                f"السجل '{table_name}#{record_id}' مقفل حاليًا بواسطة المستخدم {owner}"
                f" (منذ {locked_at}، ينتهي: {expires_at}) — "
                f"Record '{table_name}#{record_id}' is currently locked by user {owner}; "
                f"try again after the lock expires."
            )
        super().__init__(message)


class CollabEditGuard:
    """حارس تعديل السجل — One-liner pessimistic edit protection.

    Args:
        collaboration_service: خدمة التحرير التعاوني الجاهزة.
        logger: مسجل اختياري (افتراضي: مسجل الخدمة نفسها).
    """

    def __init__(self, collaboration_service, logger=None):
        self._service = collaboration_service
        self.logger = logger or getattr(collaboration_service, "logger", None)
        self.lock_info: Optional[Dict[str, Any]] = None

    @contextmanager
    def guarded_edit(
        self,
        table_name: str,
        record_id: int,
        user_id: int,
        ttl: int = 300,
        session_id: str | None = None,
        notify: bool = True,
    ) -> Iterator["CollabEditGuard"]:
        """سياق تعديل محمي بقفل — Lock-protected edit context.

        - عند الدخول: acquire_lock؛ الفشل ⇒ notify_lock_change("denied") ثم
          RecordLockedError ثنائي اللغة يحمل من/متى.
        - عند النجاح: notify_lock_change("acquired") ثم yield الذات مع
          `.lock_info`.
        - عند الخروج (طبيعي أو استثناء): release_lock دائمًا — نحرّر حتى عند
          الاستثناء عمدًا (أبسط وأمن من ترك قفل يتيم عند انهيار المحرر؛
          المسار البديل TTL/انتهاء الصلاحية يعالج الأعطال القاتلة فقط).
        """
        result = self._service.acquire_lock(
            table_name, record_id, user_id, ttl=ttl, session_id=session_id
        )
        if not result.get("acquired"):
            if notify:
                self._safe_notify(table_name, record_id, "denied", user_id)
            raise RecordLockedError(
                table_name,
                record_id,
                locked_by=result.get("locked_by"),
                locked_at=result.get("locked_at"),
                expires_at=result.get("expires_at"),
            )

        self.lock_info = result
        if notify:
            self._safe_notify(table_name, record_id, "acquired", user_id)

        try:
            yield self
        finally:
            # تحرير دائم حتى عند الاستثناء — always release (even on exception)
            try:
                released = self._service.release_lock(table_name, record_id, user_id)
                if released and notify:
                    self._safe_notify(table_name, record_id, "released", user_id)
            except Exception as exc:  # noqa: BLE001 — لا نسمح لفشل التحرير بطمس الاستثناء الأصلي
                if self.logger is not None:
                    self.logger.warning(
                        f"تعذر تحرير قفل {table_name}#{record_id} عند الخروج — "
                        f"release on exit failed (TTL سيتكفل به): {exc}"
                    )
            self.lock_info = None

    def _safe_notify(self, table_name: str, record_id: int, action: str, user_id: int) -> None:
        """إشعار محمي بتغيّر القفل — notify_lock_change, never raises."""
        try:
            self._service.notify_lock_change(table_name, record_id, action, user_id)
        except Exception as exc:  # noqa: BLE001 — الإشعار لا يُعطّل مسار القفل
            if self.logger is not None:
                self.logger.warning(
                    f"تعذر إشعار تغيّر القفل ({action}) على {table_name}#{record_id}: {exc}"
                )
