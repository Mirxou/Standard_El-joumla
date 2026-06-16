"""
Pytest Configuration and Shared Fixtures
إعدادات pytest والـ fixtures المشتركة
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

project_root = Path(__file__).parent.parent

# Force heavy tests to run in production-like environment by default
os.environ.setdefault("RUN_ALL_TESTS", "1")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Setup mocks before any tests collection
    """
    # Pre-import cryptography to avoid PyO3 Rust module re-init bug
    # (PyO3 modules must be initialized only once; loading during collection
    #  after pytest capture is set up causes ValueError on sys.stdout)
    try:
        import cryptography.fernet  # noqa: F401
        import cryptography.hazmat.bindings._rust  # noqa: F401
    except Exception:
        pass

    # Disable pyqtgraph during tests to prevent OpenGL / C++ segfaults
    # This prevents pyqtgraph.widgets.PlotWidget from crashing in headless/test environments
    sys.modules["pyqtgraph"] = None

    # Mock serial if not present to avoid ImportError in tests
    try:
        pass
    except ImportError:
        from unittest.mock import MagicMock

        mock_serial = MagicMock()
        mock_serial.Serial = MagicMock
        mock_serial.PARITY_NONE = "N"
        mock_serial.STOPBITS_ONE = 1
        mock_serial.EIGHTBITS = 8
        sys.modules["serial"] = mock_serial

    # Mock textblob if not present
    try:
        pass
    except ImportError:
        from unittest.mock import MagicMock

        mock_tb = MagicMock()
        mock_tb.TextBlob = MagicMock
        sys.modules["textblob"] = mock_tb


@pytest.fixture(scope="session")
def project_path():
    """مسار المشروع"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def temp_db_path():
    """مسار قاعدة بيانات مؤقتة للاختبارات"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    # تنظيف بعد الاختبارات
    # 🔥 CRITICAL FIX: انتظار قليل قبل الحذف للتأكد من إغلاق جميع الاتصالات
    import time

    time.sleep(0.1)  # انتظار 100ms

    # محاولة حذف الملفات بشكل آمن
    try:
        if os.path.exists(db_path):
            # محاولة إزالة الملف مباشرة
            try:
                os.remove(db_path)
            except PermissionError:
                # إذا فشل، انتظر قليلاً ثم حاول مرة أخرى
                time.sleep(0.2)
                try:
                    os.remove(db_path)
                except Exception:
                    pass  # تجاهل الخطأ - سيتم حذف المجلد لاحقاً

        # حذف المجلد المؤقت
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                # إذا فشل، تجاهل - سيتم تنظيفه لاحقاً من النظام
                pass
    except Exception:
        pass  # تجاهل أي أخطاء في التنظيف


@pytest.fixture(scope="function")
def db_manager(temp_db_path):
    """مدير قاعدة بيانات للاختبارات"""
    from src.core.database_manager import DatabaseManager

    db = DatabaseManager(db_path=temp_db_path)
    db.initialize()

    yield db

    # إغلاق جميع الاتصالات بشكل صحيح
    try:
        db.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def sample_product_data():
    """بيانات منتج نموذجية للاختبارات"""
    return {
        "name": "منتج اختبار",
        "name_en": "Test Product",
        "barcode": "1234567890123",
        "category_id": 1,
        "unit": "قطعة",
        "cost_price": 100.0,
        "selling_price": 150.0,
        "min_stock": 10,
        "current_stock": 50,
        "description": "منتج للاختبار",
        "is_active": True,
    }


@pytest.fixture(scope="function")
def sample_customer_data():
    """بيانات عميل نموذجية للاختبارات"""
    return {
        "name": "عميل اختبار",
        "email": "test@example.com",
        "phone": "0123456789",
        "address": "عنوان اختبار",
        "is_active": True,
    }


@pytest.fixture(scope="function")
def sample_sale_data():
    """بيانات فاتورة مبيعات نموذجية للاختبارات"""
    return {
        "customer_id": 1,
        "invoice_number": "INV-001",
        "subtotal": 1000.0,
        "discount_amount": 50.0,
        "tax_amount": 142.5,
        "total_amount": 1092.5,
        "payment_method": "cash",
        "status": "confirmed",
    }


@pytest.fixture(scope="function")
def sqlite_backend_fixture(temp_db_path):
    """SQLiteBackend instance للاختبارات"""
    from src.database.sqlite_backend import SQLiteBackend

    backend = SQLiteBackend(temp_db_path)
    backend.connect()
    yield backend
    backend.disconnect()


@pytest.fixture(scope="function")
def database_metrics_fixture():
    """DatabaseMetrics instance للاختبارات"""
    from src.core.database_metrics import DatabaseMetrics

    metrics = DatabaseMetrics(max_history=100)
    yield metrics
    metrics.reset()


@pytest.fixture(scope="function")
def websocket_client_fixture():
    """WebSocketClient mock للاختبارات"""
    from unittest.mock import MagicMock

    from PySide6.QtCore import QObject

    client = MagicMock(spec=QObject)
    client.is_connected = False
    client.worker = None
    client.event_handlers = {}
    return client


@pytest.fixture
def mocker():
    """Lightweight replacement for pytest-mock's fixture."""
    from unittest.mock import MagicMock, Mock, patch

    return SimpleNamespace(MagicMock=MagicMock, Mock=Mock, patch=patch)


@pytest.fixture
def qtbot():
    """Minimal qtbot replacement for synchronous signal tests."""

    class _SignalWaiter:
        def __init__(self, signal):
            self.signal = signal
            self.args = None
            self._handler = None

        def __enter__(self):
            def _handler(*args):
                self.args = list(args)

            self._handler = _handler
            self.signal.connect(_handler)
            return self

        def __exit__(self, exc_type, exc, tb):
            try:
                if self._handler is not None:
                    self.signal.disconnect(self._handler)
            except Exception:
                pass
            if exc_type is None and self.args is None:
                raise AssertionError("Signal was not emitted")
            return False

    class _QtBot:
        def waitSignal(self, signal, timeout=1000):
            return _SignalWaiter(signal)

    return _QtBot()


def _is_heavy_test(nodeid: str) -> bool:
    heavy_indicators = [
        "/ai/",
        "/integration/",
        "/ui/",
        "/stress_",
        "/performance/",
        "/web/",
        "web/__tests__",
    ]
    return any(ind in nodeid for ind in heavy_indicators)


def pytest_collection_modifyitems(config, items):
    # Heavy tests gating: run in production-like environments only
    if os.environ.get("RUN_ALL_TESTS") != "1":
        marker = pytest.mark.skip(reason="Heavy tests are skipped in development. Set RUN_ALL_TESTS=1 to run all.")
        for item in list(items):
            if _is_heavy_test(item.nodeid):
                item.add_marker(marker)

    # Improve mocks to behave as context managers for tests that use 'with Mock()'
    try:
        import unittest.mock as _mock

        def _cm_enter(self):
            return self

        def _cm_exit(self, exc_type, exc, tb):
            return False

        _mock.Mock.__enter__ = _cm_enter  # type: ignore
        _mock.Mock.__exit__ = _cm_exit  # type: ignore
        _mock.MagicMock.__enter__ = _cm_enter  # type: ignore
        _mock.MagicMock.__exit__ = _cm_exit  # type: ignore
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_singletons():
    """إعادة تعيين الـ Singletons لضمان عزل الاختبارات"""
    from src.core.tenant_isolation import reset_tenant_isolation_manager

    reset_tenant_isolation_manager()
    yield


@pytest.fixture(autouse=True)
def cleanup_cache_services():
    """تنظيف خدمات التخزين المؤقت بعد كل اختبار"""
    yield
    # تنظيف أي CacheService instances (تم تعطيل gc.get_objects بسبب البطء)
