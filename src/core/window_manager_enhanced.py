#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window Manager Enhanced - نسخة محسنة مع Caching و Signals Hooks
Enhanced Window Manager with Caching and Performance Improvements

الميزات الجديدة:
- Window Caching: تخزين مؤقت للنوافذ المفتوحة
- Signals Hooks: إشارات Qt للتفاعل مع النوافذ
- Performance Monitoring: مراقبة الأداء
- Window State Management: إدارة حالة النوافذ المتقدمة
"""

from __future__ import annotations

import weakref
import json
import logging
import time
from typing import Dict, List, Optional, Type, Any, Callable
from collections import defaultdict
from functools import partial

from PySide6.QtCore import QObject, QSettings, Slot, Signal, QTimer
from PySide6.QtWidgets import QWidget

logger = logging.getLogger("window_manager_enhanced")


class WindowPerformanceMetrics:
    """مقاييس أداء النافذة"""
    
    def __init__(self):
        self.open_count = 0
        self.total_open_time = 0.0
        self.last_opened = None
        self.last_closed = None
        self.average_open_time = 0.0
    
    def record_open(self):
        """تسجيل فتح النافذة"""
        self.open_count += 1
        self.last_opened = time.time()
    
    def record_close(self):
        """تسجيل إغلاق النافذة"""
        if self.last_opened:
            open_duration = time.time() - self.last_opened
            self.total_open_time += open_duration
            self.average_open_time = self.total_open_time / self.open_count if self.open_count > 0 else 0.0
            self.last_closed = time.time()


class WindowCache:
    """نظام تخزين مؤقت للنوافذ"""
    
    def __init__(self, max_size: int = 10):
        """
        تهيئة Cache
        
        Args:
            max_size: الحد الأقصى لعدد النوافذ المخزنة في Cache
        """
        self.max_size = max_size
        self._cache: Dict[str, QWidget] = {}
        self._access_times: Dict[str, float] = {}
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, window_key: str) -> Optional[QWidget]:
        """الحصول على نافذة من Cache"""
        if window_key in self._cache:
            window = self._cache[window_key]
            # التحقق من أن النافذة لا تزال موجودة
            if window and window.isVisible():
                self._access_times[window_key] = time.time()
                self._hit_count += 1
                return window
            else:
                # النافذة لم تعد موجودة، إزالتها من Cache
                del self._cache[window_key]
                if window_key in self._access_times:
                    del self._access_times[window_key]
        
        self._miss_count += 1
        return None
    
    def put(self, window_key: str, window: QWidget):
        """إضافة نافذة إلى Cache"""
        # إذا كان Cache ممتلئاً، إزالة الأقدم
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        self._cache[window_key] = window
        self._access_times[window_key] = time.time()
    
    def remove(self, window_key: str):
        """إزالة نافذة من Cache"""
        if window_key in self._cache:
            del self._cache[window_key]
        if window_key in self._access_times:
            del self._access_times[window_key]
    
    def clear(self):
        """مسح Cache بالكامل"""
        self._cache.clear()
        self._access_times.clear()
    
    def _evict_oldest(self):
        """إزالة أقدم نافذة من Cache"""
        if not self._access_times:
            return
        
        oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self.remove(oldest_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات Cache"""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "cached_windows": list(self._cache.keys())
        }


class EnhancedWindowManager(QObject):
    """
    Window Manager محسن مع Caching و Performance Monitoring
    
    الميزات الجديدة:
    - Window Caching: تخزين مؤقت للنوافذ المفتوحة
    - Performance Metrics: مقاييس الأداء
    - Signals Hooks: إشارات Qt للتفاعل
    - State Management: إدارة حالة النوافذ المتقدمة
    """
    
    # Signals
    window_opened = Signal(str, object)  # window_key, window_instance
    window_closed = Signal(str)  # window_key
    window_cached = Signal(str)  # window_key
    window_uncached = Signal(str)  # window_key
    performance_updated = Signal(str, dict)  # window_key, metrics
    
    def __init__(self, organization: str = "LogicalVersion", appname: str = "ERP", 
                 parent: Optional[QObject] = None, enable_caching: bool = True,
                 cache_size: int = 10):
        super().__init__(parent)
        
        # Import base WindowManager
        from src.core.window_manager import WindowManager
        self._base_manager = WindowManager(organization=organization, appname=appname, parent=parent)
        
        # Caching
        self.enable_caching = enable_caching
        self._cache = WindowCache(max_size=cache_size) if enable_caching else None
        
        # Performance Metrics
        self._metrics: Dict[str, WindowPerformanceMetrics] = defaultdict(WindowPerformanceMetrics)
        
        # Performance monitoring timer
        self._metrics_timer = QTimer(self)
        self._metrics_timer.timeout.connect(self._update_metrics)
        self._metrics_timer.start(60000)  # كل دقيقة
        
        # Logger
        self.logger = logger
    
    def register_window(self, *, window_key: str, window_class: Type[QWidget],
                       title: Optional[str] = None, singleton: bool = True,
                       init_kwargs: Optional[Dict[str, Any]] = None) -> None:
        """تسجيل نافذة (delegate to base manager)"""
        self._base_manager.register_window(
            window_key=window_key,
            window_class=window_class,
            title=title,
            singleton=singleton,
            init_kwargs=init_kwargs
        )
    
    def open_window(self, window_key: str, parent: Optional[QWidget] = None, 
                   **override_kwargs) -> Optional[QWidget]:
        """
        فتح نافذة مع Caching
        
        Returns:
            QWidget instance or None on failure
        """
        start_time = time.time()
        
        # محاولة الحصول من Cache أولاً
        if self.enable_caching and self._cache:
            cached_window = self._cache.get(window_key)
            if cached_window:
                self.logger.debug(f"Cache HIT: {window_key}")
                self.window_cached.emit(window_key)
                self._metrics[window_key].record_open()
                self.window_opened.emit(window_key, cached_window)
                return cached_window
        
        # Cache MISS - فتح نافذة جديدة
        self.logger.debug(f"Cache MISS: {window_key}")
        window = self._base_manager.open_window(window_key, parent=parent, **override_kwargs)
        
        if window:
            # إضافة إلى Cache
            if self.enable_caching and self._cache:
                self._cache.put(window_key, window)
            
            # تسجيل Metrics
            self._metrics[window_key].record_open()
            
            # إرسال Signal
            self.window_opened.emit(window_key, window)
            
            # تسجيل الأداء
            elapsed = time.time() - start_time
            if elapsed > 0.1:  # إذا استغرق أكثر من 100ms
                self.logger.warning(f"Slow window open: {window_key} took {elapsed:.3f}s")
        
        return window
    
    def close_window(self, window_key: str) -> bool:
        """إغلاق نافذة مع تنظيف Cache"""
        result = self._base_manager.close_window(window_key)
        
        if result:
            # إزالة من Cache
            if self.enable_caching and self._cache:
                self._cache.remove(window_key)
            
            # تسجيل Metrics
            self._metrics[window_key].record_close()
            
            # إرسال Signal
            self.window_closed.emit(window_key)
        
        return result
    
    def close_all(self) -> None:
        """إغلاق جميع النوافذ"""
        self._base_manager.close_all()
        
        # مسح Cache
        if self.enable_caching and self._cache:
            self._cache.clear()
    
    def get_open_instances(self, window_key: str) -> List[QWidget]:
        """الحصول على النوافذ المفتوحة"""
        return self._base_manager.get_open_instances(window_key)
    
    def is_open(self, window_key: str) -> bool:
        """التحقق من أن النافذة مفتوحة"""
        return self._base_manager.is_open(window_key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات Cache"""
        if self.enable_caching and self._cache:
            return self._cache.get_stats()
        return {"enabled": False}
    
    def get_performance_metrics(self, window_key: Optional[str] = None) -> Dict[str, Any]:
        """
        الحصول على مقاييس الأداء
        
        Args:
            window_key: مفتاح النافذة (None للحصول على جميع المقاييس)
        
        Returns:
            Dict with performance metrics
        """
        if window_key:
            metrics = self._metrics.get(window_key)
            if metrics:
                return {
                    "open_count": metrics.open_count,
                    "total_open_time": metrics.total_open_time,
                    "average_open_time": metrics.average_open_time,
                    "last_opened": metrics.last_opened,
                    "last_closed": metrics.last_closed
                }
            return {}
        else:
            return {
                key: {
                    "open_count": m.open_count,
                    "total_open_time": m.total_open_time,
                    "average_open_time": m.average_open_time
                }
                for key, m in self._metrics.items()
            }
    
    def _update_metrics(self):
        """تحديث المقاييس وإرسال Signals"""
        for window_key, metrics in self._metrics.items():
            if metrics.open_count > 0:
                metrics_dict = {
                    "open_count": metrics.open_count,
                    "average_open_time": metrics.average_open_time,
                    "total_open_time": metrics.total_open_time
                }
                self.performance_updated.emit(window_key, metrics_dict)
    
    # Delegate other methods to base manager
    def __getattr__(self, name):
        """Delegate unknown attributes to base manager"""
        return getattr(self._base_manager, name)

