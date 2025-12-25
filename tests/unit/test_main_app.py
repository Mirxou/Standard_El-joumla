import pytest
from unittest.mock import MagicMock, patch, ANY
import sys

# تأكد من أن مسار src متاح للاستيراد
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import InventoryManagementApp, DatabaseInitWorker
from PySide6.QtWidgets import QApplication


@pytest.fixture
def app(qtbot):
    """إنشاء نسخة من التطبيق الرئيسي للاختبار"""
    # التأكد من وجود QApplication instance
    q_app = QApplication.instance()
    if not q_app:
        q_app = QApplication(sys.argv)

    # استخدام patch لمنع السلوك الفعلي للخدمات التي تتطلب موارد خارجية
    with patch('main.setup_logger', return_value=MagicMock()):
        with patch('main.ConfigManager', return_value=MagicMock()):
            with patch('main.DatabaseManager') as mock_db_manager:
                # محاكاة نجاح تهيئة قاعدة البيانات
                mock_db_manager.return_value.initialize.return_value = True
                
                app_instance = InventoryManagementApp(sys.argv)
                qtbot.addWidget(app_instance) # qtbot يتتبع الكائن
                yield app_instance


class TestInventoryManagementApp:
    """اختبارات الوحدة للكلاس الرئيسي للتطبيق"""

    def test_app_initialization(self, app):
        """اختبار التهيئة الأولية للتطبيق"""
        assert app is not None
        assert app.config_manager is not None
        assert app.logger is not None
        assert app.main_window is None  # لم يتم إنشاؤها بعد

    @patch('main.DatabaseInitWorker')
    def test_run_starts_db_initialization(self, mock_init_worker, app, qtbot):
        """اختبار أن دالة run تبدأ تهيئة قاعدة البيانات"""
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

    @patch('main.LoginDialog')
    @patch('main.MainWindow')
    def test_on_init_completed_success(self, mock_main_window, mock_login_dialog, app, qtbot):
        """اختبار ما يحدث بعد نجاح تهيئة قاعدة البيانات"""
        # محاكاة نجاح تسجيل الدخول
        mock_login_instance = mock_login_dialog.return_value
        mock_login_instance.exec.return_value = mock_login_dialog.Accepted
        mock_session = MagicMock()
        mock_session.user_id = 1
        mock_login_instance.get_current_session.return_value = mock_session
        
        # محاكاة وجود مستخدم
        mock_user_manager = MagicMock()
        mock_user_manager.get_user_by_id.return_value = MagicMock(username='testuser')
        with patch('main.UserManager', return_value=mock_user_manager):
            # استدعاء الدالة مباشرة
            app.on_init_completed(True, "Success")

        # التحقق من أن الخدمات تم تهيئتها
        assert app.inventory_service is not None
        assert app.sales_service is not None
        
        # التحقق من أن نافذة تسجيل الدخول ظهرت
        mock_login_dialog.assert_called()
        
        # التحقق من أن النافذة الرئيسية ظهرت بعد تسجيل الدخول
        mock_main_window.assert_called()
        assert app.main_window is not None

    def test_on_init_completed_failure(self, app, qtbot):
        """اختبار ما يحدث عند فشل تهيئة قاعدة البيانات"""
        with patch.object(app, 'quit') as mock_quit:
            with patch.object(app, 'show_error_message') as mock_show_error:
                # استدعاء الدالة مع حالة فشل
                app.on_init_completed(False, "Database connection failed")

                # التحقق من عرض رسالة خطأ
                mock_show_error.assert_called_once_with(ANY, "Database connection failed")
                
                # التحقق من أن التطبيق يحاول الخروج
                mock_quit.assert_called_once()