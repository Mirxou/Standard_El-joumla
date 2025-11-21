"""
مدير التخزين المؤقت (Cache Manager)

نظام تخزين مؤقت ذكي لتحسين الأداء:
- تخزين نتائج الاستعلامات الشائعة
- TTL (Time To Live) قابل للتخصيص
- إدارة ذاكرة ذكية (LRU - Least Recently Used)
- إحصائيات أداء Cache
"""

from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import time


class CacheEntry:
    """مدخل واحد في الـ Cache"""
    
    def __init__(self, key: str, value: Any, ttl: int = 300):
        """
        Args:
            key: مفتاح المدخل
            value: القيمة المخزنة
            ttl: مدة الصلاحية بالثواني (افتراضي: 5 دقائق)
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.hits = 0
        self.last_access = time.time()
    
    def is_expired(self) -> bool:
        """التحقق من انتهاء صلاحية المدخل"""
        if self.ttl <= 0:  # 0 = never expire
            return False
        return (time.time() - self.created_at) > self.ttl
    
    def touch(self):
        """تحديث وقت آخر استخدام"""
        self.hits += 1
        self.last_access = time.time()


class CacheManager:
    """مدير التخزين المؤقت الذكي"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: الحد الأقصى لعدد المدخلات
            default_ttl: مدة الصلاحية الافتراضية بالثواني
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    # ==================== العمليات الأساسية ====================
    
    def get(self, key: str) -> Optional[Any]:
        """
        استرجاع قيمة من الـ Cache
        
        Args:
            key: المفتاح
        
        Returns:
            القيمة إن وجدت، None غير ذلك
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                self._remove(key)
                self._stats['misses'] += 1
                self._stats['expirations'] += 1
                return None
            
            # Update LRU order
            self._cache.move_to_end(key)
            entry.touch()
            self._stats['hits'] += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        حفظ قيمة في الـ Cache
        
        Args:
            key: المفتاح
            value: القيمة
            ttl: مدة الصلاحية (اختياري)
        """
        with self._lock:
            # Remove if exists
            if key in self._cache:
                self._remove(key)
            
            # Check size limit
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Add new entry
            ttl_value = ttl if ttl is not None else self.default_ttl
            entry = CacheEntry(key, value, ttl_value)
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        حذف مدخل من الـ Cache
        
        Returns:
            True إذا تم الحذف، False إذا لم يكن موجوداً
        """
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self):
        """مسح جميع المدخلات"""
        with self._lock:
            self._cache.clear()
    
    def exists(self, key: str) -> bool:
        """التحقق من وجود مفتاح"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                self._remove(key)
                self._stats['expirations'] += 1
                return False
            
            return True
    
    # ==================== التخزين المؤقت مع Callback ====================
    
    def get_or_set(self, key: str, callback: Callable[[], Any], 
                   ttl: Optional[int] = None) -> Any:
        """
        استرجاع من الـ Cache أو تنفيذ callback وحفظ النتيجة
        
        Args:
            key: المفتاح
            callback: دالة للحصول على القيمة إذا لم تكن موجودة
            ttl: مدة الصلاحية
        
        Returns:
            القيمة من الـ Cache أو من الـ callback
        """
        # Try to get from cache
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Execute callback
        value = callback()
        
        # Store in cache
        self.set(key, value, ttl)
        
        return value
    
    # ==================== التنظيف ====================
    
    def cleanup_expired(self) -> int:
        """
        تنظيف المدخلات المنتهية الصلاحية
        
        Returns:
            عدد المدخلات المحذوفة
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self._remove(key)
                self._stats['expirations'] += 1
            
            return len(expired_keys)
    
    def _evict_lru(self):
        """إزالة المدخل الأقل استخداماً (LRU)"""
        if self._cache:
            # OrderedDict maintains insertion order
            # First item is the least recently used
            key, _ = self._cache.popitem(last=False)
            self._stats['evictions'] += 1
    
    def _remove(self, key: str):
        """إزالة مدخل من الـ Cache"""
        if key in self._cache:
            del self._cache[key]
    
    # ==================== الإحصائيات ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات الأداء
        
        Returns:
            Dict مع الإحصائيات
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'total_requests': total_requests
            }
    
    def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        with self._lock:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expirations': 0
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        تقدير استهلاك الذاكرة
        
        Returns:
            Dict مع معلومات الذاكرة
        """
        import sys
        
        with self._lock:
            total_size = sys.getsizeof(self._cache)
            
            for entry in self._cache.values():
                total_size += sys.getsizeof(entry)
                total_size += sys.getsizeof(entry.value)
            
            return {
                'total_bytes': total_size,
                'total_kb': round(total_size / 1024, 2),
                'total_mb': round(total_size / (1024 * 1024), 2),
                'entries': len(self._cache)
            }
    
    # ==================== Namespaces ====================
    
    def get_namespaced_key(self, namespace: str, key: str) -> str:
        """إنشاء مفتاح مع namespace"""
        return f"{namespace}:{key}"
    
    def clear_namespace(self, namespace: str) -> int:
        """
        مسح جميع المدخلات في namespace محدد
        
        Returns:
            عدد المدخلات المحذوفة
        """
        with self._lock:
            prefix = f"{namespace}:"
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.startswith(prefix)
            ]
            
            for key in keys_to_delete:
                self._remove(key)
            
            return len(keys_to_delete)


# ==================== Cache Decorators ====================

def cached(cache_manager: CacheManager, ttl: int = 300, key_prefix: str = ""):
    """
    Decorator للتخزين المؤقت لنتائج الدوال
    
    Args:
        cache_manager: مدير الـ Cache
        ttl: مدة الصلاحية
        key_prefix: بادئة للمفتاح
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            
            # Add args to key
            for arg in args:
                key_parts.append(str(arg))
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# ==================== Global Cache Instance ====================

# يمكن استخدامه مباشرة عبر التطبيق
global_cache = CacheManager(max_size=1000, default_ttl=300)
