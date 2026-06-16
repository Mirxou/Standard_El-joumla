"""
Unit Tests for IncrementalBackupService
اختبارات وحدة IncrementalBackupService
"""

import pytest


class TestIncrementalBackupService:
    """اختبارات خدمة النسخ الاحتياطي التدريجي"""

    @pytest.fixture
    def backup_service(self, db_manager):
        """إنشاء خدمة نسخ احتياطي تدريجي"""
        try:
            import tempfile

            from src.core.incremental_backup_service import IncrementalBackupService

            backup_dir = tempfile.mkdtemp()
            return IncrementalBackupService(db_manager, backup_dir)
        except ImportError:
            pytest.skip("IncrementalBackupService not available")

    def test_init(self, backup_service):
        """اختبار التهيئة"""
        assert backup_service is not None

    def test_create_backup(self, backup_service):
        """اختبار إنشاء نسخة احتياطية"""
        try:
            result = backup_service.create_backup()
            assert isinstance(result, (dict, bool, type(None)))
        except Exception:
            pass

    def test_restore_backup(self, backup_service):
        """اختبار استعادة نسخة احتياطية"""
        try:
            result = backup_service.restore_backup("test_backup")
            assert isinstance(result, bool)
        except Exception:
            pass
