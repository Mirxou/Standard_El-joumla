#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window Registry - نظام التسجيل التلقائي للنوافذ
Auto-Registration System for Windows

يقوم بمسح مجلد النوافذ واستخراج جميع النوافذ التي تحتوي على window_key
وتسجيلها تلقائياً في WindowManager
"""

import os
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Type, Optional, Any
import logging

from PySide6.QtWidgets import QWidget

logger = logging.getLogger("window_registry")


class WindowRegistry:
    """
    نظام التسجيل التلقائي للنوافذ
    
    يقوم بـ:
    1. مسح مجلد النوافذ
    2. استخراج جميع الكلاسات التي تحتوي على window_key
    3. تسجيلها تلقائياً في WindowManager
    """
    
    def __init__(self, windows_directory: str = None):
        """
        تهيئة Window Registry
        
        Args:
            windows_directory: مسار مجلد النوافذ (افتراضي: src/ui/windows)
        """
        if windows_directory is None:
            # افتراضي: src/ui/windows
            # من src/core/window_registry.py إلى src/ui/windows
            base_path = Path(__file__).parent.parent  # src/
            self.windows_directory = base_path / "ui" / "windows"
        else:
            self.windows_directory = Path(windows_directory)
        
        self.discovered_windows: Dict[str, Type[QWidget]] = {}
        self.failed_imports: List[str] = []
    
    def scan_windows_directory(self) -> Dict[str, Type[QWidget]]:
        """
        مسح مجلد النوافذ واستخراج جميع النوافذ
        
        Returns:
            Dict[str, Type[QWidget]]: قاموس بـ window_key -> WindowClass
        """
        discovered = {}
        
        if not self.windows_directory.exists():
            logger.warning(f"مجلد النوافذ غير موجود: {self.windows_directory}")
            return discovered
        
        # مسح جميع ملفات Python في المجلد
        for file_path in self.windows_directory.glob("*_window.py"):
            try:
                # استخراج اسم الملف بدون الامتداد
                module_name = file_path.stem
                
                # استيراد الوحدة
                module = self._import_window_module(module_name)
                if module is None:
                    continue
                
                # البحث عن كلاسات النوافذ في الوحدة
                window_classes = self._extract_window_classes(module)
                
                for window_class in window_classes:
                    window_key = getattr(window_class, "window_key", None)
                    if window_key:
                        if window_key in discovered:
                            logger.warning(
                                f"window_key مكرر: {window_key} في {window_class.__name__} "
                                f"و {discovered[window_key].__name__}"
                            )
                        discovered[window_key] = window_class
                        logger.debug(f"تم اكتشاف نافذة: {window_key} -> {window_class.__name__}")
                
            except Exception as e:
                logger.exception(f"خطأ في مسح الملف {file_path}: {e}")
                self.failed_imports.append(str(file_path))
        
        self.discovered_windows = discovered
        return discovered
    
    def _import_window_module(self, module_name: str) -> Optional[Any]:
        """
        استيراد وحدة النافذة
        
        Args:
            module_name: اسم الوحدة (بدون .py)
        
        Returns:
            الوحدة المستوردة أو None في حالة الفشل
        """
        try:
            # بناء مسار الاستيراد
            # من: src/ui/windows/reports_window.py
            # إلى: src.ui.windows.reports_window
            relative_path = self.windows_directory.relative_to(
                Path(__file__).parent.parent.parent
            )
            module_path = ".".join(relative_path.parts) + "." + module_name
            
            module = importlib.import_module(module_path)
            return module
            
        except ImportError as e:
            logger.warning(f"فشل استيراد {module_name}: {e}")
            return None
        except Exception as e:
            logger.exception(f"خطأ غير متوقع في استيراد {module_name}: {e}")
            return None
    
    def _extract_window_classes(self, module: Any) -> List[Type[QWidget]]:
        """
        استخراج كلاسات النوافذ من الوحدة
        
        Args:
            module: الوحدة المستوردة
        
        Returns:
            List[Type[QWidget]]: قائمة بكلاسات النوافذ
        """
        window_classes = []
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # التحقق من أن الكلاس هو QWidget أو QMainWindow
            if not issubclass(obj, QWidget):
                continue
            
            # تجاهل الكلاسات المبنية (built-in)
            if obj.__module__ != module.__name__:
                continue
            
            # التحقق من وجود window_key
            if hasattr(obj, "window_key"):
                window_classes.append(obj)
        
        return window_classes
    
    def register_all(self, window_manager, init_kwargs_provider: Optional[callable] = None) -> Dict[str, bool]:
        """
        تسجيل جميع النوافذ المكتشفة في WindowManager
        
        Args:
            window_manager: WindowManager instance
            init_kwargs_provider: دالة تأخذ window_key وتعيد init_kwargs
        
        Returns:
            Dict[str, bool]: قاموس بنتائج التسجيل (window_key -> success)
        """
        if not self.discovered_windows:
            self.scan_windows_directory()
        
        results = {}
        
        for window_key, window_class in self.discovered_windows.items():
            try:
                # الحصول على init_kwargs
                init_kwargs = {}
                if init_kwargs_provider:
                    init_kwargs = init_kwargs_provider(window_key, window_class) or {}
                
                # الحصول على window_singleton
                singleton = getattr(window_class, "window_singleton", True)
                
                # الحصول على window_title
                title = getattr(window_class, "window_title", None) or window_key
                
                # التسجيل
                window_manager.register_window(
                    window_key=window_key,
                    window_class=window_class,
                    title=title,
                    singleton=singleton,
                    init_kwargs=init_kwargs
                )
                
                results[window_key] = True
                logger.info(f"✅ تم تسجيل النافذة: {window_key} ({window_class.__name__})")
                
            except Exception as e:
                results[window_key] = False
                logger.exception(f"❌ فشل تسجيل النافذة {window_key}: {e}")
        
        return results
    
    def get_discovered_windows(self) -> Dict[str, Type[QWidget]]:
        """الحصول على النوافذ المكتشفة"""
        if not self.discovered_windows:
            self.scan_windows_directory()
        return self.discovered_windows
    
    def get_failed_imports(self) -> List[str]:
        """الحصول على قائمة الملفات التي فشل استيرادها"""
        return self.failed_imports


def create_init_kwargs_provider(db_manager=None, **services):
    """
    إنشاء دالة لتوفير init_kwargs للنوافذ
    
    Args:
        db_manager: DatabaseManager instance
        **services: خدمات إضافية (payment_service, inventory_service, etc.)
    
    Returns:
        callable: دالة تأخذ window_key وتعيد init_kwargs
    """
    def provider(window_key: str, window_class: Type[QWidget]) -> Dict[str, Any]:
        kwargs = {}
        
        # إضافة db_manager لجميع النوافذ
        if db_manager:
            kwargs["db_manager"] = db_manager
        
        # إضافة خدمات خاصة حسب window_key
        if window_key == "cycle_count":
            if "cycle_count_service" in services:
                kwargs["service"] = services["cycle_count_service"]
        
        if window_key == "payment_dashboard":
            if "payment_service" in services:
                kwargs["payment_service"] = services["payment_service"]
        
        if window_key == "accounts":
            if "payment_service" in services:
                kwargs["payment_service"] = services["payment_service"]
        
        # يمكن إضافة المزيد من الحالات الخاصة هنا
        
        return kwargs
    
    return provider

