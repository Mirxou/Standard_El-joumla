#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبارات خدمة التخزين المؤقت (LRU + TTL + إحصائيات)"""
import time
import os
import pytest
from src.services.cache_service import CacheService


@pytest.fixture
def cache():
    os.environ['CACHE_USE_REDIS'] = '0'
    return CacheService()


def test_ttl_expiration(cache):
    cache.set('general', 'k', 'v', ttl=1)
    assert cache.get('general', 'k') == 'v'
    time.sleep(1.2)
    assert cache.get('general', 'k') is None


def test_stats_hits_misses(cache):
    cache.set('general', 'hit', 'x', ttl=5)
    assert cache.get('general', 'hit') == 'x'
    assert cache.get('general', 'missing') is None
    stats = cache.get_all_stats()['general']
    assert stats['hits'] >= 1
    assert stats['misses'] >= 1


def test_evictions():
    os.environ['CACHE_USE_REDIS'] = '0'
    c = CacheService()
    for i in range(600):
        c.set('products', f'p{i}', i, ttl=5)
    stats = c.get_all_stats()['products']
    assert stats['evictions'] > 0
    assert stats['size'] <= stats['max_size']


def test_top_items(cache):
    for i in range(5):
        cache.set('general', f'k{i}', i, ttl=10)
    cache.get('general', 'k3'); cache.get('general', 'k3'); cache.get('general', 'k2')
    top = cache.caches['general'].get_top_items(limit=3)
    assert len(top) == 3
    # أول عنصر لديه أعلى hits (k3 أو k2 حسب الترتيب)
    assert top[0]['hits'] >= top[1]['hits']

