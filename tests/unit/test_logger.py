"""
Unit Tests for Logger
اختبارات وحدة لنظام السجلات
"""

import logging

import pytest

from src.utils.logger import DatabaseLogger, setup_logger


class TestSetupLogger:
    """اختبارات setup_logger"""

    def test_setup_logger_default(self):
        """اختبار إعداد logger بالافتراضات"""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

    def test_setup_logger_custom_level(self):
        """اختبار إعداد logger بمستوى مخصص"""
        logger = setup_logger("test_logger_debug", log_level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_file_only(self):
        """اختبار إعداد logger للملف فقط"""
        logger = setup_logger("test_file_only", log_to_console=False, log_to_file=True)
        assert logger is not None
        # التحقق من وجود handler للملف
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_setup_logger_console_only(self):
        """اختبار إعداد logger للوحدة فقط"""
        logger = setup_logger("test_console_only", log_to_console=True, log_to_file=False)
        assert logger is not None
        # التحقق من وجود handler للوحدة
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_setup_logger_logging(self):
        """اختبار تسجيل رسائل"""
        logger = setup_logger("test_logging", log_to_file=False, log_to_console=True)

        # تسجيل رسائل بمستويات مختلفة
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # إذا لم يحدث خطأ، فالتسجيل يعمل
        assert True

    def test_setup_logger_multiple_calls(self):
        """اختبار استدعاء setup_logger عدة مرات"""
        logger1 = setup_logger("test_multiple")
        logger2 = setup_logger("test_multiple")

        # يجب أن يعيد نفس الـ logger
        assert logger1 is logger2


@pytest.mark.requires_db
class TestDatabaseLogger:
    """اختبارات DatabaseLogger"""

    @pytest.fixture(autouse=True)
    def setup_user(self, db_manager):
        try:
            db_manager.execute_non_query(
                "INSERT OR IGNORE INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                (1, "test_user", "pbkdf2:sha256:...", "admin")
            )
        except Exception:
            pass

    def test_database_logger_init(self, db_manager):
        """اختبار تهيئة DatabaseLogger"""
        db_logger = DatabaseLogger(db_manager, user_id=1)
        assert db_logger.db_manager is not None
        assert db_logger.user_id == 1
        assert db_logger.logger is not None

    def test_database_logger_log_operation(self, db_manager):
        """اختبار تسجيل عملية في قاعدة البيانات"""
        db_logger = DatabaseLogger(db_manager, user_id=1)

        # تسجيل عملية
        db_logger.log_operation(
            action="CREATE",
            table_name="test_table",
            record_id=1,
            new_values={"name": "test"},
        )

        # التحقق من أن العملية تمت بدون أخطاء
        assert True

    def test_database_logger_log_update(self, db_manager):
        """اختبار تسجيل عملية تحديث"""
        db_logger = DatabaseLogger(db_manager, user_id=1)

        db_logger.log_operation(
            action="UPDATE",
            table_name="test_table",
            record_id=1,
            old_values={"name": "old"},
            new_values={"name": "new"},
        )

        assert True

    def test_database_logger_log_delete(self, db_manager):
        """اختبار تسجيل عملية حذف"""
        db_logger = DatabaseLogger(db_manager, user_id=1)

        db_logger.log_operation(
            action="DELETE",
            table_name="test_table",
            record_id=1,
            old_values={"name": "test"},
        )

        assert True
