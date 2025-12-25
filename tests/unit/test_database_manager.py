import pytest
import sqlite3
from unittest.mock import MagicMock, patch, mock_open
import sys
from pathlib import Path
import os

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.exceptions import DatabaseException

@pytest.fixture
def in_memory_db():
    """إنشاء مدير قاعدة بيانات في الذاكرة للاختبار السريع"""
    # استخدام :memory: لإنشاء قاعدة بيانات مؤقتة
    db_manager = DatabaseManager(db_path=":memory:")
    # التهيئة ضرورية لإنشاء الجداول
    db_manager.initialize()
    yield db_manager
    # التنظيف بعد الاختبار
    db_manager.close()

class TestDatabaseManager:
    """اختبارات وحدة لمدير قاعدة البيانات"""

    def test_initialization(self, in_memory_db):
        """اختبار التهيئة الأولية لقاعدة البيانات في الذاكرة"""
        assert in_memory_db.connection is not None
        # التحقق من أن الجداول الأساسية تم إنشاؤها
        assert in_memory_db.table_exists("products")
        assert in_memory_db.table_exists("sales")
        assert in_memory_db.table_exists("users")

    def test_table_exists(self, in_memory_db):
        """اختبار دالة التحقق من وجود جدول"""
        assert in_memory_db.table_exists("products") is True
        assert in_memory_db.table_exists("non_existent_table") is False

    def test_execute_insert_returns_id(self, in_memory_db):
        """اختبار أن دالة execute_insert تعيد ID صحيح"""
        query = "INSERT INTO categories (name) VALUES (?)"
        params = ("فئة اختبار",)
        
        # استخدام execute_insert
        new_id = in_memory_db.execute_insert(query, params)
        
        assert new_id is not None
        assert new_id > 0
        
        # التحقق من أن البيانات تم إدراجها فعلاً
        result = in_memory_db.fetch_one("SELECT name FROM categories WHERE id = ?", (new_id,))
        assert result is not None
        assert result[0] == "فئة اختبار"

    def test_add_column_if_missing(self, in_memory_db):
        """اختبار إضافة عمود جديد إذا لم يكن موجوداً"""
        table_name = "products"
        column_name = "test_column"
        column_def = "TEXT"
        
        # التأكد من أن العمود غير موجود
        columns_before = in_memory_db._get_table_columns(table_name)
        assert column_name not in columns_before
        
        # إضافة العمود
        in_memory_db._add_column_if_missing(table_name, column_name, column_def)
        
        # التأكد من أن العمود تمت إضافته
        columns_after = in_memory_db._get_table_columns(table_name)
        assert column_name in columns_after

    @patch("shutil.copy2")
    @patch("os.path.exists", return_value=True)
    def test_backup_database(self, mock_exists, mock_copy, tmp_path):
        """اختبار النسخ الاحتياطي (مع عزل نظام الملفات)"""
        db_path = tmp_path / "test.db"
        backup_path = tmp_path / "backup.db"
        db_path.touch() # إنشاء ملف وهمي
        
        db_manager = DatabaseManager(db_path=str(db_path))
        
        success = db_manager.backup_database(backup_path=str(backup_path))
        
        assert success is True
        mock_copy.assert_called_once_with(str(db_path), str(backup_path))

    @patch("src.core.database_manager.EncryptedBackupService.create_backup")
    def test_encrypted_backup(self, mock_create_backup, tmp_path):
        """اختبار النسخ الاحتياطي المشفر"""
        db_path = tmp_path / "test.db"
        db_path.touch()
        
        backup_options = {
            'backup_dir': str(tmp_path / "backups"),
            'encrypted': True,
            'encryption_key_path': str(tmp_path / "key.key")
        }
        
        db_manager = DatabaseManager(db_path=str(db_path), backup_options=backup_options)
        db_manager.initialize() # لتهيئة خدمة النسخ الاحتياطي
        
        mock_create_backup.return_value = Path(backup_options['backup_dir']) / "backup.db.encrypted"
        
        backup_file = db_manager.backup_database_encrypted()
        
        assert backup_file is not None
        mock_create_backup.assert_called_once()

    @patch("time.perf_counter")
    def test_slow_query_logging(self, mock_perf_counter, in_memory_db):
        """اختبار تسجيل الاستعلامات البطيئة"""
        # محاكاة استعلام يستغرق وقتاً طويلاً
        mock_perf_counter.side_effect = [0.0, 0.5] # 500ms duration
        in_memory_db.slow_query_threshold_ms = 100.0 # عتبة 100ms
        
        # تنفيذ استعلام
        in_memory_db.fetch_all("SELECT * FROM products")
        
        # التحقق من أن الاستعلام تم تسجيله
        log_entry = in_memory_db.fetch_one("SELECT query_text, duration_ms FROM slow_queries")
        
        assert log_entry is not None
        assert "SELECT * FROM products" in log_entry[0]
        assert log_entry[1] > 100.0
    
    def test_execute_non_query(self, in_memory_db):
        """اختبار تنفيذ استعلام غير query (UPDATE/DELETE)"""
        # إنشاء سجل أولاً
        in_memory_db.execute_insert("INSERT INTO categories (name) VALUES (?)", ("Test Category",))
        
        # تحديث السجل
        result = in_memory_db.execute_non_query(
            "UPDATE categories SET name = ? WHERE name = ?",
            ("Updated Category", "Test Category")
        )
        
        assert result > 0
        
        # التحقق من التحديث
        updated = in_memory_db.fetch_one("SELECT name FROM categories WHERE name = ?", ("Updated Category",))
        assert updated is not None
        assert updated[0] == "Updated Category"
    
    def test_fetch_all(self, in_memory_db):
        """اختبار جلب جميع النتائج"""
        # إضافة عدة سجلات
        for i in range(3):
            in_memory_db.execute_insert("INSERT INTO categories (name) VALUES (?)", (f"Category {i}",))
        
        results = in_memory_db.fetch_all("SELECT name FROM categories ORDER BY id")
        
        assert len(results) >= 3
        assert all(len(row) == 1 for row in results)
    
    def test_execute_scalar(self, in_memory_db):
        """اختبار تنفيذ استعلام يعيد قيمة واحدة"""
        in_memory_db.execute_insert("INSERT INTO categories (name) VALUES (?)", ("Test",))
        
        count = in_memory_db.execute_scalar("SELECT COUNT(*) FROM categories")
        
        assert count > 0
    
    def test_get_last_insert_id(self, in_memory_db):
        """اختبار الحصول على آخر ID تم إدراجه"""
        new_id = in_memory_db.execute_insert("INSERT INTO categories (name) VALUES (?)", ("Test ID",))
        
        last_id = in_memory_db.get_last_insert_id()
        
        assert last_id == new_id
    
    def test_checkpoint_wal(self, in_memory_db):
        """اختبار نقطة التحقق WAL"""
        result = in_memory_db.checkpoint_wal()
        
        assert result is True
    
    def test_get_database_size_info(self, in_memory_db):
        """اختبار الحصول على معلومات حجم قاعدة البيانات"""
        info = in_memory_db.get_database_size_info()
        
        assert isinstance(info, dict)
        assert 'file_size_bytes' in info or 'page_count' in info
    
    def test_vacuum_database(self, in_memory_db):
        """اختبار تنظيف قاعدة البيانات"""
        result = in_memory_db.vacuum_database()
        
        assert result is True
    
    def test_get_database_info(self, in_memory_db):
        """اختبار الحصول على معلومات قاعدة البيانات"""
        info = in_memory_db.get_database_info()
        
        assert isinstance(info, dict)
        assert 'path' in info or 'tables' in info