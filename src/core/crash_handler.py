#!/usr/bin/env python3
"""
نظام التقاط الأعطال - Global Crash Handler
يلتقط كل الأخطاء غير المعالجة ويعرض حوار ودود بدل الإغلاق المفاجئ
"""

import os
import sys
import time
import traceback
import logging
import platform
import json
import faulthandler
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt


class CrashHandler:
    """نظام التقاط الأعطال العالمي — Singleton"""
    
    _instance: Optional['CrashHandler'] = None
    
    MAX_CRASHES_BEFORE_SUGGEST_RESTART = 3
    
    def __init__(self, app_name: str = "El-Joumla ERP",
                 app_version: str = "6.0.0",
                 log_dir: str = "logs/crash"):
        self.app_name = app_name
        self.app_version = app_version
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self._crash_count = 0
        self._original_excepthook = None
        self._sentry_enabled = False
        
    @classmethod
    def get_instance(cls, **kwargs) -> 'CrashHandler':
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    def install(self):
        """تثبيت معالجات الأعطال العالمية"""
        # 1. faulthandler — يلتقط C-level crashes
        try:
            crash_log = self.log_dir / "faulthandler.log"
            faulthandler.enable(file=open(crash_log, 'w'), all_threads=True)
            self.logger.info("faulthandler مفعّل")
        except Exception as e:
            self.logger.warning(f"فشل تفعيل faulthandler: {e}")
        
        # 2. Python exception hook
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler
        self.logger.info("global exception hook مثبّت")
        
        # 3. Sentry (optional)
        self._try_init_sentry()
        
        self.logger.info("نظام التقاط الأعطال مثبّت بنجاح")
    
    def _try_init_sentry(self):
        """محاولة تفعيل Sentry للإبلاغ عن الأعطال عن بُعد"""
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=os.environ.get("SENTRY_DSN", ""),
                traces_sample_rate=0.1,
                environment="production",
                release=self.app_version,
            )
            self._sentry_enabled = True
            self.logger.info("Sentry مفعّل")
        except ImportError:
            self.logger.info("sentry-sdk غير مثبّت — تقارير الأعطال محلية فقط")
        except Exception as e:
            self.logger.warning(f"فشل تفعيل Sentry: {e}")
    
    def _global_exception_handler(self, exc_type, exc_value, exc_tb):
        """معالج الاستثناءات العالمي"""
        self._crash_count += 1
        
        # تنسيق traceback
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        # تسجيل في ملف
        self._write_crash_log(exc_type, exc_value, exc_tb, tb_str)
        
        # إرسال إلى Sentry
        if self._sentry_enabled:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(exc_value)
            except Exception:
                pass
        
        # تسجيل في logger
        self.logger.critical(f"استثناء غير معالج [{self._crash_count}]: {exc_value}", 
                           exc_info=(exc_type, exc_value, exc_tb))
        
        # عرض حوار للمستخدم
        self._show_crash_dialog(exc_value, tb_str)
    
    def _write_crash_log(self, exc_type, exc_value, exc_tb, tb_str: str):
        """كتابة سجل العطل في ملف"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = self.log_dir / f"crash_{timestamp}.json"
            
            crash_data = {
                "timestamp": datetime.now().isoformat(),
                "app_name": self.app_name,
                "app_version": self.app_version,
                "crash_number": self._crash_count,
                "exception": {
                    "type": exc_type.__name__ if exc_type else "Unknown",
                    "message": str(exc_value),
                    "traceback": tb_str,
                },
                "system": self._get_system_info(),
            }
            
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(crash_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"سجل العطل كُتب في: {crash_file}")
            
        except Exception as e:
            self.logger.error(f"فشل كتابة سجل العطل: {e}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """جمع معلومات النظام للتشخيص"""
        info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "pid": os.getpid(),
            "cwd": os.getcwd(),
        }
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem = process.memory_info()
            info["memory_rss_mb"] = round(mem.rss / (1024 * 1024), 1)
            info["memory_vms_mb"] = round(mem.vms / (1024 * 1024), 1)
        except Exception:
            pass
        
        # PySide6 version
        try:
            import PySide6
            info["pyside6_version"] = PySide6.__version__
        except Exception:
            pass
        
        return info
    
    def _show_crash_dialog(self, exc_value, tb_str: str):
        """عرض حوار العطل للمستخدم"""
        try:
            app = QApplication.instance()
            if not app:
                # لا تطبيق Qt — اطبع في console
                print(f"\n{'='*60}")
                print(f"خطأ غير متوقع: {exc_value}")
                print(f"{'='*60}")
                print(tb_str)
                return
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("خطأ غير متوقع")
            msg.setTextFormat(Qt.PlainText)
            
            # رسالة مخصصة
            error_msg = str(exc_value)[:200]  # أول 200 حرف فقط
            crash_num = self._crash_count
            
            if crash_num >= self.MAX_CRASHES_BEFORE_SUGGEST_RESTART:
                text = (
                    f"حدث خطأ متكرر ({crash_num} مرة):\n\n"
                    f"{error_msg}\n\n"
                    f"يُنصح بإعادة تشغيل التطبيق لضمان الاستقرار."
                )
            else:
                text = (
                    f"حدث خطأ غير متوقع:\n\n"
                    f"{error_msg}\n\n"
                    f"يمكنك الاستمرار في العمل، لكن بعض الوظائف قد لا تعمل بشكل صحيح."
                )
            
            msg.setText(text)
            msg.setDetailedText(tb_str)
            
            # أزرار
            continue_btn = msg.addButton("استمرار", QMessageBox.AcceptRole)
            
            if crash_num >= self.MAX_CRASHES_BEFORE_SUGGEST_RESTART:
                msg.addButton("إعادة تشغيل", QMessageBox.ResetRole)
            
            msg.addButton("إغلاق التطبيق", QMessageBox.RejectRole)
            msg.setDefaultButton(continue_btn)
            
            msg.exec()
            
            # معالجة النتيجة
            if msg.buttonRole(msg.clickedButton()) == QMessageBox.RejectRole:
                sys.exit(1)
            elif msg.buttonRole(msg.clickedButton()) == QMessageBox.ResetRole:
                # إعادة التشغيل
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
        except Exception as e:
            # فشل عرض الحوار — لا خيار سوى الطباعة
            print(f"خطأ في عرض حوار العطل: {e}")
            print(f"الخطأ الأصلي: {exc_value}")
    
    @property
    def crash_count(self) -> int:
        return self._crash_count
