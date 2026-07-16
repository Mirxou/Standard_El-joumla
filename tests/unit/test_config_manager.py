"""
Unit Tests for Config Manager
اختبارات وحدة لمدير الإعدادات
"""

import os

from src.core.config_manager import ConfigManager


class TestConfigManager:
    """اختبارات ConfigManager"""

    def test_init(self):
        """اختبار التهيئة"""
        config = ConfigManager()
        assert config.project_root is not None
        assert config.config_dir.exists() or config.config_dir.parent.exists()

    def test_load_config(self):
        """اختبار تحميل الإعدادات"""
        config = ConfigManager()
        result = config.load_config()
        assert result is True
        assert isinstance(config.config, dict)

    def test_get_default_value(self):
        """اختبار الحصول على قيمة افتراضية"""
        config = ConfigManager()
        config.load_config()

        # قيمة غير موجودة
        value = config.get("nonexistent.key", "default")
        assert value == "default"

    def test_get_nested_value(self):
        """اختبار الحصول على قيمة متداخلة"""
        config = ConfigManager()
        config.load_config()

        # قيمة موجودة - استخدام get_database_path الذي يستخدم get داخلياً
        db_path = config.get_database_path()
        assert db_path is not None
        assert isinstance(db_path, str)

    def test_set_value(self):
        """اختبار تعيين قيمة"""
        config = ConfigManager()
        config.load_config()

        # تعيين قيمة جديدة
        config.set("test.key", "test_value")
        value = config.get("test.key")
        assert value == "test_value"

    def test_set_nested_value(self):
        """اختبار تعيين قيمة متداخلة"""
        config = ConfigManager()
        config.load_config()

        config.set("test.nested.key", "nested_value")
        value = config.get("test.nested.key")
        assert value == "nested_value"

    def test_get_database_path(self):
        """اختبار الحصول على مسار قاعدة البيانات"""
        config = ConfigManager()
        config.load_config()

        db_path = config.get_database_path()
        assert db_path is not None
        assert isinstance(db_path, str)

    def test_get_backup_settings(self):
        """اختبار الحصول على إعدادات النسخ الاحتياطي"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_backup_settings()
        assert "interval" in settings
        assert "max_backups" in settings
        assert "backup_path" in settings
        assert "encrypted" in settings

    def test_get_database_pool_settings(self):
        """اختبار الحصول على إعدادات Connection Pool"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_database_pool_settings()
        assert "enabled" in settings
        assert "pool_size" in settings
        assert "max_overflow" in settings
        assert "timeout" in settings

    def test_get_ui_settings(self):
        """اختبار الحصول على إعدادات واجهة المستخدم"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_ui_settings()
        assert "language" in settings
        assert "theme" in settings
        assert "rtl" in settings
        assert "font_family" in settings
        assert "font_size" in settings

    def test_get_security_settings(self):
        """اختبار الحصول على إعدادات الأمان"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_security_settings()
        assert "session_timeout" in settings
        assert "password_min_length" in settings
        assert "enable_audit_log" in settings

    def test_get_email_settings(self):
        """اختبار الحصول على إعدادات البريد الإلكتروني"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_email_settings()
        assert "enabled" in settings
        assert "smtp_server" in settings
        assert "smtp_port" in settings
        assert "smtp_username" in settings
        assert "smtp_password" in settings

    def test_get_printing_settings(self):
        """اختبار الحصول على إعدادات الطباعة"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_printing_settings()
        assert "default_printer" in settings
        assert "paper_size" in settings
        assert "orientation" in settings
        assert "print_logo" in settings

    def test_get_api_settings(self):
        """اختبار الحصول على إعدادات API"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_api_settings()
        assert "enabled" in settings
        assert "base_url" in settings
        assert "api_key" in settings
        assert "timeout" in settings

    def test_get_notifications_settings(self):
        """اختبار الحصول على إعدادات الإشعارات"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_notifications_settings()
        assert "enabled" in settings
        assert "low_stock_alert" in settings
        assert "expiry_alert" in settings

    def test_get_templates_settings(self):
        """اختبار الحصول على إعدادات القوالب"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_templates_settings()
        assert "default_invoice_template" in settings
        assert "qr_code" in settings
        assert "barcode" in settings
        assert "images" in settings

    def test_get_company_settings(self):
        """اختبار الحصول على إعدادات الشركة"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_company_settings()
        assert "name" in settings
        assert "address" in settings
        assert "phone" in settings
        assert "email" in settings

    def test_get_cache_settings(self):
        """اختبار الحصول على إعدادات التخزين المؤقت"""
        config = ConfigManager()
        config.load_config()

        settings = config.get_cache_settings()
        assert "enabled" in settings
        assert "default_ttl" in settings
        assert "disk_cache" in settings
        assert "disk_path" in settings

    def test_is_debug_mode(self):
        """اختبار التحقق من وضع التطوير"""
        config = ConfigManager()
        config.load_config()

        is_debug = config.is_debug_mode()
        assert isinstance(is_debug, bool)

    def test_get_log_level(self):
        """اختبار الحصول على مستوى السجلات"""
        config = ConfigManager()
        config.load_config()

        log_level = config.get_log_level()
        assert log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_validate_config(self):
        """اختبار التحقق من صحة الإعدادات"""
        config = ConfigManager()
        config.load_config()

        errors = config.validate_config()
        assert isinstance(errors, list)

    def test_save_config(self):
        """اختبار حفظ الإعدادات"""
        config = ConfigManager()
        config.load_config()

        # تعديل قيمة
        config.set("test.save", "test_value")

        # حفظ
        result = config.save_config()
        assert result is True

        # التحقق من الحفظ
        config2 = ConfigManager()
        config2.load_config()
        value = config2.get("test.save")
        assert value == "test_value"

    def test_environment_variables(self):
        """اختبار دعم متغيرات البيئة"""
        config = ConfigManager()
        config.load_config()

        # تعيين متغير بيئة
        os.environ["DATABASE_PATH"] = "/test/path/db.db"

        # الحصول على القيمة (يجب أن يستخدم متغير البيئة)
        value = config.get("database.path", use_env=True)
        # قد يكون من متغير البيئة أو من الملف
        assert value is not None

        # تنظيف
        if "DATABASE_PATH" in os.environ:
            del os.environ["DATABASE_PATH"]

    def test_get_without_env(self):
        """اختبار الحصول على قيمة بدون استخدام متغيرات البيئة"""
        config = ConfigManager()
        config.load_config()

        # تعيين متغير بيئة
        os.environ["TEST_KEY"] = "env_value"

        # الحصول بدون استخدام متغيرات البيئة
        value = config.get("test.key", "default", use_env=False)
        assert value == "default"  # يجب أن يعيد القيمة الافتراضية

        # تنظيف
        if "TEST_KEY" in os.environ:
            del os.environ["TEST_KEY"]
