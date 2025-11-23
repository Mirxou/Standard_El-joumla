#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار التبديل الاختياري بين Redis و LRU fallback"""
import os
import importlib
from src.services.cache_service import CacheService

def test_redis_disabled_fallback_lru(monkeypatch):
    monkeypatch.setenv('CACHE_USE_REDIS', '0')
    c = CacheService()
    # queries/general يجب أن تكون من نوع LRUCache
    assert hasattr(c.caches['queries'], 'set') and hasattr(c.caches['queries'], '_cache')
    assert hasattr(c.caches['general'], 'set') and hasattr(c.caches['general'], '_cache')

def test_redis_enabled_without_library(monkeypatch):
    # محاكاة عدم توفر redis حتى لو تم تفعيل المتغير
    monkeypatch.setenv('CACHE_USE_REDIS', '1')
    monkeypatch.delenv('REDIS_URL', raising=False)
    # إزالة الوحدة إذا كانت مستوردة
    if 'redis' in importlib.sys.modules:
        del importlib.sys.modules['redis']
    c = CacheService()
    # يجب أن يسقط إلى LRUCache
    assert hasattr(c.caches['queries'], '_cache')

