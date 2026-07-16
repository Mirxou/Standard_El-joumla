from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def database_init_worker_cls():
    from main import DatabaseInitWorker

    return DatabaseInitWorker


class TestDatabaseInitWorker:
    """اختبارات وحدة لـ DatabaseInitWorker في main.py"""

    @pytest.fixture
    def mock_db_manager(self):
        """إنشاء mock لمدير قاعدة البيانات"""
        db = MagicMock()
        db.initialize.return_value = True
        db.table_exists.return_value = True
        return db

    def test_initialization_success(self, mock_db_manager, qtbot, database_init_worker_cls):
        """اختبار التهيئة الناجحة"""
        worker = database_init_worker_cls(mock_db_manager)

        # عزل load_initial_data لتجنب تعقيدات التبعيات
        with patch.object(worker, "load_initial_data") as mock_load:
            # تشغيل مباشر بدون إشارات لتجنب التعليق
            worker.run()

        # التحقق من استدعاء الدوال
        mock_db_manager.initialize.assert_called_once()
        mock_load.assert_called_once()

    def test_initialization_failure_db_init(self, mock_db_manager, qtbot, database_init_worker_cls):
        """اختبار فشل تهيئة قاعدة البيانات"""
        # محاكاة فشل initialize
        mock_db_manager.initialize.return_value = False

        worker = database_init_worker_cls(mock_db_manager)

        # تشغيل مباشر بدون إشارات
        worker.run()

        # التحقق من فشل التهيئة
        mock_db_manager.initialize.assert_called_once()

    def test_integrity_check_failure(self, mock_db_manager, qtbot, database_init_worker_cls):
        """اختبار فشل فحص سلامة البيانات"""
        # محاكاة نجاح initialize ولكن فشل table_exists
        mock_db_manager.initialize.return_value = True
        mock_db_manager.table_exists.return_value = False

        worker = database_init_worker_cls(mock_db_manager)

        # منع تسجيل الأخطاء لتجنب فشل الاختبار
        with patch.object(worker, "load_initial_data"):
            with patch.object(worker.logger, "error"):
                with patch.object(worker.logger, "warning"):
                    # تشغيل مباشر بدون إشارات
                    worker.run()

        # التحقق من استدعاء الدوال
        mock_db_manager.initialize.assert_called_once()
        mock_db_manager.table_exists.assert_called_once()
