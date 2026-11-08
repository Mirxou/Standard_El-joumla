#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة اكتشاف الأجهزة على الشبكة المحلية (GAP-5.1) — LAN Device Discovery Service
================================================================================

الغرض / Purpose:
    اكتشاف أجهزة "Standard El-Joumla" الأخرى على الشبكة المحلية (LAN) تلقائيًا
    عبر mDNS/Zeroconf (نوع الخدمة: ``_erp-standard-joumla._tcp.local.``)،
    مع بديل HTTP آمن يعمل حتى بدون zeroconf (مسح عناوين الشبكة المحلية
    عبر فحص نقطة نهاية ``/health``).

    Automatic discovery of peer "Standard El-Joumla" devices on the LAN via
    mDNS/Zeroconf (service type ``_erp-standard-joumla._tcp.local.``), with an
    HTTP fallback that works without zeroconf (probing the ``/health``
    endpoint of candidate hosts on private subnets).

المطابقة مع SRS / SRS Reference:
    docs/SRS_ARCHITECTURE.md → Area 5 → GAP-5.1 (LAN Device Discovery &
    Auto-Configuration) — يغطي: الإعلان عن الجهاز (Advertiser)، التصفح
    (Browser)، مراقبة الحضور، وسجل الأجهزة المكتشفة (device registry).

آلية التدهور الرشيق / Graceful degradation:
    إذا لم تكن مكتبة ``zeroconf`` مثبتة، تعيد دوال التصفح قائمة فارغة ``[]``
    وتسجل تحذيرًا ("zeroconf غير مثبت — التصفح اليدوي فقط") دون أي استثناء،
    ويبقى بديل HTTP (`discover_via_http`) قابلًا للاستخدام.
    If ``zeroconf`` is not installed, browsing returns ``[]`` with a warning
    log and never raises; the HTTP fallback remains fully functional.

ملاحظة أمنية / Security note:
    كل العمليات الشبكية مغلّفة بـ try/except ولا ترفع استثناءات نحو الواجهة،
    والمهلات قصيرة (1-2 ثانية) حتى لا تتجمد واجهة المستخدم.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Dict, List, Optional

from src.utils.logger import setup_logger

# --------------------------------------------------------------------------- #
# توفر مكتبة zeroconf (اختيارية) — Optional zeroconf availability
# --------------------------------------------------------------------------- #
try:  # pragma: no cover - يتغير حسب البيئة
    from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf  # type: ignore

    ZEROCONF_AVAILABLE = True
except ImportError:  # pragma: no cover
    ServiceBrowser = None  # type: ignore[assignment]
    ServiceInfo = None  # type: ignore[assignment]
    Zeroconf = None  # type: ignore[assignment]
    ZEROCONF_AVAILABLE = False

# --------------------------------------------------------------------------- #
# ثوابت الخدمة / Service constants
# --------------------------------------------------------------------------- #
SERVICE_TYPE = "_erp-standard-joumla._tcp.local."
DEFAULT_SERVICE_NAME = "Standard El-Joumla"
DEFAULT_DISCOVERY_PORT = 8000
HEALTH_PATHS = ("/health", "/api/health")  # نقاط النهاية الحقيقية في src/api/app.py
HTTP_PROBE_TIMEOUT_S = 1.0
MAX_HTTP_CANDIDATES = 64  # سقف المرشحين لإبقاء المسح سريعًا
DEFAULT_BG_INTERVAL_S = 15.0
PING_TIMEOUT_S = 2.0

_DISCOVERED_DEVICES_DDL = """
CREATE TABLE IF NOT EXISTS discovered_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    ip TEXT,
    port INTEGER,
    properties TEXT,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, ip, port)
)
"""


class LanDiscoveryService:
    """اكتشاف أجهزة LAN عبر mDNS + بديل HTTP — LAN device discovery via mDNS + HTTP fallback.

    الخادم (Advertiser): يسجّل هذا الجهاز على الشبكة عبر mDNS.
    العميل (Browser): يكتشف الأجهزة الأخرى بشكل متزامن أو خلفي دوري.

    The server side advertises this machine via mDNS; the client side
    discovers peers synchronously (one-shot) or periodically in a daemon
    thread. Discovered devices can be persisted in a local SQLite registry
    (``discovered_devices``) when a ``db_manager`` is provided.
    """

    def __init__(
        self,
        service_name: str | None = None,
        port: int | None = None,
        logger=None,
        db_manager=None,
    ) -> None:
        """تهيئة الخدمة — Initialise the discovery service.

        Args:
            service_name: اسم الخدمة المعلن (افتراضي "Standard El-Joumla").
            port: المنفذ الافتراضي للـ API عند الإعلان/الاكتشاف (افتراضي 8000).
            logger: مسجّل مخصص (اختياري) — Custom logger.
            db_manager: مدير قاعدة بيانات لحفظ الأجهزة المكتشفة (اختياري).
        """
        self.service_type = SERVICE_TYPE
        self.service_name = service_name or DEFAULT_SERVICE_NAME
        self.port = int(port or DEFAULT_DISCOVERY_PORT)
        self.logger = logger or setup_logger(self.__class__.__name__)
        self.db_manager = db_manager

        self.machine_id = self._build_machine_id()
        self._server_hostname = self._build_server_hostname()

        # حالة الإعلان / advertising state
        self._zeroconf: Any = None
        self._service_info: Any = None
        self._advertising = False

        # حالة التصفح الخلفي / background browsing state
        self.bg_interval_s = DEFAULT_BG_INTERVAL_S
        self._bg_thread: Optional[threading.Thread] = None
        self._bg_stop = threading.Event()

        # إنشاء سجل الأجهزة عند توفر قاعدة بيانات
        if self.db_manager is not None:
            self._ensure_schema()

    # ------------------------------------------------------------------ #
    # الهوية / Identity helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_machine_id() -> str:
        """بناء معرّف ثابت للجهاز من اسم المضيف — Stable machine id from hostname."""
        try:
            hostname = socket.gethostname() or "unknown-host"
        except Exception:
            hostname = "unknown-host"
        digest = hashlib.sha1(hostname.encode("utf-8", "ignore")).hexdigest()[:8]
        return f"{hostname}-{digest}"

    @staticmethod
    def _build_server_hostname() -> str:
        """بناء اسم مضيف mDNS بنمط standard-joumla-XXXX — mDNS host "standard-joumla-XXXX"."""
        try:
            hostname = socket.gethostname() or ""
        except Exception:
            hostname = ""
        suffix = re.sub(r"[^a-zA-Z0-9-]", "", hostname).lower()[:12]
        if not suffix:
            suffix = uuid.uuid5(uuid.NAMESPACE_DNS, "el-joumla").hex[:8]
        return f"standard-joumla-{suffix}"

    def _local_ip(self) -> str:
        """اكتشاف عنوان IP المحلي بشكل سلبي (بدون إرسال حزم) — Passive local IP detection.

        Uses a UDP socket ``connect()`` trick (no packet is actually sent),
        falling back to ``getaddrinfo`` on the local hostname, and finally
        to loopback. Never raises.
        """
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                probe.connect(("8.8.8.8", 80))  # اتصال UDP سلبي — لا تُرسل حزمة
                ip = probe.getsockname()[0]
            finally:
                probe.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = info[4][0]
                if ip and not ip.startswith("127."):
                    return ip
        except Exception:
            pass
        return "127.0.0.1"

    def _local_ipv4s(self) -> List[str]:
        """جميع عناوين IPv4 المحلية (فريدة، بلا loopback/link-local) — All local IPv4s."""
        addresses: List[str] = []
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = str(info[4][0])
                if ip.startswith("127.") or ip.startswith("169.254."):
                    continue
                if ip not in addresses:
                    addresses.append(ip)
        except Exception:
            pass
        passive_ip = self._local_ip()
        if not passive_ip.startswith("127.") and passive_ip not in addresses:
            addresses.insert(0, passive_ip)
        return addresses

    # ------------------------------------------------------------------ #
    # الخادم: الإعلان عبر mDNS / Advertiser (server side)
    # ------------------------------------------------------------------ #
    def start_advertising(self, port: int, properties: dict[str, str] | None = None) -> bool:
        """الإعلان عن هذا الجهاز عبر mDNS — Advertise this device via mDNS.

        Args:
            port: منفذ API هذا الجهاز — This device's API port.
            properties: خصائص إضافية (تُدمج مع الإصدار وmachine_id).

        Returns:
            True عند النجاح، False عند الفشل أو غياب zeroconf (بدون استثناء).
        """
        if not ZEROCONF_AVAILABLE or Zeroconf is None or ServiceInfo is None:
            self.logger.warning("zeroconf غير مثبت — لا يمكن الإعلان عبر mDNS (الوضع اليدوي فقط)")
            return False
        try:
            self.stop_advertising()

            props: Dict[str, str] = {
                "version": "1.0",
                "service": "standard-el-joumla",
                "machine_id": self.machine_id,
            }
            for key, value in (properties or {}).items():
                props[str(key)] = str(value)

            zeroconf_inst = Zeroconf()
            info = ServiceInfo(
                self.service_type,
                f"{self.service_name}.{self.service_type}",
                server=f"{self._server_hostname}.local.",
                addresses=[socket.inet_aton(self._local_ip())],
                port=int(port),
                properties=props,
            )
            zeroconf_inst.register_service(info)
            self._zeroconf = zeroconf_inst
            self._service_info = info
            self._advertising = True
            self.logger.info(
                f"تم الإعلان عبر mDNS: {self.service_name} على {self._local_ip()}:{port} "
                f"(machine_id={self.machine_id})"
            )
            return True
        except Exception as exc:  # لا نرفع أبدًا — never raise outward
            self.logger.warning(f"فشل الإعلان عبر mDNS: {exc}")
            self._zeroconf = None
            self._service_info = None
            self._advertising = False
            return False

    def stop_advertising(self) -> None:
        """إيقاف الإعلان عبر mDNS — Stop advertising (guarded, never raises)."""
        try:
            if self._zeroconf is not None:
                if self._service_info is not None:
                    try:
                        self._zeroconf.unregister_service(self._service_info)
                    except Exception:
                        pass
                try:
                    self._zeroconf.close()
                except Exception:
                    pass
        finally:
            self._zeroconf = None
            self._service_info = None
            self._advertising = False

    @property
    def is_advertising(self) -> bool:
        """هل الإعلان نشط؟ — Whether mDNS advertising is active."""
        return self._advertising

    # ------------------------------------------------------------------ #
    # العميل: التصفح mDNS / Browser (client side)
    # ------------------------------------------------------------------ #
    def start_browsing(self, timeout_ms: int = 3000) -> list[dict]:
        """اكتشاف متزامن للمرة الواحدة عبر mDNS — Synchronous one-shot mDNS browse.

        Args:
            timeout_ms: مهلة الانتظار للأحداث بالمللي ثانية (افتراضي 3000).

        Returns:
            قائمة أجهزة: {name, ip, port, properties(dict), server} — أو [] عند أي فشل.
        """
        return self._discover_via_zeroconf(timeout_ms)

    def _discover_via_zeroconf(self, timeout_ms: int = 3000) -> list[dict]:
        """التنفيذ الفعلي للتصفح مع تدهور رشيق عند غياب zeroconf — Actual browse with graceful degradation."""
        if not ZEROCONF_AVAILABLE or Zeroconf is None or ServiceBrowser is None:
            self.logger.warning("zeroconf غير مثبت — التصفح اليدوي فقط")
            return []

        found_names: List[str] = []
        done = threading.Event()
        zeroconf_inst: Any = None
        try:
            zeroconf_inst = Zeroconf()
        except Exception as exc:
            self.logger.warning(f"فشل تهيئة zeroconf: {exc}")
            return []

        class _Listener:
            """مُصغي يجمع أسماء الخدمات — Listener collecting service names."""

            def add_service(self, zc_ref, type_: str, name: str) -> None:
                if name not in found_names:
                    found_names.append(name)
                done.set()

            def update_service(self, zc_ref, type_: str, name: str) -> None:
                if name not in found_names:
                    found_names.append(name)
                done.set()

            def remove_service(self, zc_ref, type_: str, name: str) -> None:  # noqa: D401
                pass

        devices: List[dict] = []
        try:
            ServiceBrowser(zc=zeroconf_inst, type_=self.service_type, listener=_Listener())
            done.wait(max(0.0, timeout_ms / 1000.0))
            for name in dict.fromkeys(found_names):
                info = None
                try:
                    info = zeroconf_inst.get_service_info(self.service_type, name, timeout=1000)
                except Exception:
                    info = None
                entry = self._service_info_to_dict(name, info)
                if entry:
                    devices.append(entry)
            return devices
        except Exception as exc:
            self.logger.warning(f"فشل التصفح mDNS: {exc}")
            return []
        finally:
            try:
                zeroconf_inst.close()
            except Exception:
                pass

    def _service_info_to_dict(self, name: str, info: Any) -> Optional[dict]:
        """تحويل ServiceInfo إلى قاموس آمن — Convert ServiceInfo to a safe dict."""
        if info is None:
            return None
        try:
            ip: Optional[str] = None
            try:
                parsed = info.parsed_addresses() or []
            except Exception:
                parsed = []
            for addr in parsed:
                if ":" not in addr:  # أول IPv4
                    ip = addr
                    break
            if ip is None:
                raw_addresses = getattr(info, "addresses", None) or []
                if raw_addresses:
                    ip = socket.inet_ntoa(raw_addresses[0])
            if not ip:
                return None

            port = int(getattr(info, "port", 0) or 0)
            server = (getattr(info, "server", "") or "").rstrip(".")

            raw_props = getattr(info, "properties", None) or {}
            properties: Dict[str, str] = {}
            for key, value in raw_props.items():
                try:
                    key_str = key.decode("utf-8", "ignore") if isinstance(key, bytes) else str(key)
                    value_str = (
                        value.decode("utf-8", "ignore") if isinstance(value, bytes) else str(value)
                    )
                    properties[key_str] = value_str
                except Exception:
                    continue

            display_name = name
            if display_name.endswith(self.service_type):
                display_name = display_name[: -len(self.service_type)].rstrip(".")

            return {
                "name": display_name,
                "ip": ip,
                "port": port,
                "properties": properties,
                "server": server,
            }
        except Exception as exc:
            self.logger.debug(f"تعذر تحويل ServiceInfo: {exc}")
            return None

    def start_background_browsing(
        self, callback: Callable[[list[dict]], None], interval_s: float | None = None
    ) -> bool:
        """تصفح دوري في خيط خلفي (daemon) — Periodic browsing in a daemon thread.

        Args:
            callback: يُستدعى بقائمة الأجهزة بعد كل دورة — Invoked with the device list each cycle.
            interval_s: الفاصل بين الدورات (افتراضي 15 ثانية) — Cycle interval (default 15s).

        Returns:
            True إذا بدأ الخيط، False إذا كان يعمل مسبقًا.
        """
        if self._bg_thread is not None and self._bg_thread.is_alive():
            self.logger.debug("التصفح الخلفي يعمل بالفعل")
            return False
        if interval_s is not None:
            self.bg_interval_s = max(0.1, float(interval_s))
        self._bg_stop.clear()

        def _loop() -> None:
            while not self._bg_stop.is_set():
                try:
                    devices = self.start_browsing(timeout_ms=3000)
                except Exception as exc:  # حماية كاملة للحلقة — full loop guard
                    self.logger.warning(f"خطأ غير متوقع في التصفح الخلفي: {exc}")
                    devices = []
                if callback is not None:
                    try:
                        callback(devices)
                    except Exception as exc:
                        self.logger.warning(f"فشل استدعاء مراقب الحضور: {exc}")
                self._bg_stop.wait(self.bg_interval_s)

        self._bg_thread = threading.Thread(
            target=_loop, name="lan-discovery-bg", daemon=True
        )
        self._bg_thread.start()
        self.logger.info(f"بدأ التصفح الخلفي للشبكة المحلية كل {self.bg_interval_s} ثانية")
        return True

    def stop_background_browsing(self) -> None:
        """إيقاف التصفح الخلفي مع انضمام الخيط (مهلة ثانيتان) — Stop bg browsing, join with 2s timeout."""
        self._bg_stop.set()
        thread = self._bg_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._bg_thread = None

    # ------------------------------------------------------------------ #
    # فحص الوصول / TCP presence probe
    # ------------------------------------------------------------------ #
    def ping_device(self, ip: str, port: int, timeout: float = PING_TIMEOUT_S) -> bool:
        """فحص TCP سريع لوصول الجهاز — TCP connect probe; never raises.

        Args:
            ip: عنوان الجهاز. port: منفذ الجهاز. timeout: مهلة الاتصال بالثواني.

        Returns:
            True إذا نجح اتصال TCP، False خلاف ذلك.
        """
        try:
            with socket.create_connection((str(ip), int(port)), timeout=max(0.1, float(timeout))):
                return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # بديل HTTP (بدون zeroconf) / HTTP fallback discovery
    # ------------------------------------------------------------------ #
    def discover_via_http(
        self,
        candidates: list[str] | None = None,
        port: int = DEFAULT_DISCOVERY_PORT,
        timeout: float = HTTP_PROBE_TIMEOUT_S,
    ) -> list[dict]:
        """اكتشاف عبر فحص /health على مرشحين — HTTP /health probing discovery (no zeroconf needed).

        Args:
            candidates: قائمة عناوين IP للفحص (افتراضي: مشتقة من الشبكات المحلية،
                سقفها 64 مرشحًا) — Candidate IPs (default derived from local subnets, capped at 64).
            port: منفذ API المرشحين (افتراضي 8000).
            timeout: مهلة كل طلب HTTP بالثواني (افتراضي 1.0).

        Returns:
            قائمة {name, ip, port, via: "http"} للأجهزة التي استجابت.
        """
        if candidates is None:
            candidates = self._default_http_candidates()
        # السقف 64 مرشحًا — hard cap at 64 candidates
        candidate_ips = [str(c).strip() for c in candidates if c][:MAX_HTTP_CANDIDATES]

        reachable: List[dict] = []
        for candidate in candidate_ips:
            if self._probe_http(candidate, int(port), float(timeout)):
                reachable.append(
                    {
                        "name": self._reverse_name(candidate),
                        "ip": candidate,
                        "port": int(port),
                        "via": "http",
                    }
                )
        return reachable

    def _probe_http(self, ip: str, port: int, timeout: float) -> bool:
        """فحص نقطة نهاية /health باستخدام urllib (stdlib) — Probe /health via stdlib urllib."""
        for path in HEALTH_PATHS:
            url = f"http://{ip}:{port}{path}"
            try:
                request = urllib.request.Request(
                    url,
                    method="GET",
                    headers={"User-Agent": "ElJoumla-LAN-Discovery/1.0"},
                )
                with urllib.request.urlopen(request, timeout=max(0.1, timeout)) as response:
                    return 200 <= getattr(response, "status", 200) < 400
            except urllib.error.HTTPError:
                # استجابة HTTP (حتى 404) تعني أن الجهاز حيّ على الشبكة
                return True
            except Exception:
                # فشل على مستوى الاتصال (رفض/مهلة) — الجهاز غير متاح
                return False
        return False

    def _reverse_name(self, ip: str) -> str:
        """محاولة عكس DNS للحصول على اسم المضيف — Best-effort reverse DNS, falls back to IP."""
        try:
            return socket.gethostbyaddr(ip)[0] or ip
        except Exception:
            return ip

    def _default_http_candidates(self) -> list[str]:
        """توليد مرشحي الشبكات الخاصة المحلية (سقف 64) — Derive private-subnet candidates (cap 64).

        يشبه المسح نطاق /24 لكل عنوان محلي خاص، بدءًا من .1، وبحد أقصى 64
        مرشحًا إجمالًا لتبقى العملية سريعة. بدون استخدام أي subprocess.
        """
        candidates: List[str] = []
        for local_ip in self._local_ipv4s():
            try:
                network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
            except Exception:
                continue
            if not network.is_private:
                continue
            base = local_ip.rsplit(".", 1)[0]
            for host in range(1, 255):
                candidates.append(f"{base}.{host}")
                if len(candidates) >= MAX_HTTP_CANDIDATES:
                    break
            if len(candidates) >= MAX_HTTP_CANDIDATES:
                break
        if not candidates:
            candidates = ["127.0.0.1"]
        return candidates[:MAX_HTTP_CANDIDATES]

    # ------------------------------------------------------------------ #
    # الاكتشاف الكامل / Full discovery pipeline
    # ------------------------------------------------------------------ #
    def discover_full(self, timeout_ms: int = 3000) -> list[dict]:
        """مسار اكتشاف كامل: تصفح ← إزالة تكرار ← فحص وصول ← حفظ — Full pipeline.

        browse → dedupe by (ip, port) → TCP ping (keep reachable only) →
        persist to ``discovered_devices`` (if db_manager) → return.
        """
        devices = self.start_browsing(timeout_ms)

        deduped: Dict[tuple, dict] = {}
        for device in devices:
            key = (device.get("ip"), device.get("port"))
            if key not in deduped:
                deduped[key] = device

        reachable: List[dict] = []
        for device in deduped.values():
            if self.ping_device(str(device.get("ip")), int(device.get("port") or 0)):
                reachable.append(device)

        if reachable and self.db_manager is not None:
            self.save_devices(reachable)
        return reachable

    # ------------------------------------------------------------------ #
    # سجل الأجهزة المكتشفة / Persistence (device registry)
    # ------------------------------------------------------------------ #
    def _ensure_schema(self) -> None:
        """إنشاء جدول discovered_devices (idempotent) — Create registry table idempotently."""
        if self.db_manager is None:
            return
        try:
            self.db_manager.execute_non_query(_DISCOVERED_DEVICES_DDL)
        except Exception as exc:
            self.logger.error(f"فشل إنشاء جدول discovered_devices: {exc}")

    def save_devices(self, devices: list[dict]) -> int:
        """حفظ/تحديث الأجهزة داخل معاملة واحدة (UPSERT) — Upsert devices in a single transaction.

        INSERT ON CONFLICT(name, ip, port) DO UPDATE SET last_seen=CURRENT_TIMESTAMP,
        properties=excluded.properties.

        Returns:
            عدد الصفوف المحفوظة، أو 0 عند الفشل / غياب db_manager.
        """
        if self.db_manager is None or not devices:
            return 0
        saved = 0
        try:
            with self.db_manager.transaction() as cursor:
                for device in devices:
                    name = str(device.get("name") or device.get("ip") or "unknown")
                    ip = str(device.get("ip") or "")
                    port = int(device.get("port") or 0)
                    properties = device.get("properties") if isinstance(
                        device.get("properties"), dict
                    ) else {}
                    properties_json = json.dumps(
                        properties, ensure_ascii=False, default=str
                    )
                    if not ip or port <= 0:
                        continue
                    cursor.execute(
                        """
                        INSERT INTO discovered_devices (name, ip, port, properties)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(name, ip, port) DO UPDATE SET
                            last_seen = CURRENT_TIMESTAMP,
                            properties = excluded.properties
                        """,
                        (name, ip, port, properties_json),
                    )
                    saved += 1
            return saved
        except Exception as exc:
            self.logger.error(f"فشل حفظ الأجهزة المكتشفة: {exc}")
            return 0

    def get_known_devices(self, max_age_minutes: int = 60) -> list[dict]:
        """الأجهزة المكتشفة حديثًا — Recently seen devices only.

        Args:
            max_age_minutes: أقصى عمر بالدقائق (افتراضي 60).

        Returns:
            قائمة {name, ip, port, properties(dict), last_seen} مرتبة تنازليًا بالرؤية الأخيرة.
        """
        if self.db_manager is None:
            return []
        try:
            rows = self.db_manager.fetch_all(
                """
                SELECT name, ip, port, properties, last_seen
                FROM discovered_devices
                WHERE last_seen >= datetime('now', ?)
                ORDER BY last_seen DESC
                """,
                (f"-{int(max_age_minutes)} minutes",),
            )
            devices: List[dict] = []
            for row in rows or []:
                properties = {}
                raw_properties = row.get("properties")
                if raw_properties:
                    try:
                        parsed = json.loads(raw_properties)
                        if isinstance(parsed, dict):
                            properties = parsed
                    except Exception:
                        properties = {}
                devices.append(
                    {
                        "name": row.get("name"),
                        "ip": row.get("ip"),
                        "port": row.get("port"),
                        "properties": properties,
                        "last_seen": row.get("last_seen"),
                    }
                )
            return devices
        except Exception as exc:
            self.logger.error(f"فشل قراءة الأجهزة المعروفة: {exc}")
            return []

    def close(self) -> None:
        """تنظيف كامل — إيقاف الخيوط والإعلان — Full cleanup (threads + advertising)."""
        self.stop_background_browsing()
        self.stop_advertising()
