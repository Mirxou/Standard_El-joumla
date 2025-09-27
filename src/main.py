#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الإصدار المنطقي - نظام إدارة التجارة العامة
Logical Release - General Trade Management System

الملف الرئيسي للتطبيق
Main Application Entry Point
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# إضافة مجلد src إلى المسار
sys.path.insert(0, str(Path(__file__).parent))

from ui.windows.main_window import MainWindow
from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from core.exceptions import DatabaseException, ConfigurationException
from utils.logger import setup_logger

class LogicalReleaseApp:
    """الفئة الرئيسية للتطبيق"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.config_manager = None
        self.db_manager = None
        self.logger = None
        
    def setup_application(self):
        """إعداد التطبيق الأساسي"""
        # إنشاء تطبيق Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("الإصدار المنطقي")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("Logical Release")
        
        # إعداد الخط العربي
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)
        
        # إعداد اتجاه النص من اليمين لليسار
        self.app.setLayoutDirection(Qt.RightToLeft)
        
        return True
    
    def load_configuration(self):
        """تحميل إعدادات التطبيق"""
        try:
            self.config_manager = ConfigManager()
            return self.config_manager.load_config()
        except ConfigurationException as e:
            QMessageBox.critical(None, "خطأ في الإعدادات", f"فشل في تحميل الإعدادات:\n{str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ غير متوقع في تحميل الإعدادات:\n{str(e)}")
            return False
    
    def setup_database(self):
        """إعداد قاعدة البيانات"""
        try:
            self.db_manager = DatabaseManager()
            return self.db_manager.initialize()
        except DatabaseException as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل في إعداد قاعدة البيانات:\n{str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ غير متوقع في قاعدة البيانات:\n{str(e)}")
            return False
    
    def setup_logging(self):
        """إعداد نظام السجلات"""
        try:
            self.logger = setup_logger()
            self.logger.info("تم بدء تشغيل التطبيق")
            return True
        except Exception as e:
            print(f"فشل في إعداد نظام السجلات: {e}")
            return False
    
    def create_main_window(self):
        """إنشاء النافذة الرئيسية"""
        try:
            self.main_window = MainWindow(
                config_manager=self.config_manager,
                db_manager=self.db_manager,
                logger=self.logger
            )
            return True
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"فشل في إنشاء النافذة الرئيسية:\n{str(e)}")
            return False
    
    def run(self):
        """تشغيل التطبيق"""
        try:
            # إعداد التطبيق
            if not self.setup_application():
                if self.logger:
                    self.logger.error("فشل في إعداد التطبيق")
                return 1
            
            # إعداد نظام السجلات
            if not self.setup_logging():
                return 1
            
            # تحميل الإعدادات
            if not self.load_configuration():
                if self.logger:
                    self.logger.error("فشل في تحميل الإعدادات")
                return 1
            
            # إعداد قاعدة البيانات
            if not self.setup_database():
                if self.logger:
                    self.logger.error("فشل في إعداد قاعدة البيانات")
                return 1
            
            # إنشاء النافذة الرئيسية
            if not self.create_main_window():
                if self.logger:
                    self.logger.error("فشل في إنشاء النافذة الرئيسية")
                return 1
            
            # عرض النافذة الرئيسية
            self.main_window.show()
            
            # تشغيل حلقة الأحداث
            return self.app.exec()
            
        except Exception as e:
            error_msg = f"خطأ في تشغيل التطبيق: {e}"
            if self.logger:
                self.logger.error(error_msg)
            else:
                print(error_msg)
            return 1
        
        finally:
            # تنظيف الموارد
            self._cleanup_resources()

    def _cleanup_resources(self):
        """تنظيف موارد التطبيق"""
        if self.db_manager:
            self.db_manager.close()
        if self.logger:
            self.logger.info("تم إغلاق التطبيق")

def main():
    """النقطة الرئيسية لدخول التطبيق"""
    app = LogicalReleaseApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())