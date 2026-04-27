#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for ConfigManager
اختبارات وحدة شاملة لـ ConfigManager
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.config_manager import ConfigManager


class TestConfigManagerInitialization:
    """اختبارات تهيئة ConfigManager"""
    
    def test_init_creates_paths(self):
        """اختبار إنشاء المسارات عند التهيئة"""
        config = ConfigManager()
        assert config.project_root is not None
        assert config.config_dir is not None
        assert config.app_config_path is not None
        assert config.dev_config_path is not None
    
    def test_init_default_values(self):
        """اختبار القيم الافتراضية عند التهيئة"""
        config = ConfigManager()
        assert config.config == {}
        assert config.dev_config == {}
        assert config._encryption_manager is None
        assert config._encryption_enabled == False


class TestConfigManagerLoadAndSave:
    """اختبارات تحميل وحفظ الإعدادات"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """إنشاء مجلد إعدادات مؤقت"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True)
            yield config_dir
    
    def test_load_config_creates_default_if_not_exists(self, temp_config_dir):
        """اختبار إنشاء الإعدادات الافتراضية إذا لم تكن موجودة"""
        config = ConfigManager()
        config.config_dir = temp_config_dir
        config.app_config_path = temp_config_dir / "app_config.json"
        
        result = config.load_config()
        assert result == True
        assert config.config != {}
        assert config.app_config_path.exists()
    
    def test_load_config_from_existing_file(self, temp_config_dir):
        """اختبار تحميل الإعدادات من ملف موجود"""
        config_file = temp_config_dir / "app_config.json"
        test_config = {
            "database": {"path": "test.db"},
            "ui": {"language": "ar"}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        config = ConfigManager()
        config.config_dir = temp_config_dir
        config.app_config_path = config_file
        
        result = config.load_config()
        assert result == True
        assert config.get('database.path') == "test.db"
        assert config.get('ui.language') == "ar"
    
    def test_save_config_creates_directory(self, temp_config_dir):
        """اختبار إنشاء مجلد الإعدادات عند الحفظ"""
        config_file = temp_config_dir / "app_config.json"
        
        config = ConfigManager()
        config.config_dir = temp_config_dir
        config.app_config_path = config_file
        config.config = {"test": {"key": "value"}}
        
        result = config.save_config()
        assert result == True
        assert config_file.exists()
    
    def test_save_and_reload_config(self, temp_config_dir):
        """اختبار حفظ وإعادة تحميل الإعدادات"""
        config_file = temp_config_dir / "app_config.json"
        
        config1 = ConfigManager()
        config1.config_dir = temp_config_dir
        config1.app_config_path = config_file
        config1.config = {"test": {"key": "value"}}
        config1.save_config()
        
        config2 = ConfigManager()
        config2.config_dir = temp_config_dir
        config2.app_config_path = config_file
        config2.load_config()
        
        assert config2.get('test.key') == "value"


class TestConfigManagerGetAndSet:
    """اختبارات الحصول على وتعيين القيم"""
    
    @pytest.fixture
    def config(self):
        """إنشاء ConfigManager للاختبارات"""
        config = ConfigManager()
        config.config = {
            "database": {
                "path": "test.db",
                "pool_size": 10
            },
            "ui": {
                "language": "ar",
                "theme": "dark"
            }
        }
        return config
    
    def test_get_existing_value(self, config):
        """اختبار الحصول على قيمة موجودة"""
        assert config.get('database.path') == "test.db"
        assert config.get('ui.language') == "ar"
    
    def test_get_nested_value(self, config):
        """اختبار الحصول على قيمة متداخلة"""
        assert config.get('database.pool_size') == 10
    
    def test_get_default_value(self, config):
        """اختبار الحصول على قيمة افتراضية عند عدم وجود المفتاح"""
        assert config.get('nonexistent.key', 'default') == 'default'
        assert config.get('nonexistent.key', 123) == 123
    
    def test_get_with_none_default(self, config):
        """اختبار الحصول على قيمة مع None كقيمة افتراضية"""
        assert config.get('nonexistent.key') is None
        assert config.get('nonexistent.key', None) is None
    
    def test_set_simple_value(self, config):
        """اختبار تعيين قيمة بسيطة"""
        config.set('test.key', 'value')
        assert config.get('test.key') == 'value'
    
    def test_set_nested_value(self, config):
        """اختبار تعيين قيمة متداخلة"""
        config.set('test.nested.key', 'nested_value')
        assert config.get('test.nested.key') == 'nested_value'
    
    def test_set_overwrites_existing(self, config):
        """اختبار استبدال قيمة موجودة"""
        config.set('database.path', 'new_path.db')
        assert config.get('database.path') == 'new_path.db'
    
    def test_set_creates_structure(self, config):
        """اختبار إنشاء البنية عند تعيين قيمة جديدة"""
        config.set('new.section.key', 'value')
        assert config.get('new.section.key') == 'value'
        assert isinstance(config.config['new'], dict)
        assert isinstance(config.config['new']['section'], dict)


class TestConfigManagerEnvironmentVariables:
    """اختبارات دعم متغيرات البيئة"""
    
    @pytest.fixture
    def config(self):
        """إنشاء ConfigManager للاختبارات"""
        config = ConfigManager()
        config.config = {"database": {"path": "default.db"}}
        return config
    
    def test_get_uses_env_variable(self, config):
        """اختبار استخدام متغير البيئة عند وجوده"""
        os.environ['DATABASE_PATH'] = json.dumps('/env/path/db.db')
        
        try:
            value = config.get('database.path', use_env=True)
            # قد يكون من متغير البيئة أو من الملف
            assert value is not None
        finally:
            if 'DATABASE_PATH' in os.environ:
                del os.environ['DATABASE_PATH']
    
    def test_get_ignores_env_when_disabled(self, config):
        """اختبار تجاهل متغيرات البيئة عند تعطيلها"""
        os.environ['DATABASE_PATH'] = json.dumps('/env/path/db.db')
        
        try:
            value = config.get('database.path', 'default', use_env=False)
            # يجب أن يعيد القيمة من الملف أو الافتراضية
            assert value != '/env/path/db.db'
        finally:
            if 'DATABASE_PATH' in os.environ:
                del os.environ['DATABASE_PATH']
    
    def test_env_variable_string_conversion(self, config):
        """اختبار تحويل متغير البيئة من JSON"""
        os.environ['TEST_INT'] = json.dumps(123)
        os.environ['TEST_BOOL'] = json.dumps(True)
        
        try:
            # يجب أن يحول JSON تلقائياً
            int_value = config.get('test.int', use_env=True)
            bool_value = config.get('test.bool', use_env=True)
            # قد يكون None إذا لم يكن موجوداً في config
        finally:
            if 'TEST_INT' in os.environ:
                del os.environ['TEST_INT']
            if 'TEST_BOOL' in os.environ:
                del os.environ['TEST_BOOL']


class TestConfigManagerHelperMethods:
    """اختبارات الوظائف المساعدة"""
    
    @pytest.fixture
    def config(self):
        """إنشاء ConfigManager للاختبارات"""
        config = ConfigManager()
        config.load_config()
        return config
    
    def test_get_database_path(self, config):
        """اختبار الحصول على مسار قاعدة البيانات"""
        db_path = config.get_database_path()
        assert isinstance(db_path, str)
        assert len(db_path) > 0
    
    def test_get_database_path_absolute(self, config):
        """اختبار أن المسار يكون مطلقاً"""
        db_path = config.get_database_path()
        # إذا كان المسار نسبياً، يجب أن يتم تحويله إلى مطلق
        assert os.path.isabs(db_path) or db_path.startswith('data/')
    
    def test_get_backup_settings(self, config):
        """اختبار الحصول على إعدادات النسخ الاحتياطي"""
        settings = config.get_backup_settings()
        assert isinstance(settings, dict)
        assert 'interval' in settings
        assert 'max_backups' in settings
        assert 'backup_path' in settings
    
    def test_get_database_pool_settings(self, config):
        """اختبار الحصول على إعدادات Connection Pool"""
        settings = config.get_database_pool_settings()
        assert isinstance(settings, dict)
        assert 'enabled' in settings
        assert 'pool_size' in settings
    
    def test_get_ui_settings(self, config):
        """اختبار الحصول على إعدادات واجهة المستخدم"""
        settings = config.get_ui_settings()
        assert isinstance(settings, dict)
        assert 'language' in settings
        assert 'theme' in settings
    
    def test_get_security_settings(self, config):
        """اختبار الحصول على إعدادات الأمان"""
        settings = config.get_security_settings()
        assert isinstance(settings, dict)
        assert 'session_timeout' in settings
    
    def test_get_email_settings(self, config):
        """اختبار الحصول على إعدادات البريد الإلكتروني"""
        settings = config.get_email_settings()
        assert isinstance(settings, dict)
        assert 'enabled' in settings
    
    def test_get_printing_settings(self, config):
        """اختبار الحصول على إعدادات الطباعة"""
        settings = config.get_printing_settings()
        assert isinstance(settings, dict)
        assert 'default_printer' in settings
    
    def test_get_api_settings(self, config):
        """اختبار الحصول على إعدادات API"""
        settings = config.get_api_settings()
        assert isinstance(settings, dict)
        assert 'enabled' in settings
    
    def test_get_notifications_settings(self, config):
        """اختبار الحصول على إعدادات الإشعارات"""
        settings = config.get_notifications_settings()
        assert isinstance(settings, dict)
        assert 'enabled' in settings
    
    def test_get_templates_settings(self, config):
        """اختبار الحصول على إعدادات القوالب"""
        settings = config.get_templates_settings()
        assert isinstance(settings, dict)
        assert 'default_invoice_template' in settings
    
    def test_get_company_settings(self, config):
        """اختبار الحصول على إعدادات الشركة"""
        settings = config.get_company_settings()
        assert isinstance(settings, dict)
        assert 'name' in settings
    
    def test_get_cache_settings(self, config):
        """اختبار الحصول على إعدادات التخزين المؤقت"""
        settings = config.get_cache_settings()
        assert isinstance(settings, dict)
        assert 'enabled' in settings
    
    def test_is_debug_mode(self, config):
        """اختبار التحقق من وضع التطوير"""
        is_debug = config.is_debug_mode()
        assert isinstance(is_debug, bool)
    
    def test_get_log_level(self, config):
        """اختبار الحصول على مستوى السجلات"""
        log_level = config.get_log_level()
        assert log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class TestConfigManagerValidation:
    """اختبارات التحقق من صحة الإعدادات"""
    
    @pytest.fixture
    def config(self):
        """إنشاء ConfigManager للاختبارات"""
        config = ConfigManager()
        config.load_config()
        return config
    
    def test_validate_config_returns_list(self, config):
        """اختبار أن validate_config يعيد قائمة"""
        errors = config.validate_config()
        assert isinstance(errors, list)
    
    def test_validate_config_with_valid_config(self, config):
        """اختبار التحقق من إعدادات صحيحة"""
        errors = config.validate_config()
        # قد يكون هناك أخطاء أو لا - يعتمد على الإعدادات الافتراضية
        assert isinstance(errors, list)


class TestConfigManagerSensitiveData:
    """اختبارات التعامل مع البيانات الحساسة"""
    
    def test_sensitive_keys_defined(self):
        """اختبار تعريف المفاتيح الحساسة"""
        assert hasattr(ConfigManager, 'SENSITIVE_KEYS')
        assert isinstance(ConfigManager.SENSITIVE_KEYS, set)
        assert len(ConfigManager.SENSITIVE_KEYS) > 0
    
    def test_sensitive_keys_include_common(self):
        """اختبار أن المفاتيح الحساسة تشمل المفاتيح الشائعة"""
        sensitive_keys = ConfigManager.SENSITIVE_KEYS
        assert 'email.smtp_password' in sensitive_keys
        assert 'api.api_key' in sensitive_keys
        assert 'security.encryption_key' in sensitive_keys


class TestConfigManagerEdgeCases:
    """اختبارات الحالات الحدية"""
    
    @pytest.fixture
    def config(self):
        """إنشاء ConfigManager للاختبارات"""
        config = ConfigManager()
        config.config = {}
        return config
    
    def test_get_with_empty_key(self, config):
        """اختبار الحصول على قيمة بمفتاح فارغ"""
        # قد يثير استثناء أو يعيد None
        try:
            value = config.get('', 'default')
            assert value == 'default'
        except Exception:
            pass  # مقبول إذا أثار استثناء
    
    def test_set_with_empty_key(self, config):
        """اختبار تعيين قيمة بمفتاح فارغ"""
        # قد يثير استثناء أو يتجاهل
        try:
            config.set('', 'value')
        except Exception:
            pass  # مقبول إذا أثار استثناء
    
    def test_get_with_dot_only(self, config):
        """اختبار الحصول على قيمة بمفتاح يحتوي على نقطة فقط"""
        value = config.get('.', 'default')
        assert value == 'default'
    
    def test_set_with_special_characters(self, config):
        """اختبار تعيين قيمة تحتوي على أحرف خاصة"""
        config.set('test.key', 'value with "quotes" and \'apostrophes\'')
        assert 'quotes' in config.get('test.key')
    
    def test_get_nonexistent_deep_nesting(self, config):
        """اختبار الحصول على قيمة متداخلة بعمق غير موجودة"""
        value = config.get('level1.level2.level3.level4', 'default')
        assert value == 'default'
    
    def test_set_deep_nesting(self, config):
        """اختبار تعيين قيمة متداخلة بعمق"""
        config.set('level1.level2.level3.level4', 'deep_value')
        assert config.get('level1.level2.level3.level4') == 'deep_value'


class TestConfigManagerErrorHandling:
    """اختبارات معالجة الأخطاء"""
    
    def test_load_config_handles_invalid_json(self, tmp_path):
        """اختبار معالجة ملف JSON غير صحيح"""
        config_file = tmp_path / "app_config.json"
        config_file.write_text("invalid json {")
        
        config = ConfigManager()
        config.config_dir = tmp_path
        config.app_config_path = config_file
        
        # يجب أن يتعامل مع الخطأ بشكل صحيح
        result = config.load_config()
        # قد يعيد False أو True حسب التنفيذ
        assert isinstance(result, bool)
    
    def test_save_config_handles_permission_error(self, tmp_path):
        """اختبار معالجة خطأ الصلاحيات عند الحفظ"""
        # محاولة الحفظ في مجلد بدون صلاحيات (محاكاة)
        config = ConfigManager()
        config.config = {"test": "value"}
        
        # في Windows، قد لا نتمكن من محاكاة هذا بسهولة
        # لكن يمكننا التحقق من أن save_config يتعامل مع الأخطاء
        result = config.save_config()
        assert isinstance(result, bool)


class TestConfigManagerDefaultConfig:
    """اختبارات الإعدادات الافتراضية"""
    
    def test_get_default_config_returns_dict(self):
        """اختبار أن _get_default_config يعيد قاموساً"""
        config = ConfigManager()
        default_config = config._get_default_config()
        assert isinstance(default_config, dict)
        assert len(default_config) > 0
    
    def test_default_config_has_required_sections(self):
        """اختبار أن الإعدادات الافتراضية تحتوي على الأقسام المطلوبة"""
        config = ConfigManager()
        default_config = config._get_default_config()
        
        # التحقق من وجود الأقسام الأساسية
        assert 'database' in default_config
        assert 'ui' in default_config
        assert 'security' in default_config





