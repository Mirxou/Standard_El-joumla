#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات التحرير التعاوني (GAP-5.3) — قاعدة بيانات SQLite حقيقية مؤقتة:

- المخطط: record_locks + sync_conflicts + فهرس الانتهاء (أيديميُّ)
- الأقفال التشاؤمية: acquire/release/heartbeat/purge + سباق التزامن
- الإشعارات الحية: notify_edit / notify_lock_change عبر WebSocketManager
- التعارضات: detect/resolve/list/get + get_record_version
- الحارس: CollabEditGuard + RecordLockedError

Collaborative editing tests (GAP-5.3) on a real temp SQLite database.
"""

import itertools
import os
import sys
import tempfile
import threading
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database_manager import DatabaseManager
from src.models.product import Product, ProductManager
from src.services.collab_edit_guard import CollabEditGuard, RecordLockedError
from src.services.collaboration_service import (
    MAX_LOCK_TTL,
    CollaborationService,
    ConflictResolutionError,
)

CLOCK_BASE = 1_700_000_000.0  # 2023-11-14 — زمن ثابت قابل للتقديم


class FakeClock:
    """ساعة قابلة للحقن لاختبار انتهاء الصلاحية — Injectable fake clock."""

    def __init__(self, start: float = CLOCK_BASE):
        self.t = float(start)

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += float(seconds)


def _iso(ts: float) -> str:
    """نفس تنسيق الخدمة — Same uniform ISO format as the service."""
    return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="microseconds")


class StubWSManager:
    """مدير WebSocket وهمي يكشف broadcast غير المتزامن (كما في الحقيقي)."""

    def __init__(self, fail: bool = False):
        self.sent: list = []
        self.fail = fail
        self.active_connections = {
            "default": {object(), object()},
            "room_b": {object()},
        }

    async def broadcast(self, message: dict) -> None:
        if self.fail:
            raise RuntimeError("broadcast exploded")
        self.sent.append(dict(message))


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


@pytest.fixture(scope="module")
def rid_factory():
    """معرّفات سجلات فريدة عبر كل الاختبارات — Module-wide unique record ids.

    قاعدة البيانات على مستوى الوحدة، والأقفال تبقى بين الاختبارات، لذلك يجب
    ألا يتكرر أي معرّف سجل بين اختبارين (وإلا تتصادم الأقفال المتروكة).
    """
    counter = itertools.count(500_000)
    return lambda: next(counter)


@pytest.fixture()
def svc(db):
    """خدمة تعاون جديدة بساعة ثابتة لكل اختبار — Fresh service per test."""
    return CollaborationService(db, clock=FakeClock(CLOCK_BASE))


# ═══════════════════════════ المخطط — Schema ════════════════════════════════

class TestSchema:
    def test_schema_idempotent_tables_and_index(self, db):
        """_ensure_schema مكرر بلا خطأ + الجداول والفهرس موجودة"""
        s1 = CollaborationService(db, clock=FakeClock(CLOCK_BASE))
        s1._ensure_schema()
        s1._ensure_schema()  # استدعاء ثانٍ — idempotent

        tables = {
            r["name"] for r in db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "record_locks" in tables
        assert "sync_conflicts" in tables
        indexes = {
            r["name"] for r in db.fetch_all("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert "idx_record_locks_expiry" in indexes

    def test_lock_columns_match_srs(self, db):
        """أعمدة record_locks وجدول التعارضات مطابقة لمخطط SRS
        + جدول التعارضات القديم (ترحيل 026) لم يُلمس إطلاقًا"""
        svc = CollaborationService(db, clock=FakeClock(CLOCK_BASE))
        cols = {r["name"] for r in db.fetch_all("PRAGMA table_info(record_locks)")}
        assert {"table_name", "record_id", "locked_by", "locked_at", "expires_at", "session_id"} <= cols

        # جدول التعارضات الفعلي للخدمة يحمل أعمدة GAP-5.3 كاملة
        cols_c = {
            r["name"] for r in db.fetch_all(f"PRAGMA table_info({svc.conflicts_table})")
        }
        assert {"table_name", "record_id", "local_data", "remote_data", "resolution",
                "resolved_by", "resolved_at", "merged_data"} <= cols_c

        # الجدول القديم للترحيل 026 بقي كما هو — لا أعمدة مضافة ولا تعديل
        legacy_cols = {r["name"] for r in db.fetch_all("PRAGMA table_info(sync_conflicts)")}
        assert "sync_settings_id" in legacy_cols          # ما زال بمخطط 026
        assert "table_name" not in legacy_cols            # لم نلوّثه بأعمدة GAP-5.3
        assert "merged_data" not in legacy_cols


# ═══════════════════════════ الأقفال — Locks ════════════════════════════════

class TestAcquireLock:
    def test_acquire_lock_fresh(self, svc, rid_factory):
        """حصول جديد على قفل سجل حر"""
        rid = rid_factory()
        result = svc.acquire_lock("products", rid, user_id=7, ttl=300)
        assert result["acquired"] is True
        assert result["locked_by"] == 7
        assert result["expires_at"] is not None
        lock = svc.get_lock("products", rid)
        assert lock is not None and lock["locked_by"] == 7

    def test_acquire_lock_denied_for_second_user(self, svc, rid_factory):
        """رفض مستخدم آخر مع معلومات المالك"""
        rid = rid_factory()
        first = svc.acquire_lock("products", rid, user_id=7, ttl=300)
        assert first["acquired"] is True
        second = svc.acquire_lock("products", rid, user_id=8, ttl=300)
        assert second["acquired"] is False
        assert second["locked_by"] == 7
        assert second["expires_at"]  # حتى متى ينتهي القفل معروف
        assert second["locked_at"]
        # القفل لم يتغير مالكه
        assert svc.get_lock("products", rid)["locked_by"] == 7

    def test_acquire_lock_same_user_refreshes_expiry(self, svc, rid_factory):
        """إعادة الحصول من نفس المستخدم = تجديد انسيابي (الانتهاء يكبر)"""
        rid = rid_factory()
        first = svc.acquire_lock("products", rid, user_id=7, ttl=300)
        exp1 = first["expires_at"]
        svc._clock.advance(10)
        second = svc.acquire_lock("products", rid, user_id=7, ttl=300)
        assert second["acquired"] is True
        assert second.get("refreshed") is True
        exp2 = second["expires_at"]
        assert exp2 > exp1  # تنسيق ISO موحد → مقارنة معجمية صحيحة
        assert svc.get_lock("products", rid)["expires_at"] == exp2

    def test_acquire_lock_after_ttl_expiry(self, svc, rid_factory):
        """انتهاء TTL: مستخدم جديد يحصل على القفل"""
        rid = rid_factory()
        assert svc.acquire_lock("products", rid, user_id=7, ttl=50)["acquired"] is True
        svc._clock.advance(60)  # تجاوز انتهاء صلاحية القفل (TTL=50)
        result = svc.acquire_lock("products", rid, user_id=8, ttl=300)
        assert result["acquired"] is True
        assert result["locked_by"] == 8


class TestReleaseLock:
    def test_release_lock_owner(self, svc, rid_factory):
        """المالك يحرر القفل"""
        rid = rid_factory()
        svc.acquire_lock("products", rid, user_id=7)
        assert svc.release_lock("products", rid, user_id=7) is True
        assert svc.get_lock("products", rid) is None

    def test_release_lock_non_owner_denied_and_persists(self, svc, rid_factory):
        """غير المالك لا يحرر والقفل يبقى"""
        rid = rid_factory()
        svc.acquire_lock("products", rid, user_id=7)
        assert svc.release_lock("products", rid, user_id=8) is False
        lock = svc.get_lock("products", rid)
        assert lock is not None and lock["locked_by"] == 7

    def test_release_lock_force(self, svc, rid_factory):
        """تجاوز المشرف force=True يحرر قفل غيره"""
        rid = rid_factory()
        svc.acquire_lock("products", rid, user_id=7)
        assert svc.release_lock("products", rid, user_id=9, force=True) is True
        assert svc.get_lock("products", rid) is None


class TestHeartbeatLock:
    def test_heartbeat_owner_extends(self, svc, rid_factory):
        """نبض المالك يمدد الانتهاء"""
        rid = rid_factory()
        svc.acquire_lock("products", rid, user_id=7, ttl=300)
        exp1 = svc.get_lock("products", rid)["expires_at"]
        svc._clock.advance(100)
        assert svc.heartbeat_lock("products", rid, user_id=7, ttl=300) is True
        exp2 = svc.get_lock("products", rid)["expires_at"]
        assert exp2 > exp1

    def test_heartbeat_non_owner_rejected(self, svc, rid_factory):
        """نبض غير المالك مرفوض ولا يغيّر الانتهاء"""
        rid = rid_factory()
        svc.acquire_lock("products", rid, user_id=7, ttl=300)
        exp1 = svc.get_lock("products", rid)["expires_at"]
        svc._clock.advance(100)
        assert svc.heartbeat_lock("products", rid, user_id=8, ttl=300) is False
        assert svc.get_lock("products", rid)["expires_at"] == exp1


class TestPurgeExpiredLocks:
    def test_purge_expired_locks_counts_and_keeps_active(self, svc, rid_factory):
        """تنظيف المنتهي فقط: العدد صحيح والنشط يبقى"""
        rid1, rid2, rid3 = rid_factory(), rid_factory(), rid_factory()
        svc.acquire_lock("products", rid1, user_id=7, ttl=50)
        svc.acquire_lock("products", rid2, user_id=7, ttl=50)
        svc.acquire_lock("products", rid3, user_id=7, ttl=10_000)
        svc._clock.advance(60)
        purged = svc.purge_expired_locks()
        assert purged == 2
        assert svc.get_lock("products", rid1) is None
        assert svc.get_lock("products", rid2) is None
        assert svc.get_lock("products", rid3) is not None

    def test_purge_null_expiry_guard(self, db, svc, rid_factory):
        """حارس القفل بدون انتهاء صلاحية الأقدم من MAX_LOCK_TTL"""
        rid = rid_factory()
        old_ts = svc._now() - 2 * MAX_LOCK_TTL
        db.execute_insert(
            """
            INSERT INTO record_locks (table_name, record_id, locked_by, locked_at, expires_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            ("collab_null_guard", rid, 7, _iso(old_ts)),
        )
        purged = svc.purge_expired_locks()
        assert purged >= 1
        assert svc.get_lock("collab_null_guard", rid) is None


class TestConcurrentAcquire:
    def test_concurrent_acquire_single_winner(self, svc, rid_factory):
        """سباق التزامن: 2 خيوط × 20 جولة — فائز واحد بالضبط لكل جولة"""
        errors: list = []

        for _round in range(20):
            rid = rid_factory()
            barrier = threading.Barrier(2)
            results: dict = {}

            def worker(uid: int):
                try:
                    barrier.wait(timeout=5)
                    results[uid] = svc.acquire_lock("products", rid, uid, ttl=300)
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)

            t1 = threading.Thread(target=worker, args=(11,), daemon=True)
            t2 = threading.Thread(target=worker, args=(12,), daemon=True)
            t1.start()
            t2.start()
            t1.join(timeout=10)
            t2.join(timeout=10)

            assert not errors, f"استثناء في الخيوط: {errors}"
            acquired = [r for r in results.values() if r and r.get("acquired")]
            assert len(acquired) == 1, f"فائز مزدوج في جولة على السجل {rid}: {results}"
            winner = acquired[0]["locked_by"]
            assert winner in (11, 12)
            # تنظيف الجولة (سجل جديد في كل جولة على أي حال)
            assert svc.release_lock("products", rid, winner) is True


# ══════════════════════ الإشعارات الحية — Notifications ═════════════════════

class TestNotifications:
    def test_notify_edit_without_manager(self, svc, rid_factory):
        """بدون مدير WebSocket: بلا إشعار وبلا انهيار"""
        result = svc.notify_edit("products", rid_factory(), "price", "12.50", user_id=7)
        assert result["notified"] is False
        assert result["recipients"] is None

    def test_notify_edit_with_stub_manager(self, db, rid_factory):
        """مدير وهمي بأسلوب broadcast الحقيقي: إشعار ناجح + حمولة صحيحة"""
        stub = StubWSManager()
        service = CollaborationService(db, websocket_manager=stub, clock=FakeClock(CLOCK_BASE))
        rid = rid_factory()
        result = service.notify_edit("products", rid, "price", 150, user_id=7)
        assert result["notified"] is True
        assert result["recipients"] == 3
        assert len(stub.sent) == 1
        msg = stub.sent[0]
        assert msg["type"] == "record_edit"
        assert msg["table"] == "products"
        assert msg["record_id"] == rid
        assert msg["field"] == "price"
        assert msg["value"] == 150
        assert msg["user_id"] == 7
        assert msg["ts"]

    def test_notify_edit_failure_swallowed_no_error_log(self, db, rid_factory):
        """فشل البث يُبتلع كـ WARNING فقط (قاعدة conftest: لا ERROR)"""
        stub = StubWSManager(fail=True)
        service = CollaborationService(db, websocket_manager=stub, clock=FakeClock(CLOCK_BASE))
        result = service.notify_edit("products", rid_factory(), "price", 99, user_id=7)
        assert result["notified"] is False
        assert result["recipients"] is None  # العدّ تم ثم فشل البث

    def test_notify_edit_broadcast_callback_fallback(self, db, rid_factory):
        """بديل البث المتزامن broadcast_callback يعمل"""
        captured: list = []

        def callback(payload: dict):
            captured.append(payload)
            return 5  # عدد المستلمين

        service = CollaborationService(db, broadcast_callback=callback, clock=FakeClock(CLOCK_BASE))
        result = service.notify_edit("products", rid_factory(), "stock", 42, user_id=7)
        assert result["notified"] is True
        assert result["recipients"] == 5
        assert captured and captured[0]["type"] == "record_edit"

    def test_notify_lock_change_payload(self, db, rid_factory):
        """حمولة تغيّر القفل صحيحة"""
        stub = StubWSManager()
        service = CollaborationService(db, websocket_manager=stub, clock=FakeClock(CLOCK_BASE))
        rid = rid_factory()
        result = service.notify_lock_change("products", rid, "acquired", user_id=7)
        assert result["notified"] is True
        msg = stub.sent[0]
        assert msg["type"] == "lock_change"
        assert msg["action"] == "acquired"
        assert msg["table"] == "products"
        assert msg["record_id"] == rid
        assert msg["user_id"] == 7


# ══════════════════════ التعارضات — Conflicts ═══════════════════════════════

class TestDetectConflict:
    def test_detect_conflict_equal_versions_no_conflict(self, svc, rid_factory):
        """إصدارات متساوية → لا تعارض ولا سجل"""
        rid = rid_factory()
        result = svc.detect_conflict("products", rid, local_version=3, remote_version=3)
        assert result["conflict"] is False
        assert result["conflict_id"] is None
        rows = db_rows(svc, "products", rid)
        assert rows == 0

    def test_detect_conflict_divergent_versions_creates_conflict(self, svc, rid_factory):
        """إصدارات متباعدة → سجل تعارض مع معرّف"""
        rid = rid_factory()
        result = svc.detect_conflict(
            "products", rid, local_version=2, remote_version=5,
            local_data={"price": 150}, remote_data={"price": 145},
        )
        assert result["conflict"] is True
        assert isinstance(result["conflict_id"], int)
        assert result["local_version"] == 2
        assert result["remote_version"] == 5
        assert svc.get_conflict(result["conflict_id"]) is not None

    def test_detect_conflict_diverged_fields(self, svc, rid_factory):
        """قائمة الحقول المتباعدة: مختلف القيمة + الموجود بطرف واحد"""
        rid = rid_factory()
        result = svc.detect_conflict(
            "products", rid, local_version=1, remote_version=2,
            local_data={"price": 150},
            remote_data={"price": 145, "stock": 200},
        )
        # price اختلفت القيمة + stock موجود بطرف واحد فقط
        assert set(result["diverged_fields"]) == {"price", "stock"}

    def test_detect_conflict_identical_data_no_diverged_fields(self, svc, rid_factory):
        """بيانات متطابقة → قائمة فارغة رغم اختلاف الإصدار"""
        result = svc.detect_conflict(
            "products", rid_factory(), local_version=1, remote_version=9,
            local_data={"name": "أ", "price": 10},
            remote_data={"name": "أ", "price": 10},
        )
        assert result["conflict"] is True
        assert result["diverged_fields"] == []


def db_rows(svc: CollaborationService, table_name: str, record_id: int) -> int:
    """عدد تعارضات سجل معين — عدد صفوف جدول التعارضات للسجل"""
    rows = svc.db.fetch_all(
        f"SELECT COUNT(*) AS c FROM {svc.conflicts_table} WHERE table_name = ? AND record_id = ?",
        (table_name, record_id),
    )
    return int(rows[0]["c"]) if rows else 0


class TestResolveConflict:
    def test_resolve_conflict_local_wins(self, svc, rid_factory):
        """local_wins يعيد بيانات المحلي ويحفظ الحل"""
        rid = rid_factory()
        cid = svc.detect_conflict(
            "products", rid, 1, 2,
            local_data={"price": 150}, remote_data={"price": 145},
        )["conflict_id"]
        final = svc.resolve_conflict(cid, "local_wins", resolved_by=7)
        assert final == {"price": 150}
        row = svc.get_conflict(cid)
        assert row["resolution"] == "local_wins"
        assert row["resolved_by"] == 7
        assert row["resolved_at"] is not None
        assert row["merged_data"] is None

    def test_resolve_conflict_remote_wins(self, svc, rid_factory):
        """remote_wins يعيد بيانات السحابة"""
        rid = rid_factory()
        cid = svc.detect_conflict(
            "products", rid, 3, 4,
            local_data={"price": 150}, remote_data={"price": 145, "stock": 195},
        )["conflict_id"]
        final = svc.resolve_conflict(cid, "remote_wins", resolved_by=8)
        assert final == {"price": 145, "stock": 195}

    def test_resolve_conflict_merged_requires_data(self, svc, rid_factory):
        """merged بدون بيانات مدمجة → خطأ ثنائي اللغة"""
        cid = svc.detect_conflict(
            "products", rid_factory(), 1, 2,
            local_data={"a": 1}, remote_data={"a": 2},
        )["conflict_id"]
        with pytest.raises(ConflictResolutionError):
            svc.resolve_conflict(cid, "merged")
        # ما زال غير محلول
        assert svc.get_conflict(cid)["resolution"] is None

    def test_resolve_conflict_merged_persists(self, svc, rid_factory):
        """merged مع بيانات: تُخزَّن وتُعاد"""
        rid = rid_factory()
        cid = svc.detect_conflict(
            "products", rid, 1, 2,
            local_data={"price": 150}, remote_data={"price": 145, "stock": 200},
        )["conflict_id"]
        merged = {"price": 148, "stock": 200}
        final = svc.resolve_conflict(cid, "merged", merged_data=merged, resolved_by=7)
        assert final == merged
        row = svc.get_conflict(cid)
        assert row["resolution"] == "merged"
        assert row["merged_data"] == merged
        assert row["resolved_at"] is not None

    def test_resolve_conflict_invalid_resolution(self, svc, rid_factory):
        """حل غير معروف → ConflictResolutionError"""
        cid = svc.detect_conflict(
            "products", rid_factory(), 1, 2,
            local_data={"a": 1}, remote_data={"a": 2},
        )["conflict_id"]
        with pytest.raises(ConflictResolutionError):
            svc.resolve_conflict(cid, "banana")


class TestListAndGetConflicts:
    def test_list_unresolved_filters_and_excludes_resolved(self, svc):
        """السرد: تصفية بالجدول واستبعاد المحلول"""
        cid_a1 = svc.detect_conflict("collab_tbl_a", 1, 1, 2)["conflict_id"]
        cid_a2 = svc.detect_conflict("collab_tbl_a", 2, 1, 2)["conflict_id"]
        svc.detect_conflict("collab_tbl_b", 1, 1, 2)["conflict_id"]
        svc.resolve_conflict(cid_a2, "local_wins")

        all_unresolved = svc.list_unresolved_conflicts()
        ids = {r["id"] for r in all_unresolved}
        assert cid_a1 in ids
        assert cid_a2 not in ids  # محلول

        filtered = svc.list_unresolved_conflicts(table_name="collab_tbl_a")
        assert [r["id"] for r in filtered] == [cid_a1]
        assert all(r["resolution"] is None for r in filtered)

        limited = svc.list_unresolved_conflicts(limit=1)
        assert len(limited) == 1

    def test_get_conflict_roundtrip_json(self, svc, rid_factory):
        """جولة كاملة: JSON يُخزَّن ويُفك صحيحًا"""
        rid = rid_factory()
        local = {"price": Decimal("150.50"), "name": "منتج تعارض"}
        remote = {"price": "145.00", "stock": 200, "extra": None}
        cid = svc.detect_conflict(
            "products", rid, 4, 7, local_data=local, remote_data=remote,
        )["conflict_id"]
        row = svc.get_conflict(cid)
        assert row is not None
        assert isinstance(row["local_data"], dict)
        assert isinstance(row["remote_data"], dict)
        assert row["local_data"]["name"] == "منتج تعارض"  # عربي سليم (ensure_ascii=False)
        assert row["local_data"]["price"] == "150.50"     # Decimal → str
        assert row["remote_data"]["stock"] == 200
        assert row["table_name"] == "products"
        assert row["record_id"] == rid
        assert row["created_at"] is not None

    def test_get_conflict_missing(self, svc):
        """معرّف غير موجود → None"""
        assert svc.get_conflict(999_999_999) is None


# ══════════════════════ إصدار السجل — Record version ════════════════════════

class TestGetRecordVersion:
    def test_get_record_version_products_hash_fallback(self, db, svc):
        """المنتجات (بدون عمود version) → بصمة updated_at كعدد صحيح"""
        pm = ProductManager(db)
        pid = pm.create_product(Product(
            name="منتج إصدار", unit="حبة",
            cost_price=Decimal("10.00"), selling_price=Decimal("15.00"),
            current_stock=5,
        ))
        assert pid
        version = svc.get_record_version("products", pid)
        assert isinstance(version, int)
        assert version > 0
        # ثابت لقيمة updated_at نفسها
        assert svc.get_record_version("products", pid) == version

    def test_get_record_version_numeric_version_column(self, db, svc):
        """عمود version رقمي له الأولوية"""
        db.execute_non_query(
            """
            CREATE TABLE IF NOT EXISTS collab_version_probe (
                id INTEGER PRIMARY KEY,
                version INTEGER,
                updated_at TEXT
            )
            """
        )
        rid = db.execute_insert(
            "INSERT INTO collab_version_probe (version, updated_at) VALUES (?, ?)",
            (7, "2025-01-01 10:00:00"),
        )
        assert svc.get_record_version("collab_version_probe", rid) == 7

    def test_get_record_version_unknown_table_and_missing_record(self, svc):
        """جدول مجهول/سجل مفقود/معرّف خبيث → None دفاعيًا"""
        assert svc.get_record_version("no_such_table_xyz", 1) is None
        assert svc.get_record_version("products", 987_654_321) is None
        assert svc.get_record_version("products; DROP TABLE products", 1) is None


# ══════════════════════ الحارس — CollabEditGuard ════════════════════════════

class TestCollabEditGuard:
    def test_guard_happy_path(self, svc, rid_factory):
        """المسار السليم: دخول يقفل، خروج يحرر، lock_info مكشوف"""
        rid = rid_factory()
        guard = CollabEditGuard(svc)
        with guard.guarded_edit("products", rid, user_id=7, ttl=300) as g:
            assert g is guard
            assert guard.lock_info["acquired"] is True
            assert guard.lock_info["locked_by"] == 7
            lock = svc.get_lock("products", rid)
            assert lock is not None and lock["locked_by"] == 7
        assert svc.get_lock("products", rid) is None
        assert guard.lock_info is None

    def test_guard_blocked_second_user_raises_bilingual(self, svc, rid_factory):
        """حارس المستخدم الثاني يفشل بخطأ يحمل رسالة عربية وتفاصيل المالك"""
        rid = rid_factory()
        svc.acquire_lock("products", rid, user_id=7, ttl=300)
        guard2 = CollabEditGuard(svc)
        with pytest.raises(RecordLockedError) as exc_info:
            with guard2.guarded_edit("products", rid, user_id=8):
                pass
        err = exc_info.value
        assert "مقفل" in str(err)  # رسالة عربية
        assert "locked" in str(err).lower()  # وجزء إنجليزي
        assert err.locked_by == 7
        assert err.table_name == "products"
        assert err.record_id == rid
        # قفل المالك الأصلي سليم
        assert svc.get_lock("products", rid)["locked_by"] == 7

    def test_guard_releases_on_exception(self, svc, rid_factory):
        """استثناء داخل الكتلة → القفل يُحرر رغم ذلك (منع التسريب)"""
        rid = rid_factory()
        guard = CollabEditGuard(svc)
        with pytest.raises(RuntimeError, match="boom"):
            with guard.guarded_edit("products", rid, user_id=7):
                raise RuntimeError("boom")
        assert svc.get_lock("products", rid) is None

    def test_guard_notifies_lock_changes_via_stub(self, db, rid_factory):
        """الحارس يبث acquired/released عبر مدير WebSocket"""
        stub = StubWSManager()
        service = CollaborationService(db, websocket_manager=stub, clock=FakeClock(CLOCK_BASE))
        rid = rid_factory()
        with CollabEditGuard(service).guarded_edit("products", rid, user_id=7):
            pass
        actions = [m["action"] for m in stub.sent if m["type"] == "lock_change"]
        assert actions == ["acquired", "released"]
