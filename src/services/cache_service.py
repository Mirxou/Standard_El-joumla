"""
Advanced Cache Service - LRU Cache with TTL
خدمة التخزين المؤقت المتقدمة
"""

from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import logging
import json
import os

try:
    from .cache_backends import RedisCache
    _HAS_REDIS = True
except Exception:
    RedisCache = None  # type: ignore
    _HAS_REDIS = False

class CacheEntry:
    """مدخل ذاكرة التخزين المؤقت"""
    
    def __init__(self, value: Any, ttl: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.hits = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """التحقق من انتهاء الصلاحية"""
        return datetime.now() > self.expires_at
    
    def touch(self):
        """تحديث آخر وصول"""
        self.hits += 1
        self.last_accessed = datetime.now()


class LRUCache:
    """LRU Cache مع TTL ودعم Thread-Safe"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """الحصول على قيمة من الذاكرة المؤقتة"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats['hits'] += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """تعيين قيمة في الذاكرة المؤقتة"""
        with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]
            
            # Check if we need to evict
            while len(self._cache) >= self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats['evictions'] += 1
            
            # Add new entry
            entry = CacheEntry(value, ttl or self.default_ttl)
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """حذف مفتاح من الذاكرة المؤقتة"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """مسح جميع المحتويات"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """تنظيف المدخلات المنتهية"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            self._stats['expirations'] += len(expired_keys)
            return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """الحصول على إحصائيات الذاكرة المؤقتة"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'usage_percent': len(self._cache) / self.max_size * 100,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations']
            }
    
    def get_top_items(self, limit: int = 10) -> list:
        """الحصول على العناصر الأكثر استخداماً"""
        with self._lock:
            items = [
                {
                    'key': key,
                    'hits': entry.hits,
                    'age_seconds': (datetime.now() - entry.created_at).seconds,
                    'last_accessed': entry.last_accessed.isoformat()
                }
                for key, entry in self._cache.items()
            ]
            
            return sorted(items, key=lambda x: x['hits'], reverse=True)[:limit]


class CacheService:
    """خدمة التخزين المؤقت الشاملة"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Multiple caches for different purposes
        use_redis = os.environ.get('CACHE_USE_REDIS', '0') == '1'
        redis_url = os.environ.get('REDIS_URL')
        self.caches = {
            'products': LRUCache(max_size=500, default_ttl=300),      # 5 min
            'customers': LRUCache(max_size=500, default_ttl=300),     # 5 min
            'suppliers': LRUCache(max_size=200, default_ttl=300),     # 5 min
            'users': LRUCache(max_size=100, default_ttl=600),         # 10 min
            'permissions': LRUCache(max_size=100, default_ttl=300),   # 5 min
            'reports': LRUCache(max_size=50, default_ttl=1800),       # 30 min
            'queries': (RedisCache(redis_url, prefix='queries:') if (use_redis and _HAS_REDIS) else LRUCache(max_size=200, default_ttl=60)),
            'general': (RedisCache(redis_url, prefix='general:') if (use_redis and _HAS_REDIS) else LRUCache(max_size=500, default_ttl=300))
        }
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """الحصول من ذاكرة مؤقتة محددة"""
        if cache_name not in self.caches:
            return None
        return self.caches[cache_name].get(key)
    
    def set(self, cache_name: str, key: str, value: Any, ttl: Optional[int] = None):
        """التعيين في ذاكرة مؤقتة محددة"""
        if cache_name not in self.caches:
            cache_name = 'general'
        self.caches[cache_name].set(key, value, ttl)
    
    def delete(self, cache_name: str, key: str) -> bool:
        """حذف من ذاكرة مؤقتة محددة"""
        if cache_name not in self.caches:
            return False
        return self.caches[cache_name].delete(key)
    
    def clear_cache(self, cache_name: str = None):
        """مسح ذاكرة مؤقتة أو جميعها"""
        if cache_name:
            if cache_name in self.caches:
                self.caches[cache_name].clear()
        else:
            for cache in self.caches.values():
                cache.clear()
    
    def get_all_stats(self) -> Dict:
        """الحصول على إحصائيات جميع الذاكرات المؤقتة"""
        stats = {}
        total_stats = {
            'total_size': 0,
            'total_max_size': 0,
            'total_hits': 0,
            'total_misses': 0,
            'total_evictions': 0,
            'total_expirations': 0
        }
        
        for name, cache in self.caches.items():
            cache_stats = cache.get_stats()
            stats[name] = cache_stats
            
            total_stats['total_size'] += cache_stats['size']
            total_stats['total_max_size'] += cache_stats['max_size']
            total_stats['total_hits'] += cache_stats['hits']
            total_stats['total_misses'] += cache_stats['misses']
            total_stats['total_evictions'] += cache_stats['evictions']
            total_stats['total_expirations'] += cache_stats['expirations']
        
        # Calculate overall hit rate
        total_requests = total_stats['total_hits'] + total_stats['total_misses']
        total_stats['overall_hit_rate'] = round(
            (total_stats['total_hits'] / total_requests * 100) if total_requests > 0 else 0,
            2
        )
        
        stats['_totals'] = total_stats
        return stats
    
    def _start_cleanup_thread(self):
        """بدء خيط التنظيف التلقائي"""
        def cleanup_loop():
            import time
            while True:
                time.sleep(60)  # Every minute
                try:
                    for cache in self.caches.values():
                        cache.cleanup_expired()
                except Exception as e:
                    self.logger.error(f"Cache cleanup error: {e}")
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    # Convenience methods for common operations
    
    def cache_product(self, product_id: int, product_data: dict):
        """تخزين منتج مؤقتاً"""
        self.set('products', f'product_{product_id}', product_data)
    
    def get_cached_product(self, product_id: int) -> Optional[dict]:
        """الحصول على منتج مخزن"""
        return self.get('products', f'product_{product_id}')
    
    def cache_customer(self, customer_id: int, customer_data: dict):
        """تخزين عميل مؤقتاً"""
        self.set('customers', f'customer_{customer_id}', customer_data)
    
    def get_cached_customer(self, customer_id: int) -> Optional[dict]:
        """الحصول على عميل مخزن"""
        return self.get('customers', f'customer_{customer_id}')
    
    def cache_query_result(self, query_hash: str, result: Any, ttl: int = 60):
        """تخزين نتيجة استعلام"""
        self.set('queries', f'query_{query_hash}', result, ttl)
    
    def get_cached_query(self, query_hash: str) -> Optional[Any]:
        """الحصول على نتيجة استعلام مخزنة"""
        return self.get('queries', f'query_{query_hash}')
    
    def invalidate_product(self, product_id: int):
        """إلغاء صلاحية منتج مخزن"""
        self.delete('products', f'product_{product_id}')
    
    def invalidate_customer(self, customer_id: int):
        """إلغاء صلاحية عميل مخزن"""
        self.delete('customers', f'customer_{customer_id}')


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """الحصول على خدمة الذاكرة المؤقتة العامة"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
