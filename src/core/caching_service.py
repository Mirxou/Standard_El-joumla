#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التخزين المؤقت (Caching Service)
نظام caching متقدم لتحسين الأداء
"""

import time
import json
import pickle
import hashlib
from typing import Any, Optional, Callable, Dict, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from collections import OrderedDict
import threading


class CacheEntry:
    """إدخال في الذاكرة المؤقتة"""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        """
        Args:
            value: القيمة المخزنة
            ttl: مدة الصلاحية بالثواني (None = لا انتهاء)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.hits = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """التحقق من انتهاء الصلاحية"""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl
    
    def get_value(self) -> Any:
        """الحصول على القيمة مع تحديث الإحصائيات"""
        self.hits += 1
        self.last_accessed = time.time()
        return self.value


class LRUCache:
    """
    Least Recently Used Cache
    يحذف العناصر الأقل استخداماً عند امتلاء الذاكرة
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Args:
            max_size: الحجم الأقصى للذاكرة المؤقتة
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        
        # إحصائيات
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'sets': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        الحصول على قيمة من الذاكرة المؤقتة
        
        Args:
            key: المفتاح
            
        Returns:
            القيمة أو None إذا لم تُوجد أو انتهت صلاحيتها
        """
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # التحقق من الصلاحية
            if entry.is_expired():
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # نقل للنهاية (الأكثر استخداماً)
            self.cache.move_to_end(key)
            
            self.stats['hits'] += 1
            return entry.get_value()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        حفظ قيمة في الذاكرة المؤقتة
        
        Args:
            key: المفتاح
            value: القيمة
            ttl: مدة الصلاحية بالثواني
        """
        with self.lock:
            # إذا كان موجوداً، تحديث
            if key in self.cache:
                del self.cache[key]
            
            # إذا امتلأت، حذف الأقدم
            elif len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
            
            # إضافة جديد
            self.cache[key] = CacheEntry(value, ttl)
            self.stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """
        حذف قيمة من الذاكرة المؤقتة
        
        Returns:
            True إذا تم الحذف
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """مسح جميع المحتويات"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الاستخدام"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self.stats,
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }
    
    def cleanup_expired(self) -> int:
        """
        تنظيف العناصر المنتهية الصلاحية
        
        Returns:
            عدد العناصر المحذوفة
        """
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)


class AdvancedCachingService:
    """
    خدمة التخزين المؤقت المتقدمة
    
    المزايا:
    - LRU Cache في الذاكرة
    - دعم TTL (Time To Live)
    - Cache للاستعلامات
    - Cache للنتائج الحسابية
    - إحصائيات الاستخدام
    - التنظيف التلقائي
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,  # ساعة واحدة
        enable_disk_cache: bool = False,
        disk_cache_path: str = "data/cache"
    ):
        """
        تهيئة خدمة التخزين المؤقت
        
        Args:
            max_size: الحجم الأقصى للذاكرة
            default_ttl: مدة الصلاحية الافتراضية
            enable_disk_cache: تفعيل التخزين على القرص
            disk_cache_path: مسار التخزين على القرص
        """
        # LRU Cache رئيسي
        self.cache = LRUCache(max_size)
        
        # إعدادات
        self.default_ttl = default_ttl
        self.enable_disk_cache = enable_disk_cache
        
        # مسار التخزين على القرص
        if enable_disk_cache:
            self.disk_cache_path = Path(disk_cache_path)
            self.disk_cache_path.mkdir(parents=True, exist_ok=True)
        else:
            self.disk_cache_path = None
        
        # بادئات لتمييز أنواع البيانات
        self.PREFIX_QUERY = "query:"
        self.PREFIX_PRODUCT = "product:"
        self.PREFIX_CUSTOMER = "customer:"
        self.PREFIX_REPORT = "report:"
        self.PREFIX_STATS = "stats:"
    
    # ==================== الوظائف الأساسية ====================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        الحصول على قيمة
        
        Args:
            key: المفتاح
            default: القيمة الافتراضية إذا لم تُوجد
            
        Returns:
            القيمة المخزنة أو القيمة الافتراضية
        """
        value = self.cache.get(key)
        
        # إذا لم تُوجد في الذاكرة، محاولة القرص
        if value is None and self.enable_disk_cache:
            value = self._load_from_disk(key)
            if value is not None:
                # إعادة للذاكرة
                self.cache.set(key, value, self.default_ttl)
        
        return value if value is not None else default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        save_to_disk: bool = False
    ) -> None:
        """
        حفظ قيمة
        
        Args:
            key: المفتاح
            value: القيمة
            ttl: مدة الصلاحية (None = استخدام الافتراضي)
            save_to_disk: حفظ على القرص أيضاً
        """
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache.set(key, value, ttl)
        
        # حفظ على القرص
        if save_to_disk and self.enable_disk_cache:
            self._save_to_disk(key, value)
    
    def delete(self, key: str, delete_from_disk: bool = True) -> bool:
        """حذف قيمة"""
        # حذف من الذاكرة
        deleted = self.cache.delete(key)
        
        # حذف من القرص
        if delete_from_disk and self.enable_disk_cache:
            self._delete_from_disk(key)
        
        return deleted
    
    def clear(self, clear_disk: bool = False) -> None:
        """مسح جميع المحتويات"""
        self.cache.clear()
        
        if clear_disk and self.enable_disk_cache and self.disk_cache_path:
            for cache_file in self.disk_cache_path.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass
    
    # ==================== Decorators ====================
    
    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = "",
        key_func: Optional[Callable] = None
    ):
        """
        ديكوريتور لتخزين نتائج الدوال مؤقتاً
        
        Args:
            ttl: مدة الصلاحية
            key_prefix: بادئة المفتاح
            key_func: دالة لإنشاء المفتاح من المعاملات
            
        Example:
            >>> cache = AdvancedCachingService()
            >>> @cache.cached(ttl=60, key_prefix="calc:")
            >>> def expensive_calculation(x, y):
            ...     return x ** y
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # إنشاء مفتاح فريد من المعاملات
                if key_func:
                    cache_key = key_prefix + key_func(*args, **kwargs)
                else:
                    cache_key = key_prefix + self._generate_key(func.__name__, args, kwargs)
                
                # محاولة الحصول من الذاكرة المؤقتة
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # تنفيذ الدالة
                result = func(*args, **kwargs)
                
                # حفظ النتيجة
                self.set(cache_key, result, ttl or self.default_ttl)
                
                return result
            
            return wrapper
        return decorator
    
    # ==================== Cache متخصصة ====================
    
    def cache_query_result(
        self,
        query: str,
        params: tuple,
        result: Any,
        ttl: int = 300  # 5 دقائق
    ) -> None:
        """
        تخزين نتيجة استعلام قاعدة البيانات
        
        Args:
            query: نص الاستعلام
            params: معاملات الاستعلام
            result: النتيجة
            ttl: مدة الصلاحية
        """
        key = self._hash_query(query, params)
        self.set(self.PREFIX_QUERY + key, result, ttl)
    
    def get_cached_query_result(
        self,
        query: str,
        params: tuple
    ) -> Optional[Any]:
        """الحصول على نتيجة استعلام مخزنة"""
        key = self._hash_query(query, params)
        return self.get(self.PREFIX_QUERY + key)
    
    def cache_product(self, product_id: int, product_data: dict, ttl: int = 600) -> None:
        """تخزين بيانات منتج"""
        key = f"{self.PREFIX_PRODUCT}{product_id}"
        self.set(key, product_data, ttl)
    
    def get_cached_product(self, product_id: int) -> Optional[dict]:
        """الحصول على بيانات منتج مخزنة"""
        key = f"{self.PREFIX_PRODUCT}{product_id}"
        return self.get(key)
    
    def invalidate_product(self, product_id: int) -> None:
        """إلغاء صلاحية cache منتج (عند التحديث)"""
        key = f"{self.PREFIX_PRODUCT}{product_id}"
        self.delete(key)
    
    def cache_customer(self, customer_id: int, customer_data: dict, ttl: int = 600) -> None:
        """تخزين بيانات عميل"""
        key = f"{self.PREFIX_CUSTOMER}{customer_id}"
        self.set(key, customer_data, ttl)
    
    def get_cached_customer(self, customer_id: int) -> Optional[dict]:
        """الحصول على بيانات عميل مخزنة"""
        key = f"{self.PREFIX_CUSTOMER}{customer_id}"
        return self.get(key)
    
    def cache_report(self, report_type: str, filters: dict, data: Any, ttl: int = 1800) -> None:
        """تخزين تقرير (التقارير قد تكون مكلفة حسابياً)"""
        key = f"{self.PREFIX_REPORT}{report_type}:{self._hash_dict(filters)}"
        self.set(key, data, ttl)
    
    def get_cached_report(self, report_type: str, filters: dict) -> Optional[Any]:
        """الحصول على تقرير مخزن"""
        key = f"{self.PREFIX_REPORT}{report_type}:{self._hash_dict(filters)}"
        return self.get(key)
    
    # ==================== وظائف مساعدة ====================
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """إنشاء مفتاح فريد من اسم الدالة ومعاملاتها"""
        key_parts = [func_name]
        
        if args:
            key_parts.append(str(args))
        
        if kwargs:
            key_parts.append(str(sorted(kwargs.items())))
        
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _hash_query(self, query: str, params: tuple) -> str:
        """إنشاء hash للاستعلام ومعاملاته"""
        query_str = f"{query}|{params}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _hash_dict(self, data: dict) -> str:
        """إنشاء hash لقاموس"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _save_to_disk(self, key: str, value: Any) -> bool:
        """حفظ على القرص"""
        if not self.disk_cache_path:
            return False
        
        try:
            # تنظيف المفتاح لاسم ملف آمن
            safe_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = self.disk_cache_path / f"{safe_key}.cache"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            return True
        except Exception:
            return False
    
    def _load_from_disk(self, key: str) -> Optional[Any]:
        """تحميل من القرص"""
        if not self.disk_cache_path:
            return None
        
        try:
            safe_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = self.disk_cache_path / f"{safe_key}.cache"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    
    def _delete_from_disk(self, key: str) -> bool:
        """حذف من القرص"""
        if not self.disk_cache_path:
            return False
        
        try:
            safe_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = self.disk_cache_path / f"{safe_key}.cache"
            
            if cache_file.exists():
                cache_file.unlink()
                return True
        except Exception:
            pass
        
        return False
    
    # ==================== إحصائيات وصيانة ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الاستخدام"""
        return self.cache.get_stats()
    
    def cleanup(self) -> int:
        """تنظيف العناصر المنتهية الصلاحية"""
        return self.cache.cleanup_expired()


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    print("=" * 70)
    print("⚡ اختبار خدمة التخزين المؤقت")
    print("=" * 70)
    
    # إنشاء الخدمة
    cache = AdvancedCachingService(max_size=100, default_ttl=60)
    
    # 1. الاستخدام الأساسي
    print("\n1️⃣ الاستخدام الأساسي:")
    cache.set("user:1", {"name": "أحمد", "email": "ahmad@example.com"})
    user = cache.get("user:1")
    print(f"   المستخدم: {user}")
    
    # 2. استخدام Decorator
    print("\n2️⃣ استخدام Decorator:")
    
    @cache.cached(ttl=30, key_prefix="calc:")
    def expensive_calculation(x: int, y: int) -> int:
        print(f"   🔄 تنفيذ الحساب: {x} ** {y}")
        time.sleep(0.1)  # محاكاة عملية مكلفة
        return x ** y
    
    # أول استدعاء - سيُنفذ
    result1 = expensive_calculation(5, 3)
    print(f"   النتيجة الأولى: {result1}")
    
    # ثاني استدعاء - من الذاكرة المؤقتة
    result2 = expensive_calculation(5, 3)
    print(f"   النتيجة الثانية (من cache): {result2}")
    
    # 3. cache للاستعلامات
    print("\n3️⃣ تخزين نتائج الاستعلامات:")
    query = "SELECT * FROM products WHERE id = ?"
    params = (1,)
    result = {"id": 1, "name": "منتج تجريبي", "price": 100}
    
    cache.cache_query_result(query, params, result)
    cached = cache.get_cached_query_result(query, params)
    print(f"   النتيجة المخزنة: {cached}")
    
    # 4. الإحصائيات
    print("\n4️⃣ إحصائيات الاستخدام:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ اكتملت جميع الاختبارات بنجاح!")
    print("=" * 70)
