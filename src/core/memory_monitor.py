#!/usr/bin/env python3
"""
نظام مراقبة الذاكرة - Memory Monitoring System
يراقب استهلاك الذاكرة ويكشف التسريبات ويطلق تحذيرات عند تجاوز الحدود
"""

import gc
import os
import time
import logging
import tracemalloc
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtCore import QObject, QTimer, Signal

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemoryMonitor(QObject):
    """نظام مراقبة الذاكرة المتكامل"""
    
    # إشارات Qt
    memory_warning = Signal(str, float)    # (level, mb_used)
    memory_critical = Signal(str, float)   # (level, mb_used)
    leak_detected = Signal(str, float)     # (description, mb_leaked)
    
    # حدود التحذير (بالميغابايت)
    WARNING_THRESHOLD_MB = 300
    CRITICAL_THRESHOLD_MB = 500
    LEAK_DELTA_MB = 20          # زيادة 20MB بين القياسات = تسريب محتمل
    LEAK_CHECK_INTERVALS = 5    # عدد القياسات قبل الإعلان عن تسريب
    
    def __init__(self, parent=None, 
                 warning_mb: float = 300,
                 critical_mb: float = 500,
                 check_interval_ms: int = 30000):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # حدود مخصصة
        self.WARNING_THRESHOLD_MB = warning_mb
        self.CRITICAL_THRESHOLD_MB = critical_mb
        
        # حالة المراقبة
        self._monitoring = False
        self._start_time: Optional[float] = None
        self._peak_rss_mb: float = 0.0
        self._history: List[Dict[str, Any]] = []
        self._max_history = 120  # 120 قياس × 30 ث = ساعة واحدة
        
        # كشف التسريب
        self._rss_samples: List[float] = []
        self._leak_confirmed = False
        
        # مؤقت Qt
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_memory)
        self._check_interval_ms = check_interval_ms
        
        # tracemalloc
        self._tracemalloc_started = False
        self._snapshot: Optional[Any] = None
        
    def start(self) -> bool:
        """بدء مراقبة الذاكرة"""
        if self._monitoring:
            return True
            
        try:
            # تشغيل tracemalloc
            if not tracemalloc.is_tracing():
                tracemalloc.start(25)  # 25 إطارات
                self._tracemalloc_started = True
            
            self._start_time = time.time()
            self._snapshot = tracemalloc.take_snapshot()
            self._monitoring = True
            
            # بدء المؤقت
            self._timer.start(self._check_interval_ms)
            
            self.logger.info(f"مراقبة الذاكرة بدأت — حدود: تحذير={self.WARNING_THRESHOLD_MB}MB, حرج={self.CRITICAL_THRESHOLD_MB}MB")
            return True
            
        except Exception as e:
            self.logger.error(f"فشل بدء مراقبة الذاكرة: {e}")
            return False
    
    def stop(self):
        """إيقاف مراقبة الذاكرة"""
        self._timer.stop()
        self._monitoring = False
        
        if self._tracemalloc_started and tracemalloc.is_tracing():
            tracemalloc.stop()
            self._tracemalloc_started = False
        
        self.logger.info("مراقبة الذاكرة أُوقفت")
    
    def _check_memory(self):
        """فحص الذاكرة دورياً"""
        try:
            stats = self.get_memory_stats()
            if not stats:
                return
            
            rss_mb = stats.get("rss_mb", 0)
            
            # تحديث الذروة
            if rss_mb > self._peak_rss_mb:
                self._peak_rss_mb = rss_mb
            
            # تسجيل في التاريخ
            self._history.append({
                "time": time.time(),
                "rss_mb": rss_mb,
                **stats
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            # فحص الحدود
            if rss_mb >= self.CRITICAL_THRESHOLD_MB:
                self.logger.critical(f"ذاكرة حرجة: {rss_mb:.1f}MB >= {self.CRITICAL_THRESHOLD_MB}MB")
                self.memory_critical.emit("critical", rss_mb)
                # محاولة تنظيف
                collected = gc.collect()
                self.logger.info(f"gc.collect() أعاد {collected} كائن")
                
            elif rss_mb >= self.WARNING_THRESHOLD_MB:
                self.logger.warning(f"ذاكرة عالية: {rss_mb:.1f}MB >= {self.WARNING_THRESHOLD_MB}MB")
                self.memory_warning.emit("warning", rss_mb)
            
            # فحص التسريب
            self._check_for_leak(rss_mb)
            
            # تحديث snapshot
            if tracemalloc.is_tracing():
                self._snapshot = tracemalloc.take_snapshot()
                
        except Exception as e:
            self.logger.error(f"خطأ في فحص الذاكرة: {e}")
    
    def _check_for_leak(self, current_rss_mb: float):
        """كشف تسريب الذاكرة"""
        self._rss_samples.append(current_rss_mb)
        
        # نحتاج عينات كافية
        if len(self._rss_samples) < self.LEAK_CHECK_INTERVALS:
            return
        
        # نحتفظ بآخر N عينات فقط
        if len(self._rss_samples) > self.LEAK_CHECK_INTERVALS * 2:
            self._rss_samples = self._rss_samples[-self.LEAK_CHECK_INTERVALS:]
        
        # فحص الاتجاه الصاعد
        recent = self._rss_samples[-self.LEAK_CHECK_INTERVALS:]
        first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
        second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        
        delta = second_half - first_half
        if delta >= self.LEAK_DELTA_MB and not self._leak_confirmed:
            self._leak_confirmed = True
            desc = f"تسريب محتمل: {delta:.1f}MB زيادة في {self.LEAK_CHECK_INTERVALS} قياس"
            self.logger.warning(desc)
            self.leak_detected.emit(desc, delta)
            
            # محاولة تنظيف
            collected = gc.collect()
            self.logger.info(f"gc.collect() بعد كشف تسريب: {collected} كائن")
        elif delta < self.LEAK_DELTA_MB / 2:
            self._leak_confirmed = False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الذاكرة"""
        stats = {}
        
        # psutil (OS-level)
        if HAS_PSUTIL:
            try:
                process = psutil.Process(os.getpid())
                mem_info = process.memory_info()
                stats["rss_mb"] = mem_info.rss / (1024 * 1024)
                stats["vms_mb"] = mem_info.vms / (1024 * 1024)
                stats["peak_rss_mb"] = self._peak_rss_mb
                
                # معلومات النظام
                sys_mem = psutil.virtual_memory()
                stats["system_total_mb"] = sys_mem.total / (1024 * 1024)
                stats["system_used_pct"] = sys_mem.percent
            except Exception:
                stats["rss_mb"] = 0
                stats["vms_mb"] = 0
        else:
            # تقدير بدون psutil
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                stats["traced_mb"] = current / (1024 * 1024)
                stats["traced_peak_mb"] = peak / (1024 * 1024)
                stats["rss_mb"] = current / (1024 * 1024)  # تقدير
            else:
                stats["rss_mb"] = 0
        
        # tracemalloc
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            stats["tracemalloc_current_mb"] = current / (1024 * 1024)
            stats["tracemalloc_peak_mb"] = peak / (1024 * 1024)
        
        # gc
        stats["gc_count"] = gc.get_count()
        stats["gc_objects"] = len(gc.get_objects())
        
        # مدة التشغيل
        if self._start_time:
            stats["uptime_seconds"] = time.time() - self._start_time
        
        return stats
    
    def get_top_allocations(self, n: int = 20) -> List[Tuple[str, float]]:
        """الحصول على أعلى N تخصيصات ذاكرة"""
        if not tracemalloc.is_tracing() or self._snapshot is None:
            return []
        
        try:
            current = tracemalloc.take_snapshot()
            stats = current.compare_to(self._snapshot, 'lineno')
            
            result = []
            for stat in stats[:n]:
                result.append((str(stat), stat.size / 1024))
            return result
        except Exception:
            return []
    
    def generate_report(self) -> str:
        """إنشاء تقرير شامل عن الذاكرة"""
        stats = self.get_memory_stats()
        lines = [
            "=" * 60,
            "تقرير مراقبة الذاكرة — El-Joumla ERP",
            "=" * 60,
            f"الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        if "rss_mb" in stats:
            lines.append(f"RSS (الذاكرة الفعلية): {stats['rss_mb']:.1f} MB")
        if "vms_mb" in stats:
            lines.append(f"VMS (الذاكرة الافتراضية): {stats['vms_mb']:.1f} MB")
        lines.append(f"الذروة: {self._peak_rss_mb:.1f} MB")
        
        if "tracemalloc_current_mb" in stats:
            lines.append(f"Python المتعقب: {stats['tracemalloc_current_mb']:.1f} MB")
            lines.append(f"Python الذروة المتعقبة: {stats['tracemalloc_peak_mb']:.1f} MB")
        
        if "system_total_mb" in stats:
            lines.append(f"ذاكرة النظام: {stats['system_total_mb']:.0f} MB ({stats['system_used_pct']:.1f}% مستخدم)")
        
        lines.append(f"كائنات gc: {stats.get('gc_objects', 'N/A')}")
        
        if "uptime_seconds" in stats:
            hours = stats['uptime_seconds'] / 3600
            lines.append(f"مدة التشغيل: {hours:.1f} ساعة")
        
        # أعلى تخصيصات
        lines.append("")
        lines.append("أعلى 10 تخصيصات ذاكرة:")
        top = self.get_top_allocations(10)
        for i, (desc, kb) in enumerate(top, 1):
            lines.append(f"  {i}. {desc[:80]} ({kb:.1f} KB)")
        
        if not top:
            lines.append("  (لا بيانات متاحة — tracemalloc غير مفعّل)")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    @property
    def is_monitoring(self) -> bool:
        return self._monitoring
    
    @property
    def peak_mb(self) -> float:
        return self._peak_rss_mb
