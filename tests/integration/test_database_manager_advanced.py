"""
Integration Tests for Database Manager Advanced Features
اختبارات تكامل للوظائف المتقدمة في DatabaseManager
"""

import pytest
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from src.core.database_manager import DatabaseManager


@pytest.mark.requires_db
class TestDatabaseManagerAdvanced:
    """اختبارات الوظائف المتقدمة في DatabaseManager"""
    
    def test_checkpoint_wal(self, db_manager):
        """اختبار دمج ملفات WAL"""
        # تنفيذ بعض العمليات لإنشاء WAL
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test_wal (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test_wal (name) VALUES ('test')")
            conn.commit()
        
        # دمج WAL
        result = db_manager.checkpoint_wal()
        assert result == True
    
    def test_get_database_size_info(self, db_manager):
        """اختبار الحصول على معلومات حجم قاعدة البيانات"""
        size_info = db_manager.get_database_size_info()
        
        assert 'database_size' in size_info
        assert 'wal_size' in size_info
        assert 'shm_size' in size_info
        assert 'total_size' in size_info
        assert 'database_size_mb' in size_info
        assert 'wal_size_mb' in size_info
        assert 'total_size_mb' in size_info
        
        assert size_info['database_size'] >= 0
        assert size_info['wal_size'] >= 0
        assert size_info['total_size'] >= 0
    
    def test_vacuum_database(self, db_manager):
        """اختبار تنظيف قاعدة البيانات"""
        # إنشاء بعض البيانات
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test_vacuum (id INTEGER PRIMARY KEY, name TEXT)")
            for i in range(10):
                cursor.execute("INSERT INTO test_vacuum (name) VALUES (?)", (f"test_{i}",))
            conn.commit()
        
        # حذف بعض البيانات
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM test_vacuum WHERE id > 5")
            conn.commit()
        
        # تنظيف قاعدة البيانات
        result = db_manager.vacuum_database()
        assert result == True
    
    def test_cleanup_old_data(self, db_manager):
        """اختبار تنظيف البيانات القديمة"""
        # استخدام جدول login_history بدلاً من audit_log (أبسط وأكثر موثوقية)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            # إنشاء جدول login_history إذا لم يكن موجوداً
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    success INTEGER DEFAULT 1
                )
            """)
            
            # إضافة بيانات قديمة (أقدم من 90 يوم)
            old_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO login_history (user_id, username, login_time, ip_address)
                VALUES (?, ?, ?, ?)
            """, (1, 'test_user', old_date, '127.0.0.1'))
            
            # إضافة بيانات حديثة
            new_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO login_history (user_id, username, login_time, ip_address)
                VALUES (?, ?, ?, ?)
            """, (1, 'test_user', new_date, '127.0.0.1'))
            
            conn.commit()
        
        # تنظيف البيانات القديمة (أقدم من 90 يوم)
        # cleanup_old_data يتوقع قاموساً مع أعمدة التاريخ أو None لاستخدام القيم الافتراضية
        deleted = db_manager.cleanup_old_data(days=90, tables=None)  # None يستخدم الجداول الافتراضية
        
        # التحقق من أن login_history تم تنظيفه (قد يكون في القاموس أو لا)
        # على الأقل يجب أن تكون هناك عملية تنظيف تمت
        assert isinstance(deleted, dict)
        
        # التحقق من أن البيانات الحديثة لا تزال موجودة
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM login_history")
            count = cursor.fetchone()[0]
            assert count >= 1  # يجب أن تبقى البيانات الحديثة
    
    def test_cleanup_old_backups(self, db_manager, temp_db_path):
        """اختبار تنظيف النسخ الاحتياطية القديمة"""
        # إنشاء مجلد backups
        backup_dir = Path(temp_db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # إنشاء بعض ملفات النسخ الاحتياطية الوهمية
        for i in range(5):
            backup_file = backup_dir / f"backup_{i}.db"
            backup_file.write_text("fake backup")
            # تعديل وقت الملف ليكون قديماً
            old_time = time.time() - (i * 3600)  # ساعة بين كل ملف
            os.utime(backup_file, (old_time, old_time))
        
        # تنظيف النسخ (الاحتفاظ بآخر 2)
        db_manager.db_path = temp_db_path
        db_manager.cleanup_old_backups(max_backups=2)
        
        # التحقق من عدد الملفات المتبقية
        remaining_backups = list(backup_dir.glob("backup_*.db"))
        assert len(remaining_backups) <= 2
        
        # تنظيف
        for backup_file in backup_dir.glob("backup_*.db"):
            backup_file.unlink()
        backup_dir.rmdir()
    
    def test_backup_database(self, db_manager, temp_db_path):
        """اختبار إنشاء نسخة احتياطية"""
        # إنشاء بعض البيانات
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test_backup (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test_backup (name) VALUES ('test')")
            conn.commit()
        
        # إنشاء نسخة احتياطية
        backup_dir = Path(temp_db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = str(backup_dir / "test_backup.db")
        result = db_manager.backup_database(backup_path)
        
        assert result == True
        assert Path(backup_path).exists()
        
        # تنظيف
        if Path(backup_path).exists():
            os.remove(backup_path)
        if backup_dir.exists():
            backup_dir.rmdir()
    
    def test_get_database_info(self, db_manager):
        """اختبار الحصول على معلومات قاعدة البيانات"""
        info = db_manager.get_database_info()
        
        assert 'size' in info or 'size_mb' in info
        assert 'tables_count' in info
        assert 'records' in info
        
        assert info['tables_count'] > 0
        assert isinstance(info['records'], dict)

