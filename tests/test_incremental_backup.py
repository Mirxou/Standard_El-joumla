#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار النسخ الاحتياطي التدريجي
"""
import pytest
from pathlib import Path
from src.core.database_manager import DatabaseManager
from src.core.incremental_backup_service import IncrementalBackupService


class TestIncrementalBackup:
    @pytest.fixture
    def db(self, tmp_path):
        """إنشاء قاعدة بيانات مؤقتة للاختبار"""
        db_path = tmp_path / "test_incremental.db"
        db = DatabaseManager(str(db_path))
        db.initialize()
        
        # إضافة بعض البيانات
        db.execute_query(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            ("Test Category 1", "Description 1")
        )
        db.execute_query(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            ("Test Category 2", "Description 2")
        )
        
        return db
    
    @pytest.fixture
    def backup_service(self, db, tmp_path):
        """إنشاء خدمة النسخ الاحتياطي التدريجي"""
        backup_dir = tmp_path / "incremental_backups"
        return IncrementalBackupService(db.db_path, str(backup_dir))
    
    def test_create_full_backup(self, backup_service):
        """اختبار إنشاء نسخة احتياطية كاملة"""
        result = backup_service.create_full_backup("test_full_backup")
        
        assert result['success'] is True
        assert result['backup_type'] == 'full'
        assert result['snapshot_name'] == "test_full_backup"
        assert result['tables_count'] > 0
        
        # التحقق من وجود الملف
        backup_file = Path(result['backup_file'])
        assert backup_file.exists()
    
    def test_create_incremental_backup_without_base(self, backup_service):
        """اختبار إنشاء نسخة تدريجية بدون نسخة أساسية"""
        result = backup_service.create_incremental_backup()
        
        # يجب أن يفشل لعدم وجود نسخة أساسية
        assert result['success'] is False
        assert 'error' in result
    
    def test_create_incremental_backup_with_base(self, backup_service, db):
        """اختبار إنشاء نسخة تدريجية بعد نسخة كاملة"""
        # إنشاء نسخة كاملة أولاً
        full_result = backup_service.create_full_backup("base_backup")
        assert full_result['success'] is True
        
        # تعديل البيانات
        db.execute_query(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            ("New Category", "New Description")
        )
        
        # إنشاء نسخة تدريجية
        incr_result = backup_service.create_incremental_backup()
        
        assert incr_result['success'] is True
        assert incr_result['backup_type'] == 'incremental'
        assert incr_result['base_snapshot'] == 'base_backup'
        assert len(incr_result['changed_tables']) > 0
    
    def test_incremental_backup_no_changes(self, backup_service):
        """اختبار نسخة تدريجية بدون تغييرات"""
        # إنشاء نسخة كاملة
        backup_service.create_full_backup("base_backup")
        
        # محاولة إنشاء نسخة تدريجية بدون تغييرات
        result = backup_service.create_incremental_backup()
        
        assert result['success'] is True
        assert result['snapshot_name'] is None
        assert 'لا توجد تغييرات' in result['message']
    
    def test_list_backups(self, backup_service):
        """اختبار عرض قائمة النسخ الاحتياطية"""
        # إنشاء عدة نسخ
        backup_service.create_full_backup("backup1")
        backup_service.create_full_backup("backup2")
        
        # الحصول على القائمة
        backups = backup_service.list_backups()
        
        assert len(backups) >= 2
        assert any(b['snapshot_name'] == 'backup1' for b in backups)
        assert any(b['snapshot_name'] == 'backup2' for b in backups)
    
    def test_get_backup_chain(self, backup_service, db):
        """اختبار الحصول على سلسلة النسخ الاحتياطية"""
        # إنشاء نسخة كاملة
        backup_service.create_full_backup("full_backup")
        
        # تعديل البيانات وإنشاء نسخة تدريجية
        db.execute_query(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            ("Category 3", "Description 3")
        )
        incr1 = backup_service.create_incremental_backup()
        
        if incr1['success'] and incr1['snapshot_name']:
            # الحصول على السلسلة
            chain = backup_service.get_backup_chain(incr1['snapshot_name'])
            
            assert len(chain) >= 2
            assert chain[0] == 'full_backup'
            assert chain[-1] == incr1['snapshot_name']
    
    def test_restore_from_full_backup(self, backup_service, tmp_path):
        """اختبار الاستعادة من نسخة كاملة"""
        # إنشاء نسخة كاملة
        result = backup_service.create_full_backup("restore_test")
        assert result['success'] is True
        
        # محاولة الاستعادة
        restore_result = backup_service.restore_from_incremental("restore_test")
        
        assert restore_result['success'] is True
        assert restore_result['snapshot_name'] == "restore_test"
    
    def test_calculate_table_checksums(self, backup_service):
        """اختبار حساب checksums للجداول"""
        checksums = backup_service._calculate_table_checksums()
        
        assert isinstance(checksums, dict)
        assert len(checksums) > 0
        
        # التحقق من بنية البيانات
        for table_name, data in checksums.items():
            assert 'checksum' in data
            assert 'row_count' in data
            assert isinstance(data['checksum'], str)
            assert isinstance(data['row_count'], int)
