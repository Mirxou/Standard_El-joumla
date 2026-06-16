import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير الإعدادات - Configuration Manager
إدارة إعدادات التطبيق وتكوينه
"""

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.utils.logger import setup_logger


class ConfigManager:
    """مدير إعدادات التطبيق"""

    # قائمة المفاتيح الحساسة التي يجب تشفيرها
    SENSITIVE_KEYS: Set[str] = {
        "email.smtp_password",
        "email.smtp_username",
        "api.api_key",
        "security.encryption_key",
        "company.tax_number",
        "company.commercial_registration",
    }

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.app_config_path = self.config_dir / "app_config.json"
        self.dev_config_path = self.config_dir / "dev_config.json"

        self.config = {}
        self.dev_config = {}
        self._encryption_manager = None
        self._encryption_enabled = False

        # تهيئة logger
        self.logger = setup_logger(__name__)

    def load_config(self) -> bool:
        """تحميل ملفات الإعدادات"""
        try:
            # تحميل الإعدادات الرئيسية
            if self.app_config_path.exists():
                with open(self.app_config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                self.config = self._get_default_config()
                self.save_config()

            # تحميل إعدادات التطوير
            if self.dev_config_path.exists():
                with open(self.dev_config_path, "r", encoding="utf-8") as f:
                    self.dev_config = json.load(f)

            # تهيئة التشفير إذا كان مفعلاً
            if self.get("security.encrypt_sensitive_config", False):
                self._init_encryption()

            # فك تشفير القيم الحساسة
            self._decrypt_sensitive_values()

            # دعم متغيرات البيئة
            self._apply_environment_variables()

            # التحقق من صحة الإعدادات
            validation_errors = self.validate_config()
            if validation_errors:
                self.logger.warning(f"أخطاء في التحقق من الإعدادات: {validation_errors}")

            # إنشاء مجلدات البيانات المطلوبة
            self._ensure_data_directories()

            return True

        except Exception as e:
            self.logger.warning(f"خطأ في تحميل الإعدادات: {e}", exc_info=True)
            return False

    def save_config(self) -> bool:
        """حفظ الإعدادات"""
        try:
            # إنشاء مجلد الإعدادات إذا لم يكن موجوداً
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # تشفير القيم الحساسة قبل الحفظ
            config_to_save = self._encrypt_sensitive_values()

            # حفظ الإعدادات الرئيسية
            with open(self.app_config_path, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"خطأ في حفظ الإعدادات: {e}", exc_info=True)
            return False

    def get(self, key: str, default: Any = None, use_env: bool = True) -> Any:
        """
        الحصول على قيمة إعداد

        Args:
            key: مفتاح الإعداد (مثل 'database.path')
            default: القيمة الافتراضية
            use_env: استخدام متغيرات البيئة إذا كانت متوفرة
        """
        # التحقق من متغيرات البيئة أولاً
        if use_env:
            env_key = key.upper().replace(".", "_")
            env_value = os.getenv(env_key)
            if env_value is not None:
                # محاولة تحويل النوع
                try:
                    return json.loads(env_value)
                except Exception:
                    # إذا فشل التحويل، إرجاع القيمة كسلسلة
                    return env_value

        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """تعيين قيمة إعداد"""
        keys = key.split(".")
        config = self.config

        # التنقل إلى المستوى الأخير
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                # إذا كانت القيمة موجودة ولكنها ليست dict، استبدالها بـ dict
                config[k] = {}
            config = config[k]

        # تعيين القيمة
        config[keys[-1]] = value

    def get_database_path(self) -> str:
        """الحصول على مسار قاعدة البيانات"""
        db_path = self.get("database.path", "data/logical_release.db")
        if not os.path.isabs(db_path):
            db_path = str(self.project_root / db_path)
        return db_path

    def get_database_backend(self) -> str:
        """الحصول على نوع database backend"""
        return self.get("database.backend", "sqlite")  # sqlite | postgresql

    def get_database_url(self) -> Optional[str]:
        """الحصول على database URL (لـ PostgreSQL)"""
        return self.get("database.url", None)

    def get_backup_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات النسخ الاحتياطي"""
        backups_config = self.get("database.backups", {})
        return {
            "interval": self.get("database.backup_interval", 24),
            "max_backups": backups_config.get("max_backups", self.get("database.max_backups", 30)),
            "backup_path": str(self.project_root / backups_config.get("backup_dir", "data/backups")),
            "encrypted": backups_config.get("encrypted", True),
            "encryption_key_path": backups_config.get("encryption_key_path"),
        }

    def get_database_pool_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات connection pool"""
        pool_config = self.get("database.pool", {})
        return {
            "enabled": pool_config.get("enabled", True),
            "pool_size": pool_config.get("pool_size", 10),
            "max_overflow": pool_config.get("max_overflow", 20),
            "timeout": pool_config.get("timeout", 30),
        }

    def get_ui_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات واجهة المستخدم"""
        return {
            "language": self.get("ui.language", "ar"),
            "theme": self.get("ui.theme", "light"),
            "rtl": self.get("ui.rtl", True),
            "font_family": self.get("ui.font_family", "Segoe UI"),
            "font_size": self.get("ui.font_size", 10),
        }

    def get_security_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الأمان"""
        return {
            "session_timeout": self.get("security.session_timeout", 480),
            "password_min_length": self.get("security.password_min_length", 6),
            "enable_audit_log": self.get("security.enable_audit_log", True),
        }

    def get_reports_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات التقارير"""
        return {
            "default_format": self.get("reports.default_format", "pdf"),
            "auto_save": self.get("reports.auto_save", True),
            "save_path": str(self.project_root / self.get("reports.save_path", "data/exports")),
        }

    def get_pos_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات نقطة البيع"""
        return {
            "auto_print": self.get("pos.auto_print", False),
            "receipt_copies": self.get("pos.receipt_copies", 1),
            "default_payment_method": self.get("pos.default_payment_method", "نقدي"),
        }

    def get_cache_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات التخزين المؤقت"""
        return {
            "enabled": self.get("cache.enabled", True),
            "default_ttl": self.get("cache.default_ttl", 600),
            "disk_cache": self.get("cache.disk_cache", False),
            "disk_path": str(self.project_root / self.get("cache.disk_path", "data/cache")),
        }

    def get_database_info(self) -> Dict[str, Any]:
        """الحصول على معلومات قاعدة البيانات - تحويل إلى DatabaseManager"""
        # هذه الطريقة تحول الاستدعاء إلى DatabaseManager
        from .database_manager import DatabaseManager

        db_manager = DatabaseManager(self.get_database_path())
        return db_manager.get_database_info()

    def is_debug_mode(self) -> bool:
        """التحقق من وضع التطوير"""
        return self.dev_config.get("debug", False)

    def get_log_level(self) -> str:
        """الحصول على مستوى السجلات"""
        if self.is_debug_mode():
            return self.dev_config.get("log_level", "DEBUG")
        return "INFO"

    def _get_default_config(self) -> Dict[str, Any]:
        """الحصول على الإعدادات الافتراضية"""
        return {
            "database": {
                "backend": "sqlite",  # sqlite | postgresql
                "path": "data/logical_release.db",
                "url": None,  # postgresql://user:pass@host:5432/dbname
                "backup_interval": 24,
                "max_backups": 30,
                "pool": {
                    "enabled": True,
                    "pool_size": 10,
                    "max_overflow": 20,
                    "timeout": 30,
                },
                "backups": {
                    "encrypted": True,
                    "backup_dir": "data/backups",
                    "max_backups": 30,
                    "encryption_key_path": None,
                },
            },
            "ui": {
                "language": "ar",
                "theme": "light",
                "rtl": True,
                "font_family": "Segoe UI",
                "font_size": 10,
            },
            "security": {
                "session_timeout": 480,
                "password_min_length": 6,
                "enable_audit_log": True,
                "encrypt_sensitive_config": False,
                "encryption_key_env": "APP_ENCRYPTION_KEY",
            },
            "reports": {
                "default_format": "pdf",
                "auto_save": True,
                "save_path": "data/exports",
            },
            "pos": {
                "auto_print": False,
                "receipt_copies": 1,
                "default_payment_method": "نقدي",
            },
            "cache": {
                "enabled": True,
                "default_ttl": 600,
                "disk_cache": False,
                "disk_path": "data/cache",
            },
            "email": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "smtp_username": "",
                "smtp_password": "",
                "smtp_use_tls": True,
                "from_email": "",
                "from_name": "",
            },
            "printing": {
                "default_printer": "",
                "paper_size": "A4",
                "orientation": "portrait",
                "margin_top": 10,
                "margin_bottom": 10,
                "margin_left": 10,
                "margin_right": 10,
                "auto_print_invoices": False,
                "print_logo": True,
                "print_qr_code": True,
                "print_barcode": True,
            },
            "api": {
                "enabled": False,
                "base_url": "http://127.0.0.1:8000",
                "api_url": "http://127.0.0.1:8000",  # Alias for base_url for backward compatibility
                "api_key": "",
                "timeout": 30,
                "retry_attempts": 3,
                "verify_ssl": True,
                "cors_origins": [
                    "*"
                ],  # في الإنتاج، حدد origins محددة مثل ["http://localhost:3000", "https://yourdomain.com"]
            },
            "notifications": {
                "enabled": True,
                "email_notifications": False,
                "low_stock_alert": True,
                "low_stock_threshold": 10,
                "expiry_alert": True,
                "expiry_days_before": 30,
                "sales_alert": False,
                "backup_alert": True,
            },
            "templates": {
                "default_invoice_template": "invoice.html",
                "default_receipt_template": "receipt.html",
                "default_quote_template": "quote.html",
                "qr_code": {
                    "enabled": True,
                    "size": 100,
                    "error_correction": "M",
                    "include_data": True,
                },
                "barcode": {
                    "enabled": True,
                    "format": "code128",
                    "height": 50,
                    "width": 2,
                },
                "images": {
                    "max_size_mb": 5,
                    "allowed_formats": ["jpg", "jpeg", "png", "gif"],
                    "auto_resize": True,
                    "thumbnail_size": 150,
                    "preview_size": 800,
                },
                "signatures": {
                    "enabled": False,
                    "require_signature": False,
                    "signature_position": "bottom",
                },
            },
            "company": {
                "name": "",
                "name_ar": "",
                "name_en": "",
                "address": "",
                "address_ar": "",
                "address_en": "",
                "phone": "",
                "mobile": "",
                "email": "",
                "website": "",
                "tax_number": "",
                "commercial_registration": "",
                "logo_path": "",
                "signature_path": "",
            },
        }

    # ==================== دوال الإعدادات الجديدة ====================

    def get_email_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات البريد الإلكتروني"""
        email_config = self.get("email", {})
        return {
            "enabled": email_config.get("enabled", False),
            "smtp_server": email_config.get("smtp_server", ""),
            "smtp_port": email_config.get("smtp_port", 587),
            "smtp_username": email_config.get("smtp_username", ""),
            "smtp_password": email_config.get("smtp_password", ""),
            "smtp_use_tls": email_config.get("smtp_use_tls", True),
            "from_email": email_config.get("from_email", ""),
            "from_name": email_config.get("from_name", ""),
        }

    def get_printing_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الطباعة"""
        printing_config = self.get("printing", {})
        return {
            "default_printer": printing_config.get("default_printer", ""),
            "paper_size": printing_config.get("paper_size", "A4"),
            "orientation": printing_config.get("orientation", "portrait"),
            "margin_top": printing_config.get("margin_top", 10),
            "margin_bottom": printing_config.get("margin_bottom", 10),
            "margin_left": printing_config.get("margin_left", 10),
            "margin_right": printing_config.get("margin_right", 10),
            "auto_print_invoices": printing_config.get("auto_print_invoices", False),
            "print_logo": printing_config.get("print_logo", True),
            "print_qr_code": printing_config.get("print_qr_code", True),
            "print_barcode": printing_config.get("print_barcode", True),
        }

    def get_api_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات API"""
        api_config = self.get("api", {})
        base_url = api_config.get("base_url") or api_config.get("api_url", "http://127.0.0.1:8000")
        return {
            "enabled": api_config.get("enabled", False),
            "base_url": base_url,
            "api_url": base_url,  # Alias for backward compatibility
            "api_key": api_config.get("api_key", ""),
            "timeout": api_config.get("timeout", 30),
            "retry_attempts": api_config.get("retry_attempts", 3),
            "verify_ssl": api_config.get("verify_ssl", True),
            "cors_origins": api_config.get("cors_origins", ["*"]),
        }

    def get_api_url(self) -> str:
        """الحصول على رابط API"""
        api_config = self.get("api", {})
        return api_config.get("api_url") or api_config.get("base_url", "http://127.0.0.1:8000")

    def get_cors_origins(self) -> list:
        """الحصول على قائمة CORS Origins المسموحة"""
        api_config = self.get("api", {})
        cors_origins = api_config.get("cors_origins", ["*"])
        # دعم environment variable
        import os

        env_cors = os.getenv("CORS_ORIGINS")
        if env_cors:
            cors_origins = [origin.strip() for origin in env_cors.split(",")]

        # إذا كان "*" أو list فارغ، أضف localhost والشبكة المحلية
        if cors_origins == ["*"] or not cors_origins:
            cors_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            ]
            # إضافة IPs في الشبكة المحلية (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
            try:
                import socket

                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                if (
                    local_ip.startswith("192.168.")
                    or local_ip.startswith("10.")
                    or local_ip.startswith("172.16.")
                    or local_ip.startswith("172.17.")
                    or local_ip.startswith("172.18.")
                    or local_ip.startswith("172.19.")
                    or local_ip.startswith("172.20.")
                    or local_ip.startswith("172.21.")
                    or local_ip.startswith("172.22.")
                    or local_ip.startswith("172.23.")
                    or local_ip.startswith("172.24.")
                    or local_ip.startswith("172.25.")
                    or local_ip.startswith("172.26.")
                    or local_ip.startswith("172.27.")
                    or local_ip.startswith("172.28.")
                    or local_ip.startswith("172.29.")
                    or local_ip.startswith("172.30.")
                    or local_ip.startswith("172.31.")
                ):
                    cors_origins.append(f"http://{local_ip}:3000")
                    cors_origins.append(f"http://{local_ip}:3001")
            except Exception:
                pass  # إذا فشل الكشف، نستخدم القيم الافتراضية فقط

        return cors_origins if isinstance(cors_origins, list) else [cors_origins]

    def get_notifications_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الإشعارات"""
        notifications_config = self.get("notifications", {})
        return {
            "enabled": notifications_config.get("enabled", True),
            "email_notifications": notifications_config.get("email_notifications", False),
            "low_stock_alert": notifications_config.get("low_stock_alert", True),
            "low_stock_threshold": notifications_config.get("low_stock_threshold", 10),
            "expiry_alert": notifications_config.get("expiry_alert", True),
            "expiry_days_before": notifications_config.get("expiry_days_before", 30),
            "sales_alert": notifications_config.get("sales_alert", False),
            "backup_alert": notifications_config.get("backup_alert", True),
        }

    def get_templates_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات القوالب"""
        templates_config = self.get("templates", {})
        return {
            "default_invoice_template": templates_config.get("default_invoice_template", "invoice.html"),
            "default_receipt_template": templates_config.get("default_receipt_template", "receipt.html"),
            "default_quote_template": templates_config.get("default_quote_template", "quote.html"),
            "qr_code": templates_config.get(
                "qr_code",
                {
                    "enabled": True,
                    "size": 100,
                    "error_correction": "M",
                    "include_data": True,
                },
            ),
            "barcode": templates_config.get(
                "barcode",
                {"enabled": True, "format": "code128", "height": 50, "width": 2},
            ),
            "images": templates_config.get(
                "images",
                {
                    "max_size_mb": 5,
                    "allowed_formats": ["jpg", "jpeg", "png", "gif"],
                    "auto_resize": True,
                    "thumbnail_size": 150,
                    "preview_size": 800,
                },
            ),
            "signatures": templates_config.get(
                "signatures",
                {
                    "enabled": False,
                    "require_signature": False,
                    "signature_position": "bottom",
                },
            ),
        }

    def get_company_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الشركة"""
        company_config = self.get("company", {})
        return {
            "name": company_config.get("name", ""),
            "name_ar": company_config.get("name_ar", ""),
            "name_en": company_config.get("name_en", ""),
            "address": company_config.get("address", ""),
            "address_ar": company_config.get("address_ar", ""),
            "address_en": company_config.get("address_en", ""),
            "phone": company_config.get("phone", ""),
            "mobile": company_config.get("mobile", ""),
            "email": company_config.get("email", ""),
            "website": company_config.get("website", ""),
            "tax_number": company_config.get("tax_number", ""),
            "commercial_registration": company_config.get("commercial_registration", ""),
            "logo_path": company_config.get("logo_path", ""),
            "signature_path": company_config.get("signature_path", ""),
        }

    # ==================== دوال التشفير ====================

    def _init_encryption(self):
        """تهيئة مدير التشفير"""
        try:
            from .encryption_manager import EncryptionManager

            # الحصول على مفتاح التشفير من متغير البيئة
            encryption_key_env = self.get("security.encryption_key_env", "APP_ENCRYPTION_KEY")
            encryption_key = os.getenv(encryption_key_env)

            if encryption_key:
                self._encryption_manager = EncryptionManager(encryption_key)
                self._encryption_enabled = True
            else:
                self.logger.warning(f"متغير البيئة {encryption_key_env} غير موجود. سيتم حفظ القيم الحساسة بدون تشفير.")
                self._encryption_enabled = False
        except Exception as e:
            self.logger.warning(f"فشل تهيئة التشفير: {e}", exc_info=True)
            self._encryption_enabled = False

    def _encrypt_sensitive_values(self) -> Dict[str, Any]:
        """تشفير القيم الحساسة قبل الحفظ"""
        config_copy = json.loads(json.dumps(self.config))  # نسخة عميقة

        if not self._encryption_enabled or not self._encryption_manager:
            return config_copy

        for key_path in self.SENSITIVE_KEYS:
            value = self.get(key_path, use_env=False)  # عدم استخدام متغيرات البيئة هنا
            if value and isinstance(value, str) and not value.startswith("encrypted:"):
                try:
                    encrypted = self._encryption_manager.encrypt_data(value)
                    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")
                    self._set_nested_value(config_copy, key_path, f"encrypted:{encrypted_b64}")
                except Exception as e:
                    self.logger.warning(f"فشل تشفير {key_path}: {e}", exc_info=True)

        return config_copy

    def _decrypt_sensitive_values(self):
        """فك تشفير القيم الحساسة بعد التحميل"""
        if not self._encryption_enabled or not self._encryption_manager:
            return

        for key_path in self.SENSITIVE_KEYS:
            value = self.get(key_path, use_env=False)  # عدم استخدام متغيرات البيئة هنا
            if value and isinstance(value, str) and value.startswith("encrypted:"):
                try:
                    encrypted_b64 = value.replace("encrypted:", "")
                    encrypted = base64.b64decode(encrypted_b64.encode("utf-8"))
                    decrypted = self._encryption_manager.decrypt_data(encrypted)
                    self.set(key_path, decrypted.decode("utf-8"))
                except Exception as e:
                    self.logger.warning(f"فشل فك تشفير {key_path}: {e}", exc_info=True)

    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any):
        """تعيين قيمة متداخلة في القاموس"""
        keys = key_path.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    # ==================== دعم متغيرات البيئة ====================

    def _apply_environment_variables(self):
        """تطبيق متغيرات البيئة على الإعدادات"""
        # قائمة المفاتيح التي يمكن استبدالها بمتغيرات البيئة
        env_mappings = {
            "DATABASE_PATH": "database.path",
            "SMTP_SERVER": "email.smtp_server",
            "SMTP_PORT": "email.smtp_port",
            "SMTP_USERNAME": "email.smtp_username",
            "SMTP_PASSWORD": "email.smtp_password",
            "API_BASE_URL": "api.base_url",
            "API_KEY": "api.api_key",
            "COMPANY_NAME": "company.name",
            "COMPANY_EMAIL": "company.email",
            "COMPANY_PHONE": "company.phone",
        }

        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # محاولة تحويل النوع
                try:
                    # محاولة تحويل إلى رقم
                    if env_value.isdigit():
                        env_value = int(env_value)
                    elif env_value.lower() in ("true", "false"):
                        env_value = env_value.lower() == "true"
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in config_manager.py")

                self.set(config_key, env_value)

    # ==================== التحقق من صحة الإعدادات ====================

    def validate_config(self) -> List[str]:
        """
        التحقق من صحة الإعدادات

        Returns:
            قائمة بأخطاء التحقق (فارغة إذا كانت جميع الإعدادات صحيحة)
        """
        errors = []

        # التحقق من إعدادات البريد الإلكتروني
        email_config = self.get("email", {})
        if email_config.get("enabled", False):
            if not email_config.get("smtp_server"):
                errors.append("إعدادات البريد: يجب تحديد خادم SMTP")
            if not email_config.get("smtp_username"):
                errors.append("إعدادات البريد: يجب تحديد اسم المستخدم")
            if not email_config.get("from_email"):
                errors.append("إعدادات البريد: يجب تحديد البريد الإلكتروني المرسل")
            if email_config.get("smtp_port", 0) <= 0:
                errors.append("إعدادات البريد: منفذ SMTP غير صحيح")

        # التحقق من إعدادات API
        api_config = self.get("api", {})
        if api_config.get("enabled", False):
            if not api_config.get("base_url"):
                errors.append("إعدادات API: يجب تحديد رابط API الأساسي")
            if not api_config.get("api_key"):
                errors.append("إعدادات API: يجب تحديد مفتاح API")

        # التحقق من إعدادات الطباعة
        printing_config = self.get("printing", {})
        if printing_config.get("paper_size") not in ["A4", "A3", "Letter", "Legal"]:
            errors.append("إعدادات الطباعة: حجم الورق غير صحيح")
        if printing_config.get("orientation") not in ["portrait", "landscape"]:
            errors.append("إعدادات الطباعة: اتجاه الورق غير صحيح")

        # التحقق من إعدادات القوالب
        templates_config = self.get("templates", {})
        templates_dir = self.project_root / "assets" / "templates"
        for template_key in [
            "default_invoice_template",
            "default_receipt_template",
            "default_quote_template",
        ]:
            template_name = templates_config.get(template_key, "")
            if template_name and not (templates_dir / template_name).exists():
                errors.append(f"إعدادات القوالب: القالب {template_name} غير موجود")

        # التحقق من إعدادات الشركة
        company_config = self.get("company", {})
        if company_config.get("logo_path"):
            logo_path = Path(company_config["logo_path"])
            if not logo_path.is_absolute():
                logo_path = self.project_root / logo_path
            if not logo_path.exists():
                errors.append("إعدادات الشركة: مسار الشعار غير موجود")

        # التحقق من صحة البريد الإلكتروني
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if company_config.get("email") and not re.match(email_pattern, company_config["email"]):
            errors.append("إعدادات الشركة: البريد الإلكتروني غير صحيح")

        # التحقق من صحة الموقع الإلكتروني
        if company_config.get("website"):
            website = company_config["website"]
            if not website.startswith(("http://", "https://")):
                errors.append("إعدادات الشركة: الموقع الإلكتروني يجب أن يبدأ بـ http:// أو https://")

        return errors

    def _ensure_data_directories(self):
        """التأكد من وجود جميع مجلدات البيانات المطلوبة"""
        try:
            # مجلد النسخ الاحتياطية
            backups_dir = self.project_root / self.get("database.backups.backup_dir", "data/backups")
            backups_dir.mkdir(parents=True, exist_ok=True)

            # مجلد التصدير
            exports_dir = self.project_root / self.get("reports.save_path", "data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)

            # مجلد القوالب
            templates_dir = self.project_root / "data" / "templates"
            templates_dir.mkdir(parents=True, exist_ok=True)

            # مجلد التخزين المؤقت (إذا كان مفعلاً)
            cache_settings = self.get_cache_settings()
            if cache_settings.get("disk_cache", False):
                cache_dir = Path(cache_settings["disk_path"])
                cache_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            self.logger.warning(f"فشل إنشاء مجلدات البيانات: {e}", exc_info=True)
