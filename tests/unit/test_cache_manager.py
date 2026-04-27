"""
Unit Tests for CacheManager
اختبارات وحدة CacheManager
"""

import pytest
import time
from src.core.cache_manager import CacheManager, CacheEntry


class TestCacheEntry:
    """اختبارات مدخل الـ Cache"""
    
    def test_cache_entry_init(self):
        """اختبار تهيئة مدخل Cache"""
        entry = CacheEntry("key1", "value1", ttl=60)
        assert entry.key == "key1"
        assert entry.value == "value1"
        assert entry.ttl == 60
        assert entry.hits == 0
    
    def test_cache_entry_is_expired(self):
        """اختبار انتهاء الصلاحية بعد مرور الوقت"""
        import time
        from unittest.mock import patch
        
        entry = CacheEntry(key="test", value="value", ttl=10)
        
        # في البداية غير منتهي الصلاحية
        assert entry.is_expired() is False
        
        # محاكاة مرور الوقت
        with patch('time.time', return_value=entry.created_at + 20):
            assert entry.is_expired() is True
    
    def test_cache_entry_never_expires(self):
        """اختبار مدخل لا ينتهي أبداً"""
        entry = CacheEntry("key1", "value1", ttl=0)
        time.sleep(0.1)
        assert entry.is_expired() is False
    
    def test_cache_entry_touch(self):
        """اختبار تحديث وقت آخر استخدام"""
        entry = CacheEntry("key1", "value1")
        initial_hits = entry.hits
        
        entry.touch()
        assert entry.hits == initial_hits + 1
        assert entry.last_access > 0


class TestCacheManager:
    """اختبارات مدير الـ Cache"""
    
    @pytest.fixture
    def cache_manager(self):
        """إنشاء مدير Cache"""
        return CacheManager(max_size=10, default_ttl=60)
    
    def test_init(self, cache_manager):
        """اختبار التهيئة"""
        assert cache_manager.max_size == 10
        assert cache_manager.default_ttl == 60
        assert cache_manager.get_stats()['hits'] == 0
        assert cache_manager.get_stats()['misses'] == 0
    
    def test_set_and_get(self, cache_manager):
        """اختبار الإضافة والاسترجاع"""
        cache_manager.set("key1", "value1")
        value = cache_manager.get("key1")
        
        assert value == "value1"
        assert cache_manager.get_stats()['hits'] == 1
    
    def test_get_nonexistent(self, cache_manager):
        """اختبار استرجاع مفتاح غير موجود"""
        value = cache_manager.get("nonexistent")
        
        assert value is None
        assert cache_manager.get_stats()['misses'] == 1
    
    def test_expiration(self, cache_manager):
        """اختبار انتهاء الصلاحية"""
        cache_manager.set("key1", "value1", ttl=1)
        assert cache_manager.get("key1") == "value1"
        
        time.sleep(1.1)
        # بعد انتهاء الصلاحية، القيمة يجب أن تكون None
        assert cache_manager.get("key1") is None
    
    def test_delete(self, cache_manager):
        """اختبار الحذف"""
        cache_manager.set("key1", "value1")
        cache_manager.delete("key1")
        
        assert cache_manager.get("key1") is None
    
    def test_clear(self, cache_manager):
        """اختبار مسح الـ Cache"""
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        
        cache_manager.clear()
        
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
    
    def test_max_size_eviction(self, cache_manager):
        """اختبار إزالة العناصر عند الوصول للحد الأقصى"""
        # إضافة عناصر أكثر من الحد الأقصى
        for i in range(12):
            cache_manager.set(f"key{i}", f"value{i}")
        
        # العناصر الأولى يجب أن تُزال (LRU)
        assert cache_manager.get("key0") is None
        assert cache_manager.get("key1") is None
        assert cache_manager.get_stats()['evictions'] >= 2
    
    def test_get_stats(self, cache_manager):
        """اختبار الحصول على الإحصائيات"""
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")
        cache_manager.get("nonexistent")
        
        stats = cache_manager.get_stats()
        
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'evictions' in stats
        assert 'expirations' in stats
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
    
    def test_exists(self, cache_manager):
        """اختبار التحقق من وجود مفتاح"""
        cache_manager.set("key1", "value1")
        
        assert cache_manager.exists("key1") is True
        assert cache_manager.exists("nonexistent") is False




