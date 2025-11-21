#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام السجلات - Logger System
إدارة سجلات التطبيق والأحداث
"""

import logging
import sys
import os
import io
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    name: str = "logical_release",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """إعداد نظام السجلات"""
    
    # إنشاء logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # تجنب إضافة handlers متعددة
    if logger.handlers:
        return logger
    
    # تنسيق الرسائل
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # إعداد السجل في ملف
    if log_to_file:
        # إنشاء مجلد السجلات
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # ملف السجل الرئيسي
        log_file = logs_dir / f"{name}.log"
        
        # إعداد RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # إعداد السجل في وحدة التحكم
    if log_to_console:
        stream = sys.stdout
        try:
            # على Windows: إجبار الترميز إلى UTF-8 لتجنب UnicodeEncodeError
            if os.name == "nt" and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            try:
                # كحل احتياطي: لفّ التدفق بمغلّف UTF-8
                stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            except Exception:
                # كحل نهائي: تجاهل الإخراج إلى وحدة التحكم إذا تعذّر الترميز
                stream = io.StringIO()

        console_handler = logging.StreamHandler(stream)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

class DatabaseLogger:
    """مسجل قاعدة البيانات للعمليات الحساسة"""
    
    def __init__(self, db_manager, user_id: Optional[int] = None):
        self.db_manager = db_manager
        self.user_id = user_id
        self.logger = setup_logger("database_operations")
    
    def log_operation(
        self,
        action: str,
        table_name: str,
        record_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None
    ):
        """تسجيل عملية في قاعدة البيانات"""
        try:
            import json
            
            # تحويل القيم إلى JSON
            old_values_json = json.dumps(old_values, ensure_ascii=False) if old_values else None
            new_values_json = json.dumps(new_values, ensure_ascii=False) if new_values else None
            
            # إدراج في جدول audit_log
            query = """
                INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            self.db_manager.execute_non_query(
                query,
                (self.user_id, action, table_name, record_id, old_values_json, new_values_json)
            )
            
            # تسجيل في ملف السجل أيضاً
            self.logger.info(
                f"عملية {action} على جدول {table_name} - المعرف: {record_id} - المستخدم: {self.user_id}"
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل العملية: {e}")
    
    def log_login(self, username: str, success: bool, ip_address: str = None):
        """تسجيل محاولة تسجيل الدخول"""
        status = "نجح" if success else "فشل"
        message = f"محاولة تسجيل دخول {status} - المستخدم: {username}"
        if ip_address:
            message += f" - IP: {ip_address}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def log_backup(self, backup_path: str, success: bool):
        """تسجيل عملية النسخ الاحتياطي"""
        if success:
            self.logger.info(f"تم إنشاء نسخة احتياطية بنجاح: {backup_path}")
        else:
            self.logger.error(f"فشل في إنشاء نسخة احتياطية: {backup_path}")
    
    def log_restore(self, backup_path: str, success: bool):
        """تسجيل عملية الاستعادة"""
        if success:
            self.logger.info(f"تم استعادة النسخة الاحتياطية بنجاح: {backup_path}")
        else:
            self.logger.error(f"فشل في استعادة النسخة الاحتياطية: {backup_path}")

class PerformanceLogger:
    """مسجل الأداء لمراقبة أداء التطبيق"""
    
    def __init__(self):
        self.logger = setup_logger("performance")
    
    def log_query_time(self, query: str, execution_time: float, record_count: int = 0):
        """تسجيل وقت تنفيذ الاستعلام"""
        if execution_time > 1.0:  # تسجيل الاستعلامات البطيئة فقط
            self.logger.warning(
                f"استعلام بطيء - الوقت: {execution_time:.3f}s - السجلات: {record_count} - الاستعلام: {query[:100]}..."
            )
    
    def log_memory_usage(self, operation: str, memory_mb: float):
        """تسجيل استخدام الذاكرة"""
        if memory_mb > 100:  # تسجيل الاستخدام العالي للذاكرة
            self.logger.warning(f"استخدام ذاكرة عالي - العملية: {operation} - الذاكرة: {memory_mb:.2f}MB")
    
    def log_startup_time(self, startup_time: float):
        """تسجيل وقت بدء التطبيق"""
        self.logger.info(f"وقت بدء التطبيق: {startup_time:.3f}s")

def get_logger(name: str = "logical_release") -> logging.Logger:
    """الحصول على logger موجود أو إنشاء جديد"""
    return logging.getLogger(name)