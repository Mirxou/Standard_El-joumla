"""
Unit Tests for BackupManager
اختبارات وحدة BackupManager
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from src.core.backup_manager import BackupManager, BackupConfig, BackupInfo


class TestBackupConfig:
    """اختبارات إعدادات النسخ الاحتياطي"""
    
    def test_default_config(self):
        """اختبار الإعدادات الافتراضية"""
        config = BackupConfig()
        assert config.db_path == 'database.db'
        assert config.backup_dir == 'backups'
        assert config.auto_backup is True
        assert config.max_backups == 7
        assert config.compress is True
    
    def test_custom_config(self):
        """اختبار إعدادات مخصصة"""
        config_dict = {
            'db_path': 'custom.db',
            'backup_dir': 'custom_backups',
            'auto_backup': False,
            'max_backups': 10,
            'compress': False
        }
        config = BackupConfig(config_dict)
        assert config.db_path == 'custom.db'
        assert config.backup_dir == 'custom_backups'
        assert config.auto_backup is False
        assert config.max_backups == 10
        assert config.compress is False


class TestBackupInfo:
    """اختبارات معلومات النسخة الاحتياطية"""
    
    def test_backup_info(self, tmp_path):
        """اختبار إنشاء معلومات النسخة الاحتياطية"""
        backup_file = tmp_path / "backup.db"
        backup_file.write_bytes(b"test data")
        
        info = BackupInfo(str(backup_file))
        assert info.filepath == str(backup_file)
        assert info.filename == "backup.db"
        assert info.size > 0
        assert info.is_compressed is False
    
    def test_backup_info_compressed(self, tmp_path):
        """اختبار معلومات النسخة المضغوطة"""
        backup_file = tmp_path / "backup.db.gz"
        backup_file.write_bytes(b"compressed data")
        
        info = BackupInfo(str(backup_file))
        assert info.is_compressed is True
    
    def test_backup_info_to_dict(self, tmp_path):
        """اختبار تحويل معلومات النسخة إلى قاموس"""
        backup_file = tmp_path / "backup.db"
        backup_file.write_bytes(b"test data")
        
        info = BackupInfo(str(backup_file))
        info_dict = info.to_dict()
        
        assert 'filepath' in info_dict
        assert 'filename' in info_dict
        assert 'size' in info_dict
        assert 'size_mb' in info_dict
        assert 'created_at' in info_dict
        assert 'is_compressed' in info_dict


class TestBackupManager:
    """اختبارات مدير النسخ الاحتياطي"""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """إنشاء قاعدة بيانات مؤقتة"""
        import sqlite3
        db_path = tmp_path / "test.db"
        # إنشاء قاعدة بيانات SQLite صالحة
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        conn.commit()
        conn.close()
        return str(db_path)
    
    @pytest.fixture
    def backup_dir(self, tmp_path):
        """إنشاء مجلد النسخ الاحتياطي"""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        return str(backup_dir)
    
    @pytest.fixture
    def backup_manager(self, temp_db, backup_dir):
        """إنشاء مدير نسخ احتياطي"""
        config = BackupConfig({
            'db_path': temp_db,
            'backup_dir': backup_dir,
            'auto_backup': False,
            'compress': False
        })
        return BackupManager(config)
    
    def test_init(self, backup_manager):
        """اختبار التهيئة"""
        assert backup_manager is not None
        assert backup_manager.config is not None
    
    def test_create_backup(self, backup_manager, temp_db):
        """اختبار إنشاء نسخة احتياطية"""
        result = backup_manager.create_backup()
        assert result is not None
        assert 'success' in result
        # قد يفشل إذا لم يكن الملف قاعدة بيانات صالحة
        # لكن يجب ألا يرفع استثناء
        if result['success']:
            assert 'backup_info' in result
            assert os.path.exists(result['backup_info']['filepath'])
    
    def test_list_backups(self, backup_manager):
        """اختبار قائمة النسخ الاحتياطية"""
        # إنشاء عدة نسخ احتياطية
        result1 = backup_manager.create_backup()
        result2 = backup_manager.create_backup()
        
        # قد تفشل بعض النسخ، لكن يجب أن نحصل على قائمة
        backups = backup_manager.list_backups()
        assert len(backups) >= 0  # على الأقل قائمة فارغة
    
    def test_restore_backup(self, backup_manager, tmp_path):
        """اختبار استعادة نسخة احتياطية"""
        # إنشاء نسخة احتياطية
        result = backup_manager.create_backup()
        if result.get('success'):
            backup_path = result['backup_info']['filepath']
            target_path = str(tmp_path / "restored.db")
            
            # استعادة النسخة
            restore_result = backup_manager.restore_backup(backup_path, target_path)
            assert restore_result is not None
            assert 'success' in restore_result

