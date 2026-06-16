"""
Unit Tests for CachingService
اختبارات وحدة CachingService
"""

import pytest

from src.core.caching_service import AdvancedCachingService, CacheEntry, LRUCache


class TestCacheEntry:
    """اختبارات مدخل الـ Cache"""

    def test_cache_entry_init(self):
        """اختبار تهيئة مدخل Cache"""
        entry = CacheEntry("value1", ttl=60)
        assert entry.value == "value1"
        assert entry.ttl == 60

    def test_cache_entry_is_expired(self):
        """اختبار انتهاء صلاحية المدخل"""
        import time

        entry = CacheEntry("value1", ttl=1)
        assert entry.is_expired() is False

        time.sleep(1.1)
        assert entry.is_expired() is True

    def test_cache_entry_get_value(self):
        """اختبار الحصول على القيمة"""
        entry = CacheEntry("value1")
        assert entry.get_value() == "value1"
        assert entry.hits == 1


class TestLRUCache:
    """اختبارات LRU Cache"""

    @pytest.fixture
    def lru_cache(self):
        """إنشاء LRU Cache"""
        return LRUCache(max_size=10)

    def test_init(self, lru_cache):
        """اختبار التهيئة"""
        assert lru_cache.max_size == 10

    def test_get_nonexistent(self, lru_cache):
        """اختبار استرجاع قيمة غير موجودة"""
        value = lru_cache.get("nonexistent_key")
        assert value is None

    def test_set_and_get(self, lru_cache):
        """اختبار الإضافة والاسترجاع"""
        lru_cache.set("key1", "value1", ttl=60)
        value = lru_cache.get("key1")

        assert value == "value1"

    def test_delete(self, lru_cache):
        """اختبار الحذف"""
        lru_cache.set("key1", "value1")
        lru_cache.delete("key1")

        assert lru_cache.get("key1") is None

    def test_clear(self, lru_cache):
        """اختبار مسح الـ Cache"""
        lru_cache.set("key1", "value1")
        lru_cache.set("key2", "value2")

        lru_cache.clear()

        assert lru_cache.get("key1") is None
        assert lru_cache.get("key2") is None

    def test_get_stats(self, lru_cache):
        """اختبار الحصول على الإحصائيات"""
        lru_cache.set("key1", "value1")
        lru_cache.get("key1")
        lru_cache.get("nonexistent")

        stats = lru_cache.get_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats


class TestAdvancedCachingService:
    """اختبارات خدمة التخزين المؤقت المتقدمة"""

    @pytest.fixture
    def caching_service(self):
        """إنشاء خدمة تخزين مؤقت متقدمة"""
        return AdvancedCachingService(max_size=10, enable_disk_cache=False)

    def test_init(self, caching_service):
        """اختبار التهيئة"""
        assert caching_service is not None
        assert caching_service.default_ttl is not None

    def test_get_nonexistent(self, caching_service):
        """اختبار استرجاع قيمة غير موجودة"""
        value = caching_service.get("nonexistent_key")
        assert value is None

    def test_set_and_get(self, caching_service):
        """اختبار الإضافة والاسترجاع"""
        caching_service.set("key1", "value1", ttl=60)
        value = caching_service.get("key1")

        assert value == "value1"

    def test_delete(self, caching_service):
        """اختبار الحذف"""
        caching_service.set("key1", "value1")
        result = caching_service.delete("key1")

        assert result is True
        assert caching_service.get("key1") is None

    def test_clear(self, caching_service):
        """اختبار مسح الـ Cache"""
        caching_service.set("key1", "value1")
        caching_service.set("key2", "value2")

        caching_service.clear()

        assert caching_service.get("key1") is None
        assert caching_service.get("key2") is None
