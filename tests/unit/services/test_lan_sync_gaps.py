#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات فجوات مزامنة الشبكة المحلية (GAP-5.1 + GAP-5.2) — قاعدة بيانات حقيقية
LAN Sync Gaps Tests — Real temp SQLite DB + real localhost HTTP server:

- GAP-5.1: خدمة اكتشاف أجهزة LAN (mDNS/zeroconf مع تدهور رشيق + بديل HTTP + سجل الأجهزة)
- GAP-5.2: خدمة التفريغ التلقائي لطابور المزامنة عند استعادة الاتصال
  (ربط المراقب، التهدئة، منطق الانتقال، عمق الطابور من المخطط الحقيقي)

ملاحظة تشغيل / Run note:
    tests/unit/conftest.py يستورد PySide6 (غير مثبت في بيئة الاختبار المعزولة)،
    لذا تُشغَّل هذه الاختبارات مع --noconftest. ملف الاختبارات مستقل تمامًا
    (لا يعتمد على أي fixture من conftest) ولا يستورد PySide6 مطلقًا.
    tests/unit/conftest.py imports PySide6 (absent in this sandbox); run with
    --noconftest. This file is fully self-contained and never imports PySide6.
"""

import json
import os
import socket
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database_manager import DatabaseManager
from src.services.lan_discovery_service import (
    MAX_HTTP_CANDIDATES,
    ZEROCONF_AVAILABLE,
    LanDiscoveryService,
)
from src.services.sync_queue_flush_service import SyncQueueFlushService

# =========================================================================
# Fixtures — قاعدة بيانات حقيقية مؤقتة + خادم HTTP محلي حقيقي
# =========================================================================


@pytest.fixture(scope="module")
def db():
    """قاعدة بيانات SQLite حقيقية مؤقتة للمجموعة (نفس نمط test_business_gaps)"""
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
    try:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
    except Exception:
        pass


class _HealthHandler(BaseHTTPRequestHandler):
    """خادم اختباري يقدم /health و /api/health كـ JSON 200 — Test double of the real API health endpoints."""

    def do_GET(self):  # noqa: N802
        if self.path in ("/health", "/api/health"):
            body = json.dumps({"status": "healthy", "version": "1.0.0"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # silence test output
        pass


@pytest.fixture()
def health_server():
    """خادم HTTP حقيقي على منفذ حر — Real localhost HTTP server on a free port."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield ("127.0.0.1", server.server_address[1])
    server.shutdown()
    server.server_close()
    thread.join(timeout=2.0)


def _closed_port() -> int:
    """منفذ حر مغلق (لا مستمع) — A free port with no listener."""
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


class FakeClock:
    """ساعة monotonic قابلة للحقن لاختبار التهدئة — Injectable monotonic clock for cooldown tests."""

    def __init__(self, start: float = 1000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class CallbackRegistryMonitor:
    """مراقب اختباري بنمط on_state_change (مطابق للخطاف المضاف) — Stub monitor with the plain hook."""

    def __init__(self):
        self.callbacks = []

    def on_state_change(self, callback):
        self.callbacks.append(callback)

    def emit(self, is_connected: bool) -> None:
        for callback in list(self.callbacks):
            callback(is_connected)


class FakeQtSignal:
    """إشارة Qt مزيّفة (connect فقط) — Minimal duck-typed Qt signal."""

    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def emit(self, *args) -> None:
        for slot in list(self.slots):
            slot(*args)


class FakeQtMonitor:
    """مراقب بنمط إشارات Qt: status_changed(bool) — Qt-signal-style stub monitor."""

    def __init__(self):
        self.status_changed = FakeQtSignal()
        self.connected = FakeQtSignal()


# =========================================================================
# GAP-5.1 — LanDiscoveryService
# =========================================================================


class TestLanDiscoveryService:
    """اكتشاف LAN: تدهور zeroconf + بديل HTTP + ping — browsing degradation, HTTP fallback, ping."""

    def test_browsing_without_zeroconf_returns_empty(self):
        """بدون zeroconf: start_browsing يعيد [] دون أي استثناء (تدهور رشيق)."""
        if ZEROCONF_AVAILABLE:
            pytest.skip("zeroconf مثبت في هذه البيئة — مسار التدهور غير قابل للاختبار")
        service = LanDiscoveryService()
        assert service.start_browsing(timeout_ms=100) == []
        # الإعلان يتدهور أيضًا بـ False
        assert service.start_advertising(port=8123) is False
        assert service.is_advertising is False
        service.stop_advertising()  # آمن عند عدم الإعلان

    def test_discover_via_http_finds_local_health_server(self, health_server):
        """بديل HTTP: خادم /health حقيقي على localhost → عنصر واحد عبر 'http'."""
        ip, port = health_server
        service = LanDiscoveryService()
        devices = service.discover_via_http(candidates=[ip], port=port, timeout=1.0)
        assert len(devices) == 1
        device = devices[0]
        assert device["ip"] == ip
        assert device["port"] == port
        assert device["via"] == "http"
        assert device["name"]  # hostname أو IP

    def test_discover_via_http_dead_port_returns_empty(self):
        """منفذ مغلق: لا نتائج ولا استثناءات."""
        service = LanDiscoveryService()
        devices = service.discover_via_http(
            candidates=["127.0.0.1"], port=_closed_port(), timeout=0.5
        )
        assert devices == []

    def test_ping_device_reachable_and_closed(self, health_server):
        """ping_device: True مع منفذ حي، False مع منفذ مغلق — بلا استثناءات."""
        ip, port = health_server
        service = LanDiscoveryService()
        assert service.ping_device(ip, port, timeout=1.0) is True
        assert service.ping_device(ip, _closed_port(), timeout=0.5) is False
        # مدخلات غير صالحة لا ترفع استثناء
        assert service.ping_device("999.999.999.999", 1, timeout=0.2) is False

    def test_http_candidates_capped_at_64(self, monkeypatch):
        """سقف المرشحين 64: لا يُفحص أكثر من 64 مرشحًا مهما طالت القائمة."""
        service = LanDiscoveryService()
        # القائمة الافتراضية من الشبكات المحلية لا تتجاوز السقف
        assert len(service._default_http_candidates()) <= MAX_HTTP_CANDIDATES

        probes = {"count": 0}
        original_probe = service._probe_http

        def counting_probe(ip, port, timeout):
            probes["count"] += 1
            return original_probe(ip, port, timeout)

        monkeypatch.setattr(service, "_probe_http", counting_probe)
        many = [f"10.123.{i // 256}.{i % 256}" for i in range(1, 101)]
        assert len(many) == 100
        service.discover_via_http(candidates=many, port=_closed_port(), timeout=0.05)
        assert probes["count"] <= MAX_HTTP_CANDIDATES

    def test_background_browsing_lifecycle(self):
        """التصفح الخلفي: خيط daemon دوري يُوقف بنجاح (مهلة انضمام ثانيتان)."""
        service = LanDiscoveryService()
        received = []
        started = service.start_background_browsing(received.append, interval_s=0.2)
        assert started is True
        # ثانية البدء تعيد False (يعمل بالفعل)
        assert service.start_background_browsing(received.append, interval_s=0.2) is False
        deadline = time.monotonic() + 2.0
        while not received and time.monotonic() < deadline:
            time.sleep(0.05)
        assert len(received) >= 1  # يعيد [] عندما لا يتوفر zeroconf
        service.stop_background_browsing()
        assert service._bg_thread is None or not service._bg_thread.is_alive()

    def test_machine_identity_and_service_type(self):
        """نمط اسم المضيف standard-joumla-XXXX ونوع الخدمة الصحيح."""
        service = LanDiscoveryService()
        assert service.service_type == "_erp-standard-joumla._tcp.local."
        assert service.service_name == "Standard El-Joumla"
        assert service._server_hostname.startswith("standard-joumla-")
        assert service.machine_id  # غير فارغ
        assert "127." in service._local_ip() or service._local_ip()


# =========================================================================
# GAP-5.1 — Persistence (سجل الأجهزة المكتشفة)
# =========================================================================


class TestDiscoveredDevicesPersistence:
    """الحفظ UPSERT + تصفية العمر — upsert semantics + age filtering."""

    def test_save_devices_upserts_single_row_with_updated_properties(self, db):
        """حفظ ثم تحديث نفس المفتاح → صف واحد وخصائص محدثة وlast_seen مجدد."""
        service = LanDiscoveryService(db_manager=db)
        payload = [
            {
                "name": "Terminal-1",
                "ip": "192.168.77.10",
                "port": 8000,
                "properties": {"version": "1.0", "machine_id": "abc-123"},
            }
        ]
        assert service.save_devices(payload) == 1
        # قدم الصف اصطناعيًا لاختبار تجديد last_seen
        db.execute_non_query(
            "UPDATE discovered_devices SET last_seen = datetime('now', '-30 minutes') "
            "WHERE ip = ? AND port = ?",
            ("192.168.77.10", 8000),
        )
        # حفظ نفس المفتاح بخصائص جديدة → UPSERT وليس INSERT
        payload[0]["properties"] = {"version": "1.1", "machine_id": "abc-123"}
        assert service.save_devices(payload) == 1

        rows = db.fetch_all(
            "SELECT name, ip, port, properties, last_seen FROM discovered_devices "
            "WHERE ip = ? AND port = ?",
            ("192.168.77.10", 8000),
        )
        assert len(rows) == 1
        row = rows[0]
        assert row["name"] == "Terminal-1"
        assert json.loads(row["properties"])["version"] == "1.1"
        # last_seen تجدد عند الـ UPSERT (خلال آخر 5 ثوانٍ)
        fresh = db.fetch_one(
            "SELECT COUNT(*) AS c FROM discovered_devices "
            "WHERE ip = ? AND last_seen >= datetime('now', '-5 seconds')",
            ("192.168.77.10",),
        )
        assert fresh["c"] == 1

    def test_get_known_devices_filters_by_age(self, db):
        """صف قديم (90 دقيقة) مستبعد مع max_age_minutes=60 و 1؛ الصف الحديث موجود."""
        service = LanDiscoveryService(db_manager=db)
        # صف قديم مباشرة عبر SQL
        db.execute_non_query(
            "INSERT OR IGNORE INTO discovered_devices (name, ip, port, properties, last_seen) "
            "VALUES ('Old-Terminal', '192.168.77.99', 8000, '{}', datetime('now', '-90 minutes'))"
        )
        # صف حديث عبر الخدمة
        service.save_devices(
            [
                {
                    "name": "Fresh-Terminal",
                    "ip": "192.168.77.11",
                    "port": 8001,
                    "properties": {"version": "1.0"},
                }
            ]
        )

        known_60 = service.get_known_devices(max_age_minutes=60)
        ips_60 = {d["ip"] for d in known_60}
        assert "192.168.77.11" in ips_60
        assert "192.168.77.99" not in ips_60

        known_1 = service.get_known_devices(max_age_minutes=1)
        ips_1 = {d["ip"] for d in known_1}
        assert "192.168.77.99" not in ips_1
        assert "192.168.77.11" in ips_1

        # الخصائص تُفك JSON إلى dict
        fresh_device = next(d for d in known_1 if d["ip"] == "192.168.77.11")
        assert fresh_device["properties"] == {"version": "1.0"}

    def test_persistence_disabled_without_db_manager(self):
        """بدون db_manager: لا حفظ ولا قراءة — عودة [] آمنة."""
        service = LanDiscoveryService()
        assert service.save_devices([{"name": "x", "ip": "10.0.0.1", "port": 8000}]) == 0
        assert service.get_known_devices() == []


# =========================================================================
# GAP-5.2 — SyncQueueFlushService
# =========================================================================


class TestSyncQueueFlushService:
    """التفريغ: نجاح/فشل/تهدئة/انتقال/انعكاس المُنفّذ — flush outcomes, cooldown, transitions, introspection."""

    def test_flush_success_with_callback(self):
        """callback يعيد 5 → success=True flushed=5 والإحصائيات محدثة."""
        calls = {"count": 0}

        def flusher():
            calls["count"] += 1
            return 5

        service = SyncQueueFlushService(flush_callback=flusher)
        result = service.flush_now(reason="test")
        assert result["success"] is True
        assert result["flushed"] == 5
        assert result["error"] is None
        assert result["skipped"] is False
        assert result["duration_ms"] >= 0
        assert result["reason"] == "test"
        assert calls["count"] == 1

        stats = service.get_stats()
        assert stats["total_flush_attempts"] == 1
        assert stats["successful"] == 1
        assert stats["failed"] == 0
        assert stats["last_flushed_count"] == 5
        assert stats["last_error"] is None
        assert stats["last_flush_at"] is not None

    def test_flush_callback_exception_caught(self):
        """callback يرفع استثناء → success=False وerror محدد وبلا رفع نحو الخارج."""
        service = SyncQueueFlushService(flush_callback=lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        result = service.flush_now(reason="failing")
        assert result["success"] is False
        assert result["flushed"] == 0
        assert result["error"] is not None
        assert "boom" in result["error"]
        assert service.get_stats()["failed"] == 1

    def test_no_flusher_available_returns_error_not_fake_success(self):
        """بلا مُنفّذ → success=False مع خطأ واضح (ممنوع النجاح المزيّف)."""
        service = SyncQueueFlushService()
        result = service.flush_now()
        assert result["success"] is False
        assert result["flushed"] == 0
        assert result["error"] is not None
        assert "flush_callback" in result["error"] or "cloud_sync_service" in result["error"]

    def test_cooldown_skips_second_immediate_flush(self):
        """تهدئة 20 ثانية: المحاولة الثانية الفورية متجاهَلة مع ساعة قابلة للحقن."""
        clock = FakeClock(start=1000.0)
        calls = {"count": 0}

        def flusher():
            calls["count"] += 1
            return 3

        service = SyncQueueFlushService(
            flush_callback=flusher, min_flush_interval_s=20.0, clock=clock
        )
        first = service.flush_now("first")
        assert first["skipped"] is False
        assert first["flushed"] == 3

        clock.advance(5.0)
        second = service.flush_now("too-soon")
        assert second["skipped"] is True
        assert second["flushed"] == 0
        assert calls["count"] == 1  # لم يُستدعَ المُنفّذ مرة أخرى
        assert service.get_stats()["skipped_flushes"] == 1

        clock.advance(21.0)
        third = service.flush_now("after-cooldown")
        assert third["skipped"] is False
        assert third["flushed"] == 3
        assert calls["count"] == 2

    def test_transition_logic_triggers_flush_only_offline_to_online(self):
        """offline→online يفرّغ؛ online مرة أخرى يُتجاهل؛ offline لا يفرّغ."""
        calls = {"count": 0}

        def flusher():
            calls["count"] += 1
            return 2

        # تهدئة = 0 لعزل منطق الانتقال عن التهدئة
        service = SyncQueueFlushService(flush_callback=flusher, min_flush_interval_s=0.0)

        offline = service.handle_state_change("offline")
        assert offline["flushed"] is False
        assert calls["count"] == 0

        online = service.handle_state_change("online")
        assert online["flushed"] is True
        assert online["result"]["success"] is True
        assert online["result"]["flushed"] == 2
        assert calls["count"] == 1

        online_again = service.handle_state_change("online")
        assert online_again["flushed"] is False
        assert online_again["skipped"] is True
        assert calls["count"] == 1  # لا انتقال جديد

        back_offline = service.handle_state_change("offline")
        assert back_offline["flushed"] is False
        assert calls["count"] == 1

    def test_bool_and_dict_flusher_results_normalized(self):
        """تطبيع النتائج: bool → 1/0، وdict {"synced": n} → n (صيغة api_client الحقيقية)."""
        bool_service = SyncQueueFlushService(flush_callback=lambda: True, min_flush_interval_s=0.0)
        assert bool_service.flush_now()["flushed"] == 1
        false_service = SyncQueueFlushService(flush_callback=lambda: False, min_flush_interval_s=0.0)
        assert false_service.flush_now()["flushed"] == 0

        dict_service = SyncQueueFlushService(
            flush_callback=lambda: {"synced": 7, "failed": 1, "pending": 2},
            min_flush_interval_s=0.0,
        )
        assert dict_service.flush_now()["flushed"] == 7

    def test_flusher_introspection_from_cloud_service(self):
        """فحص انعكاسي: sync_now بلا معاملات يُختار؛ full_sync(id) يُستبعد لصالح callback."""

        class FakeCloudService:
            def sync_now(self):
                return 4  # int

            def full_sync(self, settings_id):  # تتطلب معاملات → تُستبعد
                return 999

        calls = {"count": 0}

        def fallback():
            calls["count"] += 1
            return 1

        service = SyncQueueFlushService(
            cloud_sync_service=FakeCloudService(), flush_callback=fallback
        )
        assert service._flusher_source == "sync_now"
        result = service.flush_now("introspected")
        assert result["success"] is True
        assert result["flushed"] == 4
        assert calls["count"] == 0  # المُنفّذ من الخدمة له الأولوية

    def test_flusher_falls_back_to_callback_when_no_zero_arg_method(self):
        """خدمة cloud بلا طريقة صفرية المعاملات → يعتمد flush_callback."""

        class NeedArgsCloud:
            def full_sync(self, settings_id):
                return 500

        service = SyncQueueFlushService(
            cloud_sync_service=NeedArgsCloud(), flush_callback=lambda: 9
        )
        assert service._flusher_source == "flush_callback"
        result = service.flush_now("fallback")
        assert result["success"] is True
        assert result["flushed"] == 9

    def test_attach_to_monitor_callback_registry(self):
        """ربط ناجح بمراقب on_state_change: يفرّغ عند الانتقال فقط."""
        monitor = CallbackRegistryMonitor()
        calls = {"count": 0}
        service = SyncQueueFlushService(
            flush_callback=lambda: (calls.__setitem__("count", calls["count"] + 1) or 1),
            min_flush_interval_s=0.0,
        )
        assert service.attach_to_monitor(monitor) is True
        assert service.is_monitor_attached is True

        monitor.emit(False)  # online→offline: لا تفريغ
        assert calls["count"] == 0
        monitor.emit(True)  # offline→online: تفريغ
        assert calls["count"] == 1
        monitor.emit(True)  # بلا انتقال: لا تفريغ
        assert calls["count"] == 1

    def test_attach_to_monitor_qt_signal_style(self):
        """ربط ناجح بإشارة Qt مزيّفة status_changed(bool)."""
        monitor = FakeQtMonitor()
        calls = {"count": 0}
        service = SyncQueueFlushService(
            flush_callback=lambda: (calls.__setitem__("count", calls["count"] + 1) or 1),
            min_flush_interval_s=0.0,
        )
        assert service.attach_to_monitor(monitor) is True
        monitor.status_changed.emit(True)  # أول حالة بلا سابقة → لا انتقال
        assert calls["count"] == 0
        monitor.status_changed.emit(False)
        monitor.status_changed.emit(True)  # انتقال → تفريغ
        assert calls["count"] == 1

    def test_attach_to_monitor_garbage_returns_false(self):
        """مراقب غير معروف/None → False بدون أي استثناء."""
        service = SyncQueueFlushService(flush_callback=lambda: 1)
        assert service.attach_to_monitor(object()) is False
        assert service.attach_to_monitor(None) is False
        assert service.attach_to_monitor("not-a-monitor") is False
        assert service.is_monitor_attached is False

    def test_constructor_attaches_monitor_when_given(self):
        """التهيئة بـ connectivity_monitor تربطه تلقائيًا."""
        monitor = CallbackRegistryMonitor()
        service = SyncQueueFlushService(
            flush_callback=lambda: 1, connectivity_monitor=monitor
        )
        assert service.is_monitor_attached is True
        assert len(monitor.callbacks) == 1


# =========================================================================
# GAP-5.2 — get_queue_depth (المخطط الحقيقي)
# =========================================================================


@pytest.fixture()
def fresh_db_factory():
    """مصنع قواعد بيانات مؤقتة للتحكم في مخطط sync_queue — Temp DB factory for schema variants."""
    created = []

    def _make():
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        manager = DatabaseManager(db_path=tmp.name, pool_options={"enabled": False})
        assert manager.initialize() is True
        created.append((manager, tmp.name))
        return manager

    yield _make

    for manager, path in created:
        try:
            if manager.connection:
                manager.connection.close()
        except Exception:
            pass
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass


class TestQueueDepth:
    """عمق الطابور من الصيغ الحقيقية — depth against real schemas + absent table."""

    def test_depth_with_api_client_schema(self, fresh_db_factory):
        """المخطط الحقيقي في api_client.py (عمود synced): pending/total صحيحة."""
        manager = fresh_db_factory()
        manager.execute_non_query(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0
            )
            """
        )
        for entity_id in (1, 2, 3):
            manager.execute_non_query(
                "INSERT INTO sync_queue(entity_type, entity_id, operation) VALUES('product', ?, 'update')",
                (entity_id,),
            )
        manager.execute_non_query(
            "INSERT INTO sync_queue(entity_type, entity_id, operation, synced) VALUES('product', 4, 'update', 1)"
        )

        service = SyncQueueFlushService(db_manager=manager)
        depth = service.get_queue_depth()
        assert depth["table_exists"] is True
        assert depth["pending"] == 3
        assert depth["failed"] == 0
        assert depth["total"] == 4

    def test_depth_with_status_column_schema(self, fresh_db_factory):
        """مخطط بعمود status نصي: pending/failed تُقرأ من القيم."""
        manager = fresh_db_factory()
        manager.execute_non_query(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            )
            """
        )
        for status in ("pending", "pending", "failed", "flushed"):
            manager.execute_non_query(
                "INSERT INTO sync_queue(table_name, record_id, operation, status) VALUES('sales', 1, 'create', ?)",
                (status,),
            )
        service = SyncQueueFlushService(db_manager=manager)
        depth = service.get_queue_depth()
        assert depth["table_exists"] is True
        assert depth["pending"] == 2
        assert depth["failed"] == 1
        assert depth["total"] == 4

    def test_depth_with_local_database_manager_schema(self, fresh_db_factory):
        """مخطط local_database_manager (بلا عمود حالة): الصفوف كلها معلّقة."""
        manager = fresh_db_factory()
        manager.execute_non_query(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                data TEXT,
                retry_count INTEGER DEFAULT 0,
                last_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(table_name, record_id, operation)
            )
            """
        )
        for record_id in (10, 11):
            manager.execute_non_query(
                "INSERT OR IGNORE INTO sync_queue(table_name, record_id, operation) VALUES('products', ?, 'update')",
                (record_id,),
            )
        service = SyncQueueFlushService(db_manager=manager)
        depth = service.get_queue_depth()
        assert depth["table_exists"] is True
        assert depth["pending"] == 2
        assert depth["failed"] == 0
        assert depth["total"] == 2

    def test_depth_when_table_absent(self, fresh_db_factory):
        """بدون جدول sync_queue: أصفار مع table_exists=False."""
        manager = fresh_db_factory()  # قاعدة جديدة بلا sync_queue
        service = SyncQueueFlushService(db_manager=manager)
        depth = service.get_queue_depth()
        assert depth == {"pending": 0, "failed": 0, "total": 0, "table_exists": False}

    def test_depth_without_db_manager(self):
        """بلا db_manager: أصفار آمنة."""
        service = SyncQueueFlushService()
        depth = service.get_queue_depth()
        assert depth["table_exists"] is False
        assert depth["pending"] == 0 and depth["total"] == 0


# =========================================================================
# Integration smoke — المسار الحقيقي لمراقب الاتصال (يعمل فقط مع PySide6)
# =========================================================================


class TestConnectivityMonitorIntegration:
    """دخان تكامل مع ConnectivityMonitor الحقيقي (يتطلب PySide6)."""

    def test_real_monitor_online_transition_triggers_flush(self):
        """المسار الحقيقي: _on_result(False) ثم _on_result(True) → تفريغ عبر الخطاف المضاف."""
        pytest.importorskip("PySide6", reason="PySide6 غير مثبت")
        try:
            # connectivity_monitor يستورد QtWidgets — يفشل بدون libEGL في البيئة المعزولة
            from PySide6.QtWidgets import QApplication  # noqa: F401
        except ImportError as exc:
            pytest.skip(
                f"PySide6.QtWidgets غير قابل للتحميل في بيئة الاختبار المعزولة (headless): {exc} — "
                "تم اختبار مسار handle_state_change عبر المراقبين الاختباريين بدلًا منه"
            )
        from src.core.connectivity_monitor import ConnectivityMonitor

        app = QApplication.instance() or QApplication([])
        monitor = ConnectivityMonitor()
        calls = {"count": 0}
        service = SyncQueueFlushService(
            flush_callback=lambda: (calls.__setitem__("count", calls["count"] + 1) or 1),
            min_flush_interval_s=0.0,
        )
        assert service.attach_to_monitor(monitor) is True
        # بداية افتراضية "متصل" داخل المراقب → نقطعه يدويًا ثم نستعيد الاتصال
        monitor._is_connected = False
        monitor._on_result(False, 0.0)  # لا تغيير (offline→offline)
        assert calls["count"] == 0
        monitor._on_result(True, 12.0)  # offline→online → تفريغ
        assert calls["count"] == 1
        monitor.stop()
        app.processEvents()
