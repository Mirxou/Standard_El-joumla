# تأكد من أن مسار src متاح للاستيراد
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])


class MockQApplication:
    """Mock QApplication that serves as a base class but avoids MagicMock inheritance recursion"""

    def __init__(self, *args, **kwargs):
        self._mock_attrs = {}
        # Simulate expected Qt methods that might be called in __init__
        self.primaryScreen = MagicMock()

    def __getattr__(self, name):
        if name not in self._mock_attrs:
            self._mock_attrs[name] = MagicMock()
        return self._mock_attrs[name]

    def exec(self):
        return 0

    @staticmethod
    def instance():
        return None


@pytest.fixture
def app():
    """إنشاء نسخة من التطبيق الرئيسي للاختبار"""
    with patch("PySide6.QtWidgets.QApplication", new=MockQApplication):
        # Patch QMessageBox globally for the app initialization to prevent any popups
        with patch("PySide6.QtWidgets.QMessageBox"):
            # نحتاج لاستيراد main هنا بعد الـ patch
            from main import InventoryManagementApp

        with patch("main.setup_logger", return_value=MagicMock()), patch(
            "main.ConfigManager", return_value=MagicMock()
        ), patch("main.DatabaseManager") as mock_db_manager:
            # محاكاة نجاح تهيئة قاعدة البيانات
            mock_db_manager.return_value.initialize.return_value = True

            app_instance = InventoryManagementApp.__new__(InventoryManagementApp)
            app_instance.logger = MagicMock()
            app_instance.config_manager = MagicMock()
            app_instance.db_manager = None
            app_instance.current_user = None
            app_instance.inventory_service = None
            app_instance.sales_service = None
            app_instance.reports_service = None
            app_instance.user_service = None
            app_instance.payment_service = None
            app_instance.dashboard_service = None
            app_instance.email_service = None
            app_instance.reminder_service = None
            app_instance.task_scheduler = None
            app_instance.notifications_manager = None
            app_instance.recurring_invoice_service = None
            app_instance.marketing_automation_service = None
            app_instance.mfa_service = None
            app_instance.encryption_service = None
            app_instance.support_service = None
            app_instance.api_client = None
            app_instance.hybrid_service = None
            app_instance.main_window = None
            app_instance.reports_window = None
            app_instance.splash_screen = None
            app_instance.init_worker = None
            app_instance.processEvents = MagicMock()
            app_instance.quit = MagicMock()
            yield app_instance


class TestInventoryManagementApp:
    """اختبارات الوحدة للكلاس الرئيسي للتطبيق"""

    def test_app_initialization(self, app):
        """اختبار التهيئة الأولية للتطبيق"""
        assert app is not None
        assert app.config_manager is not None
        assert app.logger is not None

    def test_run_starts_db_initialization(self, app, qtbot):
        """اختبار أن دالة run تبدأ تهيئة قاعدة البيانات"""
        # Ensure database backend is returned so worker is created
        app.config_manager.get_database_backend.return_value = "sqlite"
        app.config_manager.get_database_path.return_value = "test.db"

        # Patch inside the test to handle module reload in fixture
        with patch("main.DatabaseInitWorker") as mock_init_worker, patch.object(
            app, "show_splash_screen"
        ) as mock_splash:  # noqa: F841

            # إعداد mock worker
            mock_worker_instance = mock_init_worker.return_value

            # تشغيل التطبيق
            app.run()

            # التحقق من أن worker تم إنشاؤه وبدء تشغيله
            mock_init_worker.assert_called_once_with(app.db_manager)
            mock_worker_instance.start.assert_called_once()

            # التحقق من ربط الإشارات
            mock_worker_instance.progress_updated.connect.assert_called_with(app.on_init_progress)
            mock_worker_instance.initialization_completed.connect.assert_called_with(app.on_init_completed)

    def test_on_init_completed_success(self, app, qtbot):
        """اختبار ما يحدث بعد نجاح تهيئة قاعدة البيانات"""
        # Setup mocks
        mock_login_instance = MagicMock()
        mock_login_instance.exec.return_value = 1  # QDialog.Accepted
        mock_session = MagicMock()
        mock_session.user_id = 1
        # Set last_activity to now to pass timeout check
        from datetime import datetime

        mock_session.last_activity = datetime.now()
        mock_session.session_id = "test_session_id"

        mock_login_instance.get_current_session.return_value = mock_session

        mock_user_manager = MagicMock()
        mock_user_manager.get_user_by_id.return_value = MagicMock(username="testuser", id=1)

        # Prepare service mocks
        mock_user_service = MagicMock()
        # validate_session must return (True, session) tuple
        mock_user_service.validate_session.return_value = (True, mock_session)
        # security settings for timeout check
        mock_user_service.security_settings.session_timeout_minutes = 30

        # Side effect for initialize_services
        def side_effect_init_services():
            app.user_service = mock_user_service
            app.inventory_service = MagicMock()
            app.sales_service = MagicMock()

        # Patch dependencies
        # Patch QMessageBox specifically if needed, though global one in fixture covers init.
        # But we reload main, so we might need to patch it again inside test scope references?
        # Actually patch('PySide6.QtWidgets.QMessageBox') handles the import globally.

        with patch("main.LoginDialog", return_value=mock_login_instance) as mock_login_dialog, patch(
            "main.MainWindow"
        ) as mock_main_window, patch.object(
            app, "initialize_services", side_effect=side_effect_init_services
        ) as mock_init_services, patch(
            "src.models.user.UserManager", return_value=mock_user_manager
        ):

            with patch.object(app, "_start_session_monitoring"):
                # استدعاء الدالة مباشرة
                app.on_init_completed(True, "Success")

            # Check calls
            mock_login_dialog.assert_called()

            # The logic: if login exec returns Accepted -> calls setup_session -> calls initialize_services
            # If exec returns 1, it should proceed.
            # If it's failing here, it means something in show_login_dialog or setup_session crashed/stopped.
            # But the popup suggested session error.

            # We verify expected calls
            mock_init_services.assert_called_once()

            # Now verify main window was shown
            mock_main_window.assert_called()
            # Since we patched main.MainWindow, app.main_window should hold the instance
            assert app.main_window is not None

    def test_on_init_completed_failure(self, app, qtbot):
        """اختبار ما يحدث عند فشل تهيئة قاعدة البيانات"""
        with patch.object(app, "quit") as mock_quit, patch("main.QMessageBox.critical") as mock_critical:

            # استدعاء الدالة مع حالة فشل
            app.on_init_completed(False, "Database connection failed")

            # التحقق من عرض رسالة خطأ
            mock_critical.assert_called()

            # التحقق من أن التطبيق يحاول الخروج
            mock_quit.assert_called_once()
