#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة السجلات المتقدمة (Advanced Logging Service)
نظام تسجيل احترافي مع Rotation، مستويات متعددة، وتنسيق منظم
"""

import logging
import logging.handlers
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """مستويات التسجيل"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """
    Formatter مخصص لإنشاء سجلات منظمة بصيغة JSON
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        تنسيق السجل بصيغة JSON منظمة
        """
        # البيانات الأساسية
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # إضافة معلومات الاستثناء إذا وجدت
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # إضافة حقول مخصصة
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data, ensure_ascii=False, indent=None)


class ColoredFormatter(logging.Formatter):
    """
    Formatter مع ألوان للطرفية (Console)
    """
    
    # رموز ANSI للألوان
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """تنسيق السجل مع ألوان"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # تنسيق الرسالة
        formatted = super().format(record)
        
        # إضافة الألوان
        return f"{color}{formatted}{reset}"


class AdvancedLoggingService:
    """
    خدمة السجلات المتقدمة
    
    المزايا:
    - تسجيل منظم (Structured Logging) بصيغة JSON
    - تدوير السجلات (Log Rotation) التلقائي
    - مستويات متعددة (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - سجلات منفصلة للأخطاء
    - دعم الألوان في الطرفية
    - تسجيل الاستثناءات مع التتبع الكامل
    """
    
    def __init__(
        self,
        app_name: str = "LogicalVersion",
        log_dir: str = "logs",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 10
    ):
        """
        تهيئة خدمة السجلات
        
        Args:
            app_name: اسم التطبيق
            log_dir: مجلد السجلات
            log_level: مستوى التسجيل الافتراضي
            enable_console: تفعيل السجلات في الطرفية
            enable_file: تفعيل السجلات في الملفات
            enable_json: تفعيل السجلات بصيغة JSON
            max_bytes: الحجم الأقصى لملف السجل قبل التدوير
            backup_count: عدد الملفات الاحتياطية
        """
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # إنشاء مجلد السجلات
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger الرئيسي
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)  # نسجل كل شيء، الفلاتر في الـ handlers
        
        # إزالة handlers القديمة (إذا وجدت)
        self.logger.handlers.clear()
        
        # إضافة handlers
        if enable_console:
            self._add_console_handler()
        
        if enable_file:
            self._add_file_handler()
            self._add_error_file_handler()
        
        if enable_json:
            self._add_json_handler()
        
        # Logger لأحداث الأمان (منفصل)
        self.security_logger = self._create_security_logger()
        
        # Logger للأداء (منفصل)
        self.performance_logger = self._create_performance_logger()
        
        self.logger.info(f"✅ تم تهيئة نظام السجلات: {app_name}")
    
    def _add_console_handler(self) -> None:
        """إضافة handler للطرفية مع ألوان"""
        # استخدام NonClosingStreamHandler لمنع إغلاق sys.stdout
        try:
            from ..utils.logger import NonClosingStreamHandler
            console_handler = NonClosingStreamHandler(sys.stdout)
        except ImportError:
            # Fallback في حالة عدم القدرة على الاستيراد
            # إعادة تعريف Class محلياً لتجنب التبعيات الدائرية
            class NonClosingStreamHandler(logging.StreamHandler):
                def close(self):
                    self.acquire()
                    try:
                        if self.stream:
                            try:
                                self.flush()
                            except Exception:
                                pass
                    finally:
                        self.stream = None
                        self.release()
            
            console_handler = NonClosingStreamHandler(sys.stdout)

        console_handler.setLevel(self.log_level)
        
        # تنسيق ملون
        formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self) -> None:
        """إضافة handler لملف السجل العام"""
        file_path = self.log_dir / f"{self.app_name.lower()}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # تنسيق نصي تفصيلي
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | '
            '%(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _add_error_file_handler(self) -> None:
        """إضافة handler منفصل لسجل الأخطاء فقط"""
        error_path = self.log_dir / f"{self.app_name.lower()}_errors.log"
        
        error_handler = logging.handlers.RotatingFileHandler(
            error_path,
            maxBytes=self.max_bytes // 2,  # نصف الحجم
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # تنسيق مفصل للأخطاء
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s\n'
            'File: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s()\n'
            'Message: %(message)s\n'
            '%(separator)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # إضافة خط فاصل
        old_format = formatter.format
        def format_with_separator(record):
            record.separator = '-' * 80
            return old_format(record)
        formatter.format = format_with_separator
        
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(error_handler)
    
    def _add_json_handler(self) -> None:
        """إضافة handler لسجلات JSON المنظمة"""
        json_path = self.log_dir / f"{self.app_name.lower()}_structured.jsonl"
        
        json_handler = logging.handlers.RotatingFileHandler(
            json_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        
        # استخدام Formatter المخصص
        json_handler.setFormatter(StructuredFormatter())
        
        self.logger.addHandler(json_handler)
    
    def _create_security_logger(self) -> logging.Logger:
        """إنشاء logger منفصل لأحداث الأمان"""
        security_logger = logging.getLogger(f"{self.app_name}.Security")
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False  # لا ترسل للـ logger الرئيسي
        
        # ملف منفصل للأمان
        security_path = self.log_dir / "security_audit.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_path,
            maxBytes=self.max_bytes,
            backupCount=20,  # حفظ أكثر للأمان
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        security_handler.setFormatter(formatter)
        
        security_logger.addHandler(security_handler)
        
        return security_logger
    
    def _create_performance_logger(self) -> logging.Logger:
        """إنشاء logger منفصل لمقاييس الأداء"""
        perf_logger = logging.getLogger(f"{self.app_name}.Performance")
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
        
        # ملف منفصل للأداء
        perf_path = self.log_dir / "performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_path,
            maxBytes=self.max_bytes,
            backupCount=5,
            encoding='utf-8'
        )
        
        formatter = StructuredFormatter()
        perf_handler.setFormatter(formatter)
        
        perf_logger.addHandler(perf_handler)
        
        return perf_logger
    
    # ==================== طرق التسجيل ====================
    
    def debug(self, message: str, **kwargs) -> None:
        """تسجيل رسالة debug"""
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """تسجيل رسالة معلوماتية"""
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """تسجيل تحذير"""
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """تسجيل خطأ"""
        self._log(logging.ERROR, message, kwargs, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """تسجيل خطأ حرج"""
        self._log(logging.CRITICAL, message, kwargs, exc_info=exc_info)
    
    def exception(self, message: str, **kwargs) -> None:
        """تسجيل استثناء مع التتبع الكامل"""
        self._log(logging.ERROR, message, kwargs, exc_info=True)
    
    def _log(self, level: int, message: str, extra: Dict[str, Any], exc_info: bool = False) -> None:
        """طريقة داخلية للتسجيل مع بيانات إضافية"""
        # إنشاء record مخصص
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(internal)",
            0,
            message,
            (),
            None,
            extra=extra
        )
        
        # إضافة الحقول الإضافية للـ record
        for key, value in extra.items():
            setattr(record, key, value)
        
        # إضافة معلومات الاستثناء إذا طُلبت
        if exc_info:
            record.exc_info = sys.exc_info()
        
        self.logger.handle(record)
    
    # ==================== تسجيل أحداث الأمان ====================
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        description: str = "",
        severity: str = "INFO"
    ) -> None:
        """
        تسجيل حدث أمني
        
        Args:
            event_type: نوع الحدث (LOGIN, LOGOUT, PASSWORD_CHANGE, etc.)
            user_id: معرف المستخدم
            username: اسم المستخدم
            ip_address: عنوان IP
            description: وصف الحدث
            severity: درجة الخطورة
        """
        message = f"[{event_type}] {description}"
        if username:
            message += f" | User: {username}"
        if ip_address:
            message += f" | IP: {ip_address}"
        
        level = getattr(logging, severity.upper(), logging.INFO)
        
        self.security_logger.log(
            level,
            message,
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'username': username,
                'ip_address': ip_address
            }
        )
    
    # ==================== تسجيل مقاييس الأداء ====================
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ) -> None:
        """
        تسجيل مقاييس الأداء
        
        Args:
            operation: اسم العملية
            duration_ms: المدة بالميلي ثانية
            success: نجحت أم فشلت
            **kwargs: معلومات إضافية
        """
        message = f"{operation} - {duration_ms:.2f}ms - {'✅ Success' if success else '❌ Failed'}"
        
        self.performance_logger.info(
            message,
            extra={
                'operation': operation,
                'duration_ms': duration_ms,
                'success': success,
                **kwargs
            }
        )
    
    # ==================== وظائف مساعدة ====================
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """
        الحصول على logger فرعي
        
        Args:
            name: اسم الـ logger الفرعي
            
        Returns:
            logging.Logger: Logger فرعي
        """
        if name:
            return self.logger.getChild(name)
        return self.logger
    
    def set_level(self, level: str) -> None:
        """
        تغيير مستوى التسجيل
        
        Args:
            level: المستوى الجديد (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        new_level = getattr(logging, level.upper())
        self.logger.setLevel(new_level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(new_level)
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        حذف السجلات القديمة
        
        Args:
            days: عدد الأيام (السجلات الأقدم من هذا سيتم حذفها)
            
        Returns:
            int: عدد الملفات المحذوفة
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.is_file():
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        log_file.unlink()
                        deleted_count += 1
                    except Exception:
                        pass
        
        return deleted_count


# ==================== Global Logger Instance ====================

_global_logging_service: Optional[AdvancedLoggingService] = None


def get_logger(name: str = None) -> logging.Logger:
    """
    الحصول على logger عام
    
    Args:
        name: اسم الـ logger
        
    Returns:
        logging.Logger
    """
    global _global_logging_service
    
    if _global_logging_service is None:
        _global_logging_service = AdvancedLoggingService()
    
    return _global_logging_service.get_logger(name)


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    # إنشاء خدمة السجلات
    log_service = AdvancedLoggingService(
        app_name="TestApp",
        log_level="DEBUG"
    )
    
    logger = log_service.get_logger("TestModule")
    
    print("=" * 70)
    print("📝 اختبار نظام السجلات المتقدم")
    print("=" * 70)
    
    # اختبار مستويات مختلفة
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # اختبار مع بيانات إضافية
    log_service.info(
        "User logged in successfully",
        user_id=123,
        username="admin",
        ip_address="192.168.1.1"
    )
    
    # اختبار تسجيل الاستثناءات
    try:
        result = 10 / 0
    except Exception as e:
        log_service.exception("Division by zero error occurred")
    
    # اختبار أحداث الأمان
    log_service.log_security_event(
        event_type="LOGIN",
        user_id=123,
        username="admin",
        ip_address="192.168.1.1",
        description="Successful login",
        severity="INFO"
    )
    
    # اختبار مقاييس الأداء
    log_service.log_performance(
        operation="database_query",
        duration_ms=45.32,
        success=True,
        query_type="SELECT",
        rows_affected=100
    )
    
    print("\n" + "=" * 70)
    print(f"✅ تم إنشاء السجلات في: {log_service.log_dir}")
    print("=" * 70)
