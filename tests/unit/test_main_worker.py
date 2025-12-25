import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject

# استيراد الكلاس من main.py
from main import DatabaseInitWorker

class TestDatabaseInitWorker:
    """اختبارات وحدة لـ DatabaseInitWorker في main.py"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """إنشاء mock لمدير قاعدة البيانات"""
        db = MagicMock()
        db.initialize.return_value = True
        db.table_exists.return_value = True
        return db

    def test_initialization_success(self, mock_db_manager, qtbot):
        """اختبار التهيئة الناجحة"""
        worker = DatabaseInitWorker(mock_db_manager)
        
        # مراقبة الإشارة initialization_completed
        with qtbot.waitSignal(worker.initialization_completed, timeout=2000) as blocker:
            # عزل load_initial_data لتجنب تعقيدات التبعيات
            with patch.object(worker, 'load_initial_data') as mock_load:
                worker.run()
        
        # التحقق من النتائج
        assert blocker.args[0] is True  # success
        assert "تم تهيئة قاعدة البيانات بنجاح" in blocker.args[1]
        
        # التحقق من استدعاء الدوال
        mock_db_manager.initialize.assert_called_once()
        mock_load.assert_called_once()

    def test_initialization_failure_db_init(self, mock_db_manager, qtbot):
        """اختبار فشل تهيئة قاعدة البيانات"""
        # محاكاة فشل initialize
        mock_db_manager.initialize.return_value = False
        
        worker = DatabaseInitWorker(mock_db_manager)
        
        with qtbot.waitSignal(worker.initialization_completed) as blocker:
            worker.run()
            
        assert blocker.args[0] is False
        assert "فشل في تهيئة" in blocker.args[1]

    def test_integrity_check_failure(self, mock_db_manager, qtbot):
        """اختبار فشل فحص سلامة البيانات"""
        # محاكاة نجاح initialize ولكن فشل table_exists
        mock_db_manager.initialize.return_value = True
        mock_db_manager.table_exists.return_value = False
        
        worker = DatabaseInitWorker(mock_db_manager)
        
        with patch.object(worker, 'load_initial_data'):
            with qtbot.waitSignal(worker.initialization_completed) as blocker:
                worker.run()
        
        assert blocker.args[0] is False
        assert "فشل في التحقق" in blocker.args[1]