#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis Cache Manager for API
مدير Redis Cache للـ API
"""

import os
import hashlib
import json
from typing import Optional, Any, Callable, Dict
from functools import wraps
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCacheManager:
    """مدير Redis Cache للـ API"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        تهيئة مدير Redis Cache
        
        Args:
            redis_url: عنوان Redis (افتراضي: من متغير البيئة)
        """
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis library not available - caching disabled")
            return
        
        try:
            self.client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info(f"✅ Redis Cache enabled: {self.redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed - caching disabled: {e}")
            self.client = None
            self.enabled = False
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """
        إنشاء مفتاح cache من المعاملات
        
        Args:
            prefix: بادئة المفتاح
            *args: معاملات إضافية
            **kwargs: معاملات مفتاحية
            
        Returns:
            مفتاح cache
        """
        # إنشاء hash من المعاملات
        key_parts = [prefix]
        
        # Helper to safely hash anything
        def safe_repr(obj):
            if isinstance(obj, (dict, list, set)):
                try:
                    return json.dumps(obj, sort_keys=True, default=str)
                except Exception:
                    return str(obj)
            return str(obj)

        if args:
            # Convert args to string representation for hashing
            args_repr = tuple(safe_repr(a) for a in args)
            key_parts.append(str(hash(args_repr)))
        
        if kwargs:
            # ترتيب kwargs للحصول على نفس المفتاح لنفس المعاملات
            sorted_items = sorted(kwargs.items())
            kwargs_repr = tuple((k, safe_repr(v)) for k, v in sorted_items)
            key_parts.append(str(hash(kwargs_repr)))
        
        key_string = ":".join(key_parts)
        return f"api:{key_string}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        الحصول من Cache
        
        Args:
            key: مفتاح Cache
            
        Returns:
            القيمة المخزنة أو None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data is None:
                return None
            
            # Deserialize JSON
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            logger.warning(f"⚠️ Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        حفظ في Cache
        
        Args:
            key: مفتاح Cache
            value: القيمة للحفظ
            ttl: مدة الصلاحية بالثواني (افتراضي: 5 دقائق)
            
        Returns:
            True إذا نجح، False خلاف ذلك
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            # Serialize to JSON
            data = json.dumps(value, default=str, ensure_ascii=False)
            self.client.setex(key, ttl, data.encode('utf-8'))
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        حذف من Cache
        
        Args:
            key: مفتاح Cache
            
        Returns:
            True إذا نجح، False خلاف ذلك
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.warning(f"⚠️ Redis delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        حذف جميع المفاتيح المطابقة للنمط
        
        Args:
            pattern: نمط البحث (مثل "api:products:*")
            
        Returns:
            عدد المفاتيح المحذوفة
        """
        if not self.enabled or not self.client:
            return 0
        
        try:
            count = 0
            for key in self.client.scan_iter(match=pattern):
                self.client.delete(key)
                count += 1
            return count
        except Exception as e:
            logger.warning(f"⚠️ Redis delete_pattern error: {e}")
            return 0
    
    def clear_cache(self, prefix: str = "api:") -> int:
        """
        مسح جميع Cache
        
        Args:
            prefix: بادئة المفاتيح (افتراضي: "api:")
            
        Returns:
            عدد المفاتيح المحذوفة
        """
        return self.delete_pattern(f"{prefix}*")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات Cache
        
        Returns:
            قاموس بالإحصائيات
        """
        if not self.enabled or not self.client:
            return {
                "enabled": False,
                "keys": 0,
                "memory": 0
            }
        
        try:
            info = self.client.info('memory')
            keys = len(list(self.client.scan_iter(match="api:*")))
            
            return {
                "enabled": True,
                "keys": keys,
                "memory": info.get('used_memory_human', '0B'),
                "redis_url": self.redis_url
            }
        except Exception as e:
            logger.warning(f"⚠️ Redis stats error: {e}")
            return {
                "enabled": False,
                "error": str(e)
            }


# Global instance
_cache_manager: Optional[RedisCacheManager] = None


def get_cache_manager() -> RedisCacheManager:
    """الحصول على مثيل Cache Manager (Singleton)"""
    global _cache_manager
    if _cache_manager is None:
        redis_url = os.environ.get('REDIS_URL')
        _cache_manager = RedisCacheManager(redis_url)
    return _cache_manager


def cached(prefix: str = "api", ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator لإضافة Caching للـ endpoints
    
    Args:
        prefix: بادئة المفتاح
        ttl: مدة الصلاحية بالثواني (افتراضي: 5 دقائق)
        key_func: دالة مخصصة لإنشاء المفتاح (اختياري)
    
    Example:
        @router.get("/products")
        @cached(prefix="products", ttl=300)
        async def get_products():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # إنشاء مفتاح Cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # استخدام prefix + function name + arguments
                func_name = func.__name__
                cache_key = cache_manager._make_key(f"{prefix}:{func_name}", *args, **kwargs)
            
            # محاولة الحصول من Cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"✅ Cache HIT: {cache_key}")
                # تسجيل Metric
                try:
                    from src.api.metrics import record_cache_operation
                    record_cache_operation("get", prefix, "hit")
                except Exception:
                    pass
                return cached_value
            
            # تنفيذ الدالة
            logger.debug(f"❌ Cache MISS: {cache_key}")
            result = await func(*args, **kwargs) if hasattr(func, '__call__') else func(*args, **kwargs)
            
            # تسجيل Metric
            try:
                from src.api.metrics import record_cache_operation
                record_cache_operation("get", prefix, "miss")
            except Exception:
                pass
            
            # حفظ في Cache
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator لإبطال Cache عند تحديث البيانات
    
    Args:
        pattern: نمط المفاتيح لإبطالها (مثل "products:*")
    
    Example:
        @router.post("/products")
        @invalidate_cache("products:*")
        async def create_product():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # تنفيذ الدالة أولاً
            result = await func(*args, **kwargs) if hasattr(func, '__call__') else func(*args, **kwargs)
            
            # إبطال Cache
            cache_manager = get_cache_manager()
            deleted = cache_manager.delete_pattern(pattern)
            if deleted > 0:
                logger.info(f"🗑️ Invalidated {deleted} cache keys matching '{pattern}'")
            
            return result
        
        return wrapper
    return decorator

