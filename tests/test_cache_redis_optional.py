import os
import pytest

from src.services.cache_service import CacheService


@pytest.mark.skipif(os.environ.get('CACHE_USE_REDIS') != '1' or not os.environ.get('REDIS_URL'), reason='Redis not enabled')
def test_cache_with_redis_backend():
    svc = CacheService()
    # will use Redis for 'general' if configured
    svc.set('general', 'it', {'a': 1}, ttl=2)
    assert svc.get('general', 'it') == {'a': 1}
