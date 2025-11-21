#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
معالج الأخطاء العام (Global Exception Handler)
يوفر معالجة موحدة وآمنة للأخطاء غير المتوقعة
"""

import sys
import traceback
import logging
from typing import Optional, Callable, Any
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import QObject, Signal


class ExceptionType:
    """أنواع الاستثناءات المخصصة"""
    
    # أخطاء عامة
    GENERAL = "GENERAL_ERROR"
    
    # أخطاء قاعدة البيانات
    DATABASE_CONNECTION = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY = "DATABASE_QUERY_ERROR"
    DATABASE_INTEGRITY = "DATABASE_INTEGRITY_ERROR"
    
    # أخطاء التحقق
    VALIDATION = "VALIDATION_ERROR"
    
    # أخطاء منطق الأعمال
    BUSINESS_LOGIC = "BUSINESS_LOGIC_ERROR"
    
    # أخطاء الشبكة
    NETWORK = "NETWORK_ERROR"
    
    # أخطاء الملفات
    FILE_IO = "FILE_IO_ERROR"
    
    # أخطاء الأذونات
    PERMISSION = "PERMISSION_ERROR"
    
    # أخطاء النظام
    SYSTEM = "SYSTEM_ERROR"


class LogicalVersionError(Exception):
    """
    استثناء عام لنظام الإصدار المنطقي
    """
    
    def __init__(
        self,
        message: str,
        error_type: str = ExceptionType.GENERAL,
        details: Optional[dict] = None,
        recoverable: bool = True
    ):
        """
        تهيئة الاستثناء
        
        Args:
            message: رسالة الخطأ
            error_type: نوع الخطأ
            details: تفاصيل إضافية
            recoverable: هل يمكن الاستمرار بعد هذا الخطأ؟
        """
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()


class DatabaseError(LogicalVersionError):
    """أخطاء قاعدة البيانات"""
    
    def __init__(self, message: str, query: str = None, **kwargs):
        super().__init__(
            message,
            error_type=ExceptionType.DATABASE_QUERY,
            details={'query': query},
            **kwargs
        )


class ValidationError(LogicalVersionError):
    """أخطاء التحقق من البيانات"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(
            message,
            error_type=ExceptionType.VALIDATION,
            details={'field': field, 'value': value},
            **kwargs
        )


class BusinessLogicError(LogicalVersionError):
    """أخطاء منطق الأعمال"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_type=ExceptionType.BUSINESS_LOGIC,
            **kwargs
        )


class GlobalExceptionHandler(QObject):
    """
    معالج عام للأخطاء غير المتوقعة
    
    المزايا:
    - اعتراض جميع الأخطاء غير المعالجة
    - تسجيل تفصيلي للأخطاء
    - عرض رسائل واضحة للمستخدم
    - محاولة الاستعادة التلقائية
    - حفظ حالة التطبيق عند الأخطاء الحرجة
    """
    
    # إشارة لإعلام التطبيق بحدوث خطأ حرج
    critical_error_occurred = Signal(str, str)
    
    def __init__(
        self,
        app_name: str = "الإصدار المنطقي",
        logger: Optional[logging.Logger] = None,
        enable_crash_dialog: bool = True,
        crash_report_path: Optional[Path] = None
    ):
        """
        تهيئة معالج الأخطاء
        
        Args:
            app_name: اسم التطبيق
            logger: مسجل الأخطاء
            enable_crash_dialog: عرض نافذة عند الأخطاء الحرجة
            crash_report_path: مسار حفظ تقارير الأعطال
        """
        super().__init__()
        
        self.app_name = app_name
        self.logger = logger or logging.getLogger(__name__)
        self.enable_crash_dialog = enable_crash_dialog
        
        # مسار تقارير الأعطال
        if crash_report_path:
            self.crash_report_path = Path(crash_report_path)
        else:
            self.crash_report_path = Path("logs") / "crash_reports"
        
        self.crash_report_path.mkdir(parents=True, exist_ok=True)
        
        # تثبيت معالج الاستثناءات
        self.install()
        
        # وظيفة للحفظ التلقائي (يمكن تعيينها من الخارج)
        self.emergency_save_callback: Optional[Callable] = None
    
    def install(self) -> None:
        """تثبيت معالج الاستثناءات العام"""
        # Python exceptions
        sys.excepthook = self.handle_exception
        
        # Qt exceptions (في حال استخدام Qt)
        try:
            import PySide6.QtCore as QtCore
            QtCore.qInstallMessageHandler(self.qt_message_handler)
        except Exception:
            pass
    
    def handle_exception(
        self,
        exc_type: type,
        exc_value: Exception,
        exc_traceback: Any
    ) -> None:
        """
        معالج الاستثناءات العام
        
        Args:
            exc_type: نوع الاستثناء
            exc_value: قيمة الاستثناء
            exc_traceback: تتبع الاستثناء
        """
        # تجاهل KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # تنسيق معلومات الخطأ
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # تحديد نوع الخطأ
        if isinstance(exc_value, LogicalVersionError):
            error_type = exc_value.error_type
            is_recoverable = exc_value.recoverable
            details = exc_value.details
        else:
            error_type = ExceptionType.GENERAL
            is_recoverable = False
            details = {}
        
        # تسجيل الخطأ
        self.logger.critical(
            f"استثناء غير معالج: {exc_type.__name__}: {exc_value}\n{error_msg}",
            extra={
                'error_type': error_type,
                'recoverable': is_recoverable,
                'details': details
            }
        )
        
        # حفظ تقرير العطل
        self._save_crash_report(exc_type, exc_value, error_msg, details)
        
        # محاولة الحفظ التلقائي
        if not is_recoverable:
            self._attempt_emergency_save()
        
        # عرض رسالة للمستخدم
        self._show_error_dialog(exc_type, exc_value, is_recoverable)
        
        # إرسال إشارة للتطبيق
        self.critical_error_occurred.emit(str(exc_value), error_type)
        
        # إنهاء التطبيق إذا كان الخطأ غير قابل للاستعادة
        if not is_recoverable:
            sys.exit(1)
    
    def qt_message_handler(
        self,
        msg_type: Any,
        context: Any,
        message: str
    ) -> None:
        """
        معالج رسائل Qt
        
        Args:
            msg_type: نوع الرسالة
            context: سياق الرسالة
            message: نص الرسالة
        """
        # تحويل رسائل Qt للـ logger
        if msg_type == 0:  # QtDebugMsg
            self.logger.debug(f"Qt: {message}")
        elif msg_type == 1:  # QtWarningMsg
            self.logger.warning(f"Qt: {message}")
        elif msg_type == 2:  # QtCriticalMsg
            self.logger.error(f"Qt: {message}")
        elif msg_type == 3:  # QtFatalMsg
            self.logger.critical(f"Qt: {message}")
    
    def _save_crash_report(
        self,
        exc_type: type,
        exc_value: Exception,
        traceback_text: str,
        details: dict
    ) -> Path:
        """
        حفظ تقرير تفصيلي عن العطل
        
        Returns:
            Path: مسار ملف التقرير
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.crash_report_path / f"crash_{timestamp}.txt"
        
        try:
            import platform
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"تقرير عطل - {self.app_name}\n")
                f.write("=" * 80 + "\n\n")
                
                # معلومات النظام
                f.write("معلومات النظام:\n")
                f.write(f"  التاريخ والوقت: {datetime.now().isoformat()}\n")
                f.write(f"  نظام التشغيل: {platform.system()} {platform.release()}\n")
                f.write(f"  Python: {sys.version}\n")
                f.write(f"  المعمارية: {platform.machine()}\n\n")
                
                # معلومات الخطأ
                f.write("معلومات الخطأ:\n")
                f.write(f"  النوع: {exc_type.__name__}\n")
                f.write(f"  الرسالة: {exc_value}\n")
                
                if details:
                    f.write(f"  التفاصيل: {details}\n")
                
                f.write("\n")
                
                # التتبع الكامل
                f.write("التتبع الكامل:\n")
                f.write(traceback_text)
                f.write("\n")
                
                # معلومات إضافية
                f.write("=" * 80 + "\n")
            
            self.logger.info(f"تم حفظ تقرير العطل في: {report_file}")
            
        except Exception as e:
            self.logger.error(f"فشل حفظ تقرير العطل: {e}")
        
        return report_file
    
    def _attempt_emergency_save(self) -> bool:
        """
        محاولة الحفظ التلقائي للبيانات
        
        Returns:
            bool: نجح الحفظ أم لا
        """
        if not self.emergency_save_callback:
            return False
        
        try:
            self.logger.warning("محاولة الحفظ التلقائي...")
            self.emergency_save_callback()
            self.logger.info("✅ نجح الحفظ التلقائي")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل الحفظ التلقائي: {e}")
            return False
    
    def _show_error_dialog(
        self,
        exc_type: type,
        exc_value: Exception,
        is_recoverable: bool
    ) -> None:
        """
        عرض نافذة خطأ للمستخدم
        
        Args:
            exc_type: نوع الاستثناء
            exc_value: قيمة الاستثناء
            is_recoverable: قابل للاستعادة؟
        """
        if not self.enable_crash_dialog:
            return
        
        try:
            app = QApplication.instance()
            if not app:
                return
            
            # تحديد نوع الرسالة
            if is_recoverable:
                icon = QMessageBox.Warning
                title = "تحذير"
                text = "حدث خطأ ولكن يمكن المتابعة"
            else:
                icon = QMessageBox.Critical
                title = "خطأ حرج"
                text = "حدث خطأ غير متوقع"
            
            # إنشاء الرسالة
            msg_box = QMessageBox()
            msg_box.setIcon(icon)
            msg_box.setWindowTitle(f"{self.app_name} - {title}")
            msg_box.setText(text)
            msg_box.setInformativeText(
                f"{exc_type.__name__}: {exc_value}\n\n"
                "سيتم حفظ تفاصيل الخطأ في السجلات."
            )
            
            if not is_recoverable:
                msg_box.setInformativeText(
                    msg_box.informativeText() + "\n\nسيتم إغلاق التطبيق."
                )
            
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setTextInteractionFlags(msg_box.textInteractionFlags())
            
            # عرض النافذة
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"فشل عرض نافذة الخطأ: {e}")
    
    def set_emergency_save_callback(self, callback: Callable) -> None:
        """
        تعيين دالة الحفظ التلقائي
        
        Args:
            callback: دالة تُستدعى عند الحفظ التلقائي
        """
        self.emergency_save_callback = callback


# ==================== Error Recovery Service ====================

class ErrorRecoveryService:
    """
    خدمة استعادة الأخطاء
    
    توفر آليات لإصلاح الأخطاء الشائعة تلقائياً
    """
    
    def __init__(self, db_manager=None, logger: Optional[logging.Logger] = None):
        """
        تهيئة خدمة الاستعادة
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger: مسجل الأحداث
        """
        self.db = db_manager
        self.logger = logger or logging.getLogger(__name__)
    
    def recover_from_database_error(self) -> bool:
        """
        محاولة إصلاح قاعدة البيانات
        
        Returns:
            bool: نجح الإصلاح أم لا
        """
        if not self.db:
            return False
        
        try:
            self.logger.info("محاولة إصلاح قاعدة البيانات...")
            
            # 1. فحص السلامة
            self.logger.debug("فحص سلامة قاعدة البيانات...")
            result = self.db.fetch_one("PRAGMA integrity_check")
            
            if result and result[0] != 'ok':
                self.logger.warning(f"مشكلة في السلامة: {result}")
                return False
            
            # 2. VACUUM لتحسين الأداء
            self.logger.debug("تنفيذ VACUUM...")
            self.db.execute_query("VACUUM")
            
            # 3. إعادة فهرسة
            self.logger.debug("إعادة الفهرسة...")
            self.db.execute_query("REINDEX")
            
            # 4. تحليل للإحصائيات
            self.logger.debug("تحليل الإحصائيات...")
            self.db.execute_query("ANALYZE")
            
            self.logger.info("✅ تم إصلاح قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل إصلاح قاعدة البيانات: {e}")
            return False
    
    def rollback_transaction(self) -> bool:
        """
        التراجع عن المعاملة الحالية
        
        Returns:
            bool: نجح التراجع أم لا
        """
        if not self.db:
            return False
        
        try:
            self.logger.info("التراجع عن المعاملة...")
            self.db.execute_query("ROLLBACK")
            self.logger.info("✅ تم التراجع بنجاح")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل التراجع: {e}")
            return False
    
    def create_backup_before_recovery(self) -> Optional[Path]:
        """
        إنشاء نسخة احتياطية قبل محاولة الإصلاح
        
        Returns:
            Optional[Path]: مسار النسخة الاحتياطية
        """
        try:
            from datetime import datetime
            import shutil
            
            if not self.db or not hasattr(self.db, 'db_path'):
                return None
            
            backup_dir = Path("data/emergency_backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"emergency_backup_{timestamp}.db"
            
            self.logger.info(f"إنشاء نسخة احتياطية في: {backup_path}")
            shutil.copy2(self.db.db_path, backup_path)
            
            self.logger.info("✅ تم إنشاء النسخة الاحتياطية")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"❌ فشل إنشاء النسخة الاحتياطية: {e}")
            return None


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    # إعداد logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # إنشاء معالج الأخطاء
    handler = GlobalExceptionHandler(
        app_name="Test App",
        logger=logger,
        enable_crash_dialog=False
    )
    
    # دالة حفظ تلقائي تجريبية
    def emergency_save():
        logger.info("تنفيذ الحفظ التلقائي...")
    
    handler.set_emergency_save_callback(emergency_save)
    
    print("=" * 70)
    print("🛡️ اختبار معالج الأخطاء العام")
    print("=" * 70)
    
    # 1. اختبار استثناء مخصص
    try:
        raise ValidationError(
            "قيمة السعر غير صالحة",
            field="price",
            value=-10
        )
    except ValidationError as e:
        print(f"\n✅ تم التقاط استثناء التحقق: {e}")
        print(f"   النوع: {e.error_type}")
        print(f"   التفاصيل: {e.details}")
    
    # 2. اختبار استثناء قاعدة بيانات
    try:
        raise DatabaseError(
            "فشل تنفيذ الاستعلام",
            query="SELECT * FROM invalid_table"
        )
    except DatabaseError as e:
        print(f"\n✅ تم التقاط خطأ قاعدة البيانات: {e}")
    
    # 3. اختبار استثناء غير معالج (سيتم اعتراضه بالمعالج العام)
    print("\n🔥 اختبار استثناء غير معالج...")
    print("(سيتم اعتراضه بواسطة المعالج العام)")
    
    # raise RuntimeError("هذا خطأ غير متوقع للاختبار!")
    
    print("\n" + "=" * 70)
    print("✅ اكتملت الاختبارات")
    print("=" * 70)
