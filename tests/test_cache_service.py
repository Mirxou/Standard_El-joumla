import time
from src.services.cache_service import CacheService

def test_cache_set_get_expire():
    cache = CacheService()
    cache.set('general', 'k', 'v', ttl=1)
    assert cache.get('general', 'k') == 'v'
    time.sleep(1.2)
    assert cache.get('general', 'k') is None

