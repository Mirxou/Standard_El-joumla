"""
Optional cache backends (Redis).
Provides RedisCache if redis library and REDIS_URL are available.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    import redis

    _REDIS_AVAILABLE = True
except Exception:
    redis = None  # type: ignore
    _REDIS_AVAILABLE = False


class RedisCache:
    def __init__(self, url: Optional[str] = None, prefix: str = "cache:"):
        if not _REDIS_AVAILABLE:
            raise ImportError("redis library not available")
        self.url = url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix.rstrip(":") + ":"
        self.client = redis.Redis.from_url(self.url, decode_responses=False)
        # Simple stats counters (approximate)
        self._hits = 0
        self._misses = 0

    def _k(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        val = self.client.get(self._k(key))
        if val is None:
            self._misses += 1
            return None
        self._hits += 1
        try:
            import pickle
            import hmac
            import hashlib

            if len(val) < 32:
                return val

            signature = val[:32]
            serialized_data = val[32:]

            secret = os.environ.get("APP_ENCRYPTION_KEY", "StandardElJoumlaERPSecureHMACDefaultKey").encode()
            expected_signature = hmac.new(secret, serialized_data, hashlib.sha256).digest()

            if not hmac.compare_digest(signature, expected_signature):
                return val

            return pickle.loads(serialized_data)
        except Exception:
            return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        try:
            import pickle
            import hmac
            import hashlib

            serialized_data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            secret = os.environ.get("APP_ENCRYPTION_KEY", "StandardElJoumlaERPSecureHMACDefaultKey").encode()
            signature = hmac.new(secret, serialized_data, hashlib.sha256).digest()
            data = signature + serialized_data
        except Exception:
            data = value
        if ttl and ttl > 0:
            self.client.set(self._k(key), data, ex=int(ttl))
        else:
            self.client.set(self._k(key), data)

    def delete(self, key: str) -> bool:
        return bool(self.client.delete(self._k(key)))

    def clear(self):
        # Danger: only delete keys with our prefix
        cursor = 0
        pattern = f"{self.prefix}*"
        while True:
            cursor, keys = self.client.scan(cursor=cursor, match=pattern, count=1000)
            if keys:
                self.client.delete(*keys)
            if cursor == 0:
                break

    def cleanup_expired(self) -> int:
        # Redis handles expirations automatically; nothing to do.
        return 0

    def get_stats(self) -> Dict:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total else 0.0
        return {
            "size": None,
            "max_size": None,
            "usage_percent": None,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": None,
            "expirations": None,
        }

    def get_top_items(self, limit: int = 10):
        # Not tracked for Redis; return empty for now.
        return []
