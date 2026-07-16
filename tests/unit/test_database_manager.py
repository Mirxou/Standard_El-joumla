import os  # noqa: F811
from pathlib import Path  # noqa: F811
from unittest.mock import patch

import pytest

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.core.database_metrics import DatabaseMetrics
from src.database.sqlite_backend import SQLiteBackend


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
        db_path.touch()  # إنشاء ملف وهمي

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
            "backup_dir": str(tmp_path / "backups"),
            "encrypted": True,
            "encryption_key_path": str(tmp_path / "key.key"),
        }

        db_manager = DatabaseManager(db_path=str(db_path), backup_options=backup_options)
        db_manager.initialize()  # لتهيئة خدمة النسخ الاحتياطي

        mock_create_backup.return_value = Path(backup_options["backup_dir"]) / "backup.db.encrypted"

        backup_file = db_manager.backup_database_encrypted()

        assert backup_file is not None
        mock_create_backup.assert_called_once()

    @patch("time.perf_counter")
    def test_slow_query_logging(self, mock_perf_counter, in_memory_db):
        """اختبار تسجيل الاستعلامات البطيئة"""
        # محاكاة استعلام يستغرق وقتاً طويلاً
        mock_perf_counter.side_effect = [0.0, 0.5]  # 500ms duration
        in_memory_db.slow_query_threshold_ms = 100.0  # عتبة 100ms

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
            ("Updated Category", "Test Category"),
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
        assert "file_size_bytes" in info or "page_count" in info

    def test_vacuum_database(self, in_memory_db):
        """اختبار تنظيف قاعدة البيانات"""
        result = in_memory_db.vacuum_database()

        assert result is True

    def test_get_database_info(self, in_memory_db):
        """اختبار الحصول على معلومات قاعدة البيانات"""
        info = in_memory_db.get_database_info()

        assert isinstance(info, dict)
        assert "path" in info or "tables" in info


class TestDatabaseManagerBackendIntegration:
    """اختبارات Database Manager مع Backend Integration"""

    @pytest.fixture
    def temp_db_path(self):
        """مسار قاعدة بيانات مؤقتة"""
        import tempfile

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_backend_integration.db")
        yield db_path
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass

    def test_database_manager_with_backend(self, temp_db_path):
        """اختبار استخدام DatabaseManager مع Backend abstraction"""
        backend = SQLiteBackend(temp_db_path)
        backend.connect()

        db_manager = DatabaseManager(db_path=temp_db_path, backend=backend)
        db_manager.initialize()

        # التحقق من أن Backend متصل
        assert db_manager.backend is not None
        assert db_manager.backend.is_connected is True

        # اختبار استخدام Backend
        db_manager.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        db_manager.connection.commit()

        # استخدام execute_query عبر Backend
        result = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
        assert len(result) == 1

        db_manager.close()

    def test_database_manager_metrics_integration(self, temp_db_path):
        """اختبار دمج Metrics في DatabaseManager"""
        db_manager = DatabaseManager(db_path=temp_db_path)
        db_manager.initialize()

        # التحقق من أن Metrics موجودة
        assert db_manager.metrics is not None
        assert isinstance(db_manager.metrics, DatabaseMetrics)

        # تنفيذ استعلام وتسجيله في Metrics
        db_manager.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        db_manager.connection.commit()

        # استخدام execute_query (يُسجل في Metrics)
        db_manager.execute_query("SELECT * FROM test_table")

        # التحقق من تسجيل الاستعلام في Metrics
        stats = db_manager.metrics.get_statistics()
        assert stats["total_queries"] > 0

        db_manager.close()

    def test_database_manager_slow_query_recording(self, temp_db_path):
        """اختبار تسجيل slow queries في Metrics"""
        db_manager = DatabaseManager(db_path=temp_db_path)
        db_manager.initialize()
        db_manager.slow_query_threshold_ms = 50.0  # عتبة منخفضة للاختبار

        db_manager.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        db_manager.connection.commit()

        # Mock time.perf_counter لمحاكاة استعلام بطيء
        import time

        original_perf_counter = time.perf_counter  # noqa: F841

        call_count = 0

        def mock_perf_counter():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 0.0
            else:
                return 0.1  # 100ms (أكبر من 50ms threshold)

        with patch("time.perf_counter", side_effect=mock_perf_counter):
            db_manager.execute_query("SELECT * FROM test_table")

        # التحقق من تسجيل slow query في Metrics
        slow_queries = db_manager.metrics.get_recent_slow_queries(limit=10)
        assert len(slow_queries) > 0

        db_manager.close()

    def test_database_manager_backend_vs_legacy(self, temp_db_path):
        """اختبار أن Backend والكود القديم يعطيان نفس النتائج"""
        # DatabaseManager مع Backend
        backend = SQLiteBackend(temp_db_path)
        backend.connect()
        db_with_backend = DatabaseManager(db_path=temp_db_path, backend=backend)
        db_with_backend.initialize()

        # DatabaseManager بدون Backend (legacy)
        import tempfile

        temp_dir = tempfile.mkdtemp()
        legacy_db_path = os.path.join(temp_dir, "test_legacy.db")
        db_legacy = DatabaseManager(db_path=legacy_db_path)
        db_legacy.initialize()

        try:
            # إنشاء جدول في كلا الحالتين
            db_with_backend.connection.execute("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT
                )
            """)
            db_with_backend.connection.commit()

            db_legacy.connection.execute("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT
                )
            """)
            db_legacy.connection.commit()

            # إدراج بيانات باستخدام Backend
            id1 = db_with_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("Backend",))

            # إدراج بيانات باستخدام Legacy
            id2 = db_legacy.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("Legacy",))

            # التحقق من أن كلا الحالتين تعملان
            assert id1 == 1
            assert id2 == 1

            # التحقق من البيانات
            results1 = db_with_backend.execute_query("SELECT name FROM test_table WHERE id = ?", (1,))
            results2 = db_legacy.execute_query("SELECT name FROM test_table WHERE id = ?", (1,))

            assert len(results1) == 1
            assert len(results2) == 1
            assert results1[0]["name"] == "Backend"
            assert results2[0]["name"] == "Legacy"

        finally:
            db_with_backend.close()
            db_legacy.close()
            try:
                if os.path.exists(legacy_db_path):
                    os.remove(legacy_db_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception:
                pass
