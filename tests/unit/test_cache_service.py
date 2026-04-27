#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Cache Service
اختبارات خدمة التخزين المؤقت
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.cache_service import CacheService


class TestCacheServiceInitialization:
    """اختبارات تهيئة خدمة التخزين المؤقت"""
    
    def test_initialization_creates_default_caches(self):
        """اختبار التهيئة تنشئ ذاكرات افتراضية"""
        service = CacheService()
        
        assert 'products' in service.caches
        assert 'customers' in service.caches
        assert 'queries' in service.caches
        assert 'general' in service.caches
    
    def test_initialization_starts_cleanup_thread(self):
        """اختبار التهيئة تبدأ خيط التنظيف"""
        with patch('threading.Thread') as mock_thread:
            service = CacheService()
            
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()


class TestGet:
    """اختبارات الحصول على قيمة من الذاكرة"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة جديدة"""
        return CacheService()
    
    def test_get_from_existing_cache(self, service):
        """اختبار الحصول من ذاكرة موجودة"""
        service.set('products', 'test_key', 'test_value')
        
        result = service.get('products', 'test_key')
        
        assert result == 'test_value'
    
    def test_get_from_non_existing_cache(self, service):
        """اختبار الحصول من ذاكرة غير موجودة"""
        result = service.get('non_existing', 'key')
        
        assert result is None
    
    def test_get_non_existing_key(self, service):
        """اختبار الحصول بمفتاح غير موجود"""
        result = service.get('products', 'non_existing_key')
        
        assert result is None
    
    def test_get_with_ttl_expired(self, service):
        """اختبار الحصول مع انتهاء صلاحية TTL"""
        service.set('products', 'key', 'value', ttl=0.01)
        
        import time
        time.sleep(0.02)
        
        result = service.get('products', 'key')
        
        assert result is None


class TestSet:
    """اختبارات تعيين قيمة في الذاكرة"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة جديدة"""
        return CacheService()
    
    def test_set_in_existing_cache(self, service):
        """اختبار التعيين في ذاكرة موجودة"""
        service.set('products', 'key', 'value')
        
        result = service.get('products', 'key')
        assert result == 'value'
    
    def test_set_in_non_existing_cache(self, service):
        """اختبار التعيين في ذاكرة غير موجودة (يستخدم general)"""
        service.set('non_existing', 'key', 'value')
        
        result = service.get('general', 'key')
        assert result == 'value'
    
    def test_set_with_ttl(self, service):
        """اختبار التعيين مع TTL"""
        service.set('products', 'key', 'value', ttl=60)
        
        result = service.get('products', 'key')
        assert result == 'value'
    
    def test_set_overwrites_existing(self, service):
        """اختبار التعيين يكتب فوق القيم الموجودة"""
        service.set('products', 'key', 'old_value')
        service.set('products', 'key', 'new_value')
        
        result = service.get('products', 'key')
        assert result == 'new_value'


class TestDelete:
    """اختبارات حذف من الذاكرة"""
    
    @pytest.fixture
    def service_with_data(self):
        """إنشاء خدمة مع بيانات"""
        service = CacheService()
        service.set('products', 'key1', 'value1')
        service.set('products', 'key2', 'value2')
        return service
    
    def test_delete_existing_key(self, service_with_data):
        """اختبار حذف مفتاح موجود"""
        result = service_with_data.delete('products', 'key1')
        
        assert result is True
        assert service_with_data.get('products', 'key1') is None
    
    def test_delete_non_existing_key(self, service_with_data):
        """اختبار حذف مفتاح غير موجود"""
        result = service_with_data.delete('products', 'non_existing')
        
        assert result is False
    
    def test_delete_from_non_existing_cache(self):
        """اختبار حذف من ذاكرة غير موجودة"""
        service = CacheService()
        
        result = service.delete('non_existing', 'key')
        
        assert result is False


class TestClearCache:
    """اختبارات مسح الذاكرة"""
    
    @pytest.fixture
    def service_with_data(self):
        """إنشاء خدمة مع بيانات"""
        service = CacheService()
        service.set('products', 'key1', 'value1')
        service.set('customers', 'key2', 'value2')
        service.set('general', 'key3', 'value3')
        return service
    
    def test_clear_specific_cache(self, service_with_data):
        """اختبار مسح ذاكرة محددة"""
        service_with_data.clear_cache('products')
        
        assert service_with_data.get('products', 'key1') is None
        assert service_with_data.get('customers', 'key2') == 'value2'
    
    def test_clear_all_caches(self, service_with_data):
        """اختبار مسح كل الذاكرات"""
        service_with_data.clear_cache()
        
        assert service_with_data.get('products', 'key1') is None
        assert service_with_data.get('customers', 'key2') is None
        assert service_with_data.get('general', 'key3') is None
    
    def test_clear_non_existing_cache(self, service_with_data):
        """اختبار مسح ذاكرة غير موجودة"""
        # يجب أن لا يرفع استثناء
        service_with_data.clear_cache('non_existing')


class TestGetAllStats:
    """اختبارات الحصول على إحصائيات كل الذاكرات"""
    
    @pytest.fixture
    def service_with_data(self):
        """إنشاء خدمة مع بيانات"""
        service = CacheService()
        service.set('products', 'key1', 'value1')
        service.get('products', 'key1')  # hit
        service.get('products', 'non_existing')  # miss
        return service
    
    def test_get_all_stats_structure(self, service_with_data):
        """اختبار بنية الإحصائيات"""
        stats = service_with_data.get_all_stats()
        
        assert 'products' in stats
        assert 'customers' in stats
        assert '_totals' in stats
    
    def test_get_all_stats_totals(self, service_with_data):
        """اختبار الإجماليات في الإحصائيات"""
        stats = service_with_data.get_all_stats()
        
        assert 'total_size' in stats['_totals']
        assert 'total_max_size' in stats['_totals']
        assert 'total_hits' in stats['_totals']
        assert 'total_misses' in stats['_totals']
        assert 'overall_hit_rate' in stats['_totals']
    
    def test_get_all_stats_empty_service(self):
        """اختبار إحصائيات خدمة فارغة"""
        service = CacheService()
        
        stats = service.get_all_stats()
        
        assert stats['_totals']['total_size'] == 0
        assert stats['_totals']['overall_hit_rate'] == 0


class TestConvenienceMethods:
    """اختبارات الطرق المختصرة"""
    
    @pytest.fixture
    def service(self):
        """إنشاء خدمة جديدة"""
        return CacheService()
    
    def test_cache_and_get_product(self, service):
        """اختبار تخزين والحصول على منتج"""
        product_data = {'id': 1, 'name': 'Test Product', 'price': 100.0}
        
        service.cache_product(1, product_data)
        result = service.get_cached_product(1)
        
        assert result == product_data
    
    def test_cache_and_get_customer(self, service):
        """اختبار تخزين والحصول على عميل"""
        customer_data = {'id': 1, 'name': 'Test Customer'}
        
        service.cache_customer(1, customer_data)
        result = service.get_cached_customer(1)
        
        assert result == customer_data
    
    def test_cache_and_get_query(self, service):
        """اختبار تخزين والحصول على نتيجة استعلام"""
        query_result = {'data': [1, 2, 3]}
        
        service.cache_query_result('hash123', query_result)
        result = service.get_cached_query('hash123')
        
        assert result == query_result
    
    def test_invalidate_product(self, service):
        """اختبار إلغاء صلاحية منتج"""
        service.cache_product(1, {'name': 'Test'})
        
        service.invalidate_product(1)
        
        result = service.get_cached_product(1)
        assert result is None


class TestCacheBackends:
    """اختبارات مخزنات الذاكرة - LRUCache هو الكلاس الفعلي"""
    
    def test_memory_cache_initialization(self):
        """اختبار تهيئة LRUCache"""
        from src.services.cache_service import LRUCache
        
        cache = LRUCache(max_size=100)
        
        assert cache.max_size == 100
        # LRUCache has no .size attr; size is via get_stats()['size']
        assert cache.get_stats()['size'] == 0
    
    def test_memory_cache_get_and_set(self):
        """اختبار تعيين والحصول من LRUCache"""
        from src.services.cache_service import LRUCache
        
        cache = LRUCache()
        cache.set('key', 'value')
        
        result = cache.get('key')
        
        assert result == 'value'
    
    def test_memory_cache_ttl_expiration(self):
        """اختبار انتهاء صلاحية TTL"""
        from src.services.cache_service import LRUCache
        import time
        
        cache = LRUCache()
        cache.set('key', 'value', ttl=0.01)
        
        time.sleep(0.02)
        
        result = cache.get('key')
        assert result is None
    
    def test_memory_cache_delete(self):
        """اختبار الحذف من LRUCache"""
        from src.services.cache_service import LRUCache
        
        cache = LRUCache()
        cache.set('key', 'value')
        
        result = cache.delete('key')
        
        assert result is True
        assert cache.get('key') is None
    
    def test_memory_cache_clear(self):
        """اختبار مسح LRUCache"""
        from src.services.cache_service import LRUCache
        
        cache = LRUCache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        cache.clear()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None
    
    def test_memory_cache_get_stats(self):
        """اختبار الحصول على إحصائيات LRUCache"""
        from src.services.cache_service import LRUCache
        
        cache = LRUCache(max_size=100)
        cache.set('key', 'value')
        cache.get('key')  # hit
        cache.get('non_existing')  # miss
        
        stats = cache.get_stats()
        
        assert stats['size'] == 1
        assert stats['max_size'] == 100
        assert stats['hits'] == 1
        assert stats['misses'] == 1
    
    def test_memory_cache_eviction_when_full(self):
        """اختبار الإزالة عند امتلاء LRUCache"""
        from src.services.cache_service import LRUCache
        
        cache = LRUCache(max_size=2)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')  # يجب أن يزيل key1
        
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'


class TestCleanupThread:
    """اختبارات خيط التنظيف"""
    
    def test_cleanup_thread_start(self):
        """اختبار بدء خيط التنظيف"""
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            service = CacheService()
            
            mock_thread.assert_called_once()
            assert mock_thread.call_args[1]['daemon'] is True
            mock_thread_instance.start.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



