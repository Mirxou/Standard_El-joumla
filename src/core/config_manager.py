#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير الإعدادات - Configuration Manager
إدارة إعدادات التطبيق وتكوينه
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """مدير إعدادات التطبيق"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.app_config_path = self.config_dir / "app_config.json"
        self.dev_config_path = self.config_dir / "dev_config.json"
        
        self.config = {}
        self.dev_config = {}
    
    def load_config(self) -> bool:
        """تحميل ملفات الإعدادات"""
        try:
            # تحميل الإعدادات الرئيسية
            if self.app_config_path.exists():
                with open(self.app_config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self._get_default_config()
                self.save_config()
            
            # تحميل إعدادات التطوير
            if self.dev_config_path.exists():
                with open(self.dev_config_path, 'r', encoding='utf-8') as f:
                    self.dev_config = json.load(f)
            
            return True
            
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
            return False
    
    def save_config(self) -> bool:
        """حفظ الإعدادات"""
        try:
            # إنشاء مجلد الإعدادات إذا لم يكن موجوداً
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # حفظ الإعدادات الرئيسية
            with open(self.app_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"خطأ في حفظ الإعدادات: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة إعداد"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """تعيين قيمة إعداد"""
        keys = key.split('.')
        config = self.config
        
        # التنقل إلى المستوى الأخير
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # تعيين القيمة
        config[keys[-1]] = value
    
    def get_database_path(self) -> str:
        """الحصول على مسار قاعدة البيانات"""
        db_path = self.get('database.path', 'data/logical_release.db')
        if not os.path.isabs(db_path):
            db_path = str(self.project_root / db_path)
        return db_path
    
    def get_backup_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات النسخ الاحتياطي"""
        return {
            'interval': self.get('database.backup_interval', 24),
            'max_backups': self.get('database.max_backups', 30),
            'backup_path': str(self.project_root / "data" / "backups")
        }
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات واجهة المستخدم"""
        return {
            'language': self.get('ui.language', 'ar'),
            'theme': self.get('ui.theme', 'light'),
            'rtl': self.get('ui.rtl', True),
            'font_family': self.get('ui.font_family', 'Segoe UI'),
            'font_size': self.get('ui.font_size', 10)
        }
    
    def get_security_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الأمان"""
        return {
            'session_timeout': self.get('security.session_timeout', 480),
            'password_min_length': self.get('security.password_min_length', 6),
            'enable_audit_log': self.get('security.enable_audit_log', True)
        }
    
    def get_reports_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات التقارير"""
        return {
            'default_format': self.get('reports.default_format', 'pdf'),
            'auto_save': self.get('reports.auto_save', True),
            'save_path': str(self.project_root / self.get('reports.save_path', 'data/exports'))
        }
    
    def get_pos_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات نقطة البيع"""
        return {
            'auto_print': self.get('pos.auto_print', False),
            'receipt_copies': self.get('pos.receipt_copies', 1),
            'default_payment_method': self.get('pos.default_payment_method', 'نقدي')
        }
    
    def get_database_info(self) -> Dict[str, Any]:
        """الحصول على معلومات قاعدة البيانات - تحويل إلى DatabaseManager"""
        # هذه الطريقة تحول الاستدعاء إلى DatabaseManager
        from .database_manager import DatabaseManager
        db_manager = DatabaseManager(self.get_database_path())
        return db_manager.get_database_info()

    def is_debug_mode(self) -> bool:
        """التحقق من وضع التطوير"""
        return self.dev_config.get('debug', False)
    
    def get_log_level(self) -> str:
        """الحصول على مستوى السجلات"""
        if self.is_debug_mode():
            return self.dev_config.get('log_level', 'DEBUG')
        return 'INFO'
    
    def _get_default_config(self) -> Dict[str, Any]:
        """الحصول على الإعدادات الافتراضية"""
        return {
            "database": {
                "path": "data/logical_release.db",
                "backup_interval": 24,
                "max_backups": 30
            },
            "ui": {
                "language": "ar",
                "theme": "light",
                "rtl": True,
                "font_family": "Segoe UI",
                "font_size": 10
            },
            "security": {
                "session_timeout": 480,
                "password_min_length": 6,
                "enable_audit_log": True
            },
            "reports": {
                "default_format": "pdf",
                "auto_save": True,
                "save_path": "data/exports"
            },
            "pos": {
                "auto_print": False,
                "receipt_copies": 1,
                "default_payment_method": "نقدي"
            }
        }