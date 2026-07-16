"""
اختبارات شاملة لـ Logger
Comprehensive tests for Logger utility
"""

import logging
import sys
import unittest
from io import StringIO

from src.utils.logger import get_logger, setup_logger


class TestLoggerSetup(unittest.TestCase):
    """اختبارات إعداد Logger"""

    def test_setup_logger_basic(self):
        """اختبار إعداد Logger الأساسي"""
        logger = setup_logger("test_logger")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test_logger")

    def test_setup_logger_with_level(self):
        """اختبار إعداد Logger مع مستوى تسجيل"""
        logger = setup_logger("test_logger", log_level="DEBUG")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logger_file_output(self):
        """اختبار إعداد Logger مع ملف output"""
        logger = setup_logger("test_logger", log_to_file=True)
        self.assertIsNotNone(logger)
        # تحقق من وجود file handler
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        self.assertTrue(has_file_handler)

    def test_get_logger_existing(self):
        """اختبار الحصول على Logger موجود"""
        setup_logger("existing_logger")
        logger = get_logger("existing_logger")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "existing_logger")

    def test_get_logger_nonexisting(self):
        """اختبار الحصول على Logger غير موجود"""
        logger = get_logger("nonexisting_logger")
        self.assertIsNotNone(logger)


class TestLoggerLogging(unittest.TestCase):
    """اختبارات تسجيل الرسائل"""

    def setUp(self):
        """إعداد قبل كل اختبار"""
        self.logger = setup_logger("test_logger", log_level="DEBUG")
        # إضافة stream handler لقراءة المخرجات
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
        self.logger.addHandler(handler)

    def test_logger_debug(self):
        """اختبار تسجيل DEBUG"""
        self.logger.debug("Debug message")
        log_output = self.log_stream.getvalue()
        self.assertIn("DEBUG", log_output)
        self.assertIn("Debug message", log_output)

    def test_logger_info(self):
        """اختبار تسجيل INFO"""
        self.logger.info("Info message")
        log_output = self.log_stream.getvalue()
        self.assertIn("INFO", log_output)
        self.assertIn("Info message", log_output)

    def test_logger_warning(self):
        """اختبار تسجيل WARNING"""
        self.logger.warning("Warning message")
        log_output = self.log_stream.getvalue()
        self.assertIn("WARNING", log_output)
        self.assertIn("Warning message", log_output)

    def test_logger_error(self):
        """اختبار تسجيل ERROR"""
        self.logger.error("Error message")
        log_output = self.log_stream.getvalue()
        self.assertIn("ERROR", log_output)
        self.assertIn("Error message", log_output)

    def test_logger_critical(self):
        """اختبار تسجيل CRITICAL"""
        self.logger.critical("Critical message")
        log_output = self.log_stream.getvalue()
        self.assertIn("CRITICAL", log_output)
        self.assertIn("Critical message", log_output)

    def test_logger_exception(self):
        """اختبار تسجيل الاستثناءات"""
        try:
            raise ValueError("Test error")
        except ValueError:
            self.logger.exception("Exception occurred")

        log_output = self.log_stream.getvalue()
        self.assertIn("ERROR", log_output)
        self.assertIn("Exception occurred", log_output)


class TestLoggerFormatting(unittest.TestCase):
    """اختبارات تنسيق رسائل السجل"""

    def test_logger_with_formatter(self):
        """اختبار Logger مع formatter"""
        logger = setup_logger("test_logger", log_level="INFO")

        # تحقق من وجود handlers
        self.assertGreater(len(logger.handlers), 0)

        # تحقق من أن handlers لديها formatter
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                self.assertIsNotNone(handler.formatter)

    def test_logger_propagate(self):
        """اختبار propagate setting"""
        logger = setup_logger("parent_logger")  # noqa: F841
        child_logger = logging.getLogger("parent_logger.child")

        self.assertTrue(child_logger.propagate)


class TestLoggerMultipleInstances(unittest.TestCase):
    """اختبارات instances متعددة من Logger"""

    def test_multiple_loggers(self):
        """اختبار عدة Logger instances"""
        logger1 = setup_logger("logger1")
        logger2 = setup_logger("logger2")
        logger3 = setup_logger("logger3")

        self.assertIsNotNone(logger1)
        self.assertIsNotNone(logger2)
        self.assertIsNotNone(logger3)

        self.assertNotEqual(logger1.name, logger2.name)
        self.assertNotEqual(logger2.name, logger3.name)

    def test_same_logger_multiple_calls(self):
        """اختبار استدعاء Logger نفسه عدة مرات"""
        logger1 = setup_logger("same_logger")
        logger2 = get_logger("same_logger")

        self.assertEqual(logger1.name, logger2.name)


class TestLoggerErrorHandling(unittest.TestCase):
    """اختبارات معالجة الأخطاء في Logger"""

    def test_logger_with_none_name(self):
        """اختبار Logger مع None كاسم"""
        # هذا قد يؤدي إلى root logger
        logger = setup_logger(None)
        self.assertIsNotNone(logger)

    def test_logger_with_empty_name(self):
        """اختبار Logger مع اسم فارغ"""
        logger = setup_logger("")
        self.assertIsNotNone(logger)

    def test_logger_cleanup(self):
        """اختبار تنظيف Logger handlers"""
        logger = setup_logger("cleanup_test")
        initial_handlers = len(logger.handlers)

        # أضف handler
        from src.utils.logger import NonClosingStreamHandler

        handler = NonClosingStreamHandler(sys.stdout)
        logger.addHandler(handler)

        self.assertGreater(len(logger.handlers), initial_handlers)

        # أزل handler
        logger.removeHandler(handler)
        handler.close()

        self.assertEqual(len(logger.handlers), initial_handlers)


if __name__ == "__main__":
    unittest.main()
